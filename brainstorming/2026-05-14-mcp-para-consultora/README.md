# MCP (Model Context Protocol) para la Consultora
## Documento de análisis estratégico

**Fecha:** 2026-05-14
**Autor:** Equipo Nelson (Tony + JARVIS)
**Estado:** Análisis — pendiente decisión de adopción

---

## ¿Qué es MCP?

MCP es un protocolo estándar de Anthropic para conectar LLMs con herramientas externas. En vez de que cada integración sea un script custom, MCP define una interfaz universal: el LLM descubre qué herramientas hay disponibles y las usa directamente.

---

## Usos identificados para nuestra consultora

### 1. Para JARVIS (Tony + asistente IA)
En vez de que las skills sean solo archivos markdown, podríamos tener MCP servers reales que expongan herramientas. Ejemplo: un MCP server "consultora" que tenga funciones como `crear_proyecto()`, `deploy_rag()`, `enviar_reporte_a_pablo()`. JARVIS las descubre automáticamente y las ejecuta sin scripts intermedios.

### 2. Para el equipo I+D+I
MCP es ideal para experimentación. El equipo I+D+I podría armar MCP servers que conecten con sistemas de clientes, bases de datos, APIs, etc. Si funciona, el equipo Central lo adopta estandarizado.

### 3. Para los agentes individuales (Beto, Ricky, etc.)
Cada agente podría tener su propio MCP server con sus herramientas especializadas. Beto expone `generar_openapi_spec()`, `crear_modelo_sqlalchemy()`. Nico expone `scaffold_componente_react()`, `crear_test_vitest()`.

---

## Pros

- **Estandarización:** una sola forma de conectar herramientas, no 10 scripts diferentes
- **Descubrimiento automático:** JARVIS ve qué herramientas hay sin leer documentación
- **Reutilizable:** un MCP server de GitHub sirve para el agente Beto, para JARVIS, y para n8n
- **Futuro-proof:** Anthropic, OpenAI y otros están adoptándolo

## Contras

- **Overkill para cosas simples:** si solo necesitás un `curl` a una API, un script bash es más rápido
- **Overhead:** cada MCP server corre como proceso aparte
- **Curva de aprendizaje:** el equipo Central necesita entender el protocolo
- **Dependencia de Node.js/Python para los servers:** más infraestructura

---

## Opinión del equipo

MCP brilla cuando tenés muchas herramientas que querés que los agentes usen de forma dinámica. En nuestra consultora, lo más valioso sería para el **equipo I+D+I**: experimentar con MCP servers que luego el equipo Central estandariza.

Para producción (equipo Central), hoy las skills markdown + scripts funcionan bien. MCP sería un upgrade cuando empecemos a tener 15+ integraciones externas.

---

## Próximos pasos sugeridos

1. Fase I+D+I: armar un MCP server de prueba (ej: conexión a una API de cliente)
2. Evaluar si el overhead vale la pena vs scripts actuales
3. Si funciona, documentar como skill `nelson-mcp-integration`
4. Considerar adopción progresiva: I+D+I primero, Central después

---

## Referencias

- Skill: `native-mcp` (documentación técnica de Hermes)
- Config: `~/.hermes/config.yaml` → sección `mcp_servers`
