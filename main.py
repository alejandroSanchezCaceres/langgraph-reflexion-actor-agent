from dotenv import load_dotenv

load_dotenv()

from typing import List

from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import END, MessageGraph

from chains import first_responder, revisor
from tool_executor import execute_tools

MAX_ITERATIONS = 2
builder = MessageGraph()
builder.add_node("responder", first_responder)
builder.add_node("execute_tools", execute_tools)
builder.add_node("revisor", revisor)

builder.add_edge("responder", "execute_tools")
builder.add_edge("execute_tools", "revisor")


def event_loop(state: List[BaseMessage]) -> str:
    count_tool_visits = sum(isinstance(m, ToolMessage) for m in state)
    if count_tool_visits >= MAX_ITERATIONS:
        return END
    return "execute_tools"


builder.add_conditional_edges(
    "revisor",
    event_loop,
    {
        "execute_tools": "execute_tools",
        END: END,
    },
)

builder.set_entry_point("responder")
graph = builder.compile()
print(graph.get_graph().draw_mermaid())
graph.get_graph().print_ascii()

if __name__ == "__main__":
    print("Hello, Replexion Agent!")
    res = graph.invoke(
        "Write about AI-Powered SOC / autonomous soc  problem domain, list startups that do that and raised capital."
    )
    print(res[-1].tool_calls[0]["args"]["answer"])
    print(res)
