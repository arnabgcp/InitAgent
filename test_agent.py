from agent import get_root_agent
import os
import dotenv

dotenv.load_dotenv()

def main():
    """Tests the root agent and the data engineer agent."""

    # This prompt simulates a user request to the root agent.
    prompt = (
        "Please process the data file 'sample_data.csv' and load it into a BigQuery table "
        "named 'my_test_dataset.my_test_table'."
    )

    # Get the root agent
    root_agent = get_root_agent()

    # Invoke the agent
    response = root_agent.call(prompt)

    # Print the agent's response
    print(response)

if __name__ == "__main__":
    main()
