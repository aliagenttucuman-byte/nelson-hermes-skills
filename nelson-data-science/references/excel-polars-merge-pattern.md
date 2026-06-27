# Patrón: Procesamiento de Excel/CSV con Polars + FastAPI

> Patrón reutilizable del PoC Excel Merger (2026-06-02).
> Caso de uso: cruzar datos de múltiples archivos Excel/CSV mediante reglas configurables.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11, FastAPI, Polars, OpenAI SDK |
| Frontend | React 19, Vite, Axios |
| Procesamiento | Polars (joins, concat, transforms) |
| Reglas LLM | NVIDIA NIM Free API (opcional) |

## Endpoints API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/excel/upload` | Subir 1 Excel |
| POST | `/excel/upload-multiple` | Subir varios Excels |
| GET | `/excel/preview/{file_id}` | Preview tabla (50 filas) |
| GET | `/excel/files` | Listar archivos subidos |
| POST | `/excel/merge` | Ejecutar cruce con reglas |
| GET | `/excel/download/{file_id}` | Descargar Excel resultante |

## Motor Polars

```python
import polars as pl
from pathlib import Path
import uuid

# Cache de DataFrames en memoria
_df_cache: dict[str, pl.DataFrame] = {}

def load_df(file_id: str, file_path: str) -> pl.DataFrame:
    if file_id in _df_cache:
        return _df_cache[file_id]
    path = Path(file_path)
    if path.suffix == ".csv":
        df = pl.read_csv(path, infer_schema_length=10000)
    else:
        df = pl.read_excel(path)
    _df_cache[file_id] = df
    return df

def merge_dataframes(
    left_id: str, left_path: str,
    right_id: str, right_path: str,
    left_key: str, right_key: str,
    join_type: str = "inner",
) -> pl.DataFrame:
    left = load_df(left_id, left_path)
    right = load_df(right_id, right_path)
    # Normalizar tipos para el join
    left = left.with_columns(pl.col(left_key).cast(pl.Utf8))
    right = right.with_columns(pl.col(right_key).cast(pl.Utf8))
    return left.join(right, left_on=left_key, right_on=right_key, how=join_type)

def save_result(df: pl.DataFrame, original_name: str = "merged") -> str:
    file_id = str(uuid.uuid4())
    filename = f"{original_name}_{file_id}.xlsx"
    df.write_excel(Path("/tmp/excel-merger") / filename)
    return filename
```

## Reglas de negocio soportadas

| Tipo | Descripción |
|------|-------------|
| **Merge** (join) | Cruzar 2+ archivos por columna común: `inner`, `left`, `outer` |
| **Concat** | Apilar verticalmente (append) |
| **LLM Rules** | Enviar muestra del DataFrame a un LLM para interpretar reglas en lenguaje natural y generar código Polars automáticamente |

## Payload de ejemplo /merge

```json
{
  "file_ids": ["uuid-1", "uuid-2"],
  "rules": [
    {
      "left_key": "ID_Cliente",
      "right_key": "ClienteID",
      "join_type": "inner",
      "how": "merge"
    }
  ],
  "llm_prompt": "Filtrar solo donde Estado='Activo' y calcular Total = Cantidad * Precio"
}
```

## Reglas LLM con NVIDIA NIM

```python
from openai import OpenAI

def apply_llm_rules(df: pl.DataFrame, prompt: str, api_key: str) -> pl.DataFrame:
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )
    schema_desc = ", ".join([f"{c} ({df[c].dtype})" for c in df.columns])
    sample = df.head(5).to_dicts()
    full_prompt = f"""Eres un experto en análisis de datos.
DataFrame con columnas: {schema_desc}
Muestra: {sample}
Regla de negocio: {prompt}
Responde SOLO con código Python usando Polars que transforme el DataFrame `df`."""
    resp = client.chat.completions.create(
        model="deepseek-ai/deepseek-v4-pro",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.2,
        max_tokens=2048,
    )
    code = resp.choices[0].message.content.strip()
    # Limpiar markdown si viene envuelto
    if code.startswith("```python"):
        code = code.split("```python", 1)[1]
    if code.endswith("```"):
        code = code.rsplit("```", 1)[0]
    code = code.strip()
    # Ejecutar de forma segura
    local_ns = {"pl": pl, "df": df}
    exec(code, {"__builtins__": {}}, local_ns)
    return local_ns.get("df", df)
```

## Pitfalls

- **Tipos de datos en joins**: Polars es estricto con tipos. Si `left_key` es `Int64` y `right_key` es `Utf8`, el join falla. Siempre normalizar a `Utf8` antes del join.
- **OneDrive bloquea archivos temporales**: Si el proyecto está en OneDrive, las carpetas `build`, `.dart_tool`, o archivos temporales de Excel pueden quedar bloqueados. Sacar el proyecto de OneDrive.
- **Vite proxy en Docker**: `localhost` en el navegador del usuario apunta a su máquina, no al servidor. Usar la URL pública del backend en `VITE_API_URL`.
- **Polars `read_excel` requiere `xlsx2csv` o `openpyxl`**: instalar `xlsx2csv>=0.8` o `openpyxl>=3.1` como dependencia.
