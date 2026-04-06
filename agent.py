from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from .tools.tools import SchemaInferenceTool, PipelineGeneratorTool, DataflowJobRunnerTool
import google.auth
import dotenv, os


dotenv.load_dotenv()

credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=credentials)
bigquery_toolset = BigQueryToolset(
  credentials_config=credentials_config,
)


# To guide the agent's focus, we place the primary workflow tools first in the list,
# followed by the comprehensive but secondary toolset.
all_tools = [
    SchemaInferenceTool(),
    PipelineGeneratorTool(),
    DataflowJobRunnerTool(),
    bigquery_toolset,
]

root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="A data engineering agent that can create and manage data pipelines.",
    instruction="""You are an automated data engineering agent. Your only goal is to create a Dataflow pipeline from a source file to a BigQuery table. 
        You must follow these steps sequentially and without asking for information you can derive yourself.

        **Execution Plan:**
        1.  **Immediately** use the `schema_inference` tool on the user-provided source file. **Do not ask for the schema.**
        2.  Use the `pipeline_generator` tool. If the user did not provide a BigQuery table name, the tool will create one for you. You have the schema from the previous step.
        3.  Use the `dataflow_job_runner` tool to execute the generated pipeline script.
        4.  Use the `get_table_info` and `execute_sql` tools to verify that the pipeline job was successful and the data is in BigQuery.

        Do not ask for project ID, region, or temp locations; they are in the environment. 
        Start the process as soon as the user provides a source file.""",
    tools=all_tools,
)

def get_root_agent():
 return root_agent

from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Wrap the agent to make it A2A-compliant
a2a_app = to_a2a(root_agent)
