
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
import google.auth
import dotenv

dotenv.load_dotenv()

credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=credentials)
bigquery_toolset = BigQueryToolset(
  credentials_config=credentials_config
)

root_agent = Agent(
 model="gemini-2.5-flash",
 name="bigquery_agent",
 description="Agent that answers questions about BigQuery data by executing SQL queries.",
 instruction=(
     """
       You are a BigQuery data analysis agent.
       You are able to answer questions on table stored in tabel:wayfair-test-378605.wc_procurement_public_data.statewide_Contract_MasterContract_SalesData_by_Customer_Contract_Vendor on the `procurement` dataset.
     """
 ),
 tools=[bigquery_toolset]
)

def get_bigquery_agent():
 return root_agent

from google.adk.a2a.utils.agent_to_a2a import to_a2a
# Existing agent code here...

# Wrap the agent to make it A2A-compliant
a2a_app = to_a2a(root_agent)