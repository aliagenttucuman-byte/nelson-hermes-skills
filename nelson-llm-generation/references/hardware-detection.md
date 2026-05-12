# Verificacion de Hardware antes de descargar modelos

## Comando para detectar VRAM real

```bash
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
```

Output ejemplo:
```
NVIDIA GeForce GTX 1650, 4096 MiB, 3846 MiB
```

## Patron comun: confusion entre VRAM y RAM

Los usuarios/clientes frecuentemente confunden:
- **VRAM** = memoria dedicada de la GPU (GDDR5/GDDR6)
- **RAM** = memoria del sistema (DDR4/DDR5)

Siempre verificar con `nvidia-smi` antes de recomendar modelos.

## Que hacer cuando el modelo no entra en VRAM

Ollama automaticamente descarga parte del modelo a la RAM del sistema (CPU offload). Esto:
- Funciona pero es mas lento
- Aumenta el uso de RAM
- Latencia de generacion sube significativamente

Para produccion con latencia baja, usar modelos que quepan enteros en VRAM.

## Tabla de decision rapida

| VRAM detectada | Modelo recomendado | Backup en CPU |
|----------------|-------------------|---------------|
| < 4GB | llama3.2:3b, qwen2.5:3b | No necesita |
| 4GB | llama3.2:3b, qwen2.5:3b | No necesita |
| 4GB | llava:7b (4.7GB) | Si, parcial en CPU |
| 6GB | llama3.1:8b, mistral:7b | No necesita |
| 8GB | phi4:14b (9GB) | Parcial en CPU |
| 12GB+ | llama3.1:8b, qwen2.5:14b | No necesita |
| 24GB+ | llama3.1:70b (cuantizado) | Parcial |
