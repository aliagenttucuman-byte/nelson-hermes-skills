# Datos Energéticos Argentina — API datos.gob.ar

## Quirks conocidos

### SSL roto
`datos.energia.gob.ar` tiene certificado SSL inválido. `curl` y `wget` fallan por defecto.
Solución: `wget --no-check-certificate` o `requests.get(..., verify=False)`.

```bash
wget --no-check-certificate --timeout=30 -O output.csv "https://datos.energia.gob.ar/..."
```

### Último mes siempre incompleto
El mes más reciente tiene muy pocas empresas reportando (a veces solo 1-2). Usar siempre
el último mes con >= 20 empresas:

```python
counts = df.groupby('fecha').size()
fecha_max = counts[counts >= 20].index.max()
```

Sin este filtro, el market share da >100% y los KPIs son basura.

## Endpoints CSV confirmados (mayo 2026)

| Dataset | URL |
|---|---|
| Petróleo por empresa (m³/día) | `https://datos.energia.gob.ar/dataset/590d1284-fd6d-4686-afd8-b3da5d90a6e9/resource/2c1f455e-0103-4d51-8f94-a49c939ac0a1/download/produccin-de-petrleo-promedio-diaria-por-empresa.csv` |
| Gas por empresa (m³/día) | `https://datos.energia.gob.ar/dataset/590d1284-fd6d-4686-afd8-b3da5d90a6e9/resource/419094dd-2905-4ac3-9398-e81513013e5e/download/produccin-de-gas-promedio-diaria-por-empresa.csv` |

Cobertura: 2009 → presente (~12.000+ registros c/u). Encoding: UTF-8 con BOM (`utf-8-sig`).

## Columnas

**Petróleo:** `anio, mes, indice_tiempo, empresa, produccion_petroleo_promedio_dia_m3`
**Gas:** `anio, mes, indice_tiempo, empresa, produccion_gas_promedio_dia_m3` (nombre varía)

`indice_tiempo` formato: `YYYY-MM` → parsear con `pd.to_datetime(df['indice_tiempo'])`.

## KPIs Abril 2026 (benchmark)

| Métrica | Valor |
|---|---|
| YPF Petróleo | 60.846 m³/día |
| YPF Gas | ~29.600 Mm³/día (~29,6 MM m³/día) |
| Market share petróleo | ~49,5% |
| Market share gas | ~33,1% |
| 2do productor petróleo | PAN AMERICAN ENERGY SL (~12.3%) |
| 2do productor gas | YPF → TOTAL AUSTRAL |

## Pipeline completo (spike validado)

```
1. Descarga CSV con wget --no-check-certificate
2. pd.read_csv(..., encoding='utf-8-sig')
3. Filtrar fecha_max con counts >= 20
4. Calcular KPIs (YPF, market share, variación mensual, top 5)
5. Generar reporte matplotlib (dark mode, 12x16, dpi=150)
6. Guardar PNG → mandar por Baileys WhatsApp
```

Script de referencia: `~/brainstorming/2026-05-19-energia-whatsapp-spike/spike_energia.py`

## Escala de producción

- Petróleo: m³/día promedio → para comunicar usar m³/día o "miles de m³/día"
- Gas: m³/día → dividir por 1.000.000 para MM m³/día (más legible en comunicación)

## Formateo matplotlib para escalas

```python
# Gas: el valor puede estar en m³, no MM m³ → detectar escala antes de formatear
max_val = max(valores)
if max_val > 1e6:
    formatter = lambda x, _: f'{x/1e6:.1f}MM'
else:
    formatter = lambda x, _: f'{x/1000:.0f}k'
ax.yaxis.set_major_formatter(mticker.FuncFormatter(formatter))
```

Sin este check, los ejes de gas pueden mostrar "0MM" si los datos están en miles, no millones.
