# Evaluación de Repos GitHub para Self-Hosting

> **Trigger:** Tony comparte un link de GitHub y pregunta "¿qué te parece?", "¿se puede self-hostear?", "¿esto sirve?". Patrón frecuente — pasa varias veces por mes.

## Recipe (orden estricto, no inventar pasos)

### 1. Stats del repo (1 comando)

```bash
curl -s https://api.github.com/repos/OWNER/REPO | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f\"Repo: {d['full_name']}\")
print(f\"Desc: {d['description']}\")
print(f\"Stars: {d['stargazers_count']:,} | Forks: {d['forks_count']:,}\")
print(f\"Lang: {d['language']} | License: {d['license']['spdx_id'] if d['license'] else 'N/A'}\")
print(f\"Created: {d['created_at'][:10]} | Updated: {d['updated_at'][:10]}\")
print(f\"Topics: {', '.join(d.get('topics', []))}\")
"
```

**Red flags inmediatos:**
- Created hace < 30 días → demasiado nuevo, esperar (sin benchmarks, sin issues triados)
- License GPL/AGPL/no-license → revisar si Tony lo usaría comercialmente
- Updated > 12 meses → abandonado

### 2. Si es ML/AI: tamaño del modelo

```bash
# Listing HF
curl -s "https://huggingface.co/api/models/ORG/MODEL" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('Tags:', d.get('tags', [])[:10])
for f in d.get('siblings', []): print(f\"  {f['rfilename']}\")
"

# Tamaño del safetensors
curl -sIL "https://huggingface.co/ORG/MODEL/resolve/main/model.safetensors" | grep -i content-length
```

**Regla VRAM:** safetensors_GB × 1.3 = VRAM mínima en inferencia (FP16/BF16). Para entrenar multiplicar por 4-6.

### 3. Match con hardware ai-server

| Componente | Valor actual |
|---|---|
| GPU | NVIDIA GTX 1650 Mobile, 4 GB VRAM, CUDA 12.2 |
| RAM | 13 GB |
| CPU | 12 cores |
| Disco libre | revisar `df -h /home` |

**Tabla de decisión rápida:**

| VRAM modelo | Veredicto ai-server |
|---|---|
| < 3 GB | ✅ SI |
| 3-4 GB | ⚠️ entra justo, validar con `nvidia-smi` durante inferencia |
| > 4 GB | ❌ NO entra. Opciones: cuantización INT4/GGUF, RunPod, HF Inference API |

### 4. Formato de respuesta a Tony

NO escribir muros de texto. Estructura fija:

```
[QUÉ ES] — 2-3 líneas, qué hace, licencia, edad
[POR QUÉ TE INTERESA] — tabla o lista de 2-4 sinergias con proyectos activos
   (AlegentAI, ForestAI, Expreso Bisonte, LAN/LATAM, equipo Nelson)
[VIABILIDAD self-host en ai-server] — tabla con veredicto claro
[CAMINOS] — A/B/C opciones con costo y riesgo
[RECOMENDACIÓN] — UNA recomendación, no tres
```

### 5. Si la respuesta es "brainstorming"

Tony suele pedir guardar el análisis. Crear:

```
~/brainstorming/YYYY-MM-DD-NOMBRE-self-hosted-spike/
└── README.md  ← con todo el análisis y status "💡 IDEA — no iniciado"
```

Status posibles: `💡 IDEA` / `🟡 SPIKE EN CURSO` / `✅ VALIDADO` / `❌ INVALIDADO`

El README debe incluir hipótesis de valor en formato:
```
CREEMOS QUE [hipótesis]
RESULTARÁ EN [output concreto]
CRITERIOS DE ACEPTACIÓN [lista verificable]
```

## Pitfalls

- **NO recomendar fine-tuning local** sin GPU dedicada. Siempre apuntar a RunPod/Lambda on-demand para training, ai-server solo para inferencia liviana.
- **NO confiar en stars como señal de calidad** cuando el repo tiene < 30 días — son hype, no validación.
- **NO ignorar licencia** — algunos modelos NVIDIA/Baidu/Meta tienen restricciones de uso comercial que Tony necesita saber antes de venderlo a AlegentAI.
- **NO sobreingenierizar PoC** — si el caso de uso real son 10 docs/día, OpenAI/Groq API es 100x más rápido de implementar que self-host.
- **NO instalar nada en el ai-server sin pedir confirmación** — análisis primero, instalación después.
- **GTX 1650 Mobile thermal throttle** — perfil 50W de laptop, cargas largas pueden bajar performance. Mencionar si el modelo va a correr 24/7.

## Ejemplos vivos en `~/brainstorming/`

- `2026-06-24-nemo-self-hosted-spike/` — NVIDIA NeMo (framework completo)
- (otros que vayan apareciendo siguiendo el mismo patrón)
