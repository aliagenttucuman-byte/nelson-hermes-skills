---
name: nelson-context-handoff
description: Protocolo formalizado para pasar contexto comprimido entre subagentes en el meta-orquestador Nelson. Define la estructura del HandoffPacket, estrategias de compresión, patrones de traspaso y anti-patrones comunes.
tags: [context, handoff, multi-agent, compression, orchestrator, nelson]
related_skills: [nelson-meta-orchestrator, nelson-lean-ctx, nelson-task-memory, nelson-ai-agents]
---

# nelson-context-handoff

## Qué es esto

Cuando JARVIS (u otro orquestador) delega trabajo a un subagente especializado —Julián para backend, Mercedes para frontend, Alma para QA— ese agente arranca con contexto vacío. Si no se le pasa información estructurada sobre qué se decidió, qué se construyó y qué está prohibido hacer, el agente va a:

- repetir investigación ya hecha
- contradecir decisiones que ya estaban cerradas
- producir artefactos incompatibles con lo que existe
- hacer preguntas que ya fueron respondidas

El **Context Handoff** es el protocolo formalizado para transferir contexto comprimido entre agentes sin explotar la ventana de contexto del receptor. La idea es: pasarle al agente exactamente lo que necesita para arrancar con intención, no un dump crudo de toda la conversación anterior.

---

## El problema del handoff

### Por qué cada agente arranca en cero

Los subagentes en Nelson son instancias independientes. No tienen memoria compartida por defecto. Cada llamada es stateless a menos que se le inyecte estado explícitamente. Esto es una feature, no un bug: permite paralelismo, aislamiento de fallos y especialización. Pero tiene un costo: el orquestador es responsable de armar el contexto de arranque.

### Qué pasa cuando el handoff es malo

Sin handoff estructurado, los problemas más comunes son:

**Contradicción silenciosa**: JARVIS ya decidió usar PostgreSQL. Julián, sin saberlo, implementa con SQLite porque "es más fácil para empezar". El código funciona, pero el deploy revienta.

**Trabajo duplicado**: El browser agent ya scrapeó la documentación de la API externa. JARVIS no se lo pasa a Julián. Julián vuelve a scrapear.

**Scope creep involuntario**: Mercedes no sabe que el módulo de pagos está fuera de scope en este sprint. Agrega la integración con Stripe porque "tiene sentido".

**Escalación prematura**: Alma no sabe a quién reportar si encuentra un bug bloqueante. Genera un reporte genérico que nadie lee.

### El costo de un contexto demasiado grande

El otro extremo también rompe todo. Pasarle a un subagente toda la conversación de JARVIS con el usuario (3000 tokens de historia) para una tarea de 200 tokens de complejidad real es:

- caro en tokens
- confuso para el agente (señal/ruido malo)
- lento

La solución es compresión intencional: seleccionar qué va en el handoff.

---

## Estructura del HandoffPacket

El HandoffPacket es la unidad mínima de contexto para iniciar un agente con intención.

```
HandoffPacket:
  - goal: str
      Qué debe lograr el agente receptor. Una oración, tiempo verbal imperativo.
      Ejemplo: "Implementar el endpoint POST /api/orders con validación Pydantic y persistencia en PostgreSQL."

  - context_summary: str (máx 500 palabras)
      Qué se hizo hasta acá. Resumen ejecutivo, no transcripción. Incluye:
      - por qué se tomaron las decisiones principales
      - qué intentos fallidos hubo y por qué fallaron
      - el estado actual del sistema

  - decisions_made: list[Decision]
      Decisiones ya cerradas. El agente receptor NO las reabre.
      Cada Decision tiene: qué se decidió, por qué, y quién decidió.

  - artifacts: list[Artifact]
      Archivos, URLs, schemas, configs producidos hasta ahora.
      Cada Artifact tiene: tipo, path o URL, descripción breve.

  - constraints: list[str]
      Qué NO hacer. Qué ya fue descartado y por qué.
      Explícito > implícito. Si no está escrito, el agente lo va a hacer.

  - success_criteria: list[str]
      Cómo saber cuándo la tarea está terminada. Criterios verificables.
      Ejemplo: "Tests pasan", "Endpoint responde 201 con el schema correcto".

  - escalate_to: str
      A quién llamar si el agente se bloquea. JARVIS por defecto.
```

---

## Implementación Python con Pydantic

```python
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator


class ArtifactType(str, Enum):
    FILE = "file"
    URL = "url"
    SCHEMA = "schema"
    CONFIG = "config"
    DATABASE = "database"
    API_SPEC = "api_spec"
    OTHER = "other"


class DecisionStatus(str, Enum):
    LOCKED = "locked"       # No se toca
    TENTATIVE = "tentative" # Puede revisarse con justificación
    DEPRECATED = "deprecated" # Fue reemplazada


class Decision(BaseModel):
    id: str = Field(description="Identificador único, e.g. 'db-engine-choice'")
    summary: str = Field(description="Qué se decidió, en una oración")
    rationale: str = Field(description="Por qué se tomó esta decisión")
    decided_by: str = Field(description="Agente o persona que tomó la decisión")
    decided_at: datetime = Field(default_factory=datetime.utcnow)
    status: DecisionStatus = Field(default=DecisionStatus.LOCKED)
    affects: list[str] = Field(
        default_factory=list,
        description="Qué componentes o módulos afecta esta decisión"
    )

    class Config:
        use_enum_values = True


class Artifact(BaseModel):
    type: ArtifactType
    path: str | None = Field(
        default=None,
        description="Path absoluto en el filesystem, si aplica"
    )
    url: str | None = Field(
        default=None,
        description="URL, si aplica"
    )
    description: str = Field(description="Qué es este artefacto y para qué sirve")
    produced_by: str = Field(description="Agente que lo produjo")
    produced_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Info adicional: versión, hash, tamaño, etc."
    )

    @model_validator(mode="after")
    def path_or_url_required(self) -> "Artifact":
        if self.path is None and self.url is None:
            raise ValueError("Artifact debe tener path o url")
        return self

    class Config:
        use_enum_values = True


class HandoffPacket(BaseModel):
    # Metadata del packet
    packet_id: str = Field(description="UUID del packet, para trazabilidad")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    from_agent: str = Field(description="Agente que genera el handoff")
    to_agent: str = Field(description="Agente receptor")
    task_id: str | None = Field(
        default=None,
        description="ID de tarea en nelson-task-memory, si existe"
    )

    # Core del handoff
    goal: Annotated[str, Field(
        description="Qué debe lograr el agente receptor. Imperativo, claro, acotado.",
        min_length=10,
        max_length=500
    )]
    context_summary: Annotated[str, Field(
        description="Resumen de qué se hizo hasta acá. Máx 500 palabras.",
        max_length=3500  # ~500 palabras en castellano
    )]
    decisions_made: list[Decision] = Field(
        default_factory=list,
        description="Decisiones ya cerradas. No reabrir sin escalar."
    )
    artifacts: list[Artifact] = Field(
        default_factory=list,
        description="Artefactos producidos hasta ahora."
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Qué NO hacer. Qué ya fue descartado."
    )
    success_criteria: list[str] = Field(
        default_factory=list,
        description="Cómo verificar que la tarea está terminada.",
        min_length=1
    )
    escalate_to: str = Field(
        default="JARVIS",
        description="A quién escalar si el agente se bloquea."
    )

    # Opcional: contexto extra para casos especiales
    previous_attempts: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Intentos fallidos anteriores, si los hubo."
    )
    deadline: datetime | None = Field(
        default=None,
        description="Deadline si hay urgencia temporal."
    )

    def to_prompt_prefix(self) -> str:
        """Serializa el HandoffPacket como prefijo de prompt para el agente receptor."""
        lines = [
            "## CONTEXTO DE HANDOFF",
            f"**De**: {self.from_agent} → **Para**: {self.to_agent}",
            f"**Task ID**: {self.task_id or 'N/A'}",
            "",
            "### Tu objetivo",
            self.goal,
            "",
            "### Qué se hizo hasta acá",
            self.context_summary,
        ]

        if self.decisions_made:
            lines += ["", "### Decisiones ya tomadas (NO reabrir)"]
            for d in self.decisions_made:
                locked = "🔒" if d.status == DecisionStatus.LOCKED else "⚠️"
                lines.append(f"{locked} **{d.id}**: {d.summary}")
                lines.append(f"   Rationale: {d.rationale}")

        if self.artifacts:
            lines += ["", "### Artefactos disponibles"]
            for a in self.artifacts:
                loc = a.path or a.url
                lines.append(f"- [{a.type}] {loc} — {a.description}")

        if self.constraints:
            lines += ["", "### Restricciones (qué NO hacer)"]
            for c in self.constraints:
                lines.append(f"- ❌ {c}")

        if self.success_criteria:
            lines += ["", "### Criterios de éxito"]
            for s in self.success_criteria:
                lines.append(f"- ✅ {s}")

        lines += [
            "",
            f"### Escalación",
            f"Si te bloqueás, escalá a: **{self.escalate_to}**",
        ]

        if self.previous_attempts:
            lines += ["", "### Intentos anteriores fallidos"]
            for i, attempt in enumerate(self.previous_attempts, 1):
                lines.append(f"{i}. {attempt.get('summary', 'sin descripción')} — Falló porque: {attempt.get('reason', 'desconocido')}")

        return "\n".join(lines)

    def compress_with_lean_ctx(self) -> "HandoffPacket":
        """
        Integración con nelson-lean-ctx.
        Comprime el context_summary si supera el umbral.
        Ver skill: nelson-lean-ctx
        """
        # Import lazy para no romper si lean-ctx no está disponible
        try:
            from nelson_lean_ctx import compress_text
            if len(self.context_summary.split()) > 400:
                compressed = compress_text(
                    self.context_summary,
                    max_words=400,
                    preserve_decisions=True
                )
                return self.model_copy(update={"context_summary": compressed})
        except ImportError:
            pass  # Si no está disponible, continúa sin comprimir
        return self

    def persist_to_task_memory(self) -> str:
        """
        Integración con nelson-task-memory.
        Persiste el packet para recuperación posterior.
        Retorna el key de storage.
        Ver skill: nelson-task-memory
        """
        try:
            from nelson_task_memory import TaskMemory
            memory = TaskMemory()
            key = f"handoff:{self.packet_id}"
            memory.set(key, self.model_dump(), ttl_hours=24)
            return key
        except ImportError:
            # Fallback: serializar a disco
            import json
            import os
            path = f"/tmp/nelson_handoff_{self.packet_id}.json"
            with open(path, "w") as f:
                json.dump(self.model_dump(mode="json"), f, indent=2, default=str)
            return path

    @classmethod
    def resume_from_task_memory(cls, packet_id: str) -> "HandoffPacket":
        """
        Recupera un HandoffPacket desde nelson-task-memory.
        Usado en Resume Handoff cuando un agente fue interrumpido.
        """
        try:
            from nelson_task_memory import TaskMemory
            memory = TaskMemory()
            data = memory.get(f"handoff:{packet_id}")
            if data:
                return cls.model_validate(data)
        except ImportError:
            pass

        # Fallback: leer desde disco
        import json
        path = f"/tmp/nelson_handoff_{packet_id}.json"
        with open(path) as f:
            return cls.model_validate(json.load(f))
```

---

## Estrategias de compresión

### Qué SÍ incluir

- Decisiones de arquitectura con su rationale (tecnología elegida, estructura de datos, APIs)
- Intentos fallidos y por qué fallaron (evita que el receptor repita el error)
- El estado actual del sistema en una oración: "El modelo User está implementado, falta Order"
- Restricciones de negocio que no son obvias: "El cliente no quiere usar AWS, solo GCP"
- Dependencias críticas: "Este módulo depende de que el schema de DB ya esté migrado"

### Qué NO incluir

- Conversación de exploración que no llevó a nada
- Drafts intermedios de código que fueron descartados
- Razonamientos internos del orquestador (el "cómo pensé esto")
- Logs de errores completos (solo el resumen de qué falló y por qué)
- Documentación externa que el agente puede buscar por sí mismo

### Regla de oro

Si el agente receptor no necesita esa información para tomar una decisión o ejecutar su tarea, no va. El context_summary debe responder tres preguntas:

1. ¿Qué existe ya?
2. ¿Qué se intentó y no funcionó?
3. ¿Por qué las decisiones fueron las que fueron?

### Técnica del "periodista"

Escribí el context_summary como si le estuvieras explicando a un periodista técnico en 2 minutos qué pasó. Pasado, no futuro. Hechos, no intenciones.

---

## Patrones de handoff

### 1. Sequential Handoff (A termina, B arranca)

El patrón más común. A completa su trabajo, genera un HandoffPacket con sus artefactos, y B arranca con ese packet.

```
JARVIS
  ↓ HandoffPacket(goal="implementar API", artifacts=[schema.sql])
Julián
  ↓ HandoffPacket(goal="testear API", artifacts=[api.py, schema.sql])
Alma
```

Cuándo usarlo: tareas con dependencia estricta. Alma no puede testear lo que Julián no terminó.

Consideración clave: el HandoffPacket de A → B debe incluir TODOS los artefactos que B necesita, no solo los que A produjo. Si Alma necesita el schema original además del código de Julián, JARVIS tiene que asegurarse de que el packet de Julián incluya ambos.

### 2. Parallel Handoff (múltiples agentes arrancan simultáneamente)

JARVIS construye un HandoffPacket base con contexto compartido, y crea variantes especializadas para cada agente.

```
JARVIS
  ├─ HandoffPacket(goal="backend API", to="Julián")
  └─ HandoffPacket(goal="frontend mockups", to="Mercedes")
```

El packet base contiene: decisiones globales de arquitectura, constraints de negocio, criterios de éxito del sistema completo.

Cada packet especializado agrega: el goal específico, artifacts relevantes para ese agente, constraints adicionales del dominio.

Precaución: los agentes paralelos NO se coordinan entre sí a menos que se diseñe explícitamente. Si Julián y Mercedes necesitan acordar un contrato de API, eso debe estar en las decisions_made del packet de ambos, no dejarlo librado al azar.

```python
def create_parallel_packets(
    base_packet: HandoffPacket,
    assignments: list[tuple[str, str, list[str]]]  # (agent, goal, extra_constraints)
) -> list[HandoffPacket]:
    """
    Crea múltiples HandoffPackets a partir de uno base.
    assignments: [(to_agent, goal, extra_constraints), ...]
    """
    import uuid
    packets = []
    for to_agent, goal, extra_constraints in assignments:
        packet = base_packet.model_copy(update={
            "packet_id": str(uuid.uuid4()),
            "to_agent": to_agent,
            "goal": goal,
            "constraints": base_packet.constraints + extra_constraints,
        })
        packets.append(packet)
    return packets
```

### 3. Hierarchical Handoff (orquestador → especialista → sub-especialista)

Cuando una tarea es suficientemente compleja, el especialista se convierte en sub-orquestador y delega a un nivel más abajo.

```
JARVIS
  ↓ HandoffPacket(goal="sistema de notificaciones completo")
Julián (actúa como sub-orquestador)
  ├─ HandoffPacket(goal="modelo de datos y migrations")
  │    → agente-db
  └─ HandoffPacket(goal="servicio de envío de emails")
       → agente-email
```

Regla crítica: cada nivel del árbol comprime el contexto. Julián no le pasa a agente-db toda la conversación de JARVIS. Le pasa solo lo que agente-db necesita.

El `escalate_to` en los packets de agente-db y agente-email apunta a Julián, no a JARVIS. JARVIS solo entra si Julián no puede resolver.

### 4. Resume Handoff (agente interrumpido, retoma con estado)

Cuando un agente es interrumpido (timeout, error, pausa deliberada), necesita retomar sin repetir trabajo.

```python
# Al interrumpir
packet.persist_to_task_memory()

# Al reanudar
resumed_packet = HandoffPacket.resume_from_task_memory(packet_id)

# Modificar el goal para reflejar el estado actual
partial_work_description = "El endpoint GET /orders está implementado. Falta POST /orders."
resumed_packet = resumed_packet.model_copy(update={
    "context_summary": f"{resumed_packet.context_summary}\n\nESTADO AL RETOMAR: {partial_work_description}",
    "goal": "Completar implementación POST /orders (GET ya está hecho y testeado)"
})
```

El packet de resume debe agregar al context_summary una sección "ESTADO AL RETOMAR" que describe exactamente qué estaba hecho y qué faltaba.

---

## Integración con nelson-lean-ctx

`nelson-lean-ctx` provee utilidades para comprimir texto preservando señal semántica alta. Se usa principalmente para comprimir el `context_summary` cuando la conversación previa fue larga.

```python
from nelson_lean_ctx import LeanCtxCompressor

def build_handoff_packet(
    conversation_history: list[dict],
    goal: str,
    decisions: list[Decision],
    artifacts: list[Artifact],
    **kwargs
) -> HandoffPacket:
    """
    Construye un HandoffPacket comprimiendo la historia de conversación.
    """
    import uuid

    compressor = LeanCtxCompressor(
        max_words=400,
        preserve_keys=["decisión", "elegimos", "descartamos", "falló", "error", "usamos"],
        language="es"
    )

    # Extraer el texto relevante de la historia
    raw_summary = "\n".join([
        msg["content"] for msg in conversation_history
        if msg["role"] in ("assistant", "user") and len(msg["content"]) > 50
    ])

    compressed_summary = compressor.compress(raw_summary)

    return HandoffPacket(
        packet_id=str(uuid.uuid4()),
        from_agent=kwargs.get("from_agent", "JARVIS"),
        to_agent=kwargs.get("to_agent", ""),
        goal=goal,
        context_summary=compressed_summary,
        decisions_made=decisions,
        artifacts=artifacts,
        constraints=kwargs.get("constraints", []),
        success_criteria=kwargs.get("success_criteria", []),
        escalate_to=kwargs.get("escalate_to", "JARVIS"),
    )
```

Configuración recomendada de LeanCtxCompressor para handoffs:
- `max_words=400`: deja margen para que el agente receptor tenga contexto propio
- `preserve_keys`: incluir palabras que marcan decisiones y descartados
- `language="es"`: el compressor ajusta stop words al castellano

---

## Integración con nelson-task-memory

`nelson-task-memory` persiste el estado de los handoffs para:
- recuperación ante fallos
- auditoría de qué agente hizo qué
- debugging de por qué un agente tomó una decisión

```python
from nelson_task_memory import TaskMemory, TaskStatus

class HandoffTracker:
    """
    Trackea el ciclo de vida de los handoffs para una tarea compleja.
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.memory = TaskMemory()

    def register_handoff(self, packet: HandoffPacket) -> None:
        """Registra que se emitió un handoff."""
        key = f"task:{self.task_id}:handoffs"
        existing = self.memory.get(key) or []
        existing.append({
            "packet_id": packet.packet_id,
            "from": packet.from_agent,
            "to": packet.to_agent,
            "goal": packet.goal,
            "created_at": packet.created_at.isoformat(),
            "status": "pending"
        })
        self.memory.set(key, existing)

    def mark_completed(self, packet_id: str, output_summary: str) -> None:
        """Marca un handoff como completado con el resumen del output."""
        key = f"task:{self.task_id}:handoffs"
        handoffs = self.memory.get(key) or []
        for h in handoffs:
            if h["packet_id"] == packet_id:
                h["status"] = "completed"
                h["output_summary"] = output_summary
                h["completed_at"] = datetime.utcnow().isoformat()
        self.memory.set(key, handoffs)

    def mark_failed(self, packet_id: str, reason: str) -> None:
        """Marca un handoff como fallido para que JARVIS pueda reintentarlo."""
        key = f"task:{self.task_id}:handoffs"
        handoffs = self.memory.get(key) or []
        for h in handoffs:
            if h["packet_id"] == packet_id:
                h["status"] = "failed"
                h["failure_reason"] = reason
        self.memory.set(key, handoffs)

    def get_completed_outputs(self) -> list[dict]:
        """Retorna los outputs de todos los handoffs completados."""
        key = f"task:{self.task_id}:handoffs"
        handoffs = self.memory.get(key) or []
        return [h for h in handoffs if h.get("status") == "completed"]
```

---

## Ejemplos concretos en el workflow de Nelson

### Ejemplo 1: JARVIS → Julián (tarea de backend)

```python
from datetime import datetime
import uuid

jarvis_a_julian = HandoffPacket(
    packet_id=str(uuid.uuid4()),
    from_agent="JARVIS",
    to_agent="Julián",
    task_id="task-2024-orders-api",
    goal="Implementar el endpoint POST /api/v1/orders con validación Pydantic, persistencia en PostgreSQL y retorno HTTP 201 con el objeto Order creado.",
    context_summary="""
El cliente pidió un sistema de órdenes para su e-commerce. Decidimos usar FastAPI + PostgreSQL.
El schema de la tabla orders fue diseñado y está en /migrations/001_create_orders.sql.
Ya existe el modelo de User en /app/models/user.py como referencia de estilo.
El entorno de dev tiene PostgreSQL corriendo en localhost:5432, base de datos 'nelson_dev'.
Intentamos usar SQLAlchemy async pero tuvimos problemas con el pool de conexiones en tests;
quedamos en usar SQLAlchemy sync con sessionmaker por ahora.
    """.strip(),
    decisions_made=[
        Decision(
            id="db-engine",
            summary="PostgreSQL como base de datos principal",
            rationale="El cliente tiene infraestructura PostgreSQL existente y el equipo tiene experiencia",
            decided_by="JARVIS + cliente",
            status=DecisionStatus.LOCKED,
            affects=["orders", "users", "products"]
        ),
        Decision(
            id="orm-style",
            summary="SQLAlchemy sync con sessionmaker, no async",
            rationale="SQLAlchemy async tuvo problemas de pool en el entorno de tests del cliente",
            decided_by="Julián (iteración anterior)",
            status=DecisionStatus.LOCKED,
            affects=["todos los modelos"]
        ),
        Decision(
            id="framework",
            summary="FastAPI para la capa HTTP",
            rationale="Tipado nativo, generación automática de docs, equipo lo conoce",
            decided_by="JARVIS",
            status=DecisionStatus.LOCKED,
            affects=["todos los endpoints"]
        ),
    ],
    artifacts=[
        Artifact(
            type=ArtifactType.FILE,
            path="/migrations/001_create_orders.sql",
            description="Schema de la tabla orders. Ya está migrado en dev.",
            produced_by="JARVIS"
        ),
        Artifact(
            type=ArtifactType.FILE,
            path="/app/models/user.py",
            description="Modelo User como referencia de estilo y convenciones ORM.",
            produced_by="JARVIS"
        ),
    ],
    constraints=[
        "No usar SQLAlchemy async — ya se probó y falla en los tests del cliente",
        "No cambiar el schema de la tabla orders sin consultar a JARVIS primero",
        "No implementar el endpoint de payments en este ticket (está fuera de scope)",
        "No agregar dependencias nuevas al pyproject.toml sin aprobación",
    ],
    success_criteria=[
        "POST /api/v1/orders retorna 201 con el objeto Order serializado",
        "POST /api/v1/orders retorna 422 con errores de validación si el body es inválido",
        "El order queda persistido en la tabla orders de PostgreSQL",
        "Existe al menos un test de integración que verifica el happy path",
        "El código sigue el estilo de /app/models/user.py",
    ],
    escalate_to="JARVIS"
)
```

### Ejemplo 2: JARVIS → Mercedes (tarea de frontend)

```python
jarvis_a_mercedes = HandoffPacket(
    packet_id=str(uuid.uuid4()),
    from_agent="JARVIS",
    to_agent="Mercedes",
    task_id="task-2024-orders-ui",
    goal="Crear el componente OrderForm en React que permite crear una nueva orden, llamando al endpoint POST /api/v1/orders.",
    context_summary="""
El backend de órdenes está siendo implementado por Julián en paralelo.
El contrato de la API ya está definido: POST /api/v1/orders recibe { customer_id, items: [{product_id, quantity}] }.
El diseño de la UI fue aprobado por el cliente: usar el componente Form existente del design system interno.
El proyecto usa React 18 + TypeScript + TanStack Query para fetching.
No hay diseño para estados de error todavía; usar el componente ErrorBanner existente como fallback.
    """.strip(),
    decisions_made=[
        Decision(
            id="api-contract",
            summary="POST /api/v1/orders acepta { customer_id, items: [{product_id, quantity}] }",
            rationale="Definido por Julián y aprobado por JARVIS",
            decided_by="Julián + JARVIS",
            status=DecisionStatus.LOCKED,
            affects=["OrderForm", "OrderService"]
        ),
        Decision(
            id="frontend-stack",
            summary="React 18 + TypeScript + TanStack Query",
            rationale="Stack existente del proyecto",
            decided_by="equipo",
            status=DecisionStatus.LOCKED,
            affects=["todos los componentes"]
        ),
    ],
    artifacts=[
        Artifact(
            type=ArtifactType.API_SPEC,
            url="http://localhost:8000/docs#/orders/create_order",
            description="Swagger auto-generado del endpoint de órdenes (disponible cuando Julián termine)",
            produced_by="Julián"
        ),
        Artifact(
            type=ArtifactType.FILE,
            path="/src/components/Form/Form.tsx",
            description="Componente Form del design system interno. Usarlo como base.",
            produced_by="equipo"
        ),
    ],
    constraints=[
        "No crear un Form custom desde cero — usar el componente Form del design system",
        "No llamar directamente a fetch — usar TanStack Query (useMutation)",
        "No implementar la vista de listado de órdenes en este ticket",
        "No cambiar el contrato de la API sin coordinar con Julián vía JARVIS",
    ],
    success_criteria=[
        "El componente OrderForm renderiza sin errores de TypeScript",
        "El formulario llama a POST /api/v1/orders al hacer submit",
        "Muestra estado de loading mientras la request está en vuelo",
        "Muestra ErrorBanner si la API retorna error",
        "Muestra mensaje de éxito si la API retorna 201",
    ],
    escalate_to="JARVIS"
)
```

### Ejemplo 3: Julián → Alma (QA handoff después de backend terminado)

```python
julian_a_alma = HandoffPacket(
    packet_id=str(uuid.uuid4()),
    from_agent="Julián",
    to_agent="Alma",
    task_id="task-2024-orders-api",
    goal="Realizar QA del endpoint POST /api/v1/orders: verificar happy path, casos de error, validaciones y edge cases de concurrencia.",
    context_summary="""
Implementé el endpoint POST /api/v1/orders con FastAPI + SQLAlchemy sync.
El endpoint valida con Pydantic (OrderCreateRequest), persiste en PostgreSQL y retorna OrderResponse con HTTP 201.
Hay tests unitarios para el modelo y tests de integración para el happy path.
NO implementé manejo de concurrencia (dos órdenes simultáneas del mismo customer) — eso está fuera de scope según JARVIS.
El endpoint tiene un bug conocido: si items es una lista vacía, retorna 500 en lugar de 422. Lo documenté en el código con un TODO.
    """.strip(),
    decisions_made=[
        Decision(
            id="concurrency-out-of-scope",
            summary="El manejo de concurrencia está fuera de scope de este ticket",
            rationale="Definido por JARVIS al inicio del ticket",
            decided_by="JARVIS",
            status=DecisionStatus.LOCKED,
            affects=["QA scope"]
        ),
    ],
    artifacts=[
        Artifact(
            type=ArtifactType.FILE,
            path="/app/api/orders.py",
            description="Implementación del endpoint POST /api/v1/orders",
            produced_by="Julián"
        ),
        Artifact(
            type=ArtifactType.FILE,
            path="/tests/test_orders_integration.py",
            description="Tests de integración existentes. Correr como referencia base.",
            produced_by="Julián"
        ),
    ],
    constraints=[
        "No reportar bugs de concurrencia como bloqueantes — están fuera de scope",
        "No modificar el código de implementación directamente — solo reportar",
    ],
    success_criteria=[
        "Happy path verificado: POST con datos válidos retorna 201 y persiste",
        "Validación verificada: POST con body inválido retorna 422 con detalle de error",
        "Bug de lista vacía documentado en el reporte como P2 (no bloqueante)",
        "Reporte de QA entregado a JARVIS con lista de bugs encontrados y severidad",
    ],
    previous_attempts=[],
    escalate_to="JARVIS"
)
```

### Ejemplo 4: Browser agent → JARVIS (handoff de resultados)

```python
browser_a_jarvis = HandoffPacket(
    packet_id=str(uuid.uuid4()),
    from_agent="browser-agent",
    to_agent="JARVIS",
    task_id="task-2024-research-payment-providers",
    goal="Entregarte los resultados del research sobre proveedores de pagos para que tomes la decisión de cuál integrar.",
    context_summary="""
Investigué tres proveedores de pagos según tu pedido: Stripe, MercadoPago y Payoneer.
Scrapié la documentación oficial de cada uno y los términos de servicio.
Hallazgos clave:
- Stripe: mejor API, pero requiere cuenta bancaria USA. No aplica para el cliente (está en Argentina).
- MercadoPago: soporta Argentina, tiene SDK Python maduro, comisión 3.5% por transacción.
- Payoneer: orientado a B2B, no tiene checkout embebido, no aplica para e-commerce retail.
Conclusión: MercadoPago es el único viable para el cliente. Stripe queda descartado por restricción geográfica.
    """.strip(),
    decisions_made=[],  # El browser agent no toma decisiones, las reporta
    artifacts=[
        Artifact(
            type=ArtifactType.FILE,
            path="/tmp/research/payment_providers_comparison.md",
            description="Comparación completa de los tres proveedores con links a documentación",
            produced_by="browser-agent"
        ),
        Artifact(
            type=ArtifactType.URL,
            url="https://www.mercadopago.com.ar/developers/es/docs",
            description="Documentación oficial de MercadoPago Argentina",
            produced_by="browser-agent"
        ),
    ],
    constraints=[
        "Stripe está descartado por restricción geográfica (requiere cuenta bancaria USA)",
        "Payoneer está descartado por no tener checkout embebido para retail",
    ],
    success_criteria=[
        "JARVIS toma una decisión sobre qué proveedor de pagos usar",
        "La decisión queda registrada en decisions_made para el próximo handoff",
    ],
    escalate_to="JARVIS"  # El browser agent siempre escala a JARVIS
)
```

---

## Anti-patterns: qué rompe los handoffs

### Anti-pattern 1: El context dump

Pasarle al agente receptor toda la conversación cruda como context_summary.

Por qué es malo: el receptor tiene que procesar 3000 tokens de ruido para extraer 300 tokens de señal. La relación señal/ruido baja, el costo sube, la calidad baja.

Cómo evitarlo: el context_summary es un resumen ejecutivo, no una transcripción. Si sentís la necesidad de copiar y pegar mensajes enteros, usá nelson-lean-ctx primero.

### Anti-pattern 2: Decisiones sin rationale

```python
# ❌ MAL
Decision(id="db", summary="PostgreSQL", rationale="", decided_by="JARVIS")

# ✅ BIEN
Decision(id="db", summary="PostgreSQL", rationale="Cliente tiene infraestructura existente y el equipo tiene experiencia con PostgreSQL en proyectos similares", decided_by="JARVIS")
```

Sin rationale, el agente receptor puede "reabrir" la decisión porque no entiende por qué se tomó. Con rationale, puede evaluar si el contexto cambió lo suficiente para justificar escalar.

### Anti-pattern 3: Constraints implícitos

```python
# ❌ MAL — asumir que Julián "ya sabe" que no puede tocar payments
constraints=[]

# ✅ BIEN — todo lo que NO debe hacer, explícito
constraints=[
    "No implementar el módulo de payments — está fuera de scope de este sprint",
    "No agregar dependencias nuevas sin aprobación",
]
```

Si no está escrito, el agente lo va a hacer. La ambigüedad en constraints es el origen del 80% de los bugs de coordinación.

### Anti-pattern 4: Success criteria vagos

```python
# ❌ MAL
success_criteria=["que funcione"]

# ✅ BIEN
success_criteria=[
    "POST /api/v1/orders retorna 201 con OrderResponse schema",
    "POST con body inválido retorna 422",
    "Al menos un test de integración pasa en CI",
]
```

"Que funcione" no es verificable. El agente no puede saber cuándo parar.

### Anti-pattern 5: Escalate_to apuntando al agente equivocado

```python
# ❌ MAL — agente-db escalando directo al usuario final
escalate_to="cliente"

# ✅ BIEN — escalar al nivel inmediatamente superior
escalate_to="Julián"  # Julián escalará a JARVIS si no puede resolver
```

La cadena de escalación debe seguir la jerarquía del árbol de handoffs. Si agente-db escala directamente al cliente, Julián y JARVIS no se enteran.

### Anti-pattern 6: Packets desactualizados en parallel handoff

En un parallel handoff, si JARVIS actualiza una decisión después de emitir los packets, los agentes que ya recibieron sus packets trabajan con información stale.

Solución: antes de emitir packets paralelos, verificar que todas las decisiones de arquitectura compartidas estén cerradas. Si una decisión cambia después de emitir, JARVIS debe notificar a todos los agentes activos con un packet de corrección.

---

## Pitfalls comunes

**El packet demasiado optimista**: El context_summary dice "todo funciona" cuando en realidad hay un bug conocido que el receptor va a encontrar. Siempre documentar bugs conocidos y limitaciones en el context_summary o en previous_attempts.

**Artifacts que no existen todavía**: En un parallel handoff, Mercedes recibe un artifact que apunta al Swagger de Julián que todavía no fue generado. El artifact debe indicar su estado: "disponible cuando Julián termine".

**Goals ambiguos con múltiples interpretaciones válidas**: "Mejorar el rendimiento del endpoint" puede significar caching, optimizar queries o cambiar la arquitectura. El goal debe ser lo suficientemente específico para que solo haya una interpretación correcta.

**No persistir en task-memory en tareas largas**: Si el agente trabaja por 2 horas y se interrumpe, sin persistencia en task-memory se pierde todo el estado. Para tareas de más de 30 minutos estimados, persistir con `persist_to_task_memory()` al inicio y al completar cada sub-tarea.

**Olvidar actualizar decisions_made al encadenar handoffs**: Cuando Julián termina y emite el packet para Alma, debe incluir las decisiones que él tomó durante su trabajo (no solo las que recibió de JARVIS). Las decisiones de implementación de Julián son contexto crítico para el QA de Alma.

**Packets de resume sin sección "ESTADO AL RETOMAR"**: Cuando un agente retoma, el context_summary original describe el estado al inicio de la tarea, no al momento de la interrupción. Sin actualizar el context_summary con el estado actual, el agente puede repetir trabajo ya hecho.

---

## Referencias rápidas

- Skill relacionado para compresión de contexto: `nelson-lean-ctx`
- Skill relacionado para persistencia de estado: `nelson-task-memory`
- Skill del meta-orquestador: `nelson-meta-orchestrator`
- Definición de los agentes (Julián, Mercedes, Alma, etc.): `nelson-ai-agents`
