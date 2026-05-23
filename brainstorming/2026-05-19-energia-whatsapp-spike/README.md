# Spike: Datos Energéticos → Reporte Visual → WhatsApp

**Fecha:** 2026-05-19
**Equipo:** I+D+I (Tony + JARVIS)
**Estado:** ✅ Completado
**Directorio:** `~/brainstorming/2026-05-19-energia-whatsapp-spike/`

---

## Objetivo

Validar que es posible consumir datos públicos de la Secretaría de Energía Argentina,
procesarlos con pandas y generar un reporte visual dark-mode listo para enviar por WhatsApp.

---

## Resultado

✅ Pipeline completo funcionando en < 10 segundos
✅ Reporte PNG dark-mode generado: `output/reporte_energia.png`
✅ KPIs correctos con datos reales

---

## Datos

- **Fuente:** [datos.gob.ar](https://datos.gob.ar) — Secretaría de Energía Argentina
- **Datasets:**
  - Producción de petróleo por empresa (m³/día)
  - Producción de gas natural por empresa (m³/día)
- **Registros:** 12.000+ registros desde 2009
- **Último mes válido:** se detecta automáticamente el mes con ≥ 20 empresas reportando

## KPIs que genera

| KPI | Valor ejemplo |
|-----|---------------|
| YPF Petróleo (último mes) | m³/día |
| YPF Gas (último mes) | m³/día |
| Market share petróleo YPF | ~50% |
| Market share gas YPF | ~33% |

---

## Archivos

```
spike_energia.py          # Script principal completo
data/
  petroleo_por_empresa.csv
  gas_por_empresa.csv
output/
  reporte_energia.png     # Reporte final dark-mode
```

---

## Script principal

```bash
python3 spike_energia.py
# Genera: output/reporte_energia.png
```

---

## Técnica

1. Descarga CSVs desde datos.gob.ar via requests
2. Parseo con pandas (encoding utf-8-sig, separador `;`)
3. Detección automática del último mes completo (≥ 20 empresas)
4. Cálculo de market share sobre el mismo mes
5. Generación de reporte con matplotlib (dark mode, GridSpec 5×3)

### Pitfalls encontrados

- El CSV tiene separador `;` no `,`
- El último mes suele estar incompleto (solo 1-2 empresas) — siempre filtrar por `count >= 20`
- Market share se calcula sobre el **mismo mes**, no sobre el acumulado anual
- Ejes del gas en `0MM` si los valores son < 1M — usar formatter condicional
- Mes en inglés por defecto — usar diccionario de traducción

---

## Siguiente paso

Ver `~/brainstorming/2026-05-19-powerbi-whatsapp-spike/` para la extensión a Power BI públicos.
