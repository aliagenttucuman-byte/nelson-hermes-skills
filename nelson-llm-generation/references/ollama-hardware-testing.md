# Ollama Hardware Testing - Resultados Reales

> Fecha: 2026-05-11
> Hardware: NVIDIA GeForce GTX 1650 Mobile/Max-Q
> VRAM: 4096 MiB GDDR5
> RAM Sistema: 13GB
> Ollama: v0.22.0

## Modelos Testeados

### llama3.2:3b (2.0 GB)
- **Descarga:** Exitosa
- **Carga VRAM:** 100% GPU
- **Velocidad:** <1 segundo por respuesta
- **Uso VRAM:** ~2GB de 4GB disponibles
- **Veredicto:** Ideal para desarrollo diario con 4GB VRAM

### qwen2.5:3b (1.9 GB)
- **Descarga:** Exitosa
- **Carga VRAM:** 100% GPU
- **Velocidad:** <1 segundo por respuesta
- **Uso VRAM:** ~1.9GB de 4GB disponibles
- **Veredicto:** Excelente para código y razonamiento técnico

### llama3.1:8b (4.9 GB)
- **Descarga:** Exitosa
- **Carga VRAM:** 57% GPU / 43% CPU (automático por Ollama)
- **Velocidad:** ~1.8 segundos por respuesta
- **Uso VRAM:** ~3.4GB en GPU, resto en RAM sistema
- **Veredicto:** Funciona bien, más lento pero calidad superior. Útil cuando se necesita más capacidad.

### llava:7b (4.7 GB)
- **Descarga:** Exitosa
- **Carga VRAM:** Mix CPU/GPU (similar a llama3.1:8b)
- **Velocidad:** ~2-3 segundos por respuesta
- **Uso VRAM:** Mayoría en GPU, parte en RAM
- **Veredicto:** Funcional para análisis de imágenes. Más lento pero usable.

### nomic-embed-text (274 MB)
- **Descarga:** Exitosa
- **Carga VRAM:** 100% GPU (cabe enterito)
- **Velocidad:** Instantáneo
- **Veredicto:** Perfecto para embeddings en RAG

## Comandos útiles

```bash
# Verificar VRAM disponible
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader

# Ver qué modelos están cargados y en qué procesador
ollama ps

# Descargar modelo
ollama pull <modelo>

# Probar modelo interactivo
ollama run llama3.2:3b

# Probar con pipeline
ollama run llama3.2:3b --nowordwrap
```

## Comportamiento de Ollama con VRAM limitada

1. Ollama detecta automáticamente cuánta VRAM hay disponible
2. Si el modelo cabe entero: carga 100% en GPU (rápido)
3. Si el modelo no cabe: divide entre GPU y CPU automáticamente
4. No requiere configuración manual
5. La división GPU/CPU se ve con `ollama ps`

## Recomendaciones por escenario

| Escenario | Modelo recomendado | Por qué |
|-----------|-------------------|---------|
| Desarrollo rápido | llama3.2:3b | 100% GPU, respuesta <1s |
| Código/técnico | qwen2.5:3b | Mejor en razonamiento lógico |
| Máxima calidad | llama3.1:8b | Más capaz, aceptablemente rápido |
| Visión/imágenes | llava:7b | Único multimodal disponible |
| Embeddings | nomic-embed-text | Rápido, liviano, 274MB |

## Pitfalls descubiertos

- `ollama ps` muestra el porcentaje GPU/CPU real, no el tamaño del modelo
- Los modelos grandes (>4GB) en 4GB VRAM usan RAM del sistema, lo cual puede afectar otros procesos
- Es mejor tener varios modelos chicos (3B) que uno grande (8B) si la velocidad es prioridad
- Para producción siempre usar APIs cloud (OpenAI, etc.), Ollama es solo para dev local
