from dotenv import load_dotenv

from logger import log_info, log_success, log_error, log_warning, log_header

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
#print(graph.get_graph().draw_mermaid())
#graph.get_graph().print_ascii()

if __name__ == "__main__":
    #query = "Investiga acerca de la industria de telecomunicaciones en México y la reglementación en el sector"
    query = "Investiga las mejores prácticas para gestionar los domicilios de instalación desde el proceso de ventas hasta el de instalación en una empresa de telecomunicaciones que ofrece servicios de internet?"
    log_header("---🤖 Sistema de Agentes IA de Investigación Procesando...")
    log_info(f"---🤖 Agente IA Investigando --> {query}")

    res = graph.invoke(
        query
    )
    log_success("---🤖 Agente IA --> Aquí está la investigación\n")
    log_info(res[-1].tool_calls[0]["args"]["answer"])
    #log_info("Referencias:")
    for i, ref in enumerate(res[-1].tool_calls[0]["args"]["references"], 1):
        log_info(f"[{i}]. {ref}")
    #    log_info(f"{i}. {ref}")
