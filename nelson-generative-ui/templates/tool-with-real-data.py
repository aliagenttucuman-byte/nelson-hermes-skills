"""
Template: Tool con datos reales embebidos en el system prompt.
Copiar a backend/tools/mi_proyecto.py y adaptar.

PATRÓN CLAVE:
- Pre-calcular datos al momento de get_system_instructions()
- Embeber JSON directamente en el prompt (no function calling)
- Usar sintaxis OpenUI Lang FUNCIONAL con nombres PascalCase exactos
- Separar labels y values como listas Python (no objetos)
"""
import json
from tools.registry import BaseTool, register


def cargar_datos() -> list[dict]:
    """Retorna lista de dicts con los datos del dataset."""
    # Reemplazar con carga real: CSV, API, JSON, DB
    return [
        {"nombre": "Empresa A", "valor": 1000},
        {"nombre": "Empresa B", "valor": 800},
        {"nombre": "Empresa C", "valor": 600},
    ]


@register
class MiProyectoTool(BaseTool):
    name = "mi_proyecto"
    description = "Descripción del proyecto — fuente de datos"

    def get_system_instructions(self) -> str:
        rows = cargar_datos()
        datos_json = json.dumps(rows, ensure_ascii=False)

        # Separar en listas para OpenUI Lang — BarChart/PieChart necesitan arrays
        labels = json.dumps([r["nombre"] for r in rows], ensure_ascii=False)
        values = json.dumps([r["valor"] for r in rows])

        return f"""
# Fuente: Mi Proyecto — Descripción de qué son los datos
Datos reales. No inventar cifras fuera de los datos provistos.

## Datos disponibles
{datos_json}

## Cómo responder — USAR EXACTAMENTE esta sintaxis OpenUI Lang

Para HorizontalBarChart (ideal cuando los labels son nombres largos):
```openui
root = Card([header, chart])
header = CardHeader("Título descriptivo")
labels = {labels}
s1 = Series("Unidad de medida", {values})
chart = HorizontalBarChart(labels, [s1])
```

Para KPI (un solo valor destacado):
```openui
root = Stack([title, value])
title = TextContent("Nombre del KPI", "small")
value = TextContent("1,234", "large-heavy")
```

Para BarChart agrupado (múltiples métricas por categoría):
```openui
root = Card([header, chart])
header = CardHeader("Comparativa")
labels = ["Cat A", "Cat B", "Cat C"]
s1 = Series("Métrica 1", [100, 200, 150])
s2 = Series("Métrica 2", [80, 160, 120])
chart = BarChart(labels, [s1, s2], "grouped")
```

## Regla de oro
Componentes válidos: BarChart, HorizontalBarChart, LineChart, PieChart,
Card, CardHeader, Stack, TextContent, Series, Table, Col, Tabs, TabItem.
Cualquier otro nombre causa unknown-component silencioso — el usuario no ve nada.
"""
