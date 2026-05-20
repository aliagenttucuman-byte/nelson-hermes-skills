# Ollama VRAM Testing - Resultados Reales

> Session: 2026-05-11 | Hardware: NVIDIA GeForce GTX 1650 Mobile/Max-Q (4GB GDDR5 VRAM)

## Modelos probados

| Modelo | Tamano | VRAM usada | Tiempo respuesta | Modo | Recomendacion |
|--------|--------|------------|------------------|------|---------------|
| llama3.2:3b | 2.0 GB | ~2.0 GB | <1s | 100% GPU | ✅ Default dev |
| qwen2.5:3b | 1.9 GB | ~1.9 GB | <1s | 100% GPU | ✅ Codigo/razonamiento |
| nomic-embed-text | 274 MB | ~274 MB | <0.5s | 100% GPU | ✅ Embeddings |
| llama3.1:8b | 4.9 GB | 3.4 GB GPU + RAM | ~1.8s | 57% GPU / 43% CPU | ✅ Calidad superior |
| llava:7b | 4.7 GB | Mix GPU+RAM | ~2s | Mix | ✅ Vision/multimodal |

## Detalle llama3.1:8b (modelo grande en 4GB VRAM)

```bash
$ ollama ps
NAME         SIZE    PROCESSOR        CONTEXT
llama3.1:8b  5.9 GB  43%/57% CPU/GPU  4096
```

- No entra entero en 4GB VRAM
- Ollama automaticamente usa VRAM para lo que entra y el resto en RAM
- Tiempo de respuesta aceptable: ~1.8-2s
- No es tan rapido como en 6-8GB VRAM, pero funciona para desarrollo

## Comandos utiles

```bash
# Ver modelos descargados
ollama list

# Ver que modelo esta corriendo y donde
ollama ps

# Descargar modelo
ollama pull llama3.2:3b

# Probar rapido
echo "Hola" | ollama run llama3.2:3b --nowordwrap
```

## Consejos para 4GB VRAM

1. Usar llama3.2:3b o qwen2.5:3b para desarrollo diario (rapido, 100% GPU)
2. Reservar llama3.1:8b para pruebas de calidad o cuando se necesite razonamiento complejo
3. No cargar multiples modelos grandes simultaneamente
4. Cerrar navegadores/tabs pesados para liberar VRAM del sistema
