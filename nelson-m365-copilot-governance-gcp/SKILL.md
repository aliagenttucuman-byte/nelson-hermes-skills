---
name: nelson-m365-copilot-governance-gcp
description: PoC de governance para Microsoft 365 Copilot enterprise sobre floci-gcp + Terraform. Ingesta de audit logs de Microsoft Graph API → GCS (parquet) → Firestore (agregados) → dashboard FastAPI/React con KPIs de uso, riesgo y compliance. Diseñada para el contrato de Nelson con LAN/LATAM (Data Scientist Sr, governance Copilot). Extiende nelson-poc-gcp-terraform-template con conectores Graph, modelos de risk scoring, y reportes ISO/SOC2-ready.
when_to_use: PoC de M365 Copilot governance; demo a LAN sobre uso/riesgo de Copilot enterprise; ingestión Graph API audit logs; dashboard compliance Copilot; risk scoring de prompts/respuestas.
---

# nelson-m365-copilot-governance-gcp

PoC de **governance de M365 Copilot** para enterprise. Tema central del contrato Nelson @ LAN/LATAM (Intermedia LLC). Construida sobre `nelson-poc-gcp-terraform-template` + `nelson-lan-airline-poc-stack`.

## Contexto del problema (lo que LAN quiere resolver)

M365 Copilot está desplegado en LATAM Airlines Group. Riesgos enterprise:

1. **Data leakage:** ¿Qué docs sensibles está leyendo Copilot vía Graph?
2. **Prompt injection / abuse:** ¿Usuarios pidiendo cosas que no deberían?
3. **Compliance:** ¿Cumplimos GDPR / Chile Ley 19.628 / ISO 27001?
4. **Adopción:** ¿Quién usa Copilot, para qué, cuánto valor genera?
5. **Costos:** ¿USD/usuario/mes vs valor entregado?
6. **Shadow AI:** ¿Hay usuarios pegando data corporativa en ChatGPT externo?

LAN necesita: **panel único** con todos esos KPIs, drillable por dirección/aerolínea/usuario, con alertas automáticas.

## Arquitectura de la PoC

```
Microsoft Graph API
       │
       │ (audit logs cada 5 min)
       ▼
   collector
   (FastAPI worker)
       │
       ├──→ GCS (parquet diario)
       │       └── governance-copilot-{lan}-data/
       │             ├── raw/year=2026/month=06/day=27/
       │             └── curated/usage_daily/, risk_events/
       │
       └──→ Firestore (agregados en tiempo real)
               ├── users/{userId}/stats
               ├── risk_events/{eventId}
               └── daily_kpis/{date}

                Dashboard FastAPI + React :8030
                   ├── /api/kpis/usage
                   ├── /api/kpis/risk
                   ├── /api/kpis/compliance
                   ├── /api/users/{id}/timeline
                   ├── /api/risk-events
                   └── /api/chat  (preguntale en NL)
```

Todo corre sobre floci-gcp local en la PoC. En prod va a Cloud Run + GCS + Firestore reales.

## KPIs del dashboard

### Usage
- Usuarios activos diarios/semanales/mensuales (DAU/WAU/MAU)
- Prompts por usuario (p50, p95, p99)
- Top apps consumidoras (Word, Excel, Outlook, Teams)
- Adopción por dirección/aerolínea (LA, JJ, LP, XL, 4M, UC)
- Time-to-value (días desde licencia → primer prompt útil)

### Risk
- **Prompts sospechosos** (clasificador propio: PII, data exfil, jailbreak intent)
- **Acceso a docs sensibles** (cruzar Sensitivity Labels MIP con prompts)
- **Picos anómalos** (un usuario hace 500 prompts en 1 hora → alerta)
- **Shadow AI detection** (cruzar con proxy logs si están disponibles)
- **Risk score** por usuario (0-100, ponderado)

### Compliance
- Audit log completeness (% eventos capturados)
- Data retention compliance (>90 días? <X días?)
- DSAR readiness (¿podés exportar lo de un usuario en 24h?)
- Consent tracking (¿hay registro del opt-in del usuario?)

### Cost
- USD/usuario/mes vs benchmark
- ROI estimado (tiempo ahorrado × salario promedio)
- Licencias inactivas (paga pero <1 prompt/mes)

## Bootstrap de la PoC

### 1) Base del template

```bash
PROYECTO=lan-copilot-gov-poc
# Seguir nelson-poc-gcp-terraform-template
```

### 2) Sumar dependencias específicas

```python
# backend/requirements.txt — agregar:
msgraph-sdk==1.0.0          # Microsoft Graph SDK
azure-identity==1.15.0      # OAuth client credentials
polars==0.20.5              # DataFrames (stack LAN)
pyarrow==15.0.0             # Parquet writer
prophet==1.1.5              # Forecasting de uso
shap==0.44.0                # Risk score explainability
xgboost==2.0.3              # Clasificador de prompts riesgosos
```

### 3) Variables de entorno extras (Secret Manager)

En `terraform/environments/local-full/main.tf`, agregar secrets:

```hcl
module "secrets" {
  source = "../../modules/secrets"
  secrets = {
    "AI_API_KEY"             = var.openai_key
    "GRAPH_TENANT_ID"        = var.tenant_id
    "GRAPH_CLIENT_ID"        = var.client_id
    "GRAPH_CLIENT_SECRET"    = var.client_secret
  }
}
```

En modo PoC local, podés usar **mock data** (no requiere tenant real M365). En prod, app registration en Entra ID con `AuditLog.Read.All`, `Directory.Read.All`, `Reports.Read.All`.

### 4) Collector worker (FastAPI background task)

```python
# backend/collectors/graph_audit.py
from msgraph import GraphServiceClient
from azure.identity import ClientSecretCredential
import polars as pl
from gcp_adapters import get_storage_client, get_firestore_client

async def collect_audit_logs(start: datetime, end: datetime):
    """Pulla audit logs de Graph y los persiste."""
    cred = ClientSecretCredential(
        tenant_id=get_secret("GRAPH_TENANT_ID"),
        client_id=get_secret("GRAPH_CLIENT_ID"),
        client_secret=get_secret("GRAPH_CLIENT_SECRET"),
    )
    client = GraphServiceClient(credentials=cred, scopes=["https://graph.microsoft.com/.default"])
    
    events = []
    async for event in client.audit_logs.directory_audits.get():
        if "Copilot" in event.activity_display_name:
            events.append(event_to_dict(event))
    
    # GCS: parquet diario
    df = pl.DataFrame(events)
    bucket = get_storage_client().bucket(f"{PROYECTO}-data")
    blob = bucket.blob(f"raw/year={start.year}/month={start.month:02d}/day={start.day:02d}/audit.parquet")
    blob.upload_from_string(df.write_parquet())
    
    # Firestore: agregados
    fs = get_firestore_client()
    for e in events:
        fs.collection("risk_events").document(e["id"]).set(e)
```

### 5) Risk scoring con XGBoost

```python
# backend/ml/risk_classifier.py
import xgboost as xgb
import shap

# Features: prompt_length, contains_pii_pattern, accessed_sensitive_label,
#           user_role_seniority, hour_of_day, app_used, ...
# Label: is_risky (manual review + GPT-4 weak labels)

class PromptRiskClassifier:
    def __init__(self):
        self.model = xgb.XGBClassifier()
        self.explainer = None
    
    def predict_with_shap(self, prompt_features):
        prob = self.model.predict_proba([prompt_features])[0, 1]
        shap_values = self.explainer.shap_values([prompt_features])
        return {"risk_score": float(prob * 100), "explanation": shap_values[0].tolist()}
```

### 6) Dashboard frontend

Vistas mínimas:

1. **Home:** 4 KPI cards (DAU, Risk Events Today, Compliance Score, Cost MTD)
2. **Usage Tab:** charts de adopción por dirección, top apps, heatmap horario
3. **Risk Tab:** lista de risk_events con score + SHAP explanation, filtros
4. **User Drilldown:** timeline de un usuario, prompts, docs accedidos, risk trend
5. **Compliance Tab:** audit completeness, retention status, DSAR exports
6. **Chat:** "¿quiénes son los top 5 usuarios de Copilot en JJ esta semana?"

## Mock data para demo (sin tenant real)

```python
# backend/mock_data/generate.py
import polars as pl
import random
from datetime import datetime, timedelta

USERS = [f"user{i:04d}@latam.com" for i in range(1, 501)]
AEROLINEAS = ["LA", "JJ", "LP", "XL", "4M", "UC"]
APPS = ["Word", "Excel", "Outlook", "Teams", "PowerPoint"]

def generate_audit_events(days: int = 30) -> pl.DataFrame:
    events = []
    for day in range(days):
        date = datetime.now() - timedelta(days=day)
        for _ in range(random.randint(800, 1500)):
            events.append({
                "id": str(uuid.uuid4()),
                "timestamp": date - timedelta(hours=random.randint(0, 23)),
                "user": random.choice(USERS),
                "aerolinea": random.choice(AEROLINEAS),
                "app": random.choice(APPS),
                "prompt_length": random.randint(20, 800),
                "risk_score": random.gauss(15, 20),  # most low risk
                "sensitive_label_accessed": random.random() < 0.05,
            })
    return pl.DataFrame(events)
```

## Pitfalls

1. **Graph API throttling:** 10k requests / 10 min por app. Implementar backoff exponencial en el collector.
2. **Audit logs delay:** Microsoft tarda 30-60 min en exponer eventos en el endpoint. NO esperés tiempo real verdadero.
3. **PII en logs:** Los audit logs traen UPNs (emails). Anonimizar antes de mostrar en demo pública. Hash SHA256 con salt.
4. **Sensitivity Labels:** Requieren licencia MIP (Microsoft Purview Information Protection). Si LAN no la tiene, ese KPI no se puede levantar — proponer alternativa.
5. **Costo Graph API:** Es gratis pero limitado. Para tenants grandes (LAN tiene ~10k usuarios) el pull diario puede tardar 1-2h. Schedular nocturno.
6. **Mock vs real:** En la demo a LAN siempre arrancar con mock data + opción de "conectar tenant real" como Phase 2. No prometer integración Day 1.
7. **GDPR + Chile 19.628:** Risk events son datos personales. Retención máxima 90 días por default, configurable. Documentar en `docs/COMPLIANCE.md`.
8. **No mostrar prompts en claro:** Solo metadata + features. Mostrar el prompt textual es violación de privacidad en mayoría de jurisdicciones.

## Deliverables al cliente

- **Repo privado:** `aliagenttucuman-byte/lan-copilot-gov-poc`
- **Demo URL:** `http://localhost:8030` durante la reunión
- **Docs:**
  - `docs/END-TO-END.md` (template estándar)
  - `docs/COMPLIANCE.md` (GDPR + Ley 19.628 + ISO 27001 mapping)
  - `docs/CONNECTORS.md` (cómo enganchar tenant real M365)
  - `docs/RISK_MODEL.md` (features del XGBoost, métricas de validación)
- **Slide deck:** problema → solución → demo en vivo → roadmap → costos

## Pasaje a prod (Cloud Run + GCP real)

```bash
cd terraform/environments/prod
# Cambiar: project_id real LAN, region us-central1 o southamerica-east1 (GRU)
terraform apply
```

Recursos extra en prod:
- Cloud Scheduler → trigger del collector cada 30 min
- BigQuery → para queries analíticas grandes (los parquet de GCS)
- Looker Studio → dashboards ejecutivos (opcional, sobre BQ)
- IAM granular: solo el SA del collector lee secrets de Graph

## Referencias

- Base: `nelson-poc-gcp-terraform-template`
- Stack LAN: `nelson-lan-airline-poc-stack`
- ML: `nelson-data-science`, `nelson-finance-ml`
- Docs LAN contractor: USER.md
- Microsoft Graph audit reference: https://learn.microsoft.com/graph/api/resources/directoryaudit
- Microsoft Purview Copilot governance: https://learn.microsoft.com/purview/ai-microsoft-purview
