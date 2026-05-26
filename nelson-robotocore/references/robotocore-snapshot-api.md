# robotocore Snapshot API

robotocore mantiene todo el estado en memoria. Para no perder datos entre reinicios del contenedor, expone una API de snapshots.

## Endpoints

### Guardar estado
```bash
curl -X POST http://localhost:4566/_robotocore/state/save
```
Responde con JSON que incluye el estado serializado. Ideal para hacer backup antes de un `docker compose down`.

### Cargar estado
```bash
curl -X POST http://localhost:4566/_robotocore/state/load \
  -H "Content-Type: application/json" \
  -d @snapshot.json
```

### Ver estado de salud general
```bash
curl -s http://localhost:4566/_robotocore/health | python3 -m json.tool
```

### Listar recursos activos
```bash
curl -s http://localhost:4566/_robotocore/resources | python3 -m json.tool
```

## Workflow recomendado para persistencia

```bash
# Antes de bajar el stack
curl -X POST http://localhost:4566/_robotocore/state/save > robotocore-snapshot-$(date +%Y%m%d-%H%M%S).json

# Después de levantar el stack
curl -X POST http://localhost:4566/_robotocore/state/load \
  -H "Content-Type: application/json" \
  -d @robotocore-snapshot-YYYYMMDD-HHMMSS.json
```

## Limitaciones

- Los snapshots NO son versionados ni colaborativos (a diferencia de LocalStack Cloud Pods)
- No hay snapshot automático al recibir SIGTERM: hay que llamar `/save` explícitamente
- Si el contenedor se destruye abruptamente (kill -9, OOM), el estado en memoria se pierde
- Para stacks críticos donde la persistencia es obligatoria, preferir **MinIO** (disco nativo)

## Comparativa con alternativas

| | robotocore snapshots | FLoCI-AWS `PERSISTENCE=1` | MinIO |
|---|---|---|---|
| Mecanismo | API manual | Env var + volumen | Disco nativo |
| Automático | No | Sí (flush periódico) | Sí (cada write) |
| Granularidad | Todo el estado | Todo el estado | Por objeto |
| Recuperación | POST /load | Al reiniciar contenedor | Inmediata |
| Recomendación | Dev/CI | Dev legacy | Producción on-premise |
