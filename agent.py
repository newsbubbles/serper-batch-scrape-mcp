# PydanticAI Agent with MCP

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from dotenv import load_dotenv
import os

load_dotenv()

import logfire
if os.getenv("LOGFIRE_API_KEY"):
    logfire.configure(token=os.getenv("LOGFIRE_API_KEY"))
    logfire.instrument_openai()

# Set up OpenRouter based model
API_KEY = os.getenv('OPENROUTER_API_KEY')
if not API_KEY:
    print("Warning: OPENROUTER_API_KEY environment variable not set")
    print("Using local Claude model if available instead")
    from pydantic_ai.models.claude import ClaudeModel
    model = ClaudeModel("claude-3-5-sonnet")
else:
    model = OpenAIModel(
        'anthropic/claude-3.5-sonnet',
        provider=OpenAIProvider(
            base_url='https://openrouter.ai/api/v1', 
            api_key=API_KEY
        ),
    )

# MCP Environment variables
env = {
    "SERPER_API_KEY": os.getenv("SERPER_API_KEY"),
}

if not os.getenv("SERPER_API_KEY"):
    print("Warning: SERPER_API_KEY environment variable not set")
    print("Google search functionality will not work")

# Set the path to the MCP server - this assumes we're running from the project root
mcp_path = os.path.join(os.getcwd(), "mcp_server.py")
mcp_servers = [
    MCPServerStdio('python', [mcp_path], env=env),
]

from datetime import datetime, timezone

# Set up Agent with Server
agent_name = "SerperScraperAgent"
def load_agent_prompt(agent:str):
    """Loads given agent replacing `time_now` var with current time"""
    print(f"Loading {agent}")
    time_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    agent_path = os.path.join(os.getcwd(), "agents", f"{agent}.md")
    with open(agent_path, "r") as f:
        agent_prompt = f.read()
    agent_prompt = agent_prompt.replace('{time_now}', time_now)
    return agent_prompt

# Load up the agent system prompt
agent_prompt = load_agent_prompt(agent_name)
print(f"Loaded agent prompt for {agent_name}")
agent = Agent(model, mcp_servers=mcp_servers, system_prompt=agent_prompt)

import random, traceback
import asyncio

async def main():
    """CLI testing in a conversation with the agent"""
    async with agent.run_mcp_servers(): 

        message_history = []
        result = None

        print("\nSerperScraperAgent ready! Type your message (Ctrl+C to exit)\n")
        while True:
            if result:
                print(f"\n{result.output}")
            user_input = input("\n> ")
            result = None
            err = None
            for i in range(0, 3):
                try:
                    result = await agent.run(
                        user_input, 
                        message_history=message_history
                    )
                    break
                except Exception as e:
                    err = e
                    traceback.print_exc()
                    if len(message_history) > 2:
                        message_history.pop(0)
                    await asyncio.sleep(2)
            if result is None:
                print(f"\nError {err}. Try again...\n")
                continue
            message_history.extend(result.new_messages())
            while len(message_history) > 6:
                message_history.pop(0)

        
if __name__ == "__main__":
    asyncio.run(main())
