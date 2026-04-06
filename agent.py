from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.agent_tool import AgentTool
from tools.tools import SchemaInferenceTool, PipelineGeneratorTool, DataflowJobRunnerTool
import google.auth
import dotenv

dotenv.load_dotenv()

credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=credentials)
bigquery_toolset = BigQueryToolset(
  credentials_config=credentials_config
)


schema_inference_tool = SchemaInferenceTool()
pipeline_generator_tool = PipelineGeneratorTool()
dataflow_job_runner_tool = DataflowJobRunnerTool()

data_engineer_agent = Agent(
    model="gemini-2.5-flash",
    name="data_engineer_agent",
    description="Specialized in data modeling, cleaning, and creating Dataflow-to-BigQuery pipelines.",
    instruction=(
        "You are a Senior Data Engineer. Your goal is to automate the end-to-end process of ingesting raw data "
        "from multiple sources, transforming it, and loading it into BigQuery via Dataflow. "
        "You have the following tools at your disposal:\n"
        "- A tool to infer the schema of a source file.\n"
        "- A tool to generate a Python script for an Apache Beam pipeline.\n"
        "- A tool to run a Dataflow job using the generated pipeline script. "
        "The project ID, region, and temporary GCS location for the Dataflow job are configured in the environment.\n"
        "- A BigQuery toolset for creating tables and running verification queries."
    ),
    tools=[
        bigquery_toolset,
        schema_inference_tool,
        pipeline_generator_tool,
        dataflow_job_runner_tool,
    ]
)

root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="A root agent that can delegate tasks to other agents.",
    instruction=(
        "You are a root agent. You can delegate tasks to other agents. "
        "You have a data engineer agent that can handle data engineering tasks like creating tables and running Dataflow jobs. "
        "You also have a BigQuery data analysis agent that can answer questions about BigQuery data."
    ),
    tools=[
        bigquery_toolset,
        data_engineer_agent,
    ]
)

def get_root_agent():
 return root_agent

from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Wrap the agent to make it A2A-compliant
a2a_app = to_a2a(root_agent)