---
name: nelson-eval-harness
description: Harness de evaluación para el meta-orquestador de Nelson. Define métricas de éxito, dimensiones de calidad por tipo de tarea, scoring 0-100, gates automáticos y humanos, y generación de reportes para Tony vía WhatsApp.
tags: [evaluation, quality, metrics, meta-agent, harness, nelson]
related_skills: [nelson-meta-orchestrator, nelson-browser-agent, nelson-code-quality, nelson-frontend-testing]
---

# Nelson Eval Harness

## 1. ¿Qué es y para qué sirve?

El eval harness es el mecanismo que le dice al meta-orquestador si hizo bien su trabajo antes de entregar algo a Tony o al cliente. No es un test suite más: es la capa de calidad que corre **después** de cada iteración del loop de Nelson y **antes** de cualquier entrega.

La pregunta central que responde es: *"¿Esto está listo para salir, o hay que seguir trabajando?"*

### Principio de diseño

- El harness evalúa outputs, no intenciones.
- Si el score total no supera el umbral configurado, el meta-orquestador NO entrega — vuelve a trabajar o escala a Tony.
- Cada dimensión tiene peso específico según el tipo de tarea.
- Los checks automáticos corren sin intervención humana. Los checks que requieren juicio estético o decisiones de negocio van a Tony.

### Quality gates antes de entrega

```
[Output del meta-agente]
        ↓
[Eval Harness corre checks automáticos]
        ↓
[Score ≥ umbral? → SI → Checks HITL pendientes?]
        ↓ NO                    ↓ NO
[Retry loop]          [Entrega a Tony/cliente]
                               ↓ SI
                    [Notifica a Tony para aprobación]
```

---

## 2. Dimensiones de evaluación por tipo de tarea

### 2.1 BACKEND

| Dimensión | Peso PoC | Peso Prod | Check automático |
|-----------|----------|-----------|-----------------|
| Tests pasan (pytest) | 30% | 25% | ✅ |
| Contrato API vs OpenAPI spec | 25% | 25% | ✅ |
| Response times < threshold | 15% | 20% | ✅ |
| Sin vulnerabilidades de seguridad | 15% | 20% | ✅ |
| Cobertura de código > umbral | 15% | 10% | ✅ |

**Umbrales por defecto:**
- Response time: PoC < 2000ms, Prod < 500ms (p95)
- Cobertura: PoC > 60%, Prod > 80%
- Seguridad: bandit score 0 issues HIGH, PoC tolera MEDIUM

**Cómo evaluar el contrato:**
```python
# Se genera el spec desde el app FastAPI en runtime y se compara
# contra el spec esperado en openapi.yaml del repo
from deepdiff import DeepDiff

def check_api_contract(app, expected_spec_path):
    from fastapi.testclient import TestClient
    client = TestClient(app)
    actual = client.get("/openapi.json").json()
    with open(expected_spec_path) as f:
        expected = yaml.safe_load(f)
    diff = DeepDiff(expected, actual, ignore_order=True)
    return len(diff) == 0, diff
```

### 2.2 FRONTEND

| Dimensión | Peso PoC | Peso Prod | Check automático |
|-----------|----------|-----------|-----------------|
| Screenshots E2E pasan visual check | 35% | 30% | ⚠️ semi-auto |
| Sin errores en consola del browser | 20% | 20% | ✅ |
| Lighthouse score > umbral | 25% | 25% | ✅ |
| Tests E2E pasan (Playwright) | 20% | 25% | ✅ |

**Umbrales Lighthouse:**
- PoC: Performance > 60, Accessibility > 70, Best Practices > 70
- Prod: Performance > 80, Accessibility > 90, Best Practices > 85

**Visual check:**
- Auto: comparación pixel-diff contra baseline (threshold < 5% cambio)
- HITL: si el diff supera 5% pero < 20%, va a Tony para aprobación
- Si supera 20%: falla automáticamente

### 2.3 RAG (Retrieval-Augmented Generation)

| Dimensión | Peso PoC | Peso Prod | Check automático |
|-----------|----------|-----------|-----------------|
| Retrieval precision@k | 30% | 25% | ✅ |
| Answer relevance | 25% | 25% | ✅ |
| Hallucination detection | 30% | 35% | ✅ |
| Latencia de consulta | 15% | 15% | ✅ |

**Métricas RAG explicadas:**

*Retrieval Precision@k:* de los k documentos recuperados, cuántos son realmente relevantes para la query. Se mide contra un golden set de queries+documentos esperados.

*Answer Relevance:* usando un LLM evaluador, se puntúa si la respuesta generada responde efectivamente la pregunta. Score 0-1, umbral > 0.7.

*Hallucination Detection:* el evaluador LLM verifica que cada claim en la respuesta esté soportado por los documentos recuperados. Score = % de claims con soporte.

```python
# Golden set format: eval/rag_golden_set.json
[
  {
    "query": "¿Cuál es la política de devoluciones?",
    "expected_doc_ids": ["doc_42", "doc_15"],
    "expected_answer_contains": ["30 días", "reembolso completo"]
  }
]
```

### 2.4 BROWSER (Automatización con nelson-browser-agent)

| Dimensión | Peso PoC | Peso Prod | Check automático |
|-----------|----------|-----------|-----------------|
| Todos los Critical Points verificados | 50% | 50% | ✅ con screenshots |
| Screenshots capturados en cada CP | 20% | 20% | ✅ |
| Flujo completa sin errores | 20% | 20% | ✅ |
| Datos extraídos correctamente | 10% | 10% | ✅ |

**Critical Points:** son los hitos definidos en el task spec del browser-agent. Cada CP debe tener su screenshot como evidencia. Si falta un screenshot de un CP, ese CP cuenta como fallido.

### 2.5 FULL PROJECT

Score compuesto: promedio ponderado de todos los tipos de tasks presentes, más:

| Dimensión adicional | Peso |
|--------------------|------|
| Documentación completa (README, API docs, setup) | 15% |
| CI verde (GitHub Actions / similar) | 20% |
| Deploy funcional (staging o prod) | 20% |
| Todos los subtypes pasan sus umbrales | 45% |

Para FULL PROJECT, **todos** los subtypes deben estar por encima de su umbral mínimo individual. Si uno falla, el proyecto falla aunque el promedio sea bueno.

---

## 3. Implementación del evaluation runner

### Estructura de archivos

```
eval/
├── __init__.py
├── runner.py              # Entry point principal
├── dimensions/
│   ├── __init__.py
│   ├── backend.py
│   ├── frontend.py
│   ├── rag.py
│   ├── browser.py
│   └── full_project.py
├── scoring.py             # Sistema de scoring 0-100
├── thresholds.py          # Config PoC vs Prod
├── report.py              # Generación de reportes
├── hitl.py                # Checks que van a Tony
└── conftest.py            # Fixtures compartidos
```

### runner.py

```python
"""
Nelson Eval Harness - Runner Principal
Corre al final de cada iteración del meta-orquestador.
"""
import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from .dimensions import backend, frontend, rag, browser, full_project
from .scoring import compute_weighted_score
from .thresholds import get_thresholds
from .report import generate_report
from .hitl import collect_hitl_items


class TaskType(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    RAG = "rag"
    BROWSER = "browser"
    FULL_PROJECT = "full_project"


class ProjectMode(str, Enum):
    POC = "poc"
    PRODUCTION = "production"


@dataclass
class EvalContext:
    task_type: TaskType
    project_mode: ProjectMode
    project_root: Path
    task_spec: dict
    iteration: int = 0
    previous_scores: list[float] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


@dataclass
class EvalResult:
    task_type: TaskType
    dimension_scores: dict[str, float]  # dimensión → score 0-100
    weighted_score: float
    passed: bool
    hitl_required: list[dict]
    report_path: Optional[Path] = None
    summary: str = ""


async def run_eval(ctx: EvalContext) -> EvalResult:
    """
    Entry point principal. Corre todos los checks para el tipo de tarea
    y retorna el resultado con score y recomendaciones.
    """
    thresholds = get_thresholds(ctx.project_mode)

    # Despachar al evaluador del tipo de tarea
    evaluator_map = {
        TaskType.BACKEND: backend.evaluate,
        TaskType.FRONTEND: frontend.evaluate,
        TaskType.RAG: rag.evaluate,
        TaskType.BROWSER: browser.evaluate,
        TaskType.FULL_PROJECT: full_project.evaluate,
    }

    evaluator = evaluator_map[ctx.task_type]
    dimension_scores = await evaluator(ctx, thresholds)

    # Calcular score ponderado
    weighted_score = compute_weighted_score(
        dimension_scores,
        task_type=ctx.task_type,
        project_mode=ctx.project_mode,
    )

    # Determinar si pasa
    min_threshold = thresholds[ctx.task_type]["min_score"]
    passed = weighted_score >= min_threshold

    # Recolectar items que necesitan aprobación humana
    hitl_items = collect_hitl_items(dimension_scores, ctx)

    # Generar reporte
    result = EvalResult(
        task_type=ctx.task_type,
        dimension_scores=dimension_scores,
        weighted_score=weighted_score,
        passed=passed,
        hitl_required=hitl_items,
    )

    report_path = generate_report(result, ctx)
    result.report_path = report_path
    result.summary = _build_summary(result, ctx)

    return result


def _build_summary(result: EvalResult, ctx: EvalContext) -> str:
    status = "✅ APROBADO" if result.passed else "❌ NECESITA TRABAJO"
    lines = [
        f"Eval Harness — Iteración {ctx.iteration}",
        f"Tipo: {result.task_type.value.upper()} | Modo: {ctx.project_mode.value}",
        f"Score total: {result.weighted_score:.1f}/100 → {status}",
        "",
        "Dimensiones:",
    ]
    for dim, score in result.dimension_scores.items():
        emoji = "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
        lines.append(f"  {emoji} {dim}: {score:.1f}")

    if result.hitl_required:
        lines.append("")
        lines.append(f"⏳ Requiere aprobación de Tony ({len(result.hitl_required)} items)")

    return "\n".join(lines)
```

### dimensions/backend.py

```python
"""Evaluador de tasks de tipo BACKEND."""
import subprocess
import time
import httpx
import yaml
from pathlib import Path
from deepdiff import DeepDiff


async def evaluate(ctx, thresholds) -> dict[str, float]:
    t = thresholds["backend"]
    scores = {}

    scores["tests"] = await _run_pytest(ctx.project_root, t)
    scores["api_contract"] = await _check_api_contract(ctx, t)
    scores["response_times"] = await _check_response_times(ctx, t)
    scores["security"] = await _run_security_scan(ctx.project_root, t)
    scores["coverage"] = await _check_coverage(ctx.project_root, t)

    return scores


async def _run_pytest(project_root: Path, t: dict) -> float:
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=short", "-q",
         f"--cov={project_root}/src",
         "--cov-report=json:eval_coverage.json"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return 100.0
    # Parsear cuántos tests pasaron
    lines = result.stdout.split("\n")
    for line in reversed(lines):
        if "passed" in line or "failed" in line:
            # Ej: "10 passed, 2 failed"
            passed = _parse_test_counts(line)
            total = passed["passed"] + passed["failed"]
            if total == 0:
                return 0.0
            return (passed["passed"] / total) * 100.0
    return 0.0


def _parse_test_counts(line: str) -> dict:
    import re
    passed = int(re.search(r"(\d+) passed", line).group(1)) if "passed" in line else 0
    failed = int(re.search(r"(\d+) failed", line).group(1)) if "failed" in line else 0
    return {"passed": passed, "failed": failed}


async def _check_api_contract(ctx, t: dict) -> float:
    spec_path = ctx.project_root / "openapi.yaml"
    if not spec_path.exists():
        spec_path = ctx.project_root / "openapi.json"
    if not spec_path.exists():
        # No hay spec esperado: no se puede evaluar, score neutro
        return 75.0

    base_url = ctx.extra.get("api_base_url", "http://localhost:8000")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{base_url}/openapi.json", timeout=5.0)
            actual = resp.json()
    except Exception:
        return 0.0

    with open(spec_path) as f:
        if str(spec_path).endswith(".yaml"):
            expected = yaml.safe_load(f)
        else:
            import json
            expected = json.load(f)

    diff = DeepDiff(expected, actual, ignore_order=True,
                    exclude_paths=["root['info']['version']"])
    if not diff:
        return 100.0

    # Penalizar por cantidad de diferencias
    n_diffs = sum(len(v) if isinstance(v, dict) else 1 for v in diff.values())
    score = max(0.0, 100.0 - (n_diffs * 10))
    return score


async def _check_response_times(ctx, t: dict) -> float:
    endpoints = ctx.extra.get("endpoints_to_benchmark", [])
    if not endpoints:
        return 80.0  # Sin endpoints configurados, score conservador

    base_url = ctx.extra.get("api_base_url", "http://localhost:8000")
    threshold_ms = t["response_time_ms_p95"]
    times = []

    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            for _ in range(10):  # 10 muestras para p95
                start = time.perf_counter()
                try:
                    await client.get(f"{base_url}{endpoint}", timeout=5.0)
                except Exception:
                    times.append(9999)
                    continue
                elapsed_ms = (time.perf_counter() - start) * 1000
                times.append(elapsed_ms)

    if not times:
        return 0.0

    times.sort()
    p95 = times[int(len(times) * 0.95)]
    if p95 <= threshold_ms:
        return 100.0
    # Degradación lineal: 2x el threshold → 0 puntos
    score = max(0.0, 100.0 * (1 - (p95 - threshold_ms) / threshold_ms))
    return score


async def _run_security_scan(project_root: Path, t: dict) -> float:
    result = subprocess.run(
        ["bandit", "-r", str(project_root / "src"),
         "-f", "json", "-o", "eval_security.json"],
        capture_output=True, text=True,
    )
    import json
    try:
        with open(project_root / "eval_security.json") as f:
            report = json.load(f)
    except Exception:
        return 50.0

    high = sum(1 for r in report.get("results", []) if r["issue_severity"] == "HIGH")
    medium = sum(1 for r in report.get("results", []) if r["issue_severity"] == "MEDIUM")

    if high > 0:
        return 0.0
    if medium > t.get("max_bandit_medium", 3):
        return 40.0
    if medium > 0:
        return 70.0
    return 100.0


async def _check_coverage(project_root: Path, t: dict) -> float:
    import json
    try:
        with open(project_root / "eval_coverage.json") as f:
            cov = json.load(f)
        pct = cov["totals"]["percent_covered"]
        threshold = t["coverage_pct"]
        if pct >= threshold:
            return 100.0
        return max(0.0, (pct / threshold) * 100.0)
    except Exception:
        return 50.0
```

### dimensions/frontend.py

```python
"""Evaluador de tasks de tipo FRONTEND."""
import asyncio
import json
import subprocess
from pathlib import Path


async def evaluate(ctx, thresholds) -> dict[str, float]:
    t = thresholds["frontend"]
    scores = {}

    scores["e2e_tests"] = await _run_playwright(ctx.project_root, t)
    scores["console_errors"] = await _check_console_errors(ctx, t)
    scores["lighthouse"] = await _run_lighthouse(ctx, t)
    scores["visual_diff"] = await _check_visual_diff(ctx, t)

    return scores


async def _run_playwright(project_root: Path, t: dict) -> float:
    result = subprocess.run(
        ["npx", "playwright", "test", "--reporter=json"],
        cwd=project_root,
        capture_output=True, text=True,
    )
    try:
        report = json.loads(result.stdout)
        total = report.get("stats", {})
        passed = total.get("expected", 0)
        failed = total.get("unexpected", 0)
        n = passed + failed
        if n == 0:
            return 75.0
        return (passed / n) * 100.0
    except Exception:
        return 0.0 if result.returncode != 0 else 75.0


async def _check_console_errors(ctx, t: dict) -> float:
    # Los errores de consola se capturan durante el run de Playwright
    # o del browser-agent. Leer del archivo de resultados del último run.
    errors_file = ctx.project_root / "eval_console_errors.json"
    if not errors_file.exists():
        return 80.0

    with open(errors_file) as f:
        errors = json.load(f)

    critical = [e for e in errors if e.get("level") == "error"]
    warnings = [e for e in errors if e.get("level") == "warning"]

    if len(critical) == 0 and len(warnings) == 0:
        return 100.0
    if len(critical) == 0:
        return max(60.0, 100.0 - len(warnings) * 5)
    return max(0.0, 100.0 - len(critical) * 20 - len(warnings) * 5)


async def _run_lighthouse(ctx, t: dict) -> float:
    url = ctx.extra.get("frontend_url", "http://localhost:3000")
    result = subprocess.run(
        ["npx", "lighthouse", url,
         "--output=json", "--output-path=eval_lighthouse.json",
         "--chrome-flags=--headless", "--quiet"],
        capture_output=True, text=True,
    )
    try:
        with open(ctx.project_root / "eval_lighthouse.json") as f:
            report = json.load(f)

        cats = report.get("categories", {})
        performance = cats.get("performance", {}).get("score", 0) * 100
        accessibility = cats.get("accessibility", {}).get("score", 0) * 100
        best_practices = cats.get("best-practices", {}).get("score", 0) * 100

        t_perf = t["lighthouse_performance"]
        t_a11y = t["lighthouse_accessibility"]
        t_bp = t["lighthouse_best_practices"]

        score_perf = min(100.0, (performance / t_perf) * 100.0)
        score_a11y = min(100.0, (accessibility / t_a11y) * 100.0)
        score_bp = min(100.0, (best_practices / t_bp) * 100.0)

        return (score_perf + score_a11y + score_bp) / 3
    except Exception:
        return 0.0


async def _check_visual_diff(ctx, t: dict) -> float:
    # Retorna un score provisional; si el diff está en zona gris,
    # se agrega a la lista HITL en hitl.py
    baseline_dir = ctx.project_root / "eval" / "visual_baseline"
    current_dir = ctx.project_root / "eval" / "visual_current"

    if not baseline_dir.exists() or not current_dir.exists():
        # Sin baseline: marcar para review humano, score neutro
        return -1.0  # -1 indica "pendiente revisión humana"

    diffs = []
    for baseline_img in baseline_dir.glob("*.png"):
        current_img = current_dir / baseline_img.name
        if not current_img.exists():
            diffs.append({"file": baseline_img.name, "pct": 100.0})
            continue
        pct = _pixel_diff_pct(baseline_img, current_img)
        diffs.append({"file": baseline_img.name, "pct": pct})

    if not diffs:
        return 100.0

    avg_diff = sum(d["pct"] for d in diffs) / len(diffs)
    if avg_diff < 2.0:
        return 100.0
    if avg_diff < 5.0:
        return 85.0
    if avg_diff < 20.0:
        return -1.0  # Zona gris: va a HITL
    return 0.0


def _pixel_diff_pct(img1_path: Path, img2_path: Path) -> float:
    try:
        from PIL import Image, ImageChops
        import numpy as np
        img1 = Image.open(img1_path).convert("RGB")
        img2 = Image.open(img2_path).convert("RGB")
        if img1.size != img2.size:
            return 50.0
        diff = ImageChops.difference(img1, img2)
        arr = np.array(diff)
        total_pixels = arr.shape[0] * arr.shape[1]
        diff_pixels = np.count_nonzero(arr.sum(axis=2))
        return (diff_pixels / total_pixels) * 100.0
    except Exception:
        return 50.0
```

### dimensions/rag.py

```python
"""Evaluador de tasks de tipo RAG."""
import json
from pathlib import Path
import httpx


async def evaluate(ctx, thresholds) -> dict[str, float]:
    t = thresholds["rag"]
    golden_set_path = ctx.project_root / "eval" / "rag_golden_set.json"

    if not golden_set_path.exists():
        raise FileNotFoundError(
            f"RAG eval requiere golden set en {golden_set_path}\n"
            "Formato: [{query, expected_doc_ids, expected_answer_contains}]"
        )

    with open(golden_set_path) as f:
        golden_set = json.load(f)

    api_url = ctx.extra.get("rag_api_url", "http://localhost:8000")
    scores = {}

    results = await _query_all(golden_set, api_url, t)

    scores["retrieval_precision"] = _compute_retrieval_precision(results, t)
    scores["answer_relevance"] = await _compute_answer_relevance(results, ctx)
    scores["hallucination"] = await _compute_hallucination_score(results, ctx)
    scores["latency"] = _compute_latency_score(results, t)

    return scores


async def _query_all(golden_set: list, api_url: str, t: dict) -> list:
    import time
    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for item in golden_set:
            start = time.perf_counter()
            try:
                resp = await client.post(
                    f"{api_url}/query",
                    json={"query": item["query"], "k": t.get("retrieval_k", 5)},
                )
                data = resp.json()
            except Exception as e:
                data = {"error": str(e), "docs": [], "answer": ""}
            elapsed_ms = (time.perf_counter() - start) * 1000
            results.append({
                "query": item["query"],
                "expected_doc_ids": item.get("expected_doc_ids", []),
                "expected_answer_contains": item.get("expected_answer_contains", []),
                "retrieved_docs": data.get("docs", []),
                "answer": data.get("answer", ""),
                "latency_ms": elapsed_ms,
            })
    return results


def _compute_retrieval_precision(results: list, t: dict) -> float:
    k = t.get("retrieval_k", 5)
    precisions = []
    for r in results:
        expected = set(r["expected_doc_ids"])
        retrieved_ids = [d.get("id", d.get("doc_id", "")) for d in r["retrieved_docs"][:k]]
        if not expected:
            continue
        hits = sum(1 for doc_id in retrieved_ids if doc_id in expected)
        precisions.append(hits / min(k, len(expected)))
    if not precisions:
        return 75.0
    return (sum(precisions) / len(precisions)) * 100.0


async def _compute_answer_relevance(results: list, ctx) -> float:
    # Usar LLM evaluador para puntuar relevancia
    evaluator_url = ctx.extra.get("llm_evaluator_url")
    if not evaluator_url:
        # Fallback: check de keywords
        scores = []
        for r in results:
            if not r["expected_answer_contains"]:
                continue
            keywords = r["expected_answer_contains"]
            answer_lower = r["answer"].lower()
            hits = sum(1 for kw in keywords if kw.lower() in answer_lower)
            scores.append(hits / len(keywords))
        if not scores:
            return 75.0
        return (sum(scores) / len(scores)) * 100.0

    # Con evaluador LLM
    scores = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for r in results:
            try:
                resp = await client.post(evaluator_url, json={
                    "task": "answer_relevance",
                    "question": r["query"],
                    "answer": r["answer"],
                })
                score = resp.json().get("score", 0.5)
                scores.append(score)
            except Exception:
                scores.append(0.5)

    return (sum(scores) / len(scores)) * 100.0 if scores else 50.0


async def _compute_hallucination_score(results: list, ctx) -> float:
    evaluator_url = ctx.extra.get("llm_evaluator_url")
    if not evaluator_url:
        return 75.0  # Sin evaluador, score conservador

    scores = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for r in results:
            try:
                resp = await client.post(evaluator_url, json={
                    "task": "hallucination_check",
                    "answer": r["answer"],
                    "source_docs": r["retrieved_docs"],
                })
                score = resp.json().get("grounded_ratio", 0.5)
                scores.append(score)
            except Exception:
                scores.append(0.5)

    return (sum(scores) / len(scores)) * 100.0 if scores else 50.0


def _compute_latency_score(results: list, t: dict) -> float:
    threshold_ms = t.get("latency_ms_p95", 3000)
    latencies = sorted(r["latency_ms"] for r in results)
    if not latencies:
        return 80.0
    p95 = latencies[int(len(latencies) * 0.95)]
    if p95 <= threshold_ms:
        return 100.0
    return max(0.0, 100.0 * (1 - (p95 - threshold_ms) / threshold_ms))
```

### dimensions/browser.py

```python
"""Evaluador de tasks de tipo BROWSER (nelson-browser-agent)."""
import json
from pathlib import Path


async def evaluate(ctx, thresholds) -> dict[str, float]:
    t = thresholds["browser"]
    scores = {}

    # El browser-agent genera un results.json con los CPs verificados
    results_path = ctx.project_root / "eval" / "browser_results.json"
    if not results_path.exists():
        results_path = ctx.extra.get("browser_results_path")

    if not results_path or not Path(results_path).exists():
        return {
            "critical_points": 0.0,
            "screenshots": 0.0,
            "flow_completion": 0.0,
            "data_extraction": 0.0,
        }

    with open(results_path) as f:
        results = json.load(f)

    scores["critical_points"] = _score_critical_points(results)
    scores["screenshots"] = _score_screenshots(results)
    scores["flow_completion"] = _score_flow_completion(results)
    scores["data_extraction"] = _score_data_extraction(results, ctx)

    return scores


def _score_critical_points(results: dict) -> float:
    cps = results.get("critical_points", [])
    if not cps:
        return 0.0
    verified = sum(1 for cp in cps if cp.get("verified", False))
    return (verified / len(cps)) * 100.0


def _score_screenshots(results: dict) -> float:
    cps = results.get("critical_points", [])
    if not cps:
        return 0.0
    with_screenshot = sum(
        1 for cp in cps
        if cp.get("screenshot_path") and Path(cp["screenshot_path"]).exists()
    )
    return (with_screenshot / len(cps)) * 100.0


def _score_flow_completion(results: dict) -> float:
    if results.get("completed", False):
        return 100.0
    steps = results.get("steps", [])
    if not steps:
        return 0.0
    completed = sum(1 for s in steps if s.get("status") == "completed")
    return (completed / len(steps)) * 100.0


def _score_data_extraction(results: dict, ctx) -> float:
    expected_fields = ctx.extra.get("expected_extracted_fields", [])
    if not expected_fields:
        return 100.0
    extracted = results.get("extracted_data", {})
    hits = sum(1 for f in expected_fields if f in extracted and extracted[f])
    return (hits / len(expected_fields)) * 100.0
```

---

## 4. Sistema de scoring

### scoring.py

```python
"""Sistema de scoring 0-100 con promedios ponderados por tipo de tarea y modo."""
from .runner import TaskType, ProjectMode

# Pesos por dimensión, por tipo de tarea, por modo de proyecto
WEIGHTS = {
    TaskType.BACKEND: {
        ProjectMode.POC: {
            "tests": 0.30,
            "api_contract": 0.25,
            "response_times": 0.15,
            "security": 0.15,
            "coverage": 0.15,
        },
        ProjectMode.PRODUCTION: {
            "tests": 0.25,
            "api_contract": 0.25,
            "response_times": 0.20,
            "security": 0.20,
            "coverage": 0.10,
        },
    },
    TaskType.FRONTEND: {
        ProjectMode.POC: {
            "e2e_tests": 0.20,
            "console_errors": 0.20,
            "lighthouse": 0.25,
            "visual_diff": 0.35,
        },
        ProjectMode.PRODUCTION: {
            "e2e_tests": 0.25,
            "console_errors": 0.20,
            "lighthouse": 0.25,
            "visual_diff": 0.30,
        },
    },
    TaskType.RAG: {
        ProjectMode.POC: {
            "retrieval_precision": 0.30,
            "answer_relevance": 0.25,
            "hallucination": 0.30,
            "latency": 0.15,
        },
        ProjectMode.PRODUCTION: {
            "retrieval_precision": 0.25,
            "answer_relevance": 0.25,
            "hallucination": 0.35,
            "latency": 0.15,
        },
    },
    TaskType.BROWSER: {
        ProjectMode.POC: {
            "critical_points": 0.50,
            "screenshots": 0.20,
            "flow_completion": 0.20,
            "data_extraction": 0.10,
        },
        ProjectMode.PRODUCTION: {
            "critical_points": 0.50,
            "screenshots": 0.20,
            "flow_completion": 0.20,
            "data_extraction": 0.10,
        },
    },
}


def compute_weighted_score(
    dimension_scores: dict[str, float],
    task_type: TaskType,
    project_mode: ProjectMode,
) -> float:
    weights = WEIGHTS.get(task_type, {}).get(project_mode, {})
    if not weights:
        # FULL_PROJECT u otro: promedio simple
        valid = [v for v in dimension_scores.values() if v >= 0]
        return sum(valid) / len(valid) if valid else 0.0

    total = 0.0
    weight_sum = 0.0
    for dim, score in dimension_scores.items():
        if score < 0:
            # Dimensión pendiente (HITL): usar 50 como proxy
            score = 50.0
        w = weights.get(dim, 0.0)
        total += score * w
        weight_sum += w

    if weight_sum == 0:
        return 0.0
    return total / weight_sum
```

---

## 5. Checks automáticos vs. HITL

### hitl.py

```python
"""
Gestión de items que requieren aprobación humana (Tony).
Regla general: si el resultado puede ser objetivamente medido → automático.
Si requiere juicio estético, decisión de negocio o es ambiguo → HITL.
"""
from .runner import EvalContext, TaskType

HITL_RULES = {
    # (task_type, dimension): función que decide si necesita revisión humana
    "frontend.visual_diff": lambda score: score == -1.0 or (50 <= score < 85),
    "rag.answer_relevance": lambda score: 60 <= score < 75,
    "full_project.docs_complete": lambda score: score < 80,
}


def collect_hitl_items(dimension_scores: dict, ctx: EvalContext) -> list[dict]:
    items = []
    for dim, score in dimension_scores.items():
        key = f"{ctx.task_type.value}.{dim}"
        rule = HITL_RULES.get(key)
        if rule and rule(score):
            items.append({
                "dimension": dim,
                "score": score,
                "task_type": ctx.task_type.value,
                "reason": _get_hitl_reason(key, score),
                "action_required": _get_action_required(key),
            })
    return items


def _get_hitl_reason(key: str, score: float) -> str:
    reasons = {
        "frontend.visual_diff": (
            "Las screenshots difieren del baseline en zona gris (5-20%). "
            "Necesita ojo humano para determinar si el cambio es intencional."
        ),
        "rag.answer_relevance": (
            "La relevancia de las respuestas está en zona borderline. "
            "Revisar si las respuestas son aceptables para el caso de uso."
        ),
        "full_project.docs_complete": (
            "La documentación no cumple el mínimo. "
            "Decidir si es aceptable para la etapa actual del proyecto."
        ),
    }
    return reasons.get(key, f"Score {score:.1f} requiere revisión humana.")


def _get_action_required(key: str) -> str:
    actions = {
        "frontend.visual_diff": "Revisar screenshots adjuntos y aprobar o rechazar cambios visuales.",
        "rag.answer_relevance": "Revisar muestra de respuestas del golden set y aprobar calidad.",
        "full_project.docs_complete": "Revisar docs generadas y decidir si son suficientes.",
    }
    return actions.get(key, "Revisar y aprobar manualmente.")
```

### Qué siempre es automático

- Tests unitarios/integración (pytest)
- Cobertura de código
- Issues de seguridad (bandit, safety)
- Response times
- Errores de consola del browser
- Lighthouse scores
- Critical Points del browser-agent (verificados con selector CSS/texto)
- Retrieval precision@k

### Qué siempre va a Tony

- Aprobación final de entrega a cliente (siempre, sin excepciones)
- Cambios visuales en zona gris
- Respuestas RAG borderline
- Cualquier dimensión que no se pudo medir (datos faltantes)
- Score total en rango 60-70 (zona de decisión)

### Qué puede ser HITL o auto según configuración

- Hallucination detection (si hay evaluador LLM disponible → auto; si no → HITL)
- Deploy working (si hay smoke tests → auto; si no → HITL con checklist)

---

## 6. Integración con nelson-browser-agent

El browser-agent genera un `browser_results.json` que el eval harness consume. Protocolo:

```json
{
  "task_id": "task_abc123",
  "completed": true,
  "steps": [
    {"step": 1, "action": "navigate", "status": "completed"},
    {"step": 2, "action": "click", "status": "completed"}
  ],
  "critical_points": [
    {
      "id": "cp_1",
      "description": "Usuario logueado correctamente",
      "verified": true,
      "screenshot_path": "/eval/screenshots/cp_1.png",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "extracted_data": {
    "product_price": "$99.99",
    "confirmation_number": "ORD-12345"
  }
}
```

El eval harness **no corre el browser-agent**: lo lee. El meta-orquestador es responsable de correr el browser-agent primero y luego el eval harness.

Para verificación visual de CPs, el eval harness puede invocar al browser-agent en modo "verify screenshot":

```python
async def request_screenshot_verification(cp_id: str, screenshot_path: str, ctx: EvalContext):
    """
    Solicita al browser-agent que verifique visualmente un screenshot.
    Solo para verificaciones adicionales, no para el flujo principal.
    """
    from nelson_browser_agent import verify_screenshot
    result = await verify_screenshot(
        screenshot_path=screenshot_path,
        expected_description=ctx.task_spec["critical_points"][cp_id]["expected_state"],
    )
    return result.confidence_score
```

---

## 7. Integración con nelson-code-quality

El code-quality skill provee checks de linting, type checking y complejidad. El eval harness los incorpora como dimensión del score de backend.

```python
# En dimensions/backend.py, agregar:
async def _run_code_quality(ctx, t: dict) -> float:
    from nelson_code_quality import run_checks
    result = await run_checks(
        project_root=ctx.project_root,
        checks=["ruff", "mypy", "radon"],
        config=ctx.extra.get("code_quality_config", {}),
    )
    # result.score viene de 0-100 según nelson-code-quality
    return result.score
```

**Pesos cuando code-quality está habilitado (reemplaza coverage en prod):**

| Dimensión | PoC | Prod |
|-----------|-----|------|
| tests | 25% | 20% |
| api_contract | 20% | 20% |
| response_times | 15% | 20% |
| security | 15% | 20% |
| coverage | 10% | 5% |
| code_quality | 15% | 15% |

---

## 8. Generación de reportes

### report.py

```python
"""
Generación de reportes: JSON machine-readable + texto legible para WhatsApp.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .runner import EvalResult, EvalContext


def generate_report(result: "EvalResult", ctx: "EvalContext") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = ctx.project_root / "eval" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    # JSON completo para el meta-orquestador
    json_path = report_dir / f"eval_{timestamp}.json"
    _write_json_report(result, ctx, json_path)

    # Resumen legible para WhatsApp
    txt_path = report_dir / f"eval_{timestamp}_summary.txt"
    _write_text_summary(result, ctx, txt_path)

    return json_path


def _write_json_report(result, ctx, path: Path):
    report = {
        "timestamp": datetime.now().isoformat(),
        "task_type": result.task_type.value,
        "project_mode": ctx.project_mode.value,
        "iteration": ctx.iteration,
        "weighted_score": result.weighted_score,
        "passed": result.passed,
        "dimension_scores": result.dimension_scores,
        "hitl_required": result.hitl_required,
        "thresholds_used": {
            "min_score": _get_min_threshold(ctx),
        },
        "project_root": str(ctx.project_root),
    }
    with open(path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def _write_text_summary(result, ctx, path: Path):
    lines = [
        "=" * 50,
        "NELSON EVAL HARNESS — REPORTE DE CALIDAD",
        "=" * 50,
        f"Proyecto: {ctx.project_root.name}",
        f"Tipo de tarea: {result.task_type.value.upper()}",
        f"Modo: {ctx.project_mode.value} | Iteración: {ctx.iteration}",
        f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        "─" * 50,
        f"SCORE TOTAL: {result.weighted_score:.1f}/100",
        f"RESULTADO: {'✅ APROBADO' if result.passed else '❌ RECHAZADO'}",
        "─" * 50,
        "",
        "DETALLE POR DIMENSIÓN:",
    ]

    for dim, score in result.dimension_scores.items():
        if score < 0:
            status = "⏳ PENDIENTE"
        elif score >= 80:
            status = "✅ BIEN"
        elif score >= 60:
            status = "⚠️  MEJORABLE"
        else:
            status = "❌ FALLA"
        lines.append(f"  {dim:25s} {score:5.1f}/100  {status}")

    if result.hitl_required:
        lines.extend([
            "",
            "─" * 50,
            f"REQUIERE REVISIÓN HUMANA ({len(result.hitl_required)} items):",
        ])
        for item in result.hitl_required:
            lines.append(f"  • {item['dimension']}: {item['reason']}")
            lines.append(f"    → {item['action_required']}")

    if not result.passed:
        lines.extend([
            "",
            "─" * 50,
            "PRÓXIMOS PASOS:",
            "  El meta-orquestador debe trabajar en las dimensiones con score bajo",
            "  antes de intentar una nueva entrega.",
        ])

    lines.append("=" * 50)

    with open(path, "w") as f:
        f.write("\n".join(lines))


def _get_min_threshold(ctx) -> float:
    from .thresholds import get_thresholds
    t = get_thresholds(ctx.project_mode)
    return t.get(ctx.task_type.value, {}).get("min_score", 70.0)


def format_whatsapp_message(result: "EvalResult", ctx: "EvalContext") -> str:
    """
    Formato conciso para enviar a Tony por WhatsApp.
    Sin markdown, con emojis para escaneabilidad rápida.
    """
    status_emoji = "✅" if result.passed else "❌"
    lines = [
        f"{status_emoji} Eval Harness — {result.task_type.value.upper()}",
        f"Score: {result.weighted_score:.0f}/100 | Modo: {ctx.project_mode.value}",
        "",
    ]

    # Top 3 dimensiones peores
    sorted_dims = sorted(result.dimension_scores.items(), key=lambda x: x[1])
    worst = [(d, s) for d, s in sorted_dims if s >= 0][:3]
    if worst:
        lines.append("Dimensiones más bajas:")
        for dim, score in worst:
            lines.append(f"  • {dim}: {score:.0f}/100")

    if result.hitl_required:
        lines.append("")
        lines.append(f"⏳ Necesito tu aprobación en {len(result.hitl_required)} punto(s):")
        for item in result.hitl_required:
            lines.append(f"  • {item['dimension']}: {item['action_required']}")

    if result.report_path:
        lines.append("")
        lines.append(f"Reporte completo adjunto.")

    return "\n".join(lines)
```

---

## 9. Configuración de umbrales por tipo de proyecto

### thresholds.py

```python
"""
Umbrales configurables por modo de proyecto.
PoC: más permisivo, foco en funcionalidad.
Producción: estricto, foco en calidad y performance.
"""
from .runner import ProjectMode

THRESHOLDS = {
    ProjectMode.POC: {
        "backend": {
            "min_score": 65.0,
            "response_time_ms_p95": 2000,
            "coverage_pct": 60,
            "max_bandit_medium": 5,
        },
        "frontend": {
            "min_score": 60.0,
            "lighthouse_performance": 60,
            "lighthouse_accessibility": 70,
            "lighthouse_best_practices": 70,
            "visual_diff_auto_pass_pct": 5.0,
            "visual_diff_auto_fail_pct": 25.0,
        },
        "rag": {
            "min_score": 60.0,
            "retrieval_k": 5,
            "latency_ms_p95": 5000,
            "min_retrieval_precision": 0.60,
        },
        "browser": {
            "min_score": 70.0,
        },
        "full_project": {
            "min_score": 62.0,
            "require_all_subtypes_pass": False,  # En PoC se puede tolerar algún subtype bajo
        },
    },
    ProjectMode.PRODUCTION: {
        "backend": {
            "min_score": 80.0,
            "response_time_ms_p95": 500,
            "coverage_pct": 80,
            "max_bandit_medium": 2,
        },
        "frontend": {
            "min_score": 78.0,
            "lighthouse_performance": 80,
            "lighthouse_accessibility": 90,
            "lighthouse_best_practices": 85,
            "visual_diff_auto_pass_pct": 2.0,
            "visual_diff_auto_fail_pct": 10.0,
        },
        "rag": {
            "min_score": 75.0,
            "retrieval_k": 5,
            "latency_ms_p95": 3000,
            "min_retrieval_precision": 0.75,
        },
        "browser": {
            "min_score": 80.0,
        },
        "full_project": {
            "min_score": 78.0,
            "require_all_subtypes_pass": True,  # En prod, todos deben pasar
        },
    },
}


def get_thresholds(project_mode: ProjectMode) -> dict:
    return THRESHOLDS[project_mode]


def override_thresholds(project_mode: ProjectMode, overrides: dict) -> dict:
    """
    Permite overrides por proyecto específico.
    Ejemplo: un proyecto financiero puede necesitar security más estricto.
    """
    import copy
    t = copy.deepcopy(THRESHOLDS[project_mode])
    for key, values in overrides.items():
        if key in t:
            t[key].update(values)
    return t
```

### Cómo configurar por proyecto

En el `task_spec` del meta-orquestador:

```json
{
  "project_mode": "production",
  "threshold_overrides": {
    "backend": {
      "response_time_ms_p95": 200,
      "max_bandit_medium": 0
    }
  }
}
```

---

## 10. Evaluación continua en el loop del meta-orquestador

### Protocolo de integración

El meta-orquestador debe correr el eval harness **al final de cada iteración**, no solo al final del trabajo. Esto permite detectar regresiones temprano.

```python
# En el meta-orquestador (nelson-meta-orchestrator)
from nelson_eval_harness import run_eval, EvalContext, TaskType, ProjectMode

async def meta_orchestrator_loop(task_spec: dict):
    ctx = EvalContext(
        task_type=TaskType(task_spec["type"]),
        project_mode=ProjectMode(task_spec.get("mode", "poc")),
        project_root=Path(task_spec["project_root"]),
        task_spec=task_spec,
        iteration=0,
    )

    max_iterations = task_spec.get("max_iterations", 5)
    best_result = None

    while ctx.iteration < max_iterations:
        # 1. El meta-orquestador trabaja (código, tests, etc.)
        await do_work(task_spec, ctx)

        # 2. Correr eval
        ctx.iteration += 1
        result = await run_eval(ctx)

        # 3. Guardar historial de scores
        ctx.previous_scores.append(result.weighted_score)

        # 4. Decisión
        if result.passed and not result.hitl_required:
            # Listo para entregar
            await notify_tony(result, ctx, final=True)
            return result

        if result.passed and result.hitl_required:
            # Pasa el score pero necesita revisión humana
            approved = await request_tony_approval(result, ctx)
            if approved:
                return result
            # Tony rechazó: continuar trabajando
            task_spec["tony_feedback"] = approved.feedback

        # 5. Si no pasó, analizar tendencia
        if ctx.iteration > 2 and _is_stagnating(ctx.previous_scores):
            await notify_tony(result, ctx, stagnating=True)
            return result

        # 6. Notificar progreso a Tony cada N iteraciones
        if ctx.iteration % 2 == 0:
            await notify_tony(result, ctx, interim=True)

        best_result = result

    # Agotamos iteraciones
    await notify_tony(best_result, ctx, max_iterations_reached=True)
    return best_result


def _is_stagnating(scores: list[float], window: int = 3) -> bool:
    """True si los últimos N scores no mejoran más de 2 puntos."""
    if len(scores) < window:
        return False
    recent = scores[-window:]
    return max(recent) - min(recent) < 2.0
```

### Eval en CI/CD

```yaml
# .github/workflows/nelson-eval.yml
name: Nelson Eval Harness

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[eval]"
      - name: Run Nelson Eval Harness
        run: |
          python -m nelson_eval_harness \
            --task-type ${{ env.TASK_TYPE }} \
            --project-mode ${{ env.PROJECT_MODE }} \
            --project-root . \
            --output eval_report.json
      - name: Upload eval report
        uses: actions/upload-artifact@v4
        with:
          name: eval-report
          path: eval/reports/
```

### Caché de resultados de eval

Para no recorrer todo el golden set de RAG o correr Lighthouse en cada iteración pequeña, usar caché con TTL:

```python
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta


def get_cached_eval(ctx, dimension: str, ttl_minutes: int = 30):
    cache_key = _compute_cache_key(ctx, dimension)
    cache_path = ctx.project_root / "eval" / ".cache" / f"{cache_key}.json"
    if not cache_path.exists():
        return None
    with open(cache_path) as f:
        cached = json.load(f)
    timestamp = datetime.fromisoformat(cached["timestamp"])
    if datetime.now() - timestamp > timedelta(minutes=ttl_minutes):
        return None
    return cached["score"]


def set_cached_eval(ctx, dimension: str, score: float):
    cache_key = _compute_cache_key(ctx, dimension)
    cache_dir = ctx.project_root / "eval" / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_dir / f"{cache_key}.json", "w") as f:
        json.dump({"score": score, "timestamp": datetime.now().isoformat()}, f)


def _compute_cache_key(ctx, dimension: str) -> str:
    content = f"{ctx.task_type.value}_{dimension}_{ctx.iteration}"
    return hashlib.md5(content.encode()).hexdigest()[:12]
```

---

## 11. Pitfalls y cómo evitarlos

### Pitfall 1: Score inflado por dimensiones no medibles

**Problema:** Si una dimensión no puede medirse (falta un archivo, servicio caído), el harness retorna un score neutro como 75 o 80, que infla el promedio y hace creer que todo está bien.

**Solución:** Registrar explícitamente las dimensiones "no medidas" y requerirlas como HITL. Nunca retornar un score positivo sin evidencia. Si no hay golden set para RAG, score = 0, no 75.

```python
# MAL:
if not golden_set_path.exists():
    return 75.0  # ← Esto miente

# BIEN:
if not golden_set_path.exists():
    raise EvalConfigError(
        "RAG eval requiere golden set. Crear eval/rag_golden_set.json"
    )
```

### Pitfall 2: Flakiness en tests E2E

**Problema:** Los tests de Playwright fallan intermitentemente por timing, generando falsos negativos que bloquean la entrega.

**Solución:** Retry automático con 3 intentos para dimensiones de E2E. Si falla 2 de 3 veces, recién se cuenta como falla.

```python
async def _run_with_retry(fn, attempts=3):
    scores = []
    for _ in range(attempts):
        try:
            scores.append(await fn())
        except Exception:
            scores.append(0.0)
    # Usar la mediana para evitar outliers
    scores.sort()
    return scores[len(scores) // 2]
```

### Pitfall 3: Visual diff contra baseline desactualizado

**Problema:** El equipo hace cambios de diseño intencionales, el baseline no se actualiza, y todas las evals de visual_diff fallan.

**Solución:** Workflow explícito para actualizar baseline. El harness detecta si el baseline tiene más de N días y avisa.

```python
def check_baseline_freshness(baseline_dir: Path, max_days: int = 30) -> bool:
    if not baseline_dir.exists():
        return False
    mtime = datetime.fromtimestamp(baseline_dir.stat().st_mtime)
    age = datetime.now() - mtime
    if age.days > max_days:
        print(f"⚠️  Baseline visual tiene {age.days} días. Considerar actualizar.")
    return True
```

### Pitfall 4: El meta-orquestador optimiza para el harness, no para el usuario

**Problema:** El agente aprende a pasar los tests sin resolver el problema real (overfitting al eval).

**Solución:**
- Rotar el golden set de RAG entre iteraciones.
- Incluir dimensiones que no se pueden "truquear" fácilmente (response times reales, Lighthouse en producción).
- Tony siempre ve el reporte completo, no solo el score.
- Al menos 20% del golden set es secreto y no lo ve el agente durante el trabajo.

### Pitfall 5: Timeouts en el runner bajo carga

**Problema:** El eval harness corre checks lentos (Lighthouse, benchmarks de performance) y bloquea el loop del meta-orquestador.

**Solución:** Separar los checks en rápidos (< 30s) y lentos (> 30s). Los lentos corren async en background y no bloquean la iteración.

```python
FAST_DIMENSIONS = ["tests", "console_errors", "critical_points"]
SLOW_DIMENSIONS = ["lighthouse", "response_times", "hallucination"]

async def run_eval_fast(ctx) -> EvalResult:
    """Para iteraciones intermedias: solo dimensiones rápidas."""
    ...

async def run_eval_full(ctx) -> EvalResult:
    """Para la iteración final antes de entrega: todas las dimensiones."""
    ...
```

### Pitfall 6: Reportes que Tony no lee

**Problema:** Se generan reportes JSON de 500 líneas que Tony ignora, y los problemas reales se pierden.

**Solución:** El mensaje de WhatsApp siempre va al grano: score, las 3 dimensiones peores, y una sola acción requerida si hay HITL. El JSON completo existe para el meta-orquestador y para auditoría, no para Tony.

### Pitfall 7: Correr el harness sin el servicio levantado

**Problema:** El harness intenta medir response times o hacer queries al RAG, pero el servidor no está corriendo.

**Solución:** Health check obligatorio antes de cualquier dimensión que requiera el servicio. Si el servicio no responde, el harness falla con error claro, no con score 0.

```python
async def assert_service_running(url: str, timeout: float = 5.0):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{url}/health", timeout=timeout)
            assert resp.status_code == 200
    except Exception as e:
        raise EvalPreconditionError(
            f"El servicio en {url} no está disponible. "
            f"Levantar antes de correr el harness. Error: {e}"
        )
```

---

## Uso rápido (TL;DR para el meta-orquestador)

```python
from nelson_eval_harness import run_eval, EvalContext, TaskType, ProjectMode
from pathlib import Path

result = await run_eval(EvalContext(
    task_type=TaskType.BACKEND,
    project_mode=ProjectMode.POC,
    project_root=Path("/home/server/mi-proyecto"),
    task_spec={"type": "backend"},
    extra={"api_base_url": "http://localhost:8000"},
))

print(result.summary)
# → Listo para enviar a Tony si result.passed y not result.hitl_required
```

```bash
# O desde CLI:
python -m nelson_eval_harness \
  --task-type backend \
  --project-mode poc \
  --project-root /home/server/mi-proyecto
```
