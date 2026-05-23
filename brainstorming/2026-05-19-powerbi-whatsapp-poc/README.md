# PoC: Datos Energéticos → Reporte Visual → WhatsApp

**Fecha:** 2026-05-19  
**Equipo:** I+D+I (Tony + JARVIS)  
**Estado:** Documentado — Ejecución: 2026-05-20  
**Directorio:** `~/brainstorming/2026-05-19-powerbi-whatsapp-poc/`

---

## Objetivo

Demostrar que JARVIS puede consumir datos públicos de energía (equivalente a un tablero PowerBI), procesarlos con un LLM, y generar un reporte visual interpretado enviado por WhatsApp.

**Es la PoC base para el caso real de YPF con PowerBI corporativo.**

---

## Flow Completo

```
API datos.gob.ar
       │
       ▼
  CSV Producción
  Petróleo/Gas
  por Empresa
       │
       ▼
  Procesamiento
  Python (pandas)
  ─ Últimos 12 meses
  ─ KPIs: total, variación, market share YPF
  ─ Top cuencas
       │
       ▼
  LLM (Claude)
  ─ Interpreta los números
  ─ Genera análisis en lenguaje natural
  ─ Detecta tendencias / anomalías
       │
       ▼
  Generación imagen
  (matplotlib + PIL)
  ─ Gráfico de barras / líneas
  ─ KPIs destacados
  ─ Análisis LLM integrado
  ─ Diseño limpio tipo reporte
       │
       ▼
  WhatsApp
  (Gateway Baileys)
  ─ Imagen del reporte
  ─ Texto de análisis
  ─ Lista de contactos
```

---

## Fuente de Datos

**API:** `https://www.datos.gob.ar/api/3/action/`  
**Dataset:** Producción de Petróleo y Gas (SESCO) — Secretaría de Energía  
**ID:** `energia-produccion-petroleo-gas-sesco`

### CSVs a usar

| Dataset | URL |
|---------|-----|
| Producción petróleo por empresa | `https://datos.energia.gob.ar/.../produccin-petrleo-sesco-tight-y-shale-captulo-iv-por-empresa.csv` |
| Producción gas por empresa | `https://datos.energia.gob.ar/.../produccin-gas-sesco-tight-y-shale-captulo-iv-por-empresa.csv` |
| Producción petróleo promedio diaria por empresa | `https://datos.energia.gob.ar/.../produccin-de-petrleo-promedio-diaria-por-empresa.csv` |
| Producción gas promedio diaria por empresa | `https://datos.energia.gob.ar/.../produccin-de-gas-promedio-diaria-por-empresa.csv` |

---

## KPIs a Calcular

### Petróleo
- Producción total Argentina último mes disponible (m³)
- Producción YPF último mes (m³)
- Market share YPF (%)
- Variación mes anterior (%)
- Tendencia últimos 6 meses

### Gas
- Producción total Argentina último mes (miles m³)
- Producción YPF último mes (miles m³)
- Market share YPF (%)
- Variación mes anterior (%)

### Contexto
- Top 3 empresas productoras de petróleo
- Top 3 empresas productoras de gas
- Comparación YPF vs resto del mercado

---

## Stack Técnico

| Capa | Tecnología |
|------|-----------|
| Fetch datos | `requests` + API REST |
| Procesamiento | `pandas` |
| LLM análisis | Claude (Anthropic API) vía Hermes |
| Visualización | `matplotlib` + `PIL` |
| Envío | WhatsApp Gateway Baileys (ya disponible) |

### Dependencias Python
```
requests
pandas
matplotlib
pillow
anthropic
```

---

## Diseño del Reporte Visual

```
┌─────────────────────────────────────────┐
│  🛢️ REPORTE ENERGÉTICO ARGENTINA        │
│  Producción Petróleo & Gas — [Mes/Año]  │
├─────────────┬─────────────┬─────────────┤
│  YPF        │  TOTAL AR   │  MARKET     │
│  XXX m³     │  XXX m³     │  SHARE XX%  │
│  ▲ +X.X%    │             │             │
├─────────────┴─────────────┴─────────────┤
│                                         │
│  [Gráfico de líneas: últimos 12 meses] │
│   YPF vs Total Argentina                │
│                                         │
├─────────────────────────────────────────┤
│  📊 Top Productoras                     │
│  1. YPF        XX%                      │
│  2. Pan Am     XX%                      │
│  3. Total      XX%                      │
├─────────────────────────────────────────┤
│  🤖 Análisis JARVIS:                    │
│  [Texto generado por LLM]               │
│  — 3 bullets clave                      │
│  — Tendencia detectada                  │
│  — Dato destacado del mes               │
└─────────────────────────────────────────┘
```

---

## Estructura de Archivos

```
2026-05-19-powerbi-whatsapp-poc/
├── README.md               ← este archivo
├── spike/
│   ├── fetch_data.py       ← descarga y limpia los CSVs
│   ├── calculate_kpis.py   ← calcula KPIs con pandas
│   ├── llm_analysis.py     ← análisis con Claude
│   ├── generate_report.py  ← genera imagen del reporte
│   └── send_whatsapp.py    ← envío final por WA
├── data/
│   └── .gitkeep            ← CSVs descargados (no commitear)
└── output/
    └── .gitkeep            ← imágenes generadas
```

---

## Plan de Ejecución — 2026-05-20

### Paso 1: Fetch & Limpieza (15 min)
- Descargar CSVs de producción petróleo y gas
- Explorar columnas, tipos de datos, fechas disponibles
- Filtrar últimos 12 meses y empresas principales

### Paso 2: KPIs (15 min)
- Calcular todos los KPIs definidos arriba
- Validar que los números tienen sentido
- Preparar dict/JSON para el LLM

### Paso 3: LLM Analysis (15 min)
- Armar prompt con los KPIs calculados
- Pedirle a Claude 3 bullets de análisis + tendencia + dato destacado
- Validar que el texto sea correcto y claro

### Paso 4: Imagen (20 min)
- Armar layout con matplotlib/PIL
- Integrar KPIs + gráfico + análisis LLM
- Exportar como PNG 1080x1920 (formato vertical WhatsApp)

### Paso 5: Envío (10 min)
- Enviar imagen + texto por WhatsApp
- Probar con el número de Tony primero
- Si OK → enviar a lista completa

**Tiempo total estimado: ~75 min**

---

## Camino hacia YPF (post-PoC)

Una vez validado el flow con datos públicos, la misma lógica aplica a PowerBI corporativo:

1. **Autenticación:** Azure AD App Registration → token OAuth2
2. **Fetch datos:** Power BI REST API → datasets, reports, páginas
3. **Export:** `POST /reports/{id}/ExportTo` → PDF o PNG del tablero
4. **Alternativa scraping:** Playwright → login AAD → screenshot tablero
5. **Mismo flow:** LLM interpreta → imagen → WhatsApp

La diferencia es solo la fuente de datos. El motor de análisis y envío es idéntico.

---

## Contactos delivery inicial

- Nelson (Tony) — número principal
- Gabi — 5491132438887
- Pablo — 5493816240691  
- Faku — 5493813022552

---

*Documentado por JARVIS — 2026-05-19*
