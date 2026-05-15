---
name: nelson-project-constitution
description: "Fase 1 del flujo SDD Nelson. Genera la CONSTITUTION.md de un proyecto nuevo: principios, stack, calidad, reglas. Sin constitucion no hay proyecto."
version: 1.0.0
author: Equipo Nelson (Tony + JARVIS)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [spec-driven-development, constitution, project-setup, nelson, workflow]
    related_skills: [nelson-spec-driven-workflow, spec-driven-development, nelson-project-bootstrap, equipo-nelson]
---

# Nelson Project Constitution

Fase 1 del flujo **Nelson Spec-Driven Development**.

Genera el archivo `CONSTITUTION.md` para un proyecto nuevo. Este documento es la "constitución" del proyecto: todos los agentes deben respetarla.

**Regla de oro:** Sin CONSTITUTION.md, no hay proyecto. No se especifica, no se planea, no se codea.

## ¿Cuándo usar?

- Cada vez que Tony dice "nuevo proyecto" o "empezamos proyecto X"
- Antes de escribir la primera línea de código
- Antes de escribir el primer OpenAPI spec

## ¿Quién la genera?

**Tony (líder) + JARVIS** en conversación. Beto (arquitecto) revisa y aprueba.

No es un documento técnico detallado. Es un acuerdo de principios que guía todas las decisiones del proyecto.

## Template CONSTITUTION.md

```markdown
# CONSTITUTION — [Nombre del Proyecto]

**Fecha:** YYYY-MM-DD
**Autor:** [Tony/JARVIS]
**Aprobadores:** [Tony, Beto]
**Equipo asignado:** [Beto, Ricky, Nico, Diego, Alma] o [I+D+I agentes]

---

## 1. Propósito del Proyecto

¿Qué problema resuelve? ¿Para quién?

## 2. Stack Tecnológico

### Backend
- **Lenguaje:** Python 3.12+
- **Framework:** FastAPI + Pydantic v2
- **ORM:** SQLAlchemy 2.0
- **DB:** PostgreSQL 15
- **Async:** Uvicorn, asyncpg
- **Background jobs:** Celery + Redis
- **Testing:** pytest, httpx

### Frontend
- **Framework:** React 19+
- **Build tool:** Vite 6+
- **Lenguaje:** TypeScript 5.7+
- **Styling:** Tailwind CSS 4
- **State:** React Query 5 (TanStack Query)
- **Routing:** React Router 7
- **Testing:** Vitest + React Testing Library + Playwright

### Infraestructura
- **Container:** Docker + docker-compose
- **Reverse proxy:** nginx
- **Vector DB:** Qdrant (si aplica RAG)
- **Local LLM:** Ollama (modelos 3B para dev, 8B+ para prod si aplica)

## 3. Estándares de Calidad

### Código
- [ ] Type hints estrictos en TODO el código Python
- [ ] Tipos compartidos backend↔frontend desde OpenAPI spec
- [ ] Docstrings en funciones públicas
- [ ] Nombres descriptivos (sin `x`, `tmp`, `data` genéricos)

### Testing
- [ ] Tests unitarios para toda lógica de negocio
- [ ] Tests de integración para endpoints críticos
- [ ] Tests E2E para flujos de usuario principales
- [ ] Cobertura mínima: 80% backend, 60% frontend

### Documentación
- [ ] README.md con setup, env vars, arquitectura
- [ ] API docs automáticas (/docs de FastAPI)
- [ ] CHANGELOG.md por release
- [ ] Decision Records (ADRs) para decisiones arquitectónicas importantes

### Seguridad
- [ ] JWT para autenticación
- [ ] Rate limiting en endpoints públicos
- [ ] Validación de inputs con Pydantic
- [ ] Secrets en .env (nunca hardcodeados)
- [ ] CORS configurado explícitamente

## 4. Principios UX

- **Mobile-first:** Todo diseño empieza en móvil
- **Accesibilidad:** WCAG 2.1 AA mínimo
- **Performance:** First Contentful Paint < 1.5s
- **Feedback:** Toda acción del usuario tiene feedback visual
- **Errores:** Mensajes de error en español, claros, sin tecnicismos

## 5. Reglas de Negocio

[Listar las reglas de negocio clave que NO pueden violarse]

Ejemplo:
- Un usuario no puede tener más de 3 reservas activas
- Las notificaciones se envían solo entre 9:00 y 21:00 hora local
- Los reportes se generan en formato PDF y Excel

## 6. Restricciones

- **Presupuesto:** [límite de infraestructura si aplica]
- **Tiempo:** [deadline si aplica]
- **Compliance:** [GDPR, ISO, etc. si aplica]
- **Hardware:** Compatible con GPU 4GB / 13GB RAM (entorno de Nelson)

## 7. Equipo y Responsabilidades

| Agente | Rol | Responsabilidad |
|--------|-----|----------------|
| Beto | Arquitecto Backend | OpenAPI spec, data model, arquitectura |
| Ricky | Backend Dev | Implementación, lógica de negocio, tests |
| Nico | Frontend Dev | UI/UX, componentes, consumo de API |
| Diego | DevOps | Docker, CI/CD, deploy, observabilidad |
| Alma | AI/QA | Integración IA, tests E2E, calidad final |

## 8. Flujo de Trabajo

1. **Especificar:** OpenAPI primero, código después
2. **Planear:** Plan técnico aprobado antes de codear
3. **Implementar:** TDD cuando sea posible, tests antes o junto al código
4. **Revisar:** PR obligatorio, review de calidad antes de mergear
5. **Documentar:** Si no está documentado, no existe

## 9. Comunicación

- **Daily:** Reporte breve por WhatsApp/audio (si es proyecto activo)
- **Bloqueos:** Reportar inmediatamente, no esperar al daily
- **Decisiones técnicas:** Documentar en ADR, aprobar por Beto o Tony
- **Cambios de scope:** Aprobar por Tony antes de implementar

## 10. Definición de Done

Una feature está terminada cuando:
- [ ] Código implementado y funcional
- [ ] Tests pasando (unitarios + integración)
- [ ] Documentación actualizada
- [ ] PR revisado y aprobado
- [ ] Deployado en staging y probado
- [ ] Tony dio el OK (para proyectos de cliente, también Pablo aprueba si es externo)
```

## Cómo Generar

### Paso 1: Tony describe el proyecto

```
Tony: "Nuevo proyecto: app de reservas para restaurantes locales"
```

### Paso 2: JARVIS hace preguntas clave

- "¿Cuál es el problema principal que resuelve?"
- "¿Quiénes son los usuarios? (clientes del restaurante, dueños, mozos)"
- "¿Hay alguna regla de negocio clave que ya conozcas?"
- "¿Es para un cliente externo o es nuestro producto?"
- "¿Hay deadline o presupuesto definido?"
- "¿Necesita integración con IA (chatbot, recomendaciones, etc.)?"

### Paso 3: JARVIS genera el CONSTITUTION.md

Completa el template con la info recopilada. Marca los checks según el contexto.

### Paso 4: Tony revisa y aprueba

Tony lee, ajusta si es necesario, y dice "aprobado".

### Paso 5: Guardar en el proyecto

```
proyecto/
├── CONSTITUTION.md         ← este archivo
├── specs/
│   ├── openapi.yaml
│   └── user-stories.md
├── backend/
├── frontend/
└── README.md
```

## Variantes

### Proyecto I+D+I (experimentación)
- Stack puede variar (se prueban tecnologías nuevas)
- Calidad: "funciona para demo" es suficiente
- Tests: mínimos, solo para validar hipótesis
- Documentación: README.md básico, sin ADRs

### Proyecto Cliente (producción)
- Stack rígido (nuestro estándar)
- Calidad enterprise (100% type hints, 80%+ cobertura)
- Tests completos
- Documentación completa + ADRs
- Definition of Done incluye aprobación del cliente

### Proyecto Interno (herramienta propia)
- Stack estándar pero flexible
- Calidad: "producción interna" (type hints, tests core)
- Documentación: README + API docs
- Definition of Done: aprobación de Tony

## Notas

- La constitución NO cambia durante el proyecto. Si cambia, es una "enmienda" que requiere aprobación de Tony.
- Los agentes deben leer la constitución antes de empezar a trabajar en el proyecto.
- Si un agente propone algo que viola la constitución, JARVIS lo rechaza automáticamente.
- La constitución se guarda en `~/brainstorming/YYYY-MM-DD-proyecto/CONSTITUTION.md`
