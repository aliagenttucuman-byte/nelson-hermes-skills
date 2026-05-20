# GitHub CLI Setup — Entorno de Nelson

## Instalación

```bash
# Método rápido (sin apt)
cd /tmp
curl -sLO https://github.com/cli/cli/releases/download/v2.63.2/gh_2.63.2_linux_amd64.tar.gz
tar -xzf gh_2.63.2_linux_amd64.tar.gz
sudo cp gh_2.63.2_linux_amd64/bin/gh /usr/local/bin/
gh --version
```

## Autenticación

### Método A: Login con token (recomendado para scripts)

```bash
# Crear script para evitar timeout en sesiones no-TTY
cat > /tmp/gh-login.sh << 'EOF'
#!/bin/bash
echo "TU_TOKEN" | gh auth login --with-token 2>&1
echo "EXIT=$?"
EOF
bash /tmp/gh-login.sh
```

> Nota: `gh auth login --with-token` directo en terminal puede cortarse por timeout en entornos sin TTY. El wrapper con script es más confiable.

### Método B: Device flow (interactivo)

```bash
gh auth login -p https -h github.com -w
# Copiar código de un solo uso, abrir https://github.com/login/device
# Iniciar sesión con la cuenta y autorizar
```

## Configuración de git

```bash
git config --global user.name "aliagenttucuman"
git config --global user.email "aliagenttucuman@gmail.com"
git config --global init.defaultBranch main
```

## Verificación

```bash
gh auth status
gh api user -q '.login'
```

## Uso con skills de Hermes

Una vez logueado, `hermes skills` puede usar taps de GitHub sin rate limit:

```bash
# Agregar repo como fuente de skills
hermes skills tap add https://github.com/wshobson/agents

# Buscar skills disponibles
hermes skills search fastapi

# Instalar skill específica
hermes skills install wshobson/agents/python-development
```

> Sin autenticación: límite de 60 requests/hora.
> Con autenticación: límite de 5.000 requests/hora.
