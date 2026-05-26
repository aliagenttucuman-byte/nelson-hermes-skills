# Instalar nelson-meta-orchestrator como systemd

## Prerequisito
El puerto 8744 puede estar ocupado por un proceso uvicorn previo lanzado manualmente.
Hay que matarlo antes de que systemd tome el control.

## Pasos

```bash
# 1. Copiar el .service e instalar
echo 'srv2026' | sudo -S bash /home/server/nelson/meta-orchestrator/install-service.sh

# 2. Si falla con "address already in use" en 8744:
fuser -k 8744/tcp
sleep 2
echo 'srv2026' | sudo -S systemctl restart nelson-meta-orchestrator

# 3. Verificar
systemctl status nelson-meta-orchestrator --no-pager
```

## Dependencia de orden (After/Wants en el .service)

El service file declara:
```
After=network.target nelson-task-memory.service nelson-agent-router.service
Wants=nelson-task-memory.service nelson-agent-router.service
```

Esto garantiza que al reiniciar el servidor, los tres servicios levanten en orden:
1. nelson-task-memory (:8742)
2. nelson-agent-router (:8743)
3. nelson-meta-orchestrator (:8744)

## Verificar los tres de una vez

```bash
systemctl list-units --all | grep nelson
```

Deben aparecer los tres como `active (running)`.
