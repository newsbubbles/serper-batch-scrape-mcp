# PydanticAI Agent with MCP

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.agent import AgentRunResult

from dotenv import load_dotenv
import os
import asyncio
import traceback
import argparse
from datetime import datetime, timezone

load_dotenv()

# Configure logfire if API key is available
import logfire
if os.getenv("LOGFIRE_API_KEY"):
    logfire.configure(token=os.getenv("LOGFIRE_API_KEY"))
    logfire.instrument_openai()

# Set up argument parser
parser = argparse.ArgumentParser(description='Serper Scraper Batch Agent')
parser.add_argument('--model', type=str, default='anthropic/claude-3.7-sonnet',
                    help='Model string to use (default: anthropic/claude-3.7-sonnet)')
args = parser.parse_args()

# Set up OpenRouter based model with the model string from arguments
API_KEY = os.getenv('OPENROUTER_API_KEY')
model = OpenAIModel(
    args.model,
    provider=OpenAIProvider(
        base_url='https://openrouter.ai/api/v1', 
        api_key=API_KEY
    ),
)

# Print the model being used
print(f"Using model: {args.model}")

# MCP Environment variables
env = {
    "SERPER_API_KEY": os.getenv("SERPER_API_KEY"),
}

if not os.getenv("SERPER_API_KEY"):
    print("Warning: SERPER_API_KEY environment variable not set")
    print("Google search functionality will not work")

# Use script_dir for more reliable path handling
script_dir = os.path.dirname(os.path.abspath(__file__))
mcp_path = os.path.join(script_dir, "mcp_server.py")

mcp_servers = [
    MCPServerStdio('python', [mcp_path], env=env),
]

# Set up Agent with Server
agent_name = "SerperScraperAgent"

def load_agent_prompt(agent: str) -> str:
    """Loads given agent replacing `time_now` var with current time"""
    print(f"Loading {agent}")
    time_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    agent_path = os.path.join(script_dir, "agents", f"{agent}.md")
    with open(agent_path, "r") as f:
        agent_prompt = f.read()
    agent_prompt = agent_prompt.replace('{time_now}', time_now)
    return agent_prompt

# Load up the agent system prompt
agent_prompt = load_agent_prompt(agent_name)
print(f"Loaded agent prompt for {agent_name}")
agent = Agent(model, mcp_servers=mcp_servers, system_prompt=agent_prompt)

async def main():
    """CLI testing in a conversation with the agent"""
    async with agent.run_mcp_servers(): 
        result = None

        print("\nSerperScraperAgent ready! Type your message (Ctrl+C to exit)\n")
        while True:
            if result:
                print(f"\n{result.output}")
            user_input = input("\n> ")
            err = None
            
            # Retry logic for resilience
            for i in range(0, 3):
                try:
                    # Use the Agent's built-in message management
                    result = await agent.run(
                        user_input, 
                        message_history=None if result is None else result.all_messages()
                    )
                    break
                except Exception as e:
                    err = e
                    traceback.print_exc()
                    await asyncio.sleep(2)
                    
            if result is None:
                print(f"\nError {err}. Try again...\n")
                continue

if __name__ == "__main__":
    asyncio.run(main())
