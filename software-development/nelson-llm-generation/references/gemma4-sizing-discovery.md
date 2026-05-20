# Gemma 4 - Tamaños reales en Ollama (descubrimiento mayo 2026)

## Contexto

Nelson (Tony Stark) tiene una NVIDIA GTX 1650 Mobile/Max-Q con **4GB GDDR5 VRAM** y quería probar Gemma 4 de Google localmente.

## Descubrimiento clave

Gemma 4 está disponible en Ollama, pero **no hay versión pequeña viable para 4GB VRAM**.

| Variante | Tamaño real en Ollama | Parámetros estimados | Viable en 4GB |
|----------|----------------------|----------------------|---------------|
| `gemma4:26b` | ~17 GB | 26B | ❌ No |
| `gemma4:31b` | ~20 GB | 31B | ❌ No |
| `gemma4:e2b` | **6.67 GB** | ~2B (variante E2B) | ❌ No |
| `gemma4:e2b-it-q4_K_M` | 6.67 GB | ~2B cuantizado Q4 | ❌ No |
| `gemma4:e2b-it-q8_0` | 7.58 GB | ~2B cuantizado Q8 | ❌ No |

## La sorpresa: E2B no es lo que parece

La variante `gemma4:e2b` pesa **6.67GB** — mucho más de lo esperado para un modelo de ~2B parámetros.

Según el artículo de Cristian Tala (cristiantala.com/gemma-4-google-guia-completa/):
- La "E" significa **Effective Parameters** — usa técnica Per-Layer Embeddings
- El artículo indica hardware mínimo de **4GB RAM** para E2B (4-bit)
- El artículo indica hardware mínimo de **5.5-6GB RAM** para E4B (4-bit)

**PERO:** La versión `gemma4:e2b` de Ollama pesa **6.67GB**, no 4GB. Esto indica que:

1. El artículo habla de una **cuantización manual a 4-bit** que resulta en ~4GB
2. La tag `gemma4:e2b` de Ollama **no está cuantizada a 4-bit** (probablemente 8-bit o sin cuantizar)
3. "E2B" no significa "2 Billion parameters" en el sentido tradicional; incluye componentes adicionales
4. El peso real cuantizado es ~3x lo que se esperaría para un modelo 2B puro

## Tabla del artículo vs realidad en Ollama

| Modelo | 4-bit (artículo) | 8-bit (artículo) | Full BF16 | Tamaño Ollama real |
|--------|------------------|-------------------|-----------|-------------------|
| E2B | 4 GB | 5-8 GB | 10 GB | **6.67 GB** (no 4GB) |
| E4B | 5.5-6 GB | 9-12 GB | 16 GB | No verificado |
| 26B-A4B | 16-18 GB | 28-30 GB | 52 GB | ~17 GB |
| 31B | 17-20 GB | 34-38 GB | 62 GB | ~20 GB |

## Comparativa con alternativas viables en 4GB VRAM

| Modelo | Peso | VRAM usado | Tiempo respuesta | Calidad |
|--------|------|------------|------------------|---------|
| `gemma3:1b` | 800 MB | ~600 MB | ~2.7s | Básica |
| `gemma3:4b` | 3.3 GB | ~2.4 GB | ~6.3s | Buena |
| `llama3.2:3b` | 2.0 GB | ~1.8 GB | ~5s | Buena |
| `qwen2.5:3b` | 1.9 GB | ~1.7 GB | ~6s | Buena |
| `gemma4:e2b` | 6.67 GB | ~5GB+ (con spill a RAM) | ~30s+ estimado | Desconocida |

## Verificación via API de Ollama

```bash
# Obtener tamaño exacto de cada variante
curl -s "https://ollama.com/v2/library/gemma4/manifests/e2b" | \
  jq '.layers[] | select(.mediaType | contains("model")) | .size'
# Resultado: 7162394016 bytes = 6.67 GB
```

## ACTUALIZACIÓN: Gemma 4 SÍ corre en 4GB VRAM con GGUF cuantizado manualmente

### Descubrimiento (sesión 12 mayo 2026)

Aunque las tags de Ollama son demasiado grandes, en **Hugging Face** existen cuantizaciones GGUF mucho más agresivas que SÍ entran en 4GB VRAM.

| Fuente | Cuantización | Tamaño | Funciona en 4GB VRAM |
|--------|-------------|--------|---------------------|
| Ollama `gemma4:e2b` | Sin cuantizar / 8-bit | 6.67 GB | ❌ No |
| HF `Q4_K_M` | 4-bit | ~3.4 GB | ⚠️ Justo |
| HF `IQ2_M` | ~2-bit | **2.62 GB** | ✅ Sí |

### Prueba real: Gemma 4 E2B IQ2_M en GTX 1650 4GB

| Métrica | Valor |
|---------|-------|
| Archivo | `google_gemma-4-E2B-it-IQ2_M.gguf` |
| Peso descargado | 2.62 GB |
| VRAM usada | **2.875 GB** de 4 GB |
| GPU% | **100% GPU** (no usa CPU) |
| Tiempo respuesta | **~55 segundos** |
| Calidad | Buena, con thinking mode incluido |

**Proceso usado:**
1. Descargar GGUF desde Hugging Face: `bartowski/google_gemma-4-E2B-it-GGUF`
2. Crear `Modelfile` con `FROM ./archivo.gguf`
3. Importar: `ollama create nombre-custom -f Modelfile`
4. Usar: `ollama run nombre-custom`

**Trade-off:** La cuantización IQ2_M (~2 bits) comprime mucho pero es lenta en inferencia. 55 segundos por respuesta es usable para experimentar, no para producción.

> Ver `references/importar-gguf-ollama.md` para el proceso completo paso a paso.

## ACTUALIZACIÓN (12 mayo 2026): E4B confirmado NO viable en 4GB VRAM

### Búsqueda de cuantizaciones E4B en Hugging Face

Revisadas todas las cuantizaciones disponibles en `bartowski/google_gemma-4-E4B-it-GGUF`:

| Cuantización | Tamaño archivo | VRAM estimada (x1.1) | Entra en 4GB? |
|-------------|---------------|---------------------|---------------|
| Q2_K | **4.46 GB** | ~4.9 GB | ❌ No |
| Q2_K_L | 5.30 GB | ~5.8 GB | ❌ No |
| Q3_K_S | 4.63 GB | ~5.1 GB | ❌ No |
| Q3_K_XS | 4.89 GB | ~5.4 GB | ❌ No |
| Q4_K_M | ~6.2 GB | ~6.8 GB | ❌ No |

**Conclusión:** Incluso la cuantización más agresiva del E4B (Q2_K, 4.46 GB) excede los 4GB VRAM cuando se carga en GPU. El límite absoluto para hardware de 4GB VRAM es **Gemma 4 E2B con cuantización IQ2_M únicamente**.

### Benchmark comparativo final (misma pregunta: ventajas de Docker)

| Modelo | Tiempo | VRAM usada | GPU% | Calidad |
|--------|--------|------------|------|---------|
| `llama3.2:3b` | **4.3 seg** | 2.8 GB | 100% | Buena |
| `gemma4-e2b-custom` (IQ2_M) | **55 seg** | 2.9 GB | 100% | Buena + thinking |

**Diferencia:** Gemma 4 E2B es ~13x más lento que Llama 3.2:3B en el mismo hardware. El trade-off es que Gemma 4 tiene thinking mode (razonamiento interno visible) y es un modelo más moderno, pero la cuantización IQ2_M lo hace muy lento para uso interactivo diario.

### Repositorio educativo clonado

Clonado `rasbt/LLMs-from-scratch` (93.5K estrellas) para referencia sobre cómo funcionan los transformers internamente. Útil para entender el fundamento de los LLMs que usamos.

## Conclusión original

Con 4GB VRAM, **Gemma 4 no es viable** usando las tags estándar de Ollama. Las alternativas Google viables son:
- `gemma3:1b` para velocidad extrema
- `gemma3:4b` para mejor calidad con uso moderado de VRAM

**PERO:** Si se descarga un GGUF cuantizado manualmente desde Hugging Face e importa a Ollama, **Gemma 4 E2B sí corre en 4GB VRAM** (versión IQ2_M, ~2.62GB). Requiere ~55 segundos por respuesta.
