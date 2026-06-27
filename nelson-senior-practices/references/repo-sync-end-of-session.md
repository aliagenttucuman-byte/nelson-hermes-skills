# Sincronizacion end-of-session de repos PoC

Cuando Nelson pide "actualizar los repositorios" al cierre de sesion (PoCs como `expreso-bisonte-excel-poc`, `yolov-orientacion-poc`, etc.), aplican estas reglas. Mercedes/Julian leen la historia git para entender que cambio — **commits monoliticos hacen el repo ilegible y rompen el handoff**.

## Reglas

1. **Direct push a `main`, sin PRs.** Los PoCs Nelson trabajan directo en main. No abrir PR a menos que Nelson lo pida explicitamente.

2. **Separar commits por tema, no por archivo.** Un commit = una intencion (UI/design system, feature de negocio, chore/gitignore, infra). Si en una sola sesion tocaste UI + pipeline + infra, salen 3 commits separados con mensajes distintos.

3. **Revisar `.gitignore` ANTES de `git add .`** Nelson trabaja con:
   - Builds que el backend sirve: `backend/static/` en Bisonte
   - `frontend/dist/`, `frontend/node_modules/`
   - Archivos del agente: `.hermes.md`, `.claude/`
   - Logs y caches: `*.log`, `__pycache__/`, `.venv/`
   
   Si faltan en `.gitignore`, agregarlos y commitearlos con el primer commit "housekeeping" de la sesion.

4. **Verificar auth del remote en cada repo.** Algunos repos tienen el token embebido en la URL (`https://user:TOKEN@github.com/...`), otros no. Si `git push` falla con `Invalid username or token. Password authentication is not supported`, copiar el token del remote de otro repo del mismo owner:
   
   ```bash
   REMOTE_AUTH=$(cd /ruta/repo-con-token && git remote get-url origin | sed 's|https://||; s|@github.com.*||')
   cd /ruta/repo-sin-token && git remote set-url origin "https://${REMOTE_AUTH}@github.com/OWNER/REPO.git"
   ```

5. **Mensajes de commit en castellano operativo, no marketing.** Listar archivos tocados y por que. Nelson y Mercedes leen estos messages cuando hacen pull.

6. **Reportar al final solo lo esencial.** Lista de repos × SHAs cortos × titulo de cada commit. NO repetir el contenido del diff en el mensaje al usuario — ya esta en git log.

## Pitfalls

- `git add .` arrastra build output, lock files no deseados, archivos del agente. Siempre `git status -sb` primero y decidir archivo por archivo.
- `package-lock.json` SI va al repo (Mercedes lo necesita para reproducir). `node_modules/` NO.
- Si el repo no tiene `.gitignore`, crearlo con: `node_modules/`, `dist/`, `__pycache__/`, `*.pyc`, `.venv/`, `.env`, `.hermes.md`, `.claude/`, `*.log`.
- NO mezclar fix de `.gitignore` con commit de feature. El gitignore va con un chore o con el primer commit "housekeeping".
- Build output servido en produccion (`backend/static/`, `frontend/dist/`): ignorarlo igual, el deploy lo regenera. No se versiona.

## Flujo tipo

```bash
# 1. Status de todos los repos tocados
for repo in /home/server/proyectos/repo-a /home/server/proyectos/repo-b; do
  echo "=== $(basename $repo) ===" && cd $repo && git status -sb
done

# 2. Por cada repo: revisar diff, decidir gitignore, separar por tema
cd /home/server/proyectos/repo-a
git diff --stat                              # ver el alcance real
# editar .gitignore si falta algo
git add .gitignore frontend/src/styles/      # commit 1: chore + UI
git commit -m "chore(ui): ..."
git add backend/services/feature.py          # commit 2: feature
git commit -m "feat(feature): ..."

# 3. Push (verificar auth si falla)
git push origin main

# 4. Reportar al usuario: SHAs cortos + titulos. Sin repetir el diff.
```

## Ejemplo real (sesion 2026-06-23)

Bisonte (`expreso-bisonte-excel-poc`):
- `c9c42b8` chore(ui): Linear x Bloomberg design system + .gitignore
- `ba05d0c` feat(contado): pipeline IA CONTADO + tabla con reglas de negocio

Yolov (`yolov-orientacion-poc`):
- `1dec3bb` chore(frontend): .gitignore + UI demo cleanup + package-lock
- `3891749` feat(species): clasificacion de especies forestales (NetFlora-inspired)

Yolov requirio fix de auth: el remote no tenia token embebido, se copio del de Bisonte (mismo owner `aliagenttucuman-byte`).
