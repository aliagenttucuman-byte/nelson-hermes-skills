# JARVIS Demo Shell — Referencia técnica

**Ubicación en servidor:** `~/jarvis-demo-shell/`
**Estado:** Corriendo (validado 2026-05-19)

## Qué es

Template base reutilizable para demos I+D+I y herramientas internas.
Frontend OpenUI (Next.js) fijo + Backend FastAPI modular por proyecto.
El usuario cambia `ACTIVE_PROJECT` en el `.env` del backend y el agente
adopta el contexto del nuevo proyecto sin tocar el frontend.

## Puertos activos

| Servicio | Puerto | URL Tailscale |
|----------|--------|---------------|
| Frontend OpenUI | 3789 | http://100.110.8.13:3789 |
| Backend FastAPI | 8765 | http://100.110.8.13:8765 |

> NOTA: Puertos 8000, 8001, 8002 están ocupados por otros servicios del servidor.
> Usar 8765 para backend y 3789 para frontend del demo shell.

## Proyectos disponibles

| ACTIVE_PROJECT | Descripción |
|----------------|-------------|
| `demo` | Genérico — muestra capacidades del shell |
| `energia` | Producción petróleo/gas Argentina — datos Sec. Energía |

## Cómo agregar un proyecto

1. Crear `backend/tools/NOMBRE.py`:

```python
from tools.registry import BaseTool, register

@register
class MiTool(BaseTool):
    name = "NOMBRE"

    def get_system_instructions(self) -> str:
        return """
        # Contexto del proyecto
        Qué datos tiene el agente, qué componentes OpenUI usar,
        cómo responder preguntas del dominio...
        """
```

2. Cambiar en `backend/.env`:
```
ACTIVE_PROJECT=NOMBRE
```

3. Reiniciar el backend: `kill $(lsof -ti :8765) && python3 -m uvicorn main:app --port 8765 --env-file .env`

## Ejemplo OpenUI Lang que el agente puede generar

```
```openui
chart tipo="barra" titulo="Market Share" x="Empresa" y="Porcentaje"
datos=[{"Empresa":"YPF","Porcentaje":34},{"Empresa":"PAE","Porcentaje":22}]
```
```

```
```openui
kpi titulo="Producción YPF" valor="1.2M m³" variacion="+3.2%" tendencia="up"
```
```

## Arquitectura del proxy

El frontend NO llama al LLM directo. Llama al backend FastAPI que:
1. Recibe el mensaje y el systemPrompt del chat UI
2. Combina el systemPrompt con las instrucciones del proyecto activo
3. Llama a Groq con streaming
4. Re-emite el stream de vuelta al frontend

Esto permite que el backend controle completamente el contexto del agente
sin tocar el código del frontend.

## Levantar desde cero

```bash
# Backend
cd ~/jarvis-demo-shell/backend
pip3 install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8765 --env-file .env

# Frontend (en otra terminal)
cd ~/jarvis-demo-shell/frontend
# Verificar que .env tiene: BACKEND_URL=http://localhost:8765
PORT=3789 npm run dev
```
