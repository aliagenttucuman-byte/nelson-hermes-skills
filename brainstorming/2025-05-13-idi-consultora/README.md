# Análisis: Área de I+D+i para la Consultora

**Fecha:** 2025-05-13
**Autor:** JARVIS / Equipo Nelson
**Estado:** Borrador para revisión
**Destinatario:** Pablo Terian + Tony Stark (Nelson Acosta)

---

## 1. Visión

El área de Investigación, Desarrollo e Innovación (I+D+i) de la consultora es el **laboratorio tecnológico** que alimenta el negocio. Su misión es detectar, evaluar y prototipar tecnologías emergentes (especialmente IA/ML, open-source y herramientas de productividad) antes de que se conviertan en obligatorias para los clientes.

> *"No queremos seguir tendencias. Queremos validarlas antes de que el mercado las exija."*

---

## 2. Objetivos Principales

| # | Objetivo | Métrica |
|---|----------|---------|
| 1 | Mantener un **radar tecnológico** actualizado 2x/día | Novedades clasificadas por semana |
| 2 | Ejecutar **spikes** (experimentos) de máximo 1-2 días | Spikes completados por mes |
| 3 | Generar **documentación reusable** de cada experimento | Docs en repo / spikes |
| 4 | Alimentar al equipo de delivery con **recomendaciones** tecnológicas | Recomendaciones adoptadas por proyecto |
| 5 | Compartir conocimiento con **YPF-I+D+i** (sinergia Nelson/YPF) | Casos de replicación cruzada |

---

## 3. Estructura: 3 Agentes Especializados

El área opera con **3 agentes de I+D+i** que reportan a Tony Stark (Líder Técnico). Cada agente tiene un scope definido y un set de skills ya existentes en el equipo.

### 3.1 Agente Backend I+D+i
**Responsable:** Experimentos con APIs, LLMs, infraestructura, bases de datos vectoriales, pipelines de datos.

**Skills que aplica:**
- `nelson-llm-generation` — integración con LLMs locales y cloud
- `nelson-vector-databases` — Qdrant, embeddings, RAG
- `nelson-rag-pipeline` — pipelines completos de RAG
- `nelson-background-jobs` — Celery, procesamiento asíncrono
- `nelson-database` — SQLAlchemy, patrones de DB
- `nelson-deploy-gcp` — deploys cloud para prototipos

**Tareas típicas:**
- Evaluar nuevo modelo de LLM (ej: gemma4, qwen3)
- Probar nueva base vectorial vs Qdrant
- Benchmark de latencia/velocidad de inferencia local
- Prototipar pipeline de embeddings para un cliente

### 3.2 Agente Frontend I+D+i
**Responsable:** Experimentos con UI/UX, visualizaciones, frameworks emergentes, herramientas de productividad frontend.

**Skills que aplica:**
- `nelson-frontend-stack` — React 18, TypeScript, Vite, Tailwind
- `nelson-frontend-testing` — testing unitario y e2e
- `nelson-react-doctor` — diagnóstico automático de apps React
- `nelson-frontend-agent` — prototipos rápidos de interfaz

**Tareas típicas:**
- Evaluar nuevo framework CSS o component library
- Prototipar dashboards de datos con D3/Recharts
- Testear herramientas de generación de UI (v0, bolt, etc.)
- Auditar performance de apps React con React Doctor

### 3.3 Agente QA I+D+i
**Responsable:** Validación de experimentos, calidad de outputs, pruebas automatizadas, detección de anomalías.

**Skills que aplica:**
- `nelson-error-review` — revisión de errores y detección de anomalías
- `nelson-code-quality` — Ruff, mypy, ESLint, calidad automatizada
- `nelson-workflow-security` — sanitización y seguridad de outputs
- `nelson-observability` — logging estructurado, monitoreo

**Tareas típicas:**
- Validar que un spike de RAG devuelve resultados correctos
- Auditar seguridad de un prototipo antes de mostrarlo a cliente
- Correr suites de tests sobre experimentos
- Documentar hallazgos de calidad y anomalías

---

## 4. Flujo de Trabajo (Pipeline I+D+i)

```
ENTRADA (Idea/Noticia)
    ↓
[1] CLASIFICACIÓN → ¿A qué agente corresponde?
    ↓
[2] CREACIÓN DE SPIKE → Template con hipótesis, alcance, tiempo máximo
    ↓
[3] EJECUCIÓN → Agente experimenta, documenta, mide
    ↓
[4] REVISIÓN QA → Validación de resultados y calidad
    ↓
[5] DECISIÓN → Adoptar / Probar / Evaluar / Descartar
    ↓
SALIDA (Documento + Recomendación)
```

**Duración máxima por spike:** 1-2 días de trabajo. Si necesita más, se convierte en proyecto formal.

---

## 5. Stack Tecnológico Base

| Capa | Herramienta | Notas |
|------|-------------|-------|
| **Agregador de noticias** | AI News Aggregator (Python/RSS) | Ya operativo, 2x/día |
| **WhatsApp Gateway** | Baileys (Node.js) | Ya operativo, envío automático |
| **LLMs locales** | Ollama | llama3.2:3b, gemma3:4b en GTX 1650 |
| **Embeddings** | nomic-embed-text vía Ollama | Ya operativo |
| **Base de datos** | SQLite (prototipos) / PostgreSQL (producción) | Ya operativo |
| **Vector DB** | Qdrant | Ya operativo |
| **CI/CD** | GitHub Actions | Lint, test, deploy |
| **Documentación** | Markdown en repo GitHub | Versionada |
| **Orchestración** | Cronjobs + scripts Python | Simple, sin complejidad innecesaria |

---

## 6. Integración con Skills Existentes

El área I+D+i **no reinventa** lo que ya existe. Reutiliza y extiende las 49 skills del equipo:

- Las skills de `software-development` son la base técnica.
- Las skills de `mlops` alimentan experimentos con modelos.
- Las skills de `nelson-*` son el estándar operativo.

Cada experimento nuevo que valga la pena se convierte en una **skill nueva** para el equipo.

---

## 7. Roadmap Propuesto (5 Etapas)

| Etapa | Nombre | Entregable | Duración estimada |
|-------|--------|------------|-------------------|
| 1 | **Análisis y Arquitectura** | Este documento aprobado | 1 día |
| 2 | **Bootstrap del Proyecto** | Estructura de carpetas + templates | 1 día |
| 3 | **Skills por Agente** | 3 skills nuevas (uno por agente) | 2 días |
| 4 | **Pipeline de Experimentos** | Script de orquestación + integración con noticias | 2 días |
| 5 | **Dashboard y Métricas** | Resumen visual de experimentos | 1-2 días |

**Total estimado:** 1 semana de trabajo distribuido (pasito a pasio).

---

## 8. Métricas y KPIs del Área

| KPI | Meta mensual | Cómo se mide |
|-----|--------------|--------------|
| Novedades clasificadas | 40+ | Contador del aggregator |
| Spikes completados | 4-6 | Registro en repo |
| Spikes adoptados | 30%+ de los completados | Tag en documentación |
| Tiempo promedio por spike | < 2 días | Tracking manual |
| Skills generadas del área | 1-2 por mes | Nuevas skills en repo |
| Sinergia YPF | 1 caso replicado por mes | Documento de caso |

---

## 9. Próximos Pasos Inmediatos

1. **Pablo y Nelson revisan y aprueban** este documento.
2. Se marca como `v1.0` y se crea la estructura base (Etapa 2).
3. Se asignan responsabilidades a cada agente.
4. Se programa la primera reunión de sincronización I+D+i (puede ser por WhatsApp).

---

## 10. Contactos Clave

| Rol | Nombre | WhatsApp | Función |
|-----|--------|----------|---------|
| Líder Técnico I+D+i | Tony Stark (Nelson) | — | Toma de decisiones, visión |
| Socio / Dirección | Pablo Terian | 5493816240691 | Aprobación estratégica, clientes |
| Agente Backend | Beto (IA) | — | Experimentos backend/infra |
| Agente Frontend | Ricky (IA) | — | Experimentos frontend/UI |
| Agente QA | Alma (IA) | — | Validación y calidad |
| Revisor / Guardián | JARVIS | — | Revisión, anomalías, automatización |

---

**Nota final:** Este documento es un borrador. Se espera feedback de Pablo y Nelson para ajustar alcance, prioridades y velocidad. La filosofía es *"menos es más"*: empezar con lo mínimo indispensable y crecer orgánicamente.

---

*Documento generado por JARVIS — Equipo Nelson*
