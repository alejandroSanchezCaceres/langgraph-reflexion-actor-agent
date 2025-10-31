# Ejemplos de Uso

Colección de ejemplos prácticos para usar el LangGraph Reflection Actor Agent.

## Ejemplos Básicos

### Ejemplo 1: Consulta Simple

Uso más básico del agente para una investigación simple.

```python
from main import graph

# Consulta simple
query = "¿Qué es la inteligencia artificial?"
result = graph.invoke(query)

# Extraer respuesta
answer = result[-1].tool_calls[0]["args"]["answer"]
print(answer)
```

**Salida esperada:**
```
Respuesta detallada de ~500 palabras sobre inteligencia artificial
con citas numéricas [1], [2], etc.
```

### Ejemplo 2: Consulta con Referencias

Obtener tanto la respuesta como sus referencias.

```python
from main import graph
from logger import log_header, log_info, log_success

query = "Investiga sobre Python 3.12 y sus nuevas características"

log_header("Iniciando investigación")
log_info(f"Consulta: {query}")

result = graph.invoke(query)

# Extraer datos
final_message = result[-1]
tool_call = final_message.tool_calls[0]
answer = tool_call["args"]["answer"]
references = tool_call["args"].get("references", [])

log_success("Investigación completada")

print("\n" + "="*60)
print("RESPUESTA:")
print("="*60)
print(answer)

print("\n" + "="*60)
print("REFERENCIAS:")
print("="*60)
for i, ref in enumerate(references, 1):
    print(f"[{i}] {ref}")
```

### Ejemplo 3: Investigación Técnica

Consulta más compleja sobre un tema técnico.

```python
from main import graph

query = """
Investiga sobre arquitecturas de microservicios.
Incluye:
- Ventajas y desventajas
- Mejores prácticas
- Casos de uso recomendados
- Herramientas populares
"""

result = graph.invoke(query)
answer = result[-1].tool_calls[0]["args"]["answer"]
print(answer)
```

## Ejemplos Intermedios

### Ejemplo 4: Análisis de Mercado

Investigación sobre tendencias de mercado.

```python
from main import graph
from logger import log_header, log_info, log_success

query = """
Analiza el mercado de vehículos eléctricos en América Latina.
Incluye:
- Principales actores
- Proyecciones de crecimiento
- Desafíos del mercado
- Políticas gubernamentales
"""

log_header("Análisis de Mercado")
log_info("Procesando consulta sobre vehículos eléctricos")

result = graph.invoke(query)

# Extraer información
final_data = result[-1].tool_calls[0]["args"]
answer = final_data["answer"]
references = final_data.get("references", [])

log_success(f"Análisis completado con {len(references)} referencias")

# Guardar resultado
with open("analisis_vehiculos_electricos.txt", "w", encoding="utf-8") as f:
    f.write("ANÁLISIS DE MERCADO: VEHÍCULOS ELÉCTRICOS EN AMÉRICA LATINA\n")
    f.write("="*60 + "\n\n")
    f.write(answer)
    f.write("\n\n" + "="*60 + "\n")
    f.write("REFERENCIAS:\n")
    for i, ref in enumerate(references, 1):
        f.write(f"[{i}] {ref}\n")
```

### Ejemplo 5: Investigación Regulatoria

Análisis de regulaciones y compliance.

```python
from main import graph

query = """
Investiga sobre GDPR (Reglamento General de Protección de Datos)
y su impacto en aplicaciones web.

Enfócate en:
- Principales obligaciones para desarrolladores
- Requisitos de consentimiento
- Derechos de los usuarios
- Sanciones por incumplimiento
- Mejores prácticas de implementación
"""

result = graph.invoke(query)

# Procesar resultado
data = result[-1].tool_calls[0]["args"]
print("RESPUESTA:")
print("-" * 60)
print(data["answer"])
print("\nREFERENCIAS:")
print("-" * 60)
for i, ref in enumerate(data.get("references", []), 1):
    print(f"{i}. {ref}")
```

### Ejemplo 6: Comparación de Tecnologías

Comparar diferentes tecnologías o herramientas.

```python
from main import graph

query = """
Compara LangGraph vs LangChain para desarrollo de agentes IA.

Incluye:
- Diferencias arquitectónicas
- Casos de uso para cada uno
- Ventajas y desventajas
- Cuándo usar cada uno
"""

result = graph.invoke(query)
answer = result[-1].tool_calls[0]["args"]["answer"]

# Formatear salida
print("=" * 70)
print("COMPARACIÓN: LANGGRAPH VS LANGCHAIN")
print("=" * 70)
print(answer)
```

## Ejemplos Avanzados

### Ejemplo 7: Función Reutilizable

Crear una función wrapper para uso repetido.

```python
from main import graph
from logger import log_header, log_info, log_success
from typing import Dict, List

def investigar(
    query: str,
    mostrar_referencias: bool = True,
    guardar_archivo: bool = False
) -> Dict[str, any]:
    """
    Función helper para ejecutar investigaciones.
    
    Args:
        query: Consulta de investigación
        mostrar_referencias: Si mostrar referencias en output
        guardar_archivo: Si guardar resultado en archivo
    
    Returns:
        Diccionario con answer, references, y metadata
    """
    log_header("Agente de Investigación")
    log_info(f"Consultando: {query}")
    
    result = graph.invoke(query)
    
    # Extraer datos
    final_msg = result[-1]
    tool_call = final_msg.tool_calls[0]
    args = tool_call["args"]
    
    respuesta = {
        "answer": args["answer"],
        "references": args.get("references", []),
        "metadata": {
            "iteraciones": len([m for m in result if hasattr(m, 'tool_calls')]),
            "total_mensajes": len(result)
        }
    }
    
    log_success("Investigación completada")
    
    # Mostrar resultado
    print("\n" + "="*60)
    print("RESPUESTA:")
    print("="*60)
    print(respuesta["answer"])
    
    if mostrar_referencias and respuesta["references"]:
        print("\n" + "="*60)
        print("REFERENCIAS:")
        print("="*60)
        for i, ref in enumerate(respuesta["references"], 1):
            print(f"[{i}] {ref}")
    
    # Guardar si se solicita
    if guardar_archivo:
        filename = f"investigacion_{len(query[:30])}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"CONSULTA: {query}\n")
            f.write("="*60 + "\n\n")
            f.write(respuesta["answer"])
            if respuesta["references"]:
                f.write("\n\n" + "="*60 + "\n")
                f.write("REFERENCIAS:\n")
                for i, ref in enumerate(respuesta["references"], 1):
                    f.write(f"[{i}] {ref}\n")
        log_info(f"Resultado guardado en {filename}")
    
    return respuesta

# Uso
resultado = investigar(
    "Investiga sobre Docker y Kubernetes",
    mostrar_referencias=True,
    guardar_archivo=True
)
```

### Ejemplo 8: Batch de Investigaciones

Ejecutar múltiples investigaciones en secuencia.

```python
from main import graph
from logger import log_header, log_info, log_success
import json

queries = [
    "¿Qué es machine learning?",
    "Explica deep learning vs machine learning",
    "¿Cuáles son las aplicaciones prácticas de AI?",
]

resultados = []

log_header("Batch de Investigaciones")
log_info(f"Procesando {len(queries)} consultas")

for i, query in enumerate(queries, 1):
    log_info(f"[{i}/{len(queries)}] Procesando: {query}")
    
    result = graph.invoke(query)
    data = result[-1].tool_calls[0]["args"]
    
    resultados.append({
        "query": query,
        "answer": data["answer"],
        "references": data.get("references", [])
    })
    
    log_success(f"[{i}/{len(queries)}] Completado")

# Guardar todos los resultados
output = {
    "total_queries": len(queries),
    "resultados": resultados
}

with open("batch_resultados.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

log_success(f"Todos los resultados guardados en batch_resultados.json")
```

### Ejemplo 9: Uso con Cadenas Individuales

Usar los componentes individualmente en lugar del grafo completo.

```python
from chains import first_responder
from tool_executor import run_queries
from chains import revisor
from langchain_core.messages import HumanMessage

# Paso 1: Generar respuesta inicial
query = "¿Qué es LangGraph?"
message = HumanMessage(content=query)

print("Paso 1: Generando respuesta inicial...")
initial_response = first_responder.invoke({"messages": [message]})

# Extraer datos de la respuesta inicial
tool_call = initial_response.tool_calls[0]
initial_data = tool_call["args"]

print(f"\nRespuesta inicial generada ({len(initial_data['answer'])} caracteres)")
print(f"Consultas sugeridas: {initial_data['search_queries']}")

# Paso 2: Ejecutar búsquedas
print("\nPaso 2: Ejecutando búsquedas...")
search_results = run_queries(initial_data["search_queries"])

print(f"Búsquedas completadas: {len(search_results)} resultados")

# Paso 3: Revisar respuesta
print("\nPaso 3: Revisando respuesta con nueva información...")

# Construir historial completo
from langchain_core.messages import ToolMessage
messages = [
    message,
    initial_response,
    ToolMessage(content=str(search_results), tool_call_id=tool_call["id"])
]

revised_response = revisor.invoke({"messages": messages})

# Extraer respuesta revisada
revised_tool_call = revised_response.tool_calls[0]
revised_data = revised_tool_call["args"]

print("\n" + "="*60)
print("RESPUESTA REVISADA:")
print("="*60)
print(revised_data["answer"])

if revised_data.get("references"):
    print("\n" + "="*60)
    print("REFERENCIAS:")
    print("="*60)
    for i, ref in enumerate(revised_data["references"], 1):
        print(f"[{i}] {ref}")
```

### Ejemplo 10: Clase Wrapper Personalizada

Crear una clase wrapper para encapsular la funcionalidad.

```python
from main import graph
from typing import Optional, List
from logger import log_header, log_info, log_success

class AgenteInvestigador:
    """Wrapper class para el agente de investigación."""
    
    def __init__(self, max_iteraciones: int = 2):
        """
        Inicializa el agente.
        
        Args:
            max_iteraciones: Número máximo de iteraciones (solo informativo)
        """
        self.graph = graph
        self.max_iteraciones = max_iteraciones
    
    def investigar(
        self,
        query: str,
        verbose: bool = True
    ) -> dict:
        """
        Ejecuta una investigación.
        
        Args:
            query: Consulta de investigación
            verbose: Si mostrar logs
        
        Returns:
            Diccionario con answer, references, reflection
        """
        if verbose:
            log_header("Agente de Investigación")
            log_info(f"Consulta: {query}")
        
        result = self.graph.invoke(query)
        
        # Extraer datos del mensaje final
        final_msg = result[-1]
        tool_call = final_msg.tool_calls[0]
        args = tool_call["args"]
        
        resultado = {
            "answer": args["answer"],
            "references": args.get("references", []),
            "reflection": args.get("reflection", {}),
            "search_queries": args.get("search_queries", []),
            "metadata": {
                "total_mensajes": len(result),
                "iteraciones": len([m for m in result if hasattr(m, 'tool_calls')])
            }
        }
        
        if verbose:
            log_success("Investigación completada")
            self._mostrar_resultado(resultado)
        
        return resultado
    
    def _mostrar_resultado(self, resultado: dict):
        """Muestra el resultado formateado."""
        print("\n" + "="*60)
        print("RESPUESTA:")
        print("="*60)
        print(resultado["answer"])
        
        if resultado["references"]:
            print("\n" + "="*60)
            print("REFERENCIAS:")
            print("="*60)
            for i, ref in enumerate(resultado["references"], 1):
                print(f"[{i}] {ref}")
        
        if resultado.get("reflection"):
            print("\n" + "="*60)
            print("REFLEXIÓN:")
            print("="*60)
            reflection = resultado["reflection"]
            if "missing" in reflection:
                print(f"Falta: {reflection['missing']}")
            if "superfluous" in reflection:
                print(f"Superfluo: {reflection['superfluous']}")

# Uso de la clase
agente = AgenteInvestigador()

resultado = agente.investigar(
    "Investiga sobre las mejores prácticas de DevOps en 2024"
)

# Acceder a datos estructurados
print(f"\nPalabras en respuesta: {len(resultado['answer'].split())}")
print(f"Número de referencias: {len(resultado['references'])}")
print(f"Iteraciones realizadas: {resultado['metadata']['iteraciones']}")
```

## Ejemplos de Integración

### Ejemplo 11: Integración con FastAPI

Crear un endpoint API para el agente.

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import graph
from typing import Optional

app = FastAPI(title="Agente de Investigación API")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    references: list[str]
    metadata: dict

@app.post("/investigar", response_model=QueryResponse)
async def investigar(request: QueryRequest):
    """Endpoint para ejecutar investigaciones."""
    try:
        result = graph.invoke(request.query)
        
        final_msg = result[-1]
        tool_call = final_msg.tool_calls[0]
        args = tool_call["args"]
        
        return QueryResponse(
            answer=args["answer"],
            references=args.get("references", []),
            metadata={
                "iteraciones": len([m for m in result if hasattr(m, 'tool_calls')]),
                "total_mensajes": len(result)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ejecutar: uvicorn main:app --reload
```

### Ejemplo 12: Uso en Script de Análisis

Integrar el agente en un script de análisis más amplio.

```python
from main import graph
import pandas as pd

def analizar_topico(topic: str) -> dict:
    """Analiza un tópico y retorna métricas."""
    query = f"Investiga sobre {topic}"
    result = graph.invoke(query)
    
    data = result[-1].tool_calls[0]["args"]
    answer = data["answer"]
    
    return {
        "topic": topic,
        "answer_length": len(answer),
        "word_count": len(answer.split()),
        "reference_count": len(data.get("references", [])),
        "has_citations": "[1]" in answer,
        "answer": answer,
        "references": data.get("references", [])
    }

# Análisis de múltiples tópicos
topics = [
    "inteligencia artificial",
    "machine learning",
    "deep learning"
]

resultados = [analizar_topico(topic) for topic in topics]

# Crear DataFrame para análisis
df = pd.DataFrame([
    {
        "topic": r["topic"],
        "length": r["answer_length"],
        "words": r["word_count"],
        "references": r["reference_count"]
    }
    for r in resultados
])

print(df)

# Guardar respuestas completas
for resultado in resultados:
    filename = f"{resultado['topic'].replace(' ', '_')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"TÓPICO: {resultado['topic']}\n")
        f.write("="*60 + "\n\n")
        f.write(resultado["answer"])
        f.write("\n\n" + "="*60 + "\n")
        f.write("REFERENCIAS:\n")
        for i, ref in enumerate(resultado["references"], 1):
            f.write(f"[{i}] {ref}\n")
```

## Casos de Uso Específicos

### Caso 1: Investigación Académica

```python
from main import graph

query = """
Investiga sobre el impacto del cambio climático en la biodiversidad marina.

Requisitos:
- Incluye datos científicos y estudios recientes
- Cita fuentes académicas cuando sea posible
- Proporciona ejemplos concretos
- Menciona posibles soluciones
"""

result = graph.invoke(query)
# Procesar resultado para formato académico...
```

### Caso 2: Análisis Competitivo

```python
from main import graph

query = """
Realiza un análisis competitivo de las principales plataformas de CI/CD:

- GitHub Actions
- GitLab CI
- Jenkins
- CircleCI

Compara características, precios y casos de uso.
"""

result = graph.invoke(query)
# Usar resultado para presentación ejecutiva...
```

### Caso 3: Investigación Legal/Regulatoria

```python
from main import graph

query = """
Investiga sobre las regulaciones de protección de datos personales
en México, incluyendo:

- Ley Federal de Protección de Datos Personales en Posesión de Particulares
- Comparación con GDPR
- Obligaciones para empresas
- Sanciones por incumplimiento
"""

result = graph.invoke(query)
# Usar para compliance...
```

## Consejos y Mejores Prácticas

### 1. Consultas Específicas

**✅ Bueno:**
```python
query = "Investiga sobre las ventajas de microservicios vs monolitos para aplicaciones web escalables"
```

**❌ Evitar:**
```python
query = "Microservicios"
```

### 2. Estructurar Consultas

```python
query = """
Investiga sobre X.

Incluye:
- Aspecto 1
- Aspecto 2
- Aspecto 3
"""
```

### 3. Manejo de Errores

```python
from main import graph
from logger import log_error

try:
    result = graph.invoke(query)
except Exception as e:
    log_error(f"Error en investigación: {e}")
    # Manejo de error...
```

### 4. Optimización de Costos

- Limita `MAX_ITERATIONS` según necesidades
- Usa consultas específicas para reducir iteraciones innecesarias
- Cachea resultados de búsquedas comunes

## Recursos Adicionales

- [README Principal](../README.md)
- [Guía de Arquitectura](./ARCHITECTURE.md)
- [Referencia de API](./API_REFERENCE.md)
- [Troubleshooting](./TROUBLESHOOTING.md)



