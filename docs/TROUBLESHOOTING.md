# Guía de Troubleshooting

Resolución de problemas comunes y preguntas frecuentes sobre el LangGraph Reflection Actor Agent.

## Problemas Comunes

### Error: "No module named 'dotenv'"

**Síntoma:**
```python
ModuleNotFoundError: No module named 'dotenv'
```

**Causa:** Las dependencias no están instaladas.

**Solución:**
```bash
# Instalar dependencias con Poetry
poetry install

# O con pip si no usas Poetry
pip install -r requirements.txt
```

---

### Error: "No API key provided"

**Síntoma:**
```python
ValueError: No API key provided
```

**Causa:** Las variables de entorno no están configuradas correctamente.

**Solución:**

1. Verifica que existe el archivo `.env` en la raíz del proyecto:
```bash
ls -la .env
```

2. Verifica el contenido del archivo `.env`:
```env
OPENAI_API_KEY=sk-tu-key-aqui
TAVILY_API_KEY=tvly-tu-key-aqui
OPENAI_MODEL=gpt-4o-mini  # Opcional
```

3. Asegúrate de que las variables se cargan correctamente:
```python
from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv("OPENAI_API_KEY"))  # Debe mostrar tu key
```

---

### Error: "Model not found" o "Invalid model"

**Síntoma:**
```python
openai.error.InvalidRequestError: The model 'gpt-5-nano' does not exist
```

**Causa:** El modelo especificado no está disponible en tu cuenta de OpenAI.

**Solución:**

1. Verifica qué modelos están disponibles:
```python
from langchain_openai import ChatOpenAI
import os

# Listar modelos disponibles
llm = ChatOpenAI()
# O usar un modelo específico conocido
llm = ChatOpenAI(model="gpt-4o-mini")
```

2. Actualiza `.env` con un modelo válido:
```env
OPENAI_MODEL=gpt-4o-mini  # o gpt-4, gpt-3.5-turbo, etc.
```

3. O modifica directamente en `chains.py`:
```python
llm = ChatOpenAI(model="gpt-4o-mini")
```

---

### Error: Rate Limit Exceeded

**Síntoma:**
```python
openai.error.RateLimitError: Rate limit exceeded
```

**Causa:** Se han excedido los límites de rate limit de la API de OpenAI.

**Solución:**

1. **Reducir iteraciones:**
```python
# En main.py
MAX_ITERATIONS = 1  # Reducir de 2 a 1
```

2. **Implementar backoff exponencial:**
```python
import time
from openai import RateLimitError

def invoke_with_retry(graph, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return graph.invoke(query)
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Backoff exponencial
                print(f"Rate limit alcanzado. Esperando {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

3. **Reducir número de búsquedas:**
```python
# En tool_executor.py
tavily_tool = TavilySearch(max_results=3)  # Reducir de 5 a 3
```

---

### Error: "Tool call failed" o "Invalid tool arguments"

**Síntoma:**
```python
ValueError: Invalid tool arguments
```

**Causa:** Los tool_calls del LLM no coinciden con los schemas esperados.

**Solución:**

1. Verifica que los schemas estén correctamente definidos:
```python
from schemas import AnswerQuestion, ReviseAnswer

# Verificar estructura
print(AnswerQuestion.model_fields)
print(ReviseAnswer.model_fields)
```

2. Agrega logging para debug:
```python
# En main.py, antes de invoke
import json

def debug_tool_calls(result):
    for msg in result:
        if hasattr(msg, 'tool_calls'):
            for tc in msg.tool_calls:
                print(f"Tool: {tc['name']}")
                print(f"Args: {json.dumps(tc['args'], indent=2)}")

result = graph.invoke(query)
debug_tool_calls(result)
```

---

### El agente no genera búsquedas o siempre retorna las mismas

**Síntoma:** El agente no mejora sus respuestas entre iteraciones.

**Causa:** Posiblemente las instrucciones del prompt no son lo suficientemente estrictas.

**Solución:**

1. **Mejorar las instrucciones de reflexión en `chains.py`:**
```python
revise_instructions = """Revise your previous answer using the new information.
        - You MUST use the previous critique to add important information to your answer.
        - You MUST include numerical citations [1], [2], etc. in your revised answer.
        - You MUST remove superfluous information from your answer.
        - Your answer MUST NOT exceed 500 words.
        - If the search results provide new relevant information, you MUST incorporate it.
"""
```

2. **Aumentar severidad de la crítica:**
```python
# En el prompt template
"2. Reflect and critique your answer. Be EXTREMELY severe and critical to maximize improvement."
```

3. **Verificar que las búsquedas se ejecutan:**
```python
# Agregar logging en tool_executor.py
def run_queries(search_queries: list[str], **kwargs) -> Any:
    print(f"Ejecutando búsquedas: {search_queries}")
    results = tavily_tool.batch([{"query": query} for query in search_queries])
    print(f"Búsquedas completadas: {len(results)} resultados")
    return results
```

---

### Respuesta muy larga o excede el límite de palabras

**Síntoma:** La respuesta generada es demasiado larga (>500 palabras).

**Causa:** El LLM no está respetando la restricción de longitud.

**Solución:**

1. **Reforzar la instrucción en el prompt:**
```python
first_instruction = """Provide a detailed answer of EXACTLY 500 words or less.
Be concise and focus on the most important information."""
```

2. **Agregar validación post-procesamiento:**
```python
def limit_answer_length(answer: str, max_words: int = 500) -> str:
    words = answer.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + "..."
    return answer
```

3. **Usar un modelo con mejor seguimiento de instrucciones:**
```python
llm = ChatOpenAI(model="gpt-4")  # En lugar de gpt-4o-mini
```

---

### Búsquedas de Tavily no retornan resultados relevantes

**Síntoma:** Los resultados de búsqueda no son útiles para mejorar la respuesta.

**Causa:** Las consultas de búsqueda generadas no son óptimas.

**Solución:**

1. **Mejorar la generación de queries en el prompt:**
```python
"3. Recommend 1-3 highly specific and targeted search queries that will find 
   precise, relevant information to address the critique. Avoid generic queries."
```

2. **Aumentar número de resultados:**
```python
tavily_tool = TavilySearch(max_results=10)  # De 5 a 10
```

3. **Filtrar resultados manualmente:**
```python
def filter_relevant_results(results, keywords):
    """Filtrar resultados por relevancia."""
    filtered = []
    for result in results:
        content = result.get('content', '').lower()
        if any(kw.lower() in content for kw in keywords):
            filtered.append(result)
    return filtered
```

---

### El agente entra en un bucle infinito

**Síntoma:** El agente no termina nunca.

**Causa:** `MAX_ITERATIONS` es demasiado alto o `event_loop` no funciona correctamente.

**Solución:**

1. **Verificar `event_loop`:**
```python
def event_loop(state: List[BaseMessage]) -> str:
    count_tool_visits = sum(isinstance(m, ToolMessage) for m in state)
    print(f"Debug: count_tool_visits={count_tool_visits}, MAX_ITERATIONS={MAX_ITERATIONS}")
    
    if count_tool_visits >= MAX_ITERATIONS:
        return END
    return "execute_tools"
```

2. **Reducir `MAX_ITERATIONS`:**
```python
MAX_ITERATIONS = 1  # Para pruebas rápidas
```

3. **Agregar timeout:**
```python
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Timeout alcanzado")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(300)  # 5 minutos timeout

try:
    result = graph.invoke(query)
finally:
    signal.alarm(0)
```

---

### Errores de encoding al guardar resultados

**Síntoma:**
```python
UnicodeEncodeError: 'ascii' codec can't encode character
```

**Causa:** Intento de escribir caracteres no-ASCII sin encoding UTF-8.

**Solución:**
```python
# Siempre especificar encoding UTF-8
with open("resultado.txt", "w", encoding="utf-8") as f:
    f.write(answer)
```

---

### Problemas con Poetry

**Síntoma:** Comandos de Poetry fallan.

**Solución:**

1. **Verificar instalación de Poetry:**
```bash
poetry --version
```

2. **Reinstalar dependencias:**
```bash
poetry lock --no-update
poetry install
```

3. **Si Poetry no está instalado:**
```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

---

## Preguntas Frecuentes (FAQ)

### ¿Cómo cambio el modelo de LLM?

Modifica la variable de entorno `OPENAI_MODEL` en `.env` o directamente en `chains.py`:
```python
llm = ChatOpenAI(model="gpt-4")
```

### ¿Puedo usar otros modelos además de OpenAI?

Actualmente el proyecto está diseñado para OpenAI. Para usar otros modelos:
1. Cambia `ChatOpenAI` por el modelo equivalente (ej: `ChatAnthropic` para Claude)
2. Asegúrate de que el modelo soporte `bind_tools`

### ¿Cómo aumento el número de iteraciones?

Modifica `MAX_ITERATIONS` en `main.py`:
```python
MAX_ITERATIONS = 3  # o el número que desees
```

### ¿Puedo usar otras herramientas de búsqueda además de Tavily?

Sí, puedes agregar más herramientas en `tool_executor.py`. Ejemplo con SerpAPI:
```python
from langchain_community.tools import SerpAPIWrapper

serp_tool = SerpAPIWrapper()

def run_queries_mixed(search_queries: list[str], **kwargs) -> Any:
    tavily_results = tavily_tool.batch([{"query": q} for q in search_queries])
    serp_results = [serp_tool.run(q) for q in search_queries]
    return {"tavily": tavily_results, "serp": serp_results}
```

### ¿Cómo visualizo el grafo?

Descomenta las líneas en `main.py`:
```python
print(graph.get_graph().draw_mermaid())
graph.get_graph().print_ascii()
```

### ¿Cómo reduzco los costos de API?

1. Reduce `MAX_ITERATIONS` a 1
2. Limita `max_results` en TavilySearch a 3
3. Usa modelos más baratos (gpt-3.5-turbo en lugar de gpt-4)
4. Cachea resultados de búsquedas comunes

### ¿Puedo ejecutar múltiples consultas en paralelo?

Actualmente el flujo es secuencial. Para paralelización:
```python
import asyncio
from main import graph

async def investigar_paralelo(queries):
    tasks = [graph.ainvoke(q) for q in queries]
    return await asyncio.gather(*tasks)

queries = ["query1", "query2", "query3"]
results = asyncio.run(investigar_paralelo(queries))
```

### ¿Cómo agrego logging personalizado?

```python
from logger import log_info
import logging

# Agregar logging estándar
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# En tus funciones
def mi_funcion():
    log_info("Usando logger del proyecto")
    logger.debug("Usando logging estándar")
```

### ¿Cómo filtro resultados de búsqueda?

```python
def filtrar_resultados_relevantes(resultados, keywords, min_score=0.5):
    """Filtrar resultados por relevancia."""
    relevantes = []
    for resultado in resultados:
        # Lógica de filtrado personalizada
        if any(kw in resultado.get('content', '').lower() for kw in keywords):
            relevantes.append(resultado)
    return relevantes
```

## Debugging

### Habilitar Logging Detallado

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Ver mensajes HTTP de LangChain
logging.getLogger("langchain").setLevel(logging.DEBUG)
```

### Inspeccionar Estado del Grafo

```python
def debug_state(state):
    """Inspeccionar estado completo del grafo."""
    print(f"Total mensajes: {len(state)}")
    for i, msg in enumerate(state):
        print(f"\n[{i}] {type(msg).__name__}")
        if hasattr(msg, 'content'):
            print(f"Content: {msg.content[:100]}...")
        if hasattr(msg, 'tool_calls'):
            print(f"Tool calls: {len(msg.tool_calls)}")
            for tc in msg.tool_calls:
                print(f"  - {tc['name']}")

# Usar en event_loop o en nodos personalizados
```

### Ver Mensajes Intermedios

```python
# Modificar main.py para logging intermedio
def responder_con_log(state):
    result = first_responder.invoke(state)
    log_info(f"Respuesta generada: {len(result.tool_calls)} tool calls")
    return result

builder.add_node("responder", responder_con_log)
```

## Recursos de Ayuda

- **Documentación LangGraph**: https://github.com/langchain-ai/langgraph
- **Documentación LangChain**: https://python.langchain.com/
- **Documentación OpenAI**: https://platform.openai.com/docs
- **Documentación Tavily**: https://docs.tavily.com/

## Reportar Problemas

Si encuentras un problema que no está documentado aquí:

1. Verifica que estás usando la versión más reciente del código
2. Revisa los logs completos del error
3. Verifica la configuración de variables de entorno
4. Abre un issue en el repositorio con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs completos del error
   - Versión de Python y dependencias

## Contribuir Soluciones

Si resolviste un problema no documentado aquí:

1. Documenta la solución en este archivo
2. Incluye ejemplos de código si es posible
3. Explica claramente la causa raíz del problema
4. Menciona versiones específicas si es relevante


