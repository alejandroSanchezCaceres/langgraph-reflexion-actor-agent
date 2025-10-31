from dotenv import load_dotenv

from logger import log_info, log_success, log_error, log_warning, log_header

load_dotenv()

from typing import List

from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import END, MessageGraph

from chains import first_responder, revisor
from tool_executor import execute_tools

# Número máximo de iteraciones del agente
MAX_ITERATIONS = 2

builder = MessageGraph()
builder.add_node("responder", first_responder)
builder.add_node("execute_tools", execute_tools)
builder.add_node("revisor", revisor)

# Conceta los nodos
builder.add_edge("responder", "execute_tools")
builder.add_edge("execute_tools", "revisor")

# Evalua la iteración de la investigación
def event_loop(state: List[BaseMessage]) -> str:
    count_tool_visits = sum(isinstance(m, ToolMessage) for m in state)
    if count_tool_visits >= MAX_ITERATIONS:
        return END
    return "execute_tools"

# Condiciona transiciones entre nodos
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
    
    query = "Investiga acerca de la industria de telecomunicaciones en México y la reglementación en el sector"
    #query = "Investiga las mejores prácticas para gestionar los domicilios de instalación duarante el proceso de Venta para un serivicio de Internet"
    
    
    
    log_header("---🤖 Agentes IA de Investigación Procesando...")
    log_info(f"---🤖 Agentes IA Investigando acerca de --> {query}")

    res = graph.invoke(
        query
    )

    log_success("---🤖 Agente IA --> Resultados de la investigación\n")
    # Respuesta
    log_info(res[-1].tool_calls[0]["args"]["answer"])
    
    # Referencias
    #for i, ref in enumerate(res[-1].tool_calls[0]["args"]["references"], 1):
    #    log_warning(f"[{i}]. {ref}")
    
