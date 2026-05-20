# Docker Pitfalls — Proyectos Python + React

## `docker-compose` vs `docker compose`

El comando `docker-compose` (con guion, V1) está deprecado en sistemas modernos. El comando correcto es `docker compose` (sin guion, V2/plugin).

```bash
# ❌ Incorrecto (puede no existir)
docker-compose up --build

# ✅ Correcto
docker compose up --build
```

## Permisos de Docker

Si el usuario no está en el grupo `docker`, los comandos fallan con:
```
permission denied while trying to connect to the docker API
```

### Solución temporal
```bash
sudo docker compose up --build -d
```

### Solución permanente
```bash
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar para que aplique
```

## Sudo no interactivo

En entornos sin TTY, `sudo` requiere password interactivo. Opciones:
- Usar `sudo -S` con pipe de password
- Agregar regla `NOPASSWD` en `/etc/sudoers` para el comando docker
- Preferir solución de grupo docker

## Docker Compose `version` obsoleta

La línea `version: '3.8'` en `docker-compose.yml` genera warning:
```
the attribute `version` is obsolete, it will be ignored
```

Es inofensivo pero se puede eliminar la línea.

## Puerto 3000 ocupado

El puerto 3000 suele estar ocupado por otros servicios. Si el frontend falla con:
```
failed to bind host port 0.0.0.0:3000/tcp: address already in use
```

Cambiar el puerto en `docker-compose.yml`:
```yaml
frontend:
  ports:
    - "8080:80"
```
