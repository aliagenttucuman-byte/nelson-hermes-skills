# thesysdev/openui — Generative UI Framework

**Repo:** https://github.com/thesysdev/openui  
**Docs / Playground:** https://openui.com  
**License:** MIT  
**Status:** Active (trending, Discord community)

## Qué es

OpenUI es un framework full-stack de Generative UI. El concepto central es **OpenUI Lang**: un lenguaje compacto, diseñado para streaming, que el modelo genera en lugar de JSON. El runtime React lo parsea y renderiza progresivamente mientras llegan tokens.

**67% más eficiente en tokens que JSON** para representar UI estructurada.

## Capacidades clave

- **OpenUI Lang** — lenguaje estructurado para generación de UI en streaming
- **Librerías de componentes integradas** — Charts, forms, tables, layouts, listas
- **Prompt generation desde el component library** — el framework genera las instrucciones al modelo desde los componentes disponibles
- **Streaming renderer** — renderiza en React mientras el modelo genera tokens
- **Chat y app surfaces** — sirve para assistants, copilots y flujos de producto

## Diferencia con wandb/openui

| | wandb/openui | thesysdev/openui |
|---|---|---|
| Propósito | Genera código de UI a partir de prompts | Renderiza UI dentro de conversaciones de agents en producción |
| Uso | Prototipado / generación de componentes | Agentes con output estructurado interactivo |
| Output | Código fuente de componentes | Componentes renderizados en tiempo real |

## Quick Start

```bash
npx @openuidev/cli@latest create --name genui-chat-app
cd genui-chat-app
echo "OPENAI_API_KEY=tu-key" > .env
npm run dev
```

Requiere una de: OpenAI, Anthropic, o Groq API key.

## Stack

- Frontend: React + Next.js + TypeScript + Tailwind
- CLI: `@openuidev/cli` via npx
- Multi-LLM: OpenAI, Anthropic, Groq
- Node.js v18+ requerido
- 629 dependencias npm (~37s de install)

## Spike en servidor Nelson

- Scaffolded en: `~/spikes/001-openui/genui-chat-app/`
- Estado: listo, esperando API key para `npm run dev`
- El CLI instala todo automaticamente, sin necesidad de clonar repo

## Notas

- No tiene relación con ninguna criptomoneda (aviso oficial en README)
- La URL del playground es https://www.openui.com/playground para testear sin instalar
