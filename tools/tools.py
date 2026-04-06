import pandas as pd
from google.adk.tools.base_tool import BaseTool
from google.cloud.bigquery import SchemaField
import json
import subprocess
import os
import google.auth


def SchemaInferenceTool():
    
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
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith(".json"):
                df = pd.read_json(file_path, lines=True)  # Assuming JSONL format
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

def PipelineGeneratorTool():
    class PipelineGeneratorTool(BaseTool):
        """A tool to generate an Apache Beam pipeline script."""

        def __init__(self):
            super().__init__(
                name="pipeline_generator",
                description="Generates an Apache Beam pipeline script.",
            )

        def call(self, source_file_path: str, bq_table: str, schema: list[dict]) -> str:
            """
            Generates an Apache Beam pipeline script.

            Args:
                source_file_path: The path to the source file.
                bq_table: The BigQuery table name in the format "dataset.table".
                schema: The BigQuery table schema.

            Returns:
                The path to the generated pipeline script.
            """
            credentials, default_project_id = google.auth.default()
            project_id = os.environ.get("GCP_PROJECT_ID", default_project_id)
            schema_str = ", ".join([f"{s['name']}:{s['type']}" for s in schema])
            
            pipeline_code = f"""
    import apache_beam as beam
    from apache_beam.options.pipeline_options import PipelineOptions

    def run():
        options = PipelineOptions(
            project='{project_id}',
        )
        with beam.Pipeline(options=options) as p:
            (
                p
                | 'ReadData' >> beam.io.ReadFromText('{source_file_path}', skip_header_lines=1)
                | 'ParseCSV' >> beam.Map(lambda line: dict(zip({json.dumps([s['name'] for s in schema])}, line.split(','))))
                | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
                    table=f'{{project_id}}:{bq_table}',
                    schema='{schema_str}',
                    write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
                    create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
                )
            )

    if __name__ == '__main__':
        run()
    """
            pipeline_file_path = "transform_pipeline.py"
            with open(pipeline_file_path, "w") as f:
                f.write(pipeline_code)

            return pipeline_file_path

def DataflowJobRunnerTool():
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

            # This is a simplified way to get the job ID.
            # In a real-world scenario, you would want to parse the output more reliably.
            job_id = None
            for line in stdout.decode().splitlines():
                if "jobId" in line:
                    job_id = line.split("jobId: ")[1]
                    break
            
            return job_id
