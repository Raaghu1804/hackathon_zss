from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.rotary_kiln_agent.agent import rotary_kiln_agent
from .sub_agents.clinker_cooler_agent.agent import clinker_cooler_agent
from .sub_agents.pre_calciner_agent.agent import pre_calciner_agent
from .tools.tools import get_current_time

root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash",
    description="Manager agent",
    instruction="""
    You are a cement plant manager agent that is responsible for overseeing the cement manufacturing.
    You need to check analomolies and reduce power consumption and should create an ideal parameters for cement manufaturing

    Always delegate the task to the appropriate agent. Use your best judgement 
    to determine which agent to delegate to.

    You are responsible for delegating tasks to the following agent:
    - pre_calciner_agent
    - rotary_kiln_agent
    - clinker_cooler_agent
    """,
    sub_agents=[rotary_kiln_agent, clinker_cooler_agent,pre_calciner_agent],
    # tools=[
    #     AgentTool(news_analyst),
    #     get_current_time,
    # ],
)
