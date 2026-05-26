# Importar Modelos GGUF Custom a Ollama

## Contexto

Los modelos en Ollama Hub no siempre tienen las cuantizaciones mas agresivas (ej: IQ2_M, Q2_K). Para hardware limitado (4GB VRAM), es necesario descargar GGUFs manualmente desde Hugging Face e importarlos a Ollama.

## Procedimiento

### 1. Encontrar el GGUF en Hugging Face

Buscar repos cuantizados por `bartowski` o `TheBloke`. Ejemplo para Gemma 4 E2B:

```bash
# Listar cuantizaciones disponibles
curl -s "https://huggingface.co/bartowski/google_gemma-4-E2B-it-GGUF/tree/main" | \
  grep -o 'google_gemma-4-E2B-it-[A-Z0-9_]*\.gguf' | sort -u
```

Tamanios tipicos para Gemma 4 E2B:
| Cuantizacion | Tamanio | VRAM estimada | Entra en 4GB? |
|-------------|---------|---------------|---------------|
| IQ2_M | 2.62 GB | ~2.9 GB | ✅ Si |
| Q2_K | 3.02 GB | ~3.3 GB | ✅ Si |
| Q3_K_M | 3.23 GB | ~3.5 GB | ✅ Justo |
| Q4_K_M | 4.0 GB+ | ~4.5 GB | ❌ No |

**Regla:** El archivo GGUF pesa X, pero en VRAM se expande ~10%. Dejar margen de 500MB.

### 2. Descargar el GGUF

```bash
mkdir -p ~/models/gemma4-e2b && cd ~/models/gemma4-e2b
curl -L -o gemma-4-e2b-it-IQ2_M.gguf \
  "https://huggingface.co/bartowski/google_gemma-4-E2B-it-GGUF/resolve/main/google_gemma-4-E2B-it-IQ2_M.gguf?download=true"
```

### 3. Crear Modelfile

El template de chat debe coincidir con el formato del modelo. Para Gemma:

```dockerfile
FROM ./gemma-4-e2b-it-IQ2_M.gguf

TEMPLATE """<start_of_turn>user
{{ .System }}<end_of_turn>
<start_of_turn>user
{{ .Prompt }}<end_of_turn>
<start_of_turn>model
"""

PARAMETER stop <end_of_turn>

SYSTEM "Sos un asistente util. Responde siempre en espanol."
```

### 4. Importar a Ollama

```bash
cd ~/models/gemma4-e2b
ollama create gemma4-e2b-custom -f Modelfile
```

### 5. Verificar

```bash
ollama list | grep gemma4
ollama run gemma4-e2b-custom "Responde en espanol: hola"
```

## Pitfalls

1. **No confiar en el nombre del modelo.** `E2B` no significa 2GB. Verificar siempre el tamanio real del GGUF.
2. **El template de chat importa.** Si el template no coincide con el formato nativo del modelo, las respuestas seran basura.
3. **Cuantizacion extrema = calidad variable.** IQ2_M (2 bits) comprime mucho pero pierde precision. Probar con prompts de referencia.
4. **VRAM > archivo.** El modelo ocupa mas en VRAM que en disco. Multiplicar por ~1.1x para estimar.
