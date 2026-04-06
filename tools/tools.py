import pandas as pd
from google.adk.tools.base_tool import BaseTool
from google.cloud.bigquery import SchemaField
import json
import subprocess
import os
import gcsfs
import google.auth


    
class SchemaInferenceTool(BaseTool):
        """A tool to infer the BigQuery schema from a source file."""

        def __init__(self):
            super().__init__(
                name="schema_inference",
                description="Infers the BigQuery schema from a source file (CSV or JSON).",
            )

        def call(self, file_path: str) -> list[dict]:
            """
            Infers the BigQuery schema from a source file.

            Args:
                file_path: The path to the source file.

            Returns:
                A list of dictionaries, where each dictionary represents a BigQuery SchemaField.
            """
            fs = None
            if file_path.startswith("gs://"):
                fs = gcsfs.GCSFileSystem()

            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path, storage_options={'fs': fs})
            elif file_path.endswith(".json"):
                df = pd.read_json(file_path, lines=True, storage_options={'fs': fs})  # Assuming JSONL format
            else:
                return {"error": f"Unsupported file type: {file_path}"}

            schema = []
            for column, dtype in df.dtypes.items():
                if pd.api.types.is_integer_dtype(dtype):
                    bq_type = "INTEGER"
                elif pd.api.types.is_float_dtype(dtype):
                    bq_type = "FLOAT"
                elif pd.api.types.is_bool_dtype(dtype):
                    bq_type = "BOOLEAN"
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    bq_type = "TIMESTAMP"
                else:
                    bq_type = "STRING"
                schema.append({"name": column, "type": bq_type, "mode": "NULLABLE"})

            return schema

class PipelineGeneratorTool(BaseTool):
        """A tool to generate an Apache Beam pipeline script."""

        def __init__(self):
            super().__init__(
                name="pipeline_generator",
                description="Generates an Apache Beam pipeline script.",
            )

        def call(self, source_file_path: str, schema: list[dict], bq_table: str = None) -> str:
            """
            Generates an Apache Beam pipeline script.

            Args:
                source_file_path: The path to the source file.
                schema: The BigQuery table schema.
                bq_table: Optional. The BigQuery table in "dataset.table" format. If not provided, it will be inferred.

            Returns:
                The path to the generated pipeline script.
            """
            credentials, default_project_id = google.auth.default()
            project_id = os.environ.get("GCP_PROJECT_ID", default_project_id)

            if not bq_table:
                dataset_id = os.environ.get("BQ_DATASET_ID", "my_dataset")
                table_name = os.path.splitext(os.path.basename(source_file_path))[0]
                bq_table = f"{dataset_id}.{table_name}"

            schema_str = ", ".join([f"{s['name']}:{s['type']}" for s in schema])

            if source_file_path.endswith(".csv"):
                read_transform = f"beam.io.ReadFromText('{source_file_path}', skip_header_lines=1)"
                parse_and_validate_transforms = f"""
        | 'SplitRows' >> beam.Map(lambda line: line.split(','))
        | 'ValidateRows' >> beam.ParDo(ValidateRow(expected_columns={len(schema)}))
        | 'ToDict' >> beam.Map(lambda fields: dict(zip({json.dumps([s['name'] for s in schema])}, fields)))
"""
            elif source_file_path.endswith(".json"):
                read_transform = f"beam.io.ReadFromText('{source_file_path}')"
                # For JSON, we can add a validation for required keys if needed in the future
                parse_and_validate_transforms = f"""
        | 'ParseJSON' >> beam.Map(lambda line: json.loads(line))
"""
            else:
                return "Error: Unsupported file type for pipeline generation. Only .csv and .json are supported."

            pipeline_code = f"""
    import apache_beam as beam
    from apache_beam.options.pipeline_options import PipelineOptions
    import json

    class ValidateRow(beam.DoFn):
        \"\"\"A DoFn to validate that each row has the expected number of columns.\"\"\"
        def __init__(self, expected_columns):
            self.expected_columns = expected_columns

        def process(self, element):
            if len(element) == self.expected_columns:
                yield element
            # Malformed rows can be sent to a dead-letter queue for inspection
            # For now, we just drop them.
            # yield beam.pvalue.TaggedOutput('malformed_rows', element)


    def run():
        options = PipelineOptions(
            project='{project_id}',
        )
        with beam.Pipeline(options=options) as p:
            (
                p
                | 'ReadData' >> {read_transform}
                {parse_and_validate_transforms} | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
                    table='{project_id}:{bq_table}',
                    schema='{schema_str}',
                    write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
                    create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                )
            )

    if __name__ == '__main__':
        run()
    """
            pipeline_file_path = "transform_pipeline.py"
            with open(pipeline_file_path, "w") as f:
                f.write(pipeline_code)

            return pipeline_file_path


class DataflowJobRunnerTool(BaseTool):
        """A tool to run a Dataflow job."""

        def __init__(self):
            super().__init__(
                name="dataflow_job_runner",
                description="Runs a Dataflow job.",
            )

        def call(self, pipeline_file_path: str) -> str:
            """
            Runs a Dataflow job.

            Args:
                pipeline_file_path: The path to the pipeline script.

            Returns:
                The job ID of the running job.
            """
            credentials, default_project_id = google.auth.default()
            project_id = os.environ.get("GCP_PROJECT_ID", default_project_id)
            region = os.environ.get("GCP_REGION")
            temp_location = os.environ.get("GCS_TEMP_LOCATION")
            command = [
                "python",
                pipeline_file_path,
                f"--project={project_id}",
                f"--region={region}",
                "--runner=DataflowRunner",
                f"--temp_location={temp_location}",
            ]
            
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                return f"Error running Dataflow job: {stderr.decode()}"

            job_id = None
            output = stderr.decode() # Dataflow job info often goes to stderr
            for line in output.splitlines():
                if "New job is" in line:
                    job_id = line.split("New job is: ")[1].strip()
                    break
                elif "jobId" in line: # Fallback for different output formats
                    job_id = line.split("jobId: ")[1].strip()
                    break

            return f"Successfully launched Dataflow job. Job ID: {job_id}" if job_id else f"Could not determine job ID from output: {output}"
