---
name: nelson-agent-routing
description: Lógica declarativa de routing para el meta-orquestador de Nelson. Dado un input o goal, determina qué agente o skill es el correcto, con scoring de confianza, soporte multi-agente y fallback LLM.
tags: [routing, agent-selection, meta-agent, orchestrator, nelson]
related_skills: [nelson-meta-orchestrator, nelson-ai-agents, nelson-spec-driven-workflow]
---

# Nelson Agent Routing

## ¿Qué es esto?

El routing de agentes es la lógica que decide, dado un input o goal del usuario, **qué agente o skill debe ejecutarlo**. Actualmente JARVIS hace esto por intuición — conoce los agentes disponibles y decide en base a contexto implícito. Esta skill lo hace **explícito, codificado y reproducible**.

El objetivo es que cualquier componente del stack Nelson (el meta-orquestador, un workflow n8n, un script Python) pueda preguntarle al router:

> "Dado este goal: 'armar un endpoint en FastAPI para subir archivos', ¿quién lo resuelve?"

Y el router responde con un resultado estructurado: agente(s), confianza, razón.

### ¿Por qué importa?

- **Escalabilidad**: cuando hay 20+ agentes, la intuición no escala.
- **Auditabilidad**: cada decisión de routing queda loggeada con su razón.
- **Consistencia**: misma tarea → mismo agente, siempre (salvo que la taxonomía cambie).
- **Composabilidad**: tareas multi-agente se pueden descomponer y rutear en paralelo o en secuencia.


---


## Taxonomía de Routing

Cada tarea se clasifica en una **categoría**. La categoría determina qué agente o skill la resuelve.

| Categoría  | Palabras clave típicas                                      | Agente / Skill principal                          |
|------------|-------------------------------------------------------------|---------------------------------------------------|
| SPEC       | spec, user story, historia de usuario, API design, contrato, OpenAPI, PRD, requerimiento | nelson-spec-driven-workflow, spec-driven-development |
| BACKEND    | Python, FastAPI, endpoint, modelo, ORM, base de datos, Postgres, SQLite, API REST, celery, pydantic | Julián (agency-ai-engineer)                       |
| FRONTEND   | React, Vite, componente, UI, interfaz, CSS, Tailwind, hook, store, página, formulario | Mercedes (nelson-frontend-agent)                  |
| BROWSER    | scraping, playwright, selenium, formulario, E2E, automatización web, click, screenshot de web | nelson-browser-agent                              |
| INFRA      | Docker, docker-compose, CI/CD, GitHub Actions, deploy, nginx, tunnel, cloudflare, VPS, servidor | nelson-ci-cd, nelson-cloudflare-tunnel-deploy     |
| RAG/AI     | embedding, vector, Chroma, Pinecone, RAG, LLM, OpenAI, Anthropic, langchain, indexar, buscar documentos | nelson-rag-pipeline, nelson-llm-generation        |
| QA         | test, testing, pytest, vitest, coverage, validar, revisar código, code review, calidad | nelson-frontend-testing, nelson-code-quality      |
| DOCS       | documentar, README, wiki, brainstorming, lluvia de ideas, explicar, escribir guía | nelson-documentation, nelson-brainstorming        |
| VISION     | imagen, OCR, screenshot, procesar foto, visión, detectar texto, analizar imagen | nelson-ai-vision                                  |
| AUDIO      | transcribir, audio, mp3, wav, voz, TTS, speech, whisper     | nelson-audio-processing                           |
| EXTERNAL   | WhatsApp, Telegram, n8n, webhook, notificación, mensaje, integración externa | nelson-whatsapp-gateway, nelson-automation-n8n    |
| SECURITY   | auth, autenticación, JWT, secretos, .env, permisos, RBAC, vulnerabilidad, auditoría de seguridad | nelson-security, nelson-workflow-security         |

> **Nota**: la categoría SPEC siempre se evalúa **primero**. Si el goal habla de "definir", "diseñar", "especificar" o "planear" algo, es SPEC antes que BACKEND o FRONTEND.


---


## Árbol de Decisión (ASCII)

```
INPUT: goal / tarea del usuario
           |
           v
   ┌───────────────────┐
   │  ¿Habla de definir │
   │  / especificar /   │──── SÍ ──→ SPEC
   │  diseñar / PRD?    │
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │  ¿Menciona Python │
   │  / FastAPI / DB /  │──── SÍ ──→ BACKEND
   │  endpoint / ORM?   │
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │  ¿Menciona React  │
   │  / Vite / UI /     │──── SÍ ──→ FRONTEND
   │  componente / CSS? │
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │  ¿Es scraping /   │
   │  automatización   │──── SÍ ──→ BROWSER
   │  web / E2E?       │
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │  ¿Docker / CI/CD  │
   │  / deploy / infra │──── SÍ ──→ INFRA
   │  / tunnel?        │
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │  ¿LLM / RAG /     │
   │  embedding /      │──── SÍ ──→ RAG/AI
   │  vector DB?       │
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │  ¿Test / review / │
   │  validar / QA?    │──── SÍ ──→ QA
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │  ¿Doc / README /  │
   │  brainstorming?   │──── SÍ ──→ DOCS
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │ ¿Imagen / OCR /   │
   │ screenshot?       │──── SÍ ──→ VISION
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │ ¿Audio / voz /    │
   │ transcribir?      │──── SÍ ──→ AUDIO
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │ ¿WhatsApp / n8n / │
   │ webhook / externa?│──── SÍ ──→ EXTERNAL
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │ ¿Auth / secretos  │
   │ / seguridad?      │──── SÍ ──→ SECURITY
   └───────────────────┘
           │ NO
           v
   ┌───────────────────┐
   │  confidence < 0.5  │──── SÍ ──→ LLM FALLBACK
   │  o sin match       │            (clasifica con LLM)
   └───────────────────┘
           │ confidence >= 0.5
           v
      ROUTING RESULT
```


---


## Implementación Python

### Estructura de archivos

```
nelson_routing/
├── __init__.py
├── router.py          # Router principal
├── taxonomy.py        # Definición de categorías y keywords
├── scoring.py         # Lógica de confidence scoring
├── llm_fallback.py    # Fallback con LLM cuando score es bajo
├── multi_agent.py     # Detección y manejo de tareas multi-agente
└── models.py          # Dataclasses / Pydantic models
```

---

### `models.py`

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Category(str, Enum):
    SPEC = "SPEC"
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"
    BROWSER = "BROWSER"
    INFRA = "INFRA"
    RAG_AI = "RAG/AI"
    QA = "QA"
    DOCS = "DOCS"
    VISION = "VISION"
    AUDIO = "AUDIO"
    EXTERNAL = "EXTERNAL"
    SECURITY = "SECURITY"
    UNKNOWN = "UNKNOWN"


@dataclass
class RoutingResult:
    category: Category
    agents: list[str]           # agentes/skills asignados
    confidence: float           # 0.0 a 1.0
    reason: str                 # razón human-readable
    matched_keywords: list[str] # keywords que dispararon el match
    is_multi_agent: bool = False
    sub_tasks: list["RoutingResult"] = field(default_factory=list)
    llm_fallback_used: bool = False
```

---

### `taxonomy.py`

```python
from .models import Category

# Cada categoría tiene:
# - keywords: strings para match exacto (lowercase)
# - patterns: regex para match más flexible
# - agents: agentes/skills que la resuelven
# - priority: orden de evaluación (menor = primero)

TAXONOMY: dict[Category, dict] = {
    Category.SPEC: {
        "priority": 1,
        "keywords": [
            "spec", "especificación", "user story", "historia de usuario",
            "api design", "diseño de api", "contrato", "openapi", "swagger",
            "prd", "product requirement", "requerimiento", "requerimientos",
            "planear", "planificar", "definir flujo", "definir api",
            "casos de uso", "acceptance criteria", "criterios de aceptación",
        ],
        "agents": ["nelson-spec-driven-workflow", "spec-driven-development"],
    },
    Category.BACKEND: {
        "priority": 2,
        "keywords": [
            "python", "fastapi", "flask", "django", "endpoint", "api rest",
            "base de datos", "database", "postgres", "postgresql", "sqlite",
            "mysql", "mongodb", "orm", "sqlalchemy", "alembic", "celery",
            "pydantic", "modelo", "schema", "migration", "migración",
            "backend", "servidor", "service", "servicio", "microservicio",
        ],
        "agents": ["julian-agent", "agency-ai-engineer"],
    },
    Category.FRONTEND: {
        "priority": 3,
        "keywords": [
            "react", "vite", "vue", "svelte", "componente", "component",
            "ui", "interfaz", "interfaz de usuario", "css", "tailwind",
            "sass", "styled-components", "hook", "useState", "useEffect",
            "store", "zustand", "redux", "página", "page", "formulario",
            "form", "frontend", "spa", "layout", "diseño visual",
        ],
        "agents": ["mercedes-agent", "nelson-frontend-agent"],
    },
    Category.BROWSER: {
        "priority": 4,
        "keywords": [
            "scraping", "scraper", "playwright", "selenium", "puppeteer",
            "automatización web", "web automation", "formulario web",
            "e2e", "end to end", "end-to-end", "click", "navegador",
            "browser", "crawl", "crawling", "raspar", "extraer datos web",
        ],
        "agents": ["nelson-browser-agent"],
    },
    Category.INFRA: {
        "priority": 5,
        "keywords": [
            "docker", "docker-compose", "dockerfile", "ci/cd", "github actions",
            "gitlab ci", "deploy", "deployment", "desplegar", "servidor",
            "nginx", "caddy", "traefik", "tunnel", "cloudflare", "vps",
            "kubernetes", "k8s", "helm", "terraform", "ansible",
            "pipeline", "infra", "infraestructura", "contenedor",
        ],
        "agents": ["nelson-ci-cd", "nelson-cloudflare-tunnel-deploy"],
    },
    Category.RAG_AI: {
        "priority": 6,
        "keywords": [
            "embedding", "embeddings", "vector", "vectores", "chroma",
            "pinecone", "weaviate", "rag", "retrieval", "langchain",
            "llm", "openai", "anthropic", "gpt", "claude", "gemini",
            "indexar", "indexar documentos", "buscar documentos",
            "semantic search", "búsqueda semántica", "fine-tuning",
            "prompt engineering", "chain", "agent llm",
        ],
        "agents": ["nelson-rag-pipeline", "nelson-llm-generation"],
    },
    Category.QA: {
        "priority": 7,
        "keywords": [
            "test", "testing", "pytest", "unittest", "vitest", "jest",
            "coverage", "cobertura", "validar", "validación", "revisar código",
            "code review", "calidad", "quality", "qa", "bug", "fix",
            "regression", "regresión", "integration test", "unit test",
        ],
        "agents": ["nelson-frontend-testing", "nelson-code-quality"],
    },
    Category.DOCS: {
        "priority": 8,
        "keywords": [
            "documentar", "documentación", "readme", "wiki", "guía",
            "tutorial", "brainstorming", "lluvia de ideas", "explicar",
            "escribir guía", "manual", "changelog", "notas de versión",
            "contributing", "onboarding", "arquitectura doc",
        ],
        "agents": ["nelson-documentation", "nelson-brainstorming"],
    },
    Category.VISION: {
        "priority": 9,
        "keywords": [
            "imagen", "image", "ocr", "reconocimiento de texto",
            "screenshot", "captura de pantalla", "visión", "vision",
            "detectar texto", "analizar imagen", "procesar foto",
            "cv", "computer vision", "yolo", "detección de objetos",
        ],
        "agents": ["nelson-ai-vision"],
    },
    Category.AUDIO: {
        "priority": 10,
        "keywords": [
            "audio", "transcribir", "transcripción", "mp3", "wav",
            "voz", "speech", "tts", "text to speech", "whisper",
            "reconocimiento de voz", "síntesis de voz", "podcast",
        ],
        "agents": ["nelson-audio-processing"],
    },
    Category.EXTERNAL: {
        "priority": 11,
        "keywords": [
            "whatsapp", "telegram", "discord", "slack", "n8n",
            "webhook", "notificación", "mensaje", "integración externa",
            "zapier", "make", "integromat", "api externa", "third party",
        ],
        "agents": ["nelson-whatsapp-gateway", "nelson-automation-n8n"],
    },
    Category.SECURITY: {
        "priority": 12,
        "keywords": [
            "auth", "autenticación", "authentication", "authorization",
            "jwt", "oauth", "secretos", "secrets", ".env", "permisos",
            "rbac", "roles", "vulnerabilidad", "auditoría de seguridad",
            "security review", "cve", "owasp", "ssl", "tls", "https",
        ],
        "agents": ["nelson-security", "nelson-workflow-security"],
    },
}
```

---

### `scoring.py`

```python
import math
from .models import Category, RoutingResult
from .taxonomy import TAXONOMY


def score_category(goal: str, category: Category) -> tuple[float, list[str]]:
    """
    Calcula el score de confianza para una categoría dado el goal.

    Returns:
        (confidence: float 0-1, matched_keywords: list[str])

    Lógica de scoring:
    - Cada keyword encontrada suma puntos.
    - Keywords más largas (más específicas) pesan más.
    - Múltiples keywords de la misma categoría aumentan la confianza.
    - La confianza se normaliza entre 0 y 1 con una función sigmoide suave.
    """
    goal_lower = goal.lower()
    config = TAXONOMY[category]
    keywords = config["keywords"]

    matched = []
    raw_score = 0.0

    for kw in keywords:
        if kw in goal_lower:
            matched.append(kw)
            # Keywords más largas y específicas pesan más
            weight = 1.0 + (len(kw.split()) - 1) * 0.5
            raw_score += weight

    if not matched:
        return 0.0, []

    # Normalizar: usar sigmoide para que el score quede suave entre 0 y 1
    # Con 1 keyword corta → ~0.7, con 3+ keywords → ~0.95
    confidence = 1 / (1 + math.exp(-0.8 * (raw_score - 1.5)))
    confidence = min(confidence, 0.99)  # nunca llegamos a 1.0 con solo keywords

    return round(confidence, 3), matched


def rank_categories(goal: str) -> list[tuple[Category, float, list[str]]]:
    """
    Rankea todas las categorías por score descendente.
    Retorna lista de (category, confidence, matched_keywords).
    """
    results = []
    for category in Category:
        if category == Category.UNKNOWN:
            continue
        conf, matched = score_category(goal, category)
        if conf > 0:
            results.append((category, conf, matched))

    # Ordenar por confidence desc, luego por priority asc (en caso de empate)
    priority_map = {cat: data["priority"] for cat, data in TAXONOMY.items()}
    results.sort(key=lambda x: (-x[1], priority_map.get(x[0], 99)))
    return results
```

---

### `llm_fallback.py`

```python
import json
from .models import Category, RoutingResult
from .taxonomy import TAXONOMY

# Asumir que el equipo Nelson usa un cliente LLM estándar
# (puede ser OpenAI, Anthropic, o el wrapper interno de Nelson)
try:
    from nelson_core.llm import chat_completion  # cliente interno Nelson
except ImportError:
    from openai import OpenAI
    _client = OpenAI()

    def chat_completion(messages: list[dict], model: str = "gpt-4o-mini") -> str:
        response = _client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
        return response.choices[0].message.content


CATEGORIES_DESCRIPTION = "\n".join(
    f"- {cat.value}: {', '.join(TAXONOMY[cat]['keywords'][:5])}..."
    for cat in Category
    if cat != Category.UNKNOWN
)

SYSTEM_PROMPT = f"""Sos un router de agentes del equipo Nelson.
Tu tarea es clasificar el goal del usuario en UNA de estas categorías:

{CATEGORIES_DESCRIPTION}

Respondé SOLO con un JSON con este formato:
{{
  "category": "NOMBRE_CATEGORIA",
  "confidence": 0.0_a_1.0,
  "reason": "razón breve en español"
}}

Si el goal necesita MÚLTIPLES agentes, indicá solo la categoría principal.
"""


def llm_classify(goal: str) -> tuple[Category, float, str]:
    """
    Usa LLM para clasificar un goal cuando el scoring por keywords es insuficiente.
    Retorna (category, confidence, reason).
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Goal: {goal}"},
    ]

    try:
        raw = chat_completion(messages)
        data = json.loads(raw)
        category = Category(data["category"])
        confidence = float(data["confidence"]) * 0.9  # penalizamos un poco el fallback
        reason = data.get("reason", "clasificado por LLM")
        return category, confidence, reason
    except Exception as e:
        return Category.UNKNOWN, 0.0, f"error en LLM fallback: {e}"
```

---

### `multi_agent.py`

```python
from .models import Category, RoutingResult
from .scoring import rank_categories

# Threshold: si hay 2+ categorías con score > este valor,
# la tarea probablemente necesita múltiples agentes
MULTI_AGENT_THRESHOLD = 0.55

# Conjuntos comunes de categorías que suelen ir juntas
COMMON_MULTI_AGENT_COMBOS = [
    ({Category.SPEC, Category.BACKEND}, "spec + implementación backend"),
    ({Category.BACKEND, Category.FRONTEND}, "fullstack feature"),
    ({Category.BACKEND, Category.INFRA}, "backend + deploy"),
    ({Category.FRONTEND, Category.QA}, "UI + testing"),
    ({Category.BACKEND, Category.QA}, "backend + testing"),
    ({Category.SPEC, Category.BACKEND, Category.FRONTEND}, "feature completa"),
    ({Category.RAG_AI, Category.BACKEND}, "AI feature con backend"),
    ({Category.BACKEND, Category.SECURITY}, "backend con auth/security"),
]


def detect_multi_agent(
    goal: str,
    ranked: list[tuple[Category, float, list[str]]],
) -> tuple[bool, list[tuple[Category, float, list[str]]]]:
    """
    Determina si una tarea necesita múltiples agentes.

    Returns:
        (is_multi_agent: bool, relevant_categories)
    """
    high_confidence = [
        (cat, conf, kws)
        for cat, conf, kws in ranked
        if conf >= MULTI_AGENT_THRESHOLD
    ]

    if len(high_confidence) < 2:
        return False, []

    # Verificar si el conjunto de categorías es un combo conocido
    cat_set = {cat for cat, _, _ in high_confidence}
    for combo, _ in COMMON_MULTI_AGENT_COMBOS:
        if combo.issubset(cat_set):
            return True, high_confidence

    # Si hay 2+ con alta confianza aunque no sea combo conocido, igual es multi
    if len(high_confidence) >= 2:
        return True, high_confidence[:3]  # máximo 3 categorías paralelas

    return False, []


def decompose_task(goal: str, categories: list[tuple]) -> list[RoutingResult]:
    """
    Descompone una tarea multi-agente en sub-tareas por categoría.
    Cada sub-tarea es un RoutingResult independiente.
    """
    from .taxonomy import TAXONOMY
    sub_tasks = []
    for cat, conf, matched in categories:
        agents = TAXONOMY[cat]["agents"]
        sub_tasks.append(
            RoutingResult(
                category=cat,
                agents=agents,
                confidence=conf,
                reason=f"sub-tarea {cat.value} detectada en goal multi-agente",
                matched_keywords=matched,
                is_multi_agent=False,
            )
        )
    return sub_tasks
```

---

### `router.py` (clase principal)

```python
import logging
from .models import Category, RoutingResult
from .scoring import rank_categories
from .llm_fallback import llm_classify
from .multi_agent import detect_multi_agent, decompose_task
from .taxonomy import TAXONOMY

logger = logging.getLogger("nelson.router")

# Si el top score está por debajo de este threshold, usamos LLM fallback
LLM_FALLBACK_THRESHOLD = 0.45


class NelsonRouter:
    """
    Router principal de agentes para el equipo Nelson.

    Uso básico:
        router = NelsonRouter()
        result = router.route("crear endpoint FastAPI para subir archivos")
        print(result.category)   # BACKEND
        print(result.agents)     # ['julian-agent', 'agency-ai-engineer']
        print(result.confidence) # 0.89
    """

    def __init__(
        self,
        llm_fallback_threshold: float = LLM_FALLBACK_THRESHOLD,
        enable_llm_fallback: bool = True,
        enable_multi_agent: bool = True,
    ):
        self.llm_fallback_threshold = llm_fallback_threshold
        self.enable_llm_fallback = enable_llm_fallback
        self.enable_multi_agent = enable_multi_agent

    def route(self, goal: str) -> RoutingResult:
        """
        Rutea un goal al agente/skill correcto.

        Args:
            goal: descripción de la tarea en lenguaje natural

        Returns:
            RoutingResult con categoría, agentes, confianza y razón
        """
        logger.info(f"Routing goal: {goal[:100]}...")

        # 1. Scoring por keywords
        ranked = rank_categories(goal)

        if not ranked:
            return self._handle_no_match(goal)

        top_cat, top_conf, top_keywords = ranked[0]

        # 2. Detección multi-agente (antes de decidir si usar LLM)
        if self.enable_multi_agent:
            is_multi, multi_cats = detect_multi_agent(goal, ranked)
            if is_multi:
                return self._build_multi_agent_result(goal, multi_cats)

        # 3. Si confianza es baja → LLM fallback
        if top_conf < self.llm_fallback_threshold and self.enable_llm_fallback:
            logger.info(
                f"Score bajo ({top_conf}) para '{top_cat.value}', usando LLM fallback"
            )
            return self._llm_fallback(goal)

        # 4. Resultado con keyword match
        agents = TAXONOMY[top_cat]["agents"]
        result = RoutingResult(
            category=top_cat,
            agents=agents,
            confidence=top_conf,
            reason=self._build_reason(top_cat, top_keywords),
            matched_keywords=top_keywords,
        )
        logger.info(
            f"Routed to {top_cat.value} ({top_conf:.2f}) → {agents}"
        )
        return result

    def route_batch(self, goals: list[str]) -> list[RoutingResult]:
        """Rutea múltiples goals de una vez."""
        return [self.route(goal) for goal in goals]

    def _handle_no_match(self, goal: str) -> RoutingResult:
        if self.enable_llm_fallback:
            return self._llm_fallback(goal)
        return RoutingResult(
            category=Category.UNKNOWN,
            agents=[],
            confidence=0.0,
            reason="No se encontró match por keywords y LLM fallback deshabilitado",
            matched_keywords=[],
        )

    def _llm_fallback(self, goal: str) -> RoutingResult:
        category, confidence, reason = llm_classify(goal)
        agents = TAXONOMY.get(category, {}).get("agents", [])
        return RoutingResult(
            category=category,
            agents=agents,
            confidence=confidence,
            reason=reason,
            matched_keywords=[],
            llm_fallback_used=True,
        )

    def _build_multi_agent_result(
        self, goal: str, categories: list[tuple]
    ) -> RoutingResult:
        sub_tasks = decompose_task(goal, categories)
        primary = sub_tasks[0]
        all_agents = []
        for st in sub_tasks:
            all_agents.extend(st.agents)

        return RoutingResult(
            category=primary.category,
            agents=list(dict.fromkeys(all_agents)),  # dedup preservando orden
            confidence=primary.confidence,
            reason=f"Tarea multi-agente: {', '.join(st.category.value for st in sub_tasks)}",
            matched_keywords=primary.matched_keywords,
            is_multi_agent=True,
            sub_tasks=sub_tasks,
        )

    def _build_reason(self, category: Category, keywords: list[str]) -> str:
        kw_str = ", ".join(f"'{k}'" for k in keywords[:3])
        return f"Categoría {category.value} detectada por keywords: {kw_str}"
```

---

### Uso rápido

```python
from nelson_routing import NelsonRouter

router = NelsonRouter()

# Tarea simple
result = router.route("implementar autenticación JWT en FastAPI")
print(result.category)    # BACKEND
print(result.agents)      # ['julian-agent', 'agency-ai-engineer']
print(result.confidence)  # 0.923

# Tarea multi-agente
result = router.route("crear feature de login: spec, backend y frontend")
print(result.is_multi_agent)  # True
print(result.sub_tasks)       # [SPEC, BACKEND, FRONTEND]

# Tarea ambigua → LLM fallback
result = router.route("hacer que funcione la cosa esa del archivo")
print(result.llm_fallback_used)  # True
```


---


## Confidence Scoring

El scoring tiene 4 niveles:

| Rango     | Nivel       | Significado                                              | Acción                          |
|-----------|-------------|----------------------------------------------------------|---------------------------------|
| 0.85–1.00 | MUY ALTO    | Match claro, múltiples keywords específicas              | Ejecutar directo                |
| 0.65–0.84 | ALTO        | Match sólido, 1-2 keywords fuertes                       | Ejecutar con log                |
| 0.45–0.64 | MEDIO       | Match parcial, posible ambigüedad                        | Usar si no hay mejor candidato  |
| 0.00–0.44 | BAJO        | Sin match suficiente por keywords                        | LLM fallback obligatorio        |

### Factores que aumentan la confianza

- Múltiples keywords de la misma categoría en el goal
- Keywords largas y específicas (ej: "sqlalchemy" pesa más que "db")
- Keywords únicas de una categoría (no ambiguas entre categorías)

### Factores que bajan la confianza

- Goal muy corto (menos de 5 palabras)
- Keywords genéricas que aparecen en múltiples categorías (ej: "script")
- Goal en idioma no reconocido o con mucho argot técnico mixto


---


## Tareas Multi-Agente

Cuando una tarea involucra múltiples categorías con alta confianza, el router la descompone en sub-tareas.

### Ejemplos de combos frecuentes

```
"Implementar feature de upload de archivos completa"
→ SPEC  (0.72) → nelson-spec-driven-workflow
→ BACKEND (0.89) → julian-agent
→ FRONTEND (0.81) → mercedes-agent
→ INFRA (0.61) → nelson-ci-cd
```

```
"Indexar documentos PDF con RAG y exponerlos vía API"
→ RAG/AI (0.91) → nelson-rag-pipeline
→ BACKEND (0.77) → julian-agent
```

### Estrategias de ejecución multi-agente

El meta-orquestador puede ejecutar los sub-agentes de distintas formas:

| Estrategia    | Cuándo usarla                                      | Ejemplo                                    |
|---------------|----------------------------------------------------|--------------------------------------------|
| SECUENCIAL    | Hay dependencias entre sub-tareas                  | SPEC → BACKEND → QA                        |
| PARALELO      | Sub-tareas independientes                          | FRONTEND y BACKEND de features distintas   |
| JERÁRQUICO    | Un agente coordina a los demás                     | JARVIS coordina a Julián + Mercedes         |

```python
# En el meta-orquestador, interpretar el RoutingResult multi-agente:
if result.is_multi_agent:
    execution_plan = orchestrator.plan_execution(result.sub_tasks)
    # execution_plan decide si es SECUENCIAL, PARALELO o JERÁRQUICO
```


---


## Integración con nelson-meta-orchestrator

El router es invocado como primer paso en el meta-orquestador, antes de cualquier ejecución:

```python
# En nelson_meta_orchestrator/core.py

from nelson_routing import NelsonRouter
from nelson_routing.models import Category

router = NelsonRouter()


async def handle_user_goal(goal: str, context: dict) -> AgentResponse:
    """
    Entry point principal del meta-orquestador.
    """
    # 1. Routing
    routing = router.route(goal)

    # 2. Log para auditabilidad
    await audit_log.write({
        "goal": goal,
        "category": routing.category.value,
        "agents": routing.agents,
        "confidence": routing.confidence,
        "llm_fallback": routing.llm_fallback_used,
    })

    # 3. Si confianza muy baja, pedir confirmación al usuario
    if routing.confidence < 0.40:
        return await ask_user_confirmation(goal, routing)

    # 4. Dispatch al agente correcto
    if routing.is_multi_agent:
        return await orchestrator.dispatch_multi(routing)
    else:
        return await orchestrator.dispatch_single(routing)
```

### Señales que el meta-orquestador expone al router

El orquestador puede enriquecer el contexto del router con:

- `project_type`: si el proyecto en curso es frontend-heavy, backend-heavy, etc.
- `active_agents`: agentes disponibles en este momento
- `recent_tasks`: últimas tareas resueltas (para contexto de conversación)

```python
router.route(goal, context={
    "project_type": "fullstack",
    "active_agents": ["julian-agent", "mercedes-agent"],
    "recent_category": Category.BACKEND,
})
```


---


## Ejemplos de Decisiones de Routing

### Ejemplo 1: Tarea clara BACKEND

```
Input:  "Crear un endpoint POST /api/v1/users en FastAPI que valide con Pydantic"
Output:
  category:  BACKEND
  agents:    ['julian-agent', 'agency-ai-engineer']
  confidence: 0.951
  keywords:  ['fastapi', 'endpoint', 'pydantic']
  multi:     False
```

---

### Ejemplo 2: Tarea clara FRONTEND

```
Input:  "Armar un componente React de tabla con paginación usando Tailwind"
Output:
  category:  FRONTEND
  agents:    ['mercedes-agent', 'nelson-frontend-agent']
  confidence: 0.934
  keywords:  ['react', 'componente', 'tailwind']
  multi:     False
```

---

### Ejemplo 3: Tarea SPEC (detectada antes que BACKEND)

```
Input:  "Especificar la API de autenticación: endpoints, payloads, errores"
Output:
  category:  SPEC
  agents:    ['nelson-spec-driven-workflow', 'spec-driven-development']
  confidence: 0.882
  keywords:  ['especificar', 'api', 'endpoints']
  multi:     False
```

---

### Ejemplo 4: Multi-agente BACKEND + INFRA

```
Input:  "Dockerizar la app FastAPI y configurar GitHub Actions para deploy automático"
Output:
  category:  BACKEND (primaria)
  is_multi:  True
  sub_tasks:
    - BACKEND  (0.78) → julian-agent
    - INFRA    (0.91) → nelson-ci-cd, nelson-cloudflare-tunnel-deploy
  agents:    ['julian-agent', 'nelson-ci-cd', 'nelson-cloudflare-tunnel-deploy']
```

---

### Ejemplo 5: LLM Fallback

```
Input:  "Necesito que la app haga lo que acordamos ayer con la integración"
Output:
  category:  UNKNOWN (keyword score: 0.0)
  llm_fallback: True
  → LLM responde: { "category": "EXTERNAL", "confidence": 0.55,
                    "reason": "menciona 'integración', posiblemente externa" }
  agents:    ['nelson-whatsapp-gateway', 'nelson-automation-n8n']
  confidence: 0.495 (penalizado por ser fallback)
```

---

### Ejemplo 6: RAG/AI

```
Input:  "Indexar todos los PDFs del cliente en Chroma y armar un chatbot con RAG"
Output:
  category:  RAG/AI
  agents:    ['nelson-rag-pipeline', 'nelson-llm-generation']
  confidence: 0.963
  keywords:  ['indexar', 'chroma', 'rag', 'chatbot']
  multi:     False
```

---

### Ejemplo 7: QA

```
Input:  "Escribir tests unitarios con pytest para los endpoints de la API"
Output:
  category:  QA
  agents:    ['nelson-code-quality']
  confidence: 0.871
  keywords:  ['tests', 'pytest', 'endpoints']
  multi:     False
```


---


## Cómo Extender el Router

### Agregar una nueva categoría

1. Agregar el valor al enum `Category` en `models.py`:

```python
class Category(str, Enum):
    # ... existentes ...
    DATA_PIPELINE = "DATA_PIPELINE"  # nueva
```

2. Agregar la entrada en `TAXONOMY` en `taxonomy.py`:

```python
Category.DATA_PIPELINE: {
    "priority": 13,  # siempre al final si es nueva
    "keywords": [
        "etl", "pipeline de datos", "airflow", "prefect",
        "ingesta", "transformar datos", "spark", "dbt",
    ],
    "agents": ["nelson-data-pipeline", "nelson-etl-agent"],
},
```

3. (Opcional) Agregar combos multi-agente en `multi_agent.py`:

```python
COMMON_MULTI_AGENT_COMBOS = [
    # ... existentes ...
    ({Category.DATA_PIPELINE, Category.BACKEND}, "data pipeline con API"),
]
```

4. Actualizar el SYSTEM_PROMPT del LLM fallback para incluir la nueva categoría.

5. Escribir tests:

```python
def test_data_pipeline_routing():
    router = NelsonRouter(enable_llm_fallback=False)
    result = router.route("crear pipeline ETL con Airflow para ingestar datos de Postgres")
    assert result.category == Category.DATA_PIPELINE
    assert result.confidence > 0.7
```

### Agregar un agente a una categoría existente

```python
# En taxonomy.py, simplemente agregar al array de agents:
Category.BACKEND: {
    "agents": ["julian-agent", "agency-ai-engineer", "nuevo-backend-agent"],
    ...
}
```

### Cambiar el agente primario de una categoría

El primer agente del array es el primario. Para cambiarlo, reordenar el array.


---


## Pitfalls y Antipatrones

### 1. No sobrecargar las keywords con términos genéricos

**Mal:**
```python
"script", "archivo", "cosa", "proceso", "hacer"
```
Estas palabras aparecen en cualquier goal y generan falsos positivos.

**Bien:** usar términos técnicos específicos de cada dominio.

---

### 2. No saltear SPEC cuando corresponde

El error más común es que un goal del tipo "diseñar el módulo de pagos" se rutea a BACKEND porque menciona APIs. SPEC tiene prioridad 1 justamente para evitar esto. Si alguien modifica la priority de SPEC, los demás categorías van a "robar" esos goals.

---

### 3. No confiar ciegamente en el score

Un score de 0.95 con UNA sola keyword larga es menos confiable que 0.88 con tres keywords medianas. El scoring actual penaliza esto vía la función sigmoide, pero siempre revisar los `matched_keywords` para entender la decisión.

---

### 4. LLM fallback no es magia

El LLM puede alucinar categorías si el goal es demasiado vago. Cuando el fallback retorna confianza < 0.50, el meta-orquestador debería pedir clarificación al usuario en lugar de ejecutar a ciegas.

---

### 5. Multi-agente no siempre significa paralelo

SPEC → BACKEND → QA es secuencial por definición (no podés testear algo que no está implementado). El router detecta el multi-agente pero **no determina el orden**: eso es responsabilidad del meta-orquestador usando la lógica de dependencias.

---

### 6. Agregar keywords en el idioma correcto

El router acepta goals en español e inglés mezclados (rioplatense + técnico inglés), por eso las keywords están en ambos idiomas. Al agregar una nueva categoría, incluir variantes en ambos idiomas.

---

### 7. No hardcodear nombres de agentes fuera del taxonomy

Si cambia el nombre de un agente (ej: `julian-agent` → `julian-v2`), el único lugar donde se actualiza es `TAXONOMY`. No hardcodear los nombres en el router, el orquestador, ni en ningún otro lado.

---

### 8. El router no ejecuta, solo decide

El router es **stateless** y **sin side effects**. No llama agentes, no escribe en DB, no hace nada excepto retornar un `RoutingResult`. Toda la ejecución es responsabilidad del meta-orquestador.


---


## Resumen de Convenciones Nelson

- Español rioplatense en logs, comentarios y documentación.
- Inglés para nombres de variables, funciones, clases y constantes (Python convention).
- Todos los cambios a la taxonomía pasan por PR con al menos 1 reviewer.
- Cada nueva categoría necesita mínimo 5 tests de routing.
- El `audit_log` de routing decisions es **obligatorio** en producción.
- Los agentes se nombran en kebab-case: `julian-agent`, `mercedes-agent`, `nelson-browser-agent`.
- El router corre en el mismo proceso que el meta-orquestador (no es un microservicio separado).
