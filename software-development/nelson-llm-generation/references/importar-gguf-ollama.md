# Importar modelos GGUF a Ollama

## Cuándo usar esto

- Ollama no tiene la cuantización específica que necesitás
- Querés un modelo que solo existe en Hugging Face como GGUF
- Necesitás una cuantización muy agresiva (IQ2_M, Q2_K) para hardware limitado
- Querés probar un modelo antes de que Ollama lo publique oficialmente

## Paso a paso

### 1. Encontrar el GGUF en Hugging Face

Buscar en https://huggingface.co/models con filtro `gguf`. Recomendados quantizadores:
- `bartowski/` — cuantizaciones muy completas (IQ2_M, Q2_K, Q3_K, Q4_K, Q5_K, Q6_K, Q8, bf16)
- `unsloth/` — cuantizaciones populares
- `lmstudio-community/` — compatibilidad con LM Studio

```bash
# Ejemplo: Gemma 4 E2B cuantizado por bartowski
REPO="bartowski/google_gemma-4-E2B-it-GGUF"
FILE="google_gemma-4-E2B-it-IQ2_M.gguf"
```

### 2. Descargar el archivo

```bash
mkdir -p ~/models/mi-modelo && cd ~/models/mi-modelo

# URL pattern de HF
curl -L -o "$FILE" \
  "https://huggingface.co/$REPO/resolve/main/$FILE?download=true"
```

**Tamaños típicos:**
| Cuantización | Bits | Tamaño archivo | VRAM estimada | Uso |
|-------------|------|---------------|---------------|-----|
| IQ2_M | ~2 | ~2.6 GB | ~2.9 GB | 4GB VRAM justo |
| Q2_K | 2 | ~3.0 GB | ~3.3 GB | 4GB VRAM |
| Q3_K_S | 3 | ~3.1 GB | ~3.4 GB | 4GB VRAM |
| Q4_K_M | 4 | ~3.4 GB | ~3.7 GB | 4-6GB VRAM |
| Q4_0 | 4 | ~3.5 GB | ~3.9 GB | 4-6GB VRAM |
| Q5_K_M | 5 | ~4.1 GB | ~4.5 GB | 6GB VRAM |
| Q6_K | 6 | ~4.7 GB | ~5.2 GB | 6-8GB VRAM |
| Q8_0 | 8 | ~6.2 GB | ~6.8 GB | 8GB+ VRAM |
| bf16 | 16 | ~9.5 GB | ~10.5 GB | 12GB+ VRAM |

> **Regla de VRAM:** El archivo GGUF ocupa aproximadamente su tamaño de archivo en VRAM, con un factor de expansión de ~1.1x. Necesitás `archivo_GGUF * 1.1 < VRAM_disponible`.
>
> **Ejemplo real:** Gemma 4 E2B IQ2_M (2.62 GB archivo) → 2.88 GB VRAM. Gemma 4 E4B Q2_K (4.46 GB archivo) → ~5.0 GB VRAM → **NO entra en 4GB VRAM**.

### 3. Crear el Modelfile

```dockerfile
FROM ./nombre-del-archivo.gguf

TEMPLATE """{{ if .System }}<start_of_turn>user
{{ .System }}<end_of_turn>
{{ end }}{{ range .Messages }}<start_of_turn>{{ .Role }}
{{ .Content }}<end_of_turn>
{{ end }}<start_of_turn>model
"""

PARAMETER stop <end_of_turn>

SYSTEM "Sos un asistente util. Responde siempre en espanol."
```

**Notas sobre el template:**
- Cada modelo usa un template de chat diferente. Buscar en la página de HF el `chat_template` del modelo base.
- Gemma usa `<start_of_turn>role\ncontent<end_of_turn>`.
- Llama usa `<|start_header_id|>role<|end_header_id|>\ncontent<|eot_id|>`.
- Si el template está mal, el modelo responde con basura o repite el prompt.

### 4. Importar a Ollama

```bash
cd ~/models/mi-modelo
ollama create nombre-custom -f Modelfile
```

Ollama copiará el archivo a su registro interno (~/.ollama/models/).

### 5. Verificar e instanciar

```bash
# Listar modelos instalados
ollama list | grep nombre-custom

# Correr
ollama run nombre-custom "Hola, ¿cómo estás?"

# Ver uso de VRAM/GPU
ollama ps
nvidia-smi
```

## Ejemplo completo: Gemma 4 E2B en GTX 1650 4GB

```bash
# 1. Preparar
mkdir -p ~/models/gemma4-e2b && cd ~/models/gemma4-e2b

# 2. Descargar (2.62 GB)
curl -L -o gemma-4-e2b-it-IQ2_M.gguf \
  "https://huggingface.co/bartowski/google_gemma-4-E2B-it-GGUF/resolve/main/google_gemma-4-E2B-it-IQ2_M.gguf?download=true"

# 3. Crear Modelfile
cat > Modelfile << 'EOF'
FROM ./gemma-4-e2b-it-IQ2_M.gguf

TEMPLATE """{{ if .System }}<start_of_turn>user
{{ .System }}<end_of_turn>
{{ end }}{{ range .Messages }}<start_of_turn>{{ .Role }}
{{ .Content }}<end_of_turn>
{{ end }}<start_of_turn>model
"""

PARAMETER stop <end_of_turn>

SYSTEM "Sos un asistente util. Responde siempre en espanol."
EOF

# 4. Importar
ollama create gemma4-e2b-custom -f Modelfile

# 5. Probar
ollama run gemma4-e2b-custom "Responde en espanol: ¿Cuáles son las ventajas de Docker?"
```

## Troubleshooting

| Síntoma | Causa | Fix |
|---------|-------|-----|
| Modelo repite el prompt | Template incorrecto | Buscar el chat_template correcto en HF |
| "Error: invalid file magic" | Archivo corrupto o no es GGUF | Re-descargar, verificar checksum |
| Muy lento (>60s) | Cuantización muy agresiva | Probar Q3_K_M o Q4_K_M |
| No usa GPU (0% en nvidia-smi) | Modelo > VRAM disponible | Usar cuantización más agresiva |
| Respuestas en inglés | SYSTEM prompt no funciona | Agregar "Responde en español" al prompt directo |
| "gathering model components" se cuelga | Archivo muy grande | Esperar, puede tardar varios minutos |

## Obtener tamaño exacto de una tag de Ollama

```bash
# Ver cuánto pesa realmente un modelo antes de descargar
curl -s "https://ollama.com/v2/library/gemma4/manifests/e2b" | \
  jq '[.layers[] | select(.mediaType | contains("model")) | .size] | add' | \
  awk '{printf "%.2f GB\n", $1/1024/1024/1024}'
```

## Comparativa: Ollama vs HF GGUF

| Aspecto | Ollama nativo | HF GGUF + import |
|---------|---------------|------------------|
| Facilidad | `ollama pull` | Descargar + Modelfile + create |
| Tamaño | Uno solo por tag | Múltiples cuantizaciones |
| Template | Pre-configurado | Manual (puede fallar) |
| Updates | Automático | Manual (re-descargar) |
| Modelos | Los que Ollama hostea | Cualquier GGUF de HF |
| Hardware | Optimizado genérico | Elegir cuantización exacta para tu VRAM |
