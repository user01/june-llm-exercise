from agno.agent import Agent
from agno.team.team import Team
from agno.tools.duckdb import DuckDbTools
from agno.models.base import Model
from exercise_tooling.prompts import COORDINATOR, ANALYSIS, SQL_AGENT


def generate_team(model: Model, database_path: str) -> Team:
    duck = DuckDbTools(db_path=database_path)

    agent_data = Agent(
        name="Data Agent",
        role="Provide access to the duckdb Monthly Prescription Drug Plan Formulary and Pharmacy Network Information database.",
        model=model,
        tools=[duck],
        show_tool_calls=True,
        system_message=SQL_AGENT,
    )

    agent_analysis = Agent(
        name="Analysis Agent",
        role="Provide detailed analysis to answer questions when provided with data",
        model=model,
        system_message=ANALYSIS,
    )

    team = Team(
        name="Medical Data Analysis Team",
        mode="coordinate",
        model=model,
        members=[agent_data, agent_analysis],
        system_message=COORDINATOR,
        # enable_agentic_context=True,  # Allow the agent to maintain a shared context and send that to members.
        # share_member_interactions=True,  # Share all member responses with subsequent member requests.
        # show_tool_calls=True,
        markdown=True,
        instructions="You are running a team of expert medical data analysts. You will work together to collect data to answer the user's questions directly, correctly, and properly sourced.",
        # show_members_responses=True,
        success_criteria="Produce clear and direct answers to the user's questions based on the available data.",
    )
    return team
