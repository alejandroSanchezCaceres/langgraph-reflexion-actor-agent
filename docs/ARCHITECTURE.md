# Guía de Arquitectura

Documentación detallada de la arquitectura del sistema LangGraph Reflection Actor Agent.

## Visión General

El proyecto implementa un agente de investigación basado en el patrón de reflexión, que permite al agente evaluar y mejorar sus propias respuestas mediante búsquedas web iterativas.

## Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────┐
│                     Usuario / Cliente                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   Grafo de LangGraph                         │
│  ┌──────────┐    ┌──────────────┐    ┌──────────┐          │
│  │ Responder│───▶│ Execute Tools │───▶│ Revisor  │          │
│  └──────────┘    └──────────────┘    └────┬─────┘          │
│                                              │                │
│                                              ▼                │
│                                         Event Loop            │
│                                              │                │
│                    ┌─────────────────────────┘                │
│                    ▼                                           │
│            ¿Más iteraciones?                                  │
│                    │                                           │
│        ┌───────────┴───────────┐                             │
│        ▼                        ▼                             │
│   execute_tools                END                            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Servicios Externos                        │
│  ┌──────────────┐              ┌──────────────┐             │
│  │   OpenAI     │              │  Tavily API   │             │
│  │   (LLM)      │              │  (Búsqueda)   │             │
│  └──────────────┘              └──────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. Grafo de Flujo (LangGraph)

El corazón del sistema es un `MessageGraph` de LangGraph que orquesta el flujo de trabajo.

#### Nodos del Grafo

**a) Nodo `responder`**
- **Función**: `first_responder` (de `chains.py`)
- **Responsabilidad**: Generar una respuesta inicial basada en el conocimiento del LLM
- **Input**: `HumanMessage` con la consulta del usuario
- **Output**: `AIMessage` con `tool_calls` estructurados según `AnswerQuestion`
- **Procesamiento**:
  1. Recibe la consulta del usuario
  2. Genera una respuesta de ~500 palabras
  3. Reflexiona y critica su propia respuesta
  4. Genera 1-3 consultas de búsqueda sugeridas

**b) Nodo `execute_tools`**
- **Función**: `execute_tools` (de `tool_executor.py`)
- **Responsabilidad**: Ejecutar búsquedas web basadas en las consultas sugeridas
- **Input**: `AIMessage` con `tool_calls` que incluyen `search_queries`
- **Output**: `ToolMessage` con resultados de búsqueda
- **Procesamiento**:
  1. Extrae `search_queries` del `tool_call`
  2. Ejecuta búsquedas en batch usando TavilySearch
  3. Retorna resultados estructurados

**c) Nodo `revisor`**
- **Función**: `revisor` (de `chains.py`)
- **Responsabilidad**: Revisar y mejorar la respuesta inicial usando nueva información
- **Input**: Historial completo de mensajes (respuesta inicial + resultados de búsqueda)
- **Output**: `AIMessage` con `tool_calls` estructurados según `ReviseAnswer`
- **Procesamiento**:
  1. Analiza la respuesta inicial y su crítica
  2. Incorpora información de los resultados de búsqueda
  3. Mejora la respuesta eliminando información superflua
  4. Incluye referencias y citas numéricas
  5. Genera nuevas consultas de búsqueda si es necesario

#### Flujo de Control

```
START → responder → execute_tools → revisor → event_loop
                                              │
                    ┌─────────────────────────┘
                    │
          ¿count_tool_visits >= MAX_ITERATIONS?
                    │
        ┌───────────┴───────────┐
        │                      │
       NO                      YES
        │                      │
        ▼                      ▼
execute_tools                 END
        │
        └──────────────────────┘
              (loop)
```

**Función `event_loop`**:
- Evalúa el estado actual del grafo
- Cuenta los `ToolMessage` en el historial
- Decide si continuar iterando o finalizar

### 2. Cadenas de Procesamiento (Chains)

Las cadenas definen cómo el LLM procesa información en cada etapa.

#### Template Base (`actor_prompt_template`)

```python
Template Structure:
┌─────────────────────────────────────────┐
│ System Message 1                         │
│ - "You are expert researcher"            │
│ - Current time: {time}                  │
│ - {first_instruction}                    │
│ - Reflect and critique instructions      │
│ - Search query recommendation            │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Messages Placeholder                     │
│ - Historial de mensajes                  │
│ - HumanMessage (consulta inicial)        │
│ - AIMessage (respuestas)                 │
│ - ToolMessage (resultados búsqueda)      │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ System Message 2                         │
│ - "Answer using required format"         │
└─────────────────────────────────────────┘
```

#### Primera Respuesta (`first_responder`)

**Pipeline:**
```
HumanMessage
    │
    ▼
[ChatPromptTemplate]
    │
    ▼
[LLM.bind_tools(AnswerQuestion)]
    │
    ▼
AIMessage con tool_calls
```

**Instrucciones específicas:**
- "Provide a detailed ~500 word answer"
- "Reflect and critique your answer. Be severe to maximize improvement"
- "Recommend search queries to research information"

#### Revisión (`revisor`)

**Pipeline:**
```
Historial de Mensajes
    │
    ▼
[ChatPromptTemplate con revise_instructions]
    │
    ▼
[LLM.bind_tools(ReviseAnswer)]
    │
    ▼
AIMessage con tool_calls (incluye references)
```

**Instrucciones específicas:**
- "Revise your previous answer using the new information"
- "Use the previous critique to add important information"
- "Include numerical citations in your revised answer"
- "Remove superfluous information"
- "Ensure answer is not more than 500 words"

### 3. Modelos de Datos (Schemas)

Los schemas Pydantic estructuran las respuestas del agente.

#### Jerarquía de Schemas

```
BaseModel
    │
    ├─── Reflection
    │    ├── missing: str
    │    └── superfluous: str
    │
    └─── AnswerQuestion
         ├── answer: str
         ├── reflection: Reflection
         └── search_queries: List[str]
              │
              └─── ReviseAnswer (hereda de AnswerQuestion)
                   ├── answer: str
                   ├── reflection: Reflection
                   ├── search_queries: List[str]
                   └── references: List[str] (nuevo)
```

#### Flujo de Datos a través de Schemas

```
Consulta Usuario
    │
    ▼
[first_responder]
    │
    ▼
AnswerQuestion {
    answer: "Respuesta inicial...",
    reflection: {
        missing: "Falta información sobre...",
        superfluous: "La sección sobre... es innecesaria"
    },
    search_queries: ["query1", "query2"]
}
    │
    ▼
[execute_tools]
    │
    ▼
ToolMessage {
    content: Resultados de búsqueda
}
    │
    ▼
[revisor]
    │
    ▼
ReviseAnswer {
    answer: "Respuesta mejorada [1] [2]...",
    reflection: {...},
    search_queries: [...],
    references: ["url1", "url2"]
}
```

### 4. Sistema de Herramientas

#### Ejecución de Búsquedas

```python
ToolNode Structure:
┌─────────────────────────────────────┐
│ execute_tools (ToolNode)            │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ StructuredTool                │  │
│  │ name: "AnswerQuestion"        │  │
│  │ func: run_queries             │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ StructuredTool                │  │
│  │ name: "ReviseAnswer"          │  │
│  │ func: run_queries             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ TavilySearch                        │
│ - max_results: 5                    │
│ - batch([{"query": q} for q in qs]) │
└─────────────────────────────────────┘
```

**Proceso de ejecución:**
1. `execute_tools` recibe `AIMessage` con `tool_calls`
2. Identifica el tool_call relevante (`AnswerQuestion` o `ReviseAnswer`)
3. Extrae `search_queries` de los argumentos
4. Llama a `run_queries()` con la lista de queries
5. `run_queries()` ejecuta búsquedas en batch usando TavilySearch
6. Retorna `ToolMessage` con resultados

### 5. Sistema de Logging

El logger proporciona visualización colorizada del proceso.

```
Logger Functions:
┌─────────────────────────────────┐
│ log_info()    → Cyan            │
│ log_success() → Green            │
│ log_warning() → Yellow          │
│ log_error()   → Red             │
│ log_header()  → Purple + Bold   │
└─────────────────────────────────┘
```

## Flujo de Datos Completo

### Ejecución de una Consulta

```
1. Usuario: "Investiga sobre X"
   │
   ▼
2. main.py: graph.invoke(query)
   │
   ▼
3. [responder] first_responder
   │
   ├─► Prompt Template
   ├─► LLM Processing
   └─► AIMessage {
         tool_calls: [{
           name: "AnswerQuestion",
           args: {
             answer: "...",
             reflection: {...},
             search_queries: ["q1", "q2"]
           }
         }]
       }
   │
   ▼
4. [execute_tools] run_queries(["q1", "q2"])
   │
   ├─► TavilySearch.batch()
   └─► ToolMessage {
         content: [{
           title: "...",
           url: "...",
           content: "..."
         }, ...]
       }
   │
   ▼
5. [revisor] revisor
   │
   ├─► Prompt con historial completo
   ├─► LLM Processing
   └─► AIMessage {
         tool_calls: [{
           name: "ReviseAnswer",
           args: {
             answer: "Respuesta mejorada [1] [2]...",
             reflection: {...},
             search_queries: ["q3"],
             references: ["url1", "url2"]
           }
         }]
       }
   │
   ▼
6. [event_loop] evalúa estado
   │
   ├─► count_tool_visits = 2
   ├─► MAX_ITERATIONS = 2
   └─► count_tool_visits >= MAX_ITERATIONS
   │
   ▼
7. END → Retorna resultado final
```

### Estado del Grafo

El estado del grafo es una lista de mensajes:

```python
state: List[BaseMessage] = [
    HumanMessage(content="Investiga sobre X"),
    AIMessage(tool_calls=[...]),  # De responder
    ToolMessage(content=[...]),   # De execute_tools
    AIMessage(tool_calls=[...]),  # De revisor
    # ... más mensajes si hay más iteraciones
]
```

## Patrón de Reflexión

El sistema implementa el patrón de reflexión del paper MIT:

### Fase 1: Generación Inicial
```
Consulta → Respuesta Inicial + Reflexión
```

### Fase 2: Crítica
```
Reflexión → {
    missing: "Falta información sobre..."
    superfluous: "La parte sobre... no es relevante"
}
```

### Fase 3: Búsqueda
```
Crítica → Consultas de Búsqueda → Resultados
```

### Fase 4: Revisión
```
Respuesta Inicial + Resultados → Respuesta Mejorada
```

### Iteración
```
Respuesta Mejorada → Nueva Reflexión → Más Búsquedas → ...
```

## Decisiones de Diseño

### 1. Uso de MessageGraph

**Razón**: Permite mantener historial completo de conversación y facilita el debugging.

**Alternativa considerada**: `StateGraph` con estado personalizado
**Razón de rechazo**: Mayor complejidad sin beneficios claros para este caso de uso.

### 2. ToolNode para Herramientas

**Razón**: Integración automática con tool_calls del LLM.

**Alternativa considerada**: Nodo personalizado con lógica de ejecución manual
**Razón de rechazo**: ToolNode simplifica la integración y manejo de errores.

### 3. Pydantic Schemas para Estructura

**Razón**: Validación automática y parsing estructurado de respuestas del LLM.

**Alternativa considerada**: Parsing manual de JSON
**Razón de rechazo**: Mayor propensión a errores y menos mantenibilidad.

### 4. Límite de Iteraciones

**Razón**: Prevenir bucles infinitos y controlar costos de API.

**Mejora futura**: Lógica adaptativa basada en calidad de respuesta.

## Escalabilidad

### Limitaciones Actuales

1. **Iteraciones secuenciales**: No se pueden paralelizar búsquedas entre iteraciones
2. **Un solo modelo LLM**: No hay soporte para múltiples modelos
3. **Una sola herramienta de búsqueda**: Solo TavilySearch

### Oportunidades de Mejora

1. **Búsquedas paralelas**: Ejecutar múltiples queries en paralelo
2. **Caché de búsquedas**: Evitar búsquedas duplicadas
3. **Múltiples herramientas**: Integrar más fuentes de información
4. **Evaluación automática**: Scoring de calidad de respuesta para decisión adaptativa

## Seguridad y Privacidad

### Consideraciones

1. **API Keys**: Almacenadas en `.env`, no en el código
2. **Datos de búsqueda**: Enviados a TavilySearch (revisar política de privacidad)
3. **Consultas del usuario**: Procesadas por OpenAI (revisar política de datos)

### Recomendaciones

1. Rotar API keys regularmente
2. Revisar logs para evitar exposición de datos sensibles
3. Implementar rate limiting para producción

## Testing y Debugging

### Visualización del Grafo

```python
# Diagrama ASCII
graph.get_graph().print_ascii()

# Diagrama Mermaid
print(graph.get_graph().draw_mermaid())
```

### Logging de Estado

```python
# Agregar logging en cada nodo
def responder(state):
    log_info(f"Estado actual: {len(state)} mensajes")
    result = first_responder.invoke(state)
    log_success("Respuesta generada")
    return result
```

### Inspección de Mensajes

```python
# Ver estructura de mensajes
for msg in state:
    print(f"Tipo: {type(msg).__name__}")
    if hasattr(msg, 'tool_calls'):
        print(f"Tool calls: {msg.tool_calls}")
```

## Referencias Arquitectónicas

- **LangGraph**: https://github.com/langchain-ai/langgraph
- **Reflexion Paper**: `docs/ReflexionIvenstigationPaperMIT_2303.11366v4.pdf`
- **LangChain**: https://github.com/langchain-ai/langchain
- **Pydantic**: https://docs.pydantic.dev/


