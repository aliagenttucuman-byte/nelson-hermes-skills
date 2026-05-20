# Gemma 3 Benchmarks — 4GB VRAM (GTX 1650)

> Fecha: 2025-05-12 | Hardware: NVIDIA GeForce GTX 1650 Mobile/Max-Q, 4096 MiB GDDR5, 13GB RAM sistema

## Modelos probados (Ollama)

| Modelo | Tamaño descarga | VRAM en uso | Tiempo respuesta* | Calidad | Recomendación |
|--------|----------------|-------------|-------------------|---------|---------------|
| `gemma3:1b` | 800 MB | ~500 MB GPU | **2.7s** | ⭐⭐⭐ Básica | **Velocidad extrema**, tareas simples |
| `gemma3:4b` | 3.3 GB | 2.4 GB GPU | **6.3s** | ⭐⭐⭐⭐ Buena | Más capacidad, deja poco margen VRAM |
| `llama3.2:3b` | 2.0 GB | ~1.8 GB GPU | **5.0s** | ⭐⭐⭐⭐ Buena | **Default recomendado**, balance ideal |
| `qwen2.5:3b` | 1.9 GB | ~1.7 GB GPU | **6.3s** | ⭐⭐⭐⭐ Buena | Buen alternativa, ligeramente más lenta |
| `llama3.1:8b` | 4.9 GB | 43% CPU / 57% GPU | **~2s** | ⭐⭐⭐⭐⭐ Excelente | Máxima calidad, mix CPU/GPU automático |
| `nomic-embed-text` | 274 MB | ~200 MB GPU | Instantáneo | N/A | Embeddings, siempre usar este |

*Tiempo medido con `time ollama run <modelo> "pregunta de 3 oraciones en español"`. Pregunta usada: "¿Cuáles son las ventajas de usar Docker en desarrollo de software? Responde en 3 oraciones."

## Gemma 4 — Disponibilidad

**Gemma 4 NO está disponible en tamaños pequeños en Ollama.** Solo existen:
- `gemma4:26b` (~17 GB cuantizado Q4)
- `gemma4:31b` (~20 GB cuantizado Q4)

**Conclusión:** Con 4GB VRAM, Gemma 4 es inaccesible. Usar Gemma 3:1b o Gemma 3:4b como alternativa Google.

## Comportamiento observado

- **Gemma 3:4b** ocupa 2.4 GB de 4 GB VRAM disponibles. Deja ~1.6 GB libres. Si se corre junto con otro modelo (ej: embeddings), puede quedar justo.
- **Gemma 3:1b** es el modelo más rápido probado en esta máquina (2.7s). Útil para prototipos rápidos o cuando la latencia es crítica.
- **Calidad de respuesta:** Gemma 3:4b ≈ llama3.2:3b ≈ qwen2.5:3b. Todos coherentes y útiles. Gemma 3:1b es ligeramente menos detallada pero correcta.

## Recomendación por caso de uso (4GB VRAM)

| Caso | Modelo | Por qué |
|------|--------|---------|
| **Default / desarrollo** | `llama3.2:3b` | Equilibrio velocidad, calidad, VRAM |
| **Máxima velocidad** | `gemma3:1b` | 2.7s, 800MB, deja VRAM libre |
| **Máxima calidad** | `llama3.1:8b` | Mix CPU/GPU, respuesta excelente |
| **RAG / embeddings** | `nomic-embed-text` | 768 dims, rápido, siempre en GPU |
| **Alternativa Google** | `gemma3:4b` | Si se prefiere arquitectura Gemma |
