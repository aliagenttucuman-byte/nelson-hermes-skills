# Patrón: Página HTML de Análisis Técnico de Proyecto

## Cuándo usar
Cuando Nelson pida analizar un repositorio completo o challenge técnico y quiere
un documento rico para estudiar, compartir o presentar. Más útil que un texto plano
porque tiene tabs, barras de progreso, código resaltado y no requiere Markdown.

## Flujo de construcción

### 1. Leer el código en paralelo con delegate_task (3 subagentes simultáneos)
Dividir los archivos por dominio:
- Subagente 1: código principal (model.py, api.py, módulos core)
- Subagente 2: documentación, tests, requirements, data files
- Subagente 3: frontend (JSX/TSX), Dockerfile, docker-compose, CI/CD

Cada subagente devuelve el contenido COMPLETO de cada archivo + observaciones.
No resumir antes de tiempo — el análisis necesita el contexto completo.

### 2. Construir la página HTML con tabs
Estructura estándar de tabs para análisis de proyecto:
- 📐 Descripción — qué es, el contexto del negocio, las partes del challenge/spec
- 🏗️ Arquitectura — diagramas de flujo con .arch-flow/.arch-box, stack tecnológico
- 🤖 Modelo/Core — el corazón técnico del proyecto con analogías
- ✅ Aciertos — lo que se hizo bien con justificación y código
- ⚠️ Problemas — bugs, problemas de seguridad, malas prácticas con severidad
- 🚀 Mejoras — próximos pasos con código concreto y estimaciones de esfuerzo/impacto

### 3. Guardar en public/ del proyecto edu-platform
```
/home/server/brainstorming/2026-05-27-edu-platform-ia/frontend/public/NOMBRE-proyecto.html
```

### 4. Servir con python3 -m http.server en 0.0.0.0
```bash
# CRÍTICO: siempre --bind 0.0.0.0, no 127.0.0.1 ni sin --bind
# De lo contrario Cloudflare no puede conectarse (intenta IPv6)
python3 -m http.server 8030 --bind 0.0.0.0 --directory public &
```

### 5. Exponer con Cloudflare Tunnel
```bash
cloudflared tunnel --url http://localhost:8030 --protocol http2 2>&1 | tee /tmp/cf_eduplatform.log &
sleep 15
grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cf_eduplatform.log | tail -1
```

## CSS/HTML base reutilizable

El archivo `latam-flight-delay.html` en
`/home/server/brainstorming/2026-05-27-edu-platform-ia/frontend/public/`
es la referencia canónica con los siguientes componentes CSS ya definidos:

| Clase CSS | Uso |
|-----------|-----|
| `.card` / `.card-title` | Secciones de contenido con borde y título en rojo LATAM |
| `.arch-flow` / `.arch-box` | Diagramas de flujo horizontal con cajas coloreadas |
| `.note-blue/green/yellow/red` | Bloques de nota con borde izquierdo de color |
| `.score-card` | KPIs grandes con número y label |
| `.feature-row` / `.feature-bar-fill` | Barras de importancia de features ML |
| `.item` / `.item-icon` / `.item-body` | Items tipo lista con ícono + título + descripción + snippet |
| `.prio prio-high/med/low` | Badges de prioridad (crítico/medio/bajo) |
| `.tag-green/yellow/red` | Colores de texto para tablas |
| `pre` / `code` | Código con fondo oscuro, colores amber para código inline |

## Patrón de expansión progresiva

Cuando Nelson pide "ampliar las explicaciones":
1. Usar dos subagentes en paralelo (delegate_task) — uno para la primera mitad de tabs, otro para la segunda
2. Cada subagente: lee el archivo HTML completo, patcha solo su sección con StrReplace/patch
3. El archivo crece de ~50KB a ~120KB+ sin conflictos porque los subagentes trabajan tabs distintos
4. Verificar al final: `wc -c archivo.html` debe mostrar el crecimiento esperado

## Pitfalls

- **No resumir el código antes de analizarlo:** los subagentes deben devolver el contenido COMPLETO de cada archivo para que el análisis sea profundo y preciso
- **Servidor en 127.0.0.1:** Cloudflare falla por IPv6. Siempre `--bind 0.0.0.0`
- **Cambio de URL del túnel:** las URLs de trycloudflare son efímeras. Si el proceso muere, relanzar y mandar la URL nueva
- **HTML inválido tras patch:** cada subagente debe verificar que los tags queden correctamente cerrados. Si hay tabs que se rompen, es por un `</div>` faltante

## Sesión de referencia
Usado en 2026-05-28 para análisis del challenge LATAM Flight Delay.
Repositorio: github.com/aliagenttucuman-byte/latam-flight-delay
Resultado: 6 tabs, 124KB, análisis completo de model.py/api.py/ai_insights.py/frontend/Docker/CI-CD.
