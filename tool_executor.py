from typing import Any

# Load environment variables from a .env file
from dotenv import load_dotenv

load_dotenv()

# Import the TavilySearch tool for web search capabilities
from langchain_tavily import TavilySearch

# Import StructuredTool for defining tools with structured input/output
from langchain_core.tools import StructuredTool

# Import ToolNode for executing tools within a LangGraph workflow
from langgraph.prebuilt import ToolNode

# Import custom Pydantic schemas for answer and revision handling
from schemas import AnswerQuestion, ReviseAnswer

# Initialize the TavilySearch tool with a maximum of 5 results per query
tavily_tool = TavilySearch(max_results=5)

def run_queries(search_queries: list[str], **kwargs) -> Any:
    """
    Run a batch of search queries using the TavilySearch tool.

    Args:
        search_queries (list[str]): A list of search query strings.
        **kwargs: Additional keyword arguments (not used here).

    Returns:
        The results from the TavilySearch batch query.
    """
    # NOTE: There is a typo in 'bacth' - should be 'batch' if using TavilySearch API.
    return tavily_tool.batch([{"query": query} for query in search_queries])

# Define a ToolNode that can execute tools for answering and revising questions.
# Each tool is wrapped as a StructuredTool for structured input/output.
execute_tools = ToolNode(
    [
        StructuredTool.from_function(
            func=run_queries,
            name=AnswerQuestion.__name__  # Uses the name of the AnswerQuestion schema
        ),
        StructuredTool.from_function(
            func=run_queries,
            name=ReviseAnswer.__name__    # Uses the name of the ReviseAnswer schema
        ),
    ]
)
