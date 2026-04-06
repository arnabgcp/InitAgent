import datetime
from zoneinfo import ZoneInfo
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.agents import Agent
import requests
import asyncio


def get_weather(city: str) -> str:
    """
    Retrieves the current temperature for a specified city.
    
    Args:
        city: The name of the city (e.g., 'London', 'New York').
    
    Returns:
        A string describing the current temperature in Celsius.
    """
    try:
        # Geocoding: Get coordinates
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url).json()
        
        if "results" not in geo_res:
            return f"Could not find coordinates for {city}."
            
        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]

        # Weather: Get temperature
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url).json()
        
        temp = weather_res["current_weather"]["temperature"]
        return f"The current temperature in {city} is {temp}°C."
    except Exception as e:
        return f"Error retrieving weather: {str(e)}"

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """

    if city.lower() != "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}

# @title Define Tools for Greeting and Farewell Agents
from typing import Optional # Make sure to import Optional

# Ensure 'get_weather' from Step 1 is available if running this step independently.
# def get_weather(city: str) -> dict: ... (from Step 1)

def say_hello(name: Optional[str] = None) -> str:
    """Provides a simple greeting. If a name is provided, it will be used.

    Args:
        name (str, optional): The name of the person to greet. Defaults to a generic greeting if not provided.

    Returns:
        str: A friendly greeting message.
    """
    if name:
        greeting = f"Hello, {name}!"
        print(f"--- Tool: say_hello called with name: {name} ---")
    else:
        greeting = "Hello there!" # Default greeting if name is None or not explicitly passed
        print(f"--- Tool: say_hello called without a specific name (name_arg_value: {name}) ---")
    return greeting

def say_goodbye() -> str:
    """Provides a simple farewell message to conclude the conversation."""
    print(f"--- Tool: say_goodbye called ---")
    
    return "Goodbye! Have a great day."

greeting_agent = Agent(
        # Using a potentially different/cheaper model for a simple task
        model="gemini-2.5-flash",
        # model=LiteLlm(model=MODEL_GPT_4O), # If you would like to experiment with other models
        name="greeting_agent",
        instruction="You are the Greeting Agent. Your ONLY task is to provide a friendly greeting to the user. "
                    "Use the 'say_hello' tool to generate the greeting. "
                    "If the user provides their name, make sure to pass it to the tool. "
                    "Do not engage in any other conversation or tasks.",
        description="Handles simple greetings and hellos using the 'say_hello' tool.", # Crucial for delegation
        tools=[say_hello],
)

farewell_agent = Agent(
        # Can use the same or a different model
        model="gemini-2.5-flash",
        # model=LiteLlm(model=MODEL_GPT_4O), # If you would like to experiment with other models
        name="farewell_agent",
        instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message. "
                    "Use the 'say_goodbye' tool when the user indicates they are leaving or ending the conversation "
                    "(e.g., using words like 'bye', 'goodbye', 'thanks bye', 'see you'). "
                    "Do not perform any other actions.",
        description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.", # Crucial for delegation
        tools=[say_goodbye],
)

from google.adk.tools import google_search  # Import the tool

# stream_agent = Agent(
#    # A unique name for the agent.
#    name="basic_search_agent",
#    # The Large Language Model (LLM) that agent will use.
#    # Please fill in the latest model id that supports live from
#    # https://google.github.io/adk-docs/get-started/streaming/quickstart-streaming/#supported-models
#    model="gemini-3-flash-preview",
#    # A short description of the agent's purpose.
#    description="Agent to answer questions using Google Search.",
#    # Instructions to set the agent's behavior.
#    instruction="You are an expert researcher. You always stick to the facts.",
#    # Add google_search tool to perform grounding with Google search.
#    tools=[google_search]
# )

root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.5-flash",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    # instruction=(
    #     "You are a helpful agent who can answer user questions about the time and weather in a city. Also you can answer other questions too based on LLM response."
    #     "if no tool applies to the user's request, provide a direct answer based on your internal capabilities"
    # ),
    instruction="You are the main Weather Agent coordinating a team. Your primary responsibility is to provide weather information. "
                    "Use the 'get_weather' tool ONLY for specific weather requests (e.g., 'weather in London'). "
                    "You have specialized sub-agents: "
                    "1. 'greeting_agent': Handles simple greetings like 'Hi', 'Hello'. Delegate to it for these. "
                    "2. 'farewell_agent': Handles simple farewells like 'Bye', 'See you'. Delegate to it for these. "
                    "Analyze the user's query. If it's a greeting, delegate to 'greeting_agent'. If it's a farewell "
                    "If it's a weather request, handle it yourself using 'get_weather'. "
                    "For anything else, respond appropriately or state you cannot handle it."
                    "if no tool applies to the user's request, provide a direct answer based on your internal capabilities",
    tools=[get_weather, get_current_time],
    sub_agents=[greeting_agent, farewell_agent],
)

from google.adk.a2a.utils.agent_to_a2a import to_a2a
# Existing agent code here...

# Wrap the agent to make it A2A-compliant
a2a_app = to_a2a(root_agent)