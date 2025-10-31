# Referencia de API

Documentación detallada de todas las funciones, clases y módulos del proyecto LangGraph Reflection Actor Agent.

## Módulos

### `main.py`

Punto de entrada principal y configuración del grafo de LangGraph.

#### Variables

- **`MAX_ITERATIONS`** (int): Número máximo de iteraciones del agente. Por defecto: `2`.

#### Funciones

##### `event_loop(state: List[BaseMessage]) -> str`

Función de control que evalúa si el agente debe continuar iterando o finalizar.

**Parámetros:**
- `state` (List[BaseMessage]): Lista de mensajes en el estado actual del grafo.

**Retorna:**
- `str`: `"execute_tools"` si debe continuar iterando, `END` si debe finalizar.

**Lógica:**
- Cuenta el número de `ToolMessage` en el estado.
- Si el conteo es mayor o igual a `MAX_ITERATIONS`, retorna `END`.
- De lo contrario, retorna `"execute_tools"` para continuar la iteración.

#### Objetos Exportados

- **`graph`**: Grafo compilado de LangGraph listo para ejecución.

### `chains.py`

Módulo que define las cadenas de procesamiento LLM y templates de prompts.

#### Variables

##### `llm`

Instancia de `ChatOpenAI` configurada con el modelo especificado en la variable de entorno `OPENAI_MODEL` o `gpt-5-nano` por defecto.

##### `parser`

Instancia de `JsonOutputToolsParser` configurada con `return_id=True`.

##### `parser_pydantic`

Instancia de `PydanticToolsParser` configurada con las herramientas `[AnswerQuestion]`.

##### `actor_prompt_template`

Template base de prompts para el actor investigador.

**Estructura:**
- Mensaje del sistema con instrucciones dinámicas
- `{time}`: Timestamp actual en formato ISO
- `{first_instruction}`: Instrucción específica del nodo
- Placeholder para mensajes históricos
- Instrucción final para formatear la respuesta

##### `first_responder_prompt_template`

Template de prompt para el primer respondedor, extendiendo `actor_prompt_template` con:
- `first_instruction`: `"Provide a detailed ~500 word answer."`

##### `first_responder`

Cadena de procesamiento que genera la respuesta inicial.

**Flujo:**
```
first_responder_prompt_template → llm.bind_tools(tools=[AnswerQuestion], tool_choice="AnswerQuestion")
```

**Input:** Mensajes de usuario (HumanMessage)
**Output:** AIMessage con tool_calls estructurados según `AnswerQuestion`.

##### `revisor`

Cadena de procesamiento que revisa y mejora respuestas.

**Instrucciones de revisión:**
- Revisar la respuesta anterior usando nueva información
- Usar la crítica previa para agregar información importante
- Incluir citas numéricas en la respuesta revisada
- Remover información superflua
- Asegurar que no exceda 500 palabras

**Flujo:**
```
actor_prompt_template.partial(first_instruction=revise_instructions) → llm.bind_tools(tools=[ReviseAnswer], tool_choice="ReviseAnswer")
```

**Input:** Mensajes históricos incluyendo respuestas y resultados de búsqueda
**Output:** AIMessage con tool_calls estructurados según `ReviseAnswer`.

### `schemas.py`

Módulo que define los modelos Pydantic para estructurar las respuestas del agente.

#### Clases

##### `Reflection(BaseModel)`

Modelo para críticas y reflexiones sobre respuestas.

**Campos:**
- `missing` (str): Crítica sobre qué información falta en la respuesta.
- `superfluous` (str): Crítica sobre qué información es superflua o innecesaria.

##### `AnswerQuestion(BaseModel)`

Modelo para respuestas iniciales del agente.

**Campos:**
- `answer` (str): Respuesta detallada de aproximadamente 500 palabras.
- `reflection` (Reflection): Reflexión y crítica sobre la respuesta generada.
- `search_queries` (List[str]): Lista de 1-3 consultas de búsqueda sugeridas para mejorar la respuesta.

**Uso:** Utilizado por el nodo `first_responder` para estructurar la respuesta inicial.

##### `ReviseAnswer(AnswerQuestion)`

Modelo para respuestas revisadas, hereda de `AnswerQuestion`.

**Campos adicionales:**
- `references` (List[str]): Lista de URLs o referencias como citas que apoyan la respuesta revisada.

**Uso:** Utilizado por el nodo `revisor` para estructurar respuestas mejoradas con referencias.

### `tool_executor.py`

Módulo que gestiona la ejecución de herramientas de búsqueda web.

#### Variables

##### `tavily_tool`

Instancia de `TavilySearch` configurada con `max_results=5`.

#### Funciones

##### `run_queries(search_queries: list[str], **kwargs) -> Any`

Ejecuta múltiples consultas de búsqueda en batch usando TavilySearch.

**Parámetros:**
- `search_queries` (list[str]): Lista de consultas de búsqueda a ejecutar.
- `**kwargs`: Argumentos adicionales (no utilizados actualmente).

**Retorna:**
- Resultados del batch query de TavilySearch.

**Ejemplo:**
```python
results = run_queries([
    "OpenAI GPT models",
    "LangGraph architecture"
])
```

#### Objetos Exportados

##### `execute_tools`

Instancia de `ToolNode` que ejecuta herramientas estructuradas.

**Herramientas configuradas:**
1. Herramienta basada en `run_queries` con nombre `AnswerQuestion`
2. Herramienta basada en `run_queries` con nombre `ReviseAnswer`

**Uso:** Nodo de LangGraph que recibe tool_calls del LLM y ejecuta las búsquedas web correspondientes.

### `logger.py`

Módulo que proporciona funciones de logging con colores para mejor visualización.

#### Clase `Colors`

Constantes ANSI para códigos de color:

- `PURPLE = "\033[95m"`
- `CYAN = "\033[96m"`
- `DARKCYAN = "\033[36m"`
- `BLUE = "\033[94m"`
- `GREEN = "\033[92m"`
- `YELLOW = "\033[93m"`
- `RED = "\033[91m"`
- `BOLD = "\033[1m"`
- `UNDERLINE = "\033[4m"`
- `END = "\033[0m"`

#### Funciones

##### `log_info(message: str, color: str = Colors.CYAN) -> None`

Registra un mensaje informativo con color.

**Parámetros:**
- `message` (str): Mensaje a registrar.
- `color` (str, opcional): Color a usar. Por defecto: `Colors.CYAN`.

**Ejemplo:**
```python
log_info("Procesando consulta...")
```

##### `log_success(message: str) -> None`

Registra un mensaje de éxito en verde.

**Parámetros:**
- `message` (str): Mensaje a registrar.

**Ejemplo:**
```python
log_success("Operación completada exitosamente")
```

##### `log_error(message: str) -> None`

Registra un mensaje de error en rojo.

**Parámetros:**
- `message` (str): Mensaje a registrar.

**Ejemplo:**
```python
log_error("Error al procesar la consulta")
```

##### `log_warning(message: str) -> None`

Registra un mensaje de advertencia en amarillo.

**Parámetros:**
- `message` (str): Mensaje a registrar.

**Ejemplo:**
```python
log_warning("API key no encontrada, usando valores por defecto")
```

##### `log_header(message: str) -> None`

Registra un encabezado destacado con formato especial (púrpura y bold).

**Parámetros:**
- `message` (str): Mensaje a registrar.

**Ejemplo:**
```python
log_header("Iniciando agente de investigación")
```

## Flujo de Datos

### Estructura de Mensajes

El proyecto utiliza el sistema de mensajes de LangChain:

#### `HumanMessage`

Mensaje inicial del usuario con la consulta de investigación.

**Ejemplo:**
```python
from langchain_core.messages import HumanMessage

query = "Investiga sobre inteligencia artificial"
message = HumanMessage(content=query)
```

#### `AIMessage`

Mensaje generado por el LLM con tool_calls estructurados.

**Estructura de tool_calls:**
```python
{
    "name": "AnswerQuestion" | "ReviseAnswer",
    "args": {
        "answer": str,
        "reflection": {
            "missing": str,
            "superfluous": str
        },
        "search_queries": [str],
        # Solo en ReviseAnswer:
        "references": [str]
    }
}
```

#### `ToolMessage`

Mensaje generado por las herramientas después de ejecutar búsquedas web.

**Contenido:** Resultados de las búsquedas de TavilySearch.

### Grafo de LangGraph

#### Nodos

1. **`responder`**: Ejecuta `first_responder` chain
2. **`execute_tools`**: Ejecuta `execute_tools` ToolNode
3. **`revisor`**: Ejecuta `revisor` chain

#### Transiciones

- `responder` → `execute_tools` (siempre)
- `execute_tools` → `revisor` (siempre)
- `revisor` → `execute_tools` o `END` (condicional, basado en `event_loop`)

#### Punto de Entrada

- `responder` (configurado con `builder.set_entry_point("responder")`)

## Ejemplos de Uso de API

### Invocar el Grafo

```python
from main import graph

# Consulta simple
result = graph.invoke("Investiga sobre Python 3.12")

# Extraer respuesta
answer = result[-1].tool_calls[0]["args"]["answer"]
references = result[-1].tool_calls[0]["args"].get("references", [])
```

### Usar Cadenas Individualmente

```python
from chains import first_responder
from langchain_core.messages import HumanMessage

# Generar respuesta inicial
message = HumanMessage(content="¿Qué es LangGraph?")
response = first_responder.invoke({"messages": [message]})

# Extraer datos
tool_call = response.tool_calls[0]
answer = tool_call["args"]["answer"]
reflection = tool_call["args"]["reflection"]
queries = tool_call["args"]["search_queries"]
```

### Ejecutar Búsquedas Manualmente

```python
from tool_executor import run_queries

# Ejecutar búsquedas
results = run_queries([
    "OpenAI API documentation",
    "LangGraph tutorial"
])

# Procesar resultados
for result in results:
    print(f"Título: {result.get('title')}")
    print(f"URL: {result.get('url')}")
    print(f"Contenido: {result.get('content')[:200]}...")
```

### Usar Logger

```python
from logger import log_header, log_info, log_success, log_warning, log_error

log_header("Inicio del proceso")
log_info("Información relevante")
log_success("Operación exitosa")
log_warning("Advertencia importante")
log_error("Error crítico")
```

## Configuración Avanzada

### Cambiar Modelo LLM

```python
# En chains.py
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
```

### Ajustar Máximo de Resultados de Búsqueda

```python
# En tool_executor.py
from langchain_tavily import TavilySearch

tavily_tool = TavilySearch(max_results=10)  # Cambiar de 5 a 10
```

### Modificar Límite de Iteraciones

```python
# En main.py
MAX_ITERATIONS = 3  # Cambiar de 2 a 3
```

### Personalizar Prompts

```python
# En chains.py
first_responder_prompt_template = actor_prompt_template.partial(
    first_instruction="Provide a detailed ~1000 word answer with examples."
)
```

## Tipos de Datos

### `BaseMessage`

Tipo base de todos los mensajes en LangChain/LangGraph. Incluye:
- `HumanMessage`
- `AIMessage`
- `ToolMessage`
- `SystemMessage`

### `List[BaseMessage]`

Tipo utilizado para el estado del grafo, que contiene la secuencia de mensajes intercambiados durante la ejecución.

## Manejo de Errores

### Errores Comunes

1. **API Key no encontrada**: Asegúrate de que `.env` esté configurado correctamente.
2. **Modelo no disponible**: Verifica que el modelo especificado en `OPENAI_MODEL` esté disponible en tu cuenta de OpenAI.
3. **Límite de rate limit**: Implementa backoff exponencial o reduce `MAX_ITERATIONS`.
4. **Tool calls inválidos**: Verifica que los schemas Pydantic coincidan con las herramientas configuradas.

## Extensiones Futuras

### Agregar Nuevas Herramientas

```python
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import ToolNode

def nueva_herramienta(param: str) -> str:
    """Descripción de la herramienta"""
    # Implementación
    return resultado

execute_tools = ToolNode([
    StructuredTool.from_function(func=run_queries, name="AnswerQuestion"),
    StructuredTool.from_function(func=nueva_herramienta, name="NuevaHerramienta"),
])
```

### Agregar Nuevos Nodos

```python
# En main.py
def nuevo_nodo(state: List[BaseMessage]) -> List[BaseMessage]:
    # Procesamiento del nodo
    return estado_modificado

builder.add_node("nuevo_nodo", nuevo_nodo)
builder.add_edge("revisor", "nuevo_nodo")
builder.add_edge("nuevo_nodo", END)
```



