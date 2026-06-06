# Patrón: Excel Merger con Polars + LLM

## Resumen

Arquitectura completa para cruzar múltiples archivos Excel/CSV, aplicar reglas de negocio generadas por LLM, y devolver un Excel resultante.

**Backend:** FastAPI + Polars + openpyxl
**Frontend:** React + TypeScript + Tailwind + shadcn/ui + Lucide
**LLM:** NVIDIA NIM Free API (OpenAI SDK compatible)
**Caso real:** PoC "Excel Merger" (2026-05-22) — procesa múltiples Excels, cruza por columnas clave, aplica reglas via LLM, descarga resultado.

## Backend — FastAPI Service

```python
# app/services/excel_processor.py
import polars as pl
from pathlib import Path
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import io

def read_excel_to_df(file_bytes: bytes, filename: str) -> pl.DataFrame:
    """Lee Excel/CSV a Polars DataFrame."""
    ext = Path(filename).suffix.lower()
    if ext == '.csv':
        return pl.read_csv(io.BytesIO(file_bytes))
    else:
        return pl.read_excel(io.BytesIO(file_bytes))


def merge_dataframes(
    left: pl.DataFrame, right: pl.DataFrame,
    left_key: str, right_key: str, join_type: str = "inner"
) -> pl.DataFrame:
    """Join seguro con cast a string para evitar mismatch de tipos."""
    if left_key not in left.columns:
        raise ValueError(f"Columna '{left_key}' no existe. Columnas: {left.columns}")
    if right_key not in right.columns:
        raise ValueError(f"Columna '{right_key}' no existe. Columnas: {right.columns}")
    left = left.with_columns(pl.col(left_key).cast(pl.Utf8))
    right = right.with_columns(pl.col(right_key).cast(pl.Utf8))
    return left.join(right, left_on=left_key, right_on=right_key, how=join_type)


def build_llm_prompt(df: pl.DataFrame, user_prompt: str) -> str:
    """Construye prompt enriquecido con esquema y muestra."""
    schema_desc = "\n".join([f"  - {c}: {df[c].dtype}" for c in df.columns])
    sample = df.head(5).to_dicts()
    sample_str = "\n".join([f"  {row}" for row in sample])
    return f"""Sos un experto en análisis de datos con Polars (Python).

Tu tarea es:
1. Entender la intención del usuario (cruces, filtros, cálculos, agrupaciones).
2. Generar UNA ÚNICA expresión de código Python usando Polars que transforme el DataFrame `df`.
3. La expresión debe devolver un nuevo DataFrame de Polars.
4. No escribas explicaciones. Solo código. No uses markdown.

REGLAS DE SEGURIDAD:
- NO uses `eval()`, `exec()`, `open()`, `os`, `sys`, `subprocess`.
- SOLO usa operaciones de Polars: filtros, joins, groupby, select, with_columns, etc.
- El resultado debe ser un DataFrame de Polars.

ESTRUCTURA DEL DATAFRAME:
{schema_desc}

MUESTRA DE DATOS (primeras 5 filas):
{sample_str}

DESCRIPCIÓN DEL USUARIO:
{user_prompt}

GENERÁ SOLO EL CÓDIGO (una expresión que devuelva el DataFrame transformado):"""


def apply_llm_dataframe_rules(
    df: pl.DataFrame, prompt: str, client, model: str
) -> pl.DataFrame:
    """Envía prompt al LLM y ejecuta código Polars generado de forma segura."""
    full_prompt = build_llm_prompt(df, prompt)
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": full_prompt}],
        temperature=0.1, max_tokens=2048,
    )
    code = resp.choices[0].message.content.strip()
    # Limpiar markdown
    for prefix in ["```python", "```"]:
        if code.startswith(prefix):
            code = code[len(prefix):]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()

    local_ns = {"pl": pl, "df": df}
    exec(code, {"__builtins__": {}}, local_ns)
    result = local_ns.get("df", df)
    for key, val in local_ns.items():
        if isinstance(val, pl.DataFrame) and key != "df":
            result = val
            break
    return result


def df_to_excel_bytes(df: pl.DataFrame) -> bytes:
    """Exporta DataFrame Polars a bytes Excel (.xlsx)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = df.columns
    ws.append(list(headers))
    for row in df.to_dicts():
        ws.append([row.get(h, None) for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
```

## Frontend — React Component (Drag & Drop + Preview)

```tsx
// src/pages/Merger.tsx
import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileSpreadsheet, Download, Play, RotateCcw } from 'lucide-react';

interface MergeResult {
  row_count: number;
  columns: string[];
  preview: Record<string, unknown>[];
}

export function MergerPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [leftKey, setLeftKey] = useState('');
  const [rightKey, setRightKey] = useState('');
  const [joinType, setJoinType] = useState('inner');
  const [llmPrompt, setLlmPrompt] = useState('');
  const [model, setModel] = useState('qwen/qwen3.5-397b-a17b');
  const [result, setResult] = useState<MergeResult | null>(null);
  const [loading, setLoading] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    setFiles(prev => [...prev, ...accepted]);
  }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'], 'text/csv': ['.csv'] }
  });

  const handleMerge = async () => {
    if (files.length < 2) return;
    setLoading(true);
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('left_key', leftKey);
    formData.append('right_key', rightKey);
    formData.append('join_type', joinType);
    formData.append('llm_prompt', llmPrompt);
    formData.append('model', model);

    const res = await fetch('/api/merge', { method: 'POST', body: formData });
    const data = await res.json();
    setResult(data);
    setLoading(false);
  };

  const downloadResult = async () => {
    const res = await fetch('/api/merge/download');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'resultado.xlsx';
    a.click();
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Excel Merger</h1>
      {/* Dropzone */}
      <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${isDragActive ? 'border-blue-400 bg-blue-50/5' : 'border-gray-600'}`}>
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg">Arrastrá archivos Excel/CSV acá</p>
        <p className="text-sm text-gray-400 mt-2">o hacé click para seleccionar</p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {files.map((f, i) => (
            <span key={i} className="bg-gray-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
              <FileSpreadsheet className="h-4 w-4" />{f.name}
            </span>
          ))}
        </div>
      )}

      {/* Configuración */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <input value={leftKey} onChange={e => setLeftKey(e.target.value)} placeholder="Columna clave izquierda" className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2" />
        <input value={rightKey} onChange={e => setRightKey(e.target.value)} placeholder="Columna clave derecha" className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2" />
        <select value={joinType} onChange={e => setJoinType(e.target.value)} className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2">
          <option value="inner">Inner Join</option><option value="left">Left Join</option><option value="right">Right Join</option><option value="full">Full Outer</option><option value="cross">Cross</option>
        </select>
      </div>

      {/* Selector de modelo */}
      <div className="mt-4">
        <label className="block text-sm text-gray-400 mb-1">Modelo LLM (NVIDIA NIM)</label>
        <select value={model} onChange={e => setModel(e.target.value)} className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 w-full">
          <option value="qwen/qwen3.5-397b-a17b">Qwen 3.5 397B (default)</option>
          <option value="deepseek-ai/deepseek-v4-pro">DeepSeek V4 Pro</option>
          <option value="deepseek-ai/deepseek-v4-flash">DeepSeek V4 Flash</option>
          <option value="mistralai/mistral-medium-3.5-128b">Mistral Medium 3.5 128B</option>
          <option value="meta/llama-3.2-90b-vision-instruct">Llama 3.2 90B Vision</option>
        </select>
      </div>

      {/* Prompt LLM */}
      <div className="mt-4">
        <label className="block text-sm text-gray-400 mb-1">Reglas adicionales (opcional — el LLM genera código Polars)</label>
        <textarea value={llmPrompt} onChange={e => setLlmPrompt(e.target.value)} placeholder="Ej: filtrar donde 'Estado' == 'Activo', calcular 'Total' = 'Cantidad' * 'Precio', agrupar por 'Categoría'..." rows={3} className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 w-full" />
      </div>

      {/* Acciones */}
      <div className="flex gap-4 mt-6">
        <button onClick={handleMerge} disabled={loading || files.length < 2} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-6 py-3 rounded-lg font-medium">
          <Play className="h-5 w-5" /> {loading ? 'Procesando...' : 'Cruzar y Procesar'}
        </button>
        <button onClick={() => { setFiles([]); setResult(null); }} className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 px-6 py-3 rounded-lg">
          <RotateCcw className="h-5 w-5" /> Limpiar
        </button>
      </div>

      {/* Resultado */}
      {result && (
        <div className="mt-8 bg-gray-800 rounded-xl p-6">
          <div className="flex justify-between items-center mb-4">
            <div><h3 className="text-xl font-semibold">Resultado</h3><p className="text-gray-400">{result.row_count} filas × {result.columns.length} columnas</p></div>
            <button onClick={downloadResult} className="flex items-center gap-2 bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg"><Download className="h-5 w-5" /> Descargar Excel</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-700"><tr>{result.columns.map(c => <th key={c} className="px-4 py-2 text-left">{c}</th>)}</tr></thead>
              <tbody>{result.preview.map((row, i) => <tr key={i} className="border-t border-gray-700">{result.columns.map(c => <td key={c} className="px-4 py-2">{String(row[c] ?? '')}</td>)}</tr>)}</tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

## API Endpoint (FastAPI)

```python
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
import tempfile

app = FastAPI()

@app.post("/api/merge")
async def merge_excel(
    files: list[UploadFile] = File(...),
    left_key: str = Form(...),
    right_key: str = Form(...),
    join_type: str = Form("inner"),
    llm_prompt: str = Form(""),
    model: str = Form("qwen/qwen3.5-397b-a17b"),
):
    dfs = []
    for f in files:
        content = await f.read()
        dfs.append(read_excel_to_df(content, f.filename))

    if len(dfs) < 2:
        raise HTTPException(400, "Se necesitan al menos 2 archivos")

    merged = dfs[0]
    for i, df in enumerate(dfs[1:], 1):
        merged = merge_dataframes(merged, df, left_key, right_key, join_type)

    if llm_prompt.strip():
        merged = apply_llm_dataframe_rules(merged, llm_prompt, nvidia_client, model)

    # Guardar en temp para descarga posterior
    result_bytes = df_to_excel_bytes(merged)
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(result_bytes)
        tmp_path = tmp.name

    return {
        "row_count": merged.shape[0],
        "columns": merged.columns,
        "preview": merged.head(20).to_dicts(),
        "download_url": f"/api/merge/download?file={tmp_path}"
    }

@app.get("/api/merge/download")
async def download_result(file: str):
    with open(file, "rb") as f:
        return StreamingResponse(f, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=resultado.xlsx"})
```

## Dependencias

```toml
# pyproject.toml
"polars>=1.15",
"openpyxl>=3.1",
"fastapi>=0.115",
"uvicorn>=0.34",
"python-multipart>=0.0.20",
"openai>=1.65",
```

```json
// package.json
"react-dropzone": "^14.3",
"lucide-react": "^0.460",
"tailwindcss": "^4.1",
```

## Checklist de implementación

- [ ] Backend: endpoint `/api/merge` acepta múltiples archivos + config
- [ ] Backend: endpoint `/api/merge/download` devuelve Excel
- [ ] Frontend: drag & drop con `react-dropzone`
- [ ] Frontend: preview de tabla con paginación (máximo 20 filas preview)
- [ ] Frontend: selector de modelo NVIDIA NIM
- [ ] Prompt LLM incluye esquema + muestra de datos (evita alucinaciones)
- [ ] Temperatura baja (0.1) para determinismo en código
- [ ] Namespace aislado sin `__builtins__` en `exec()`
- [ ] Fallback si el código generado falla
- [ ] Limpiar markdown del código antes de ejecutar
- [ ] VITE_API_URL vacío (`""`) para URLs relativas
- [ ] Build de producción verificado con `grep localhost dist/assets/*.js` (debe dar 0)
