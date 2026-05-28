# OpenCode Zen — Modelos Testados (Mayo 2026)

URL base: `https://opencode.ai/zen/v1/chat/completions`
Headers obligatorios: `Authorization: Bearer <key>`, `HTTP-Referer`, `X-Title`
Backend: Proxy sobre OpenRouter (BYOK)

---

## Modelos que FUNCIONAN ✅

| Modelo ID | Tipo | Contexto | Precio est. | Notas |
|-----------|------|----------|-------------|-------|
| `gpt-5.4-nano` | GPT (OpenAI) | ? | ~$0.0001/1K tok | **Default del equipo.** Barato, rápido, calidad básica. Math limitado. |
| `gpt-5.4-mini` | GPT (OpenAI) | ? | ~$0.0006/1K tok | Media-alta. Error en test inicial (posiblemente temporal). |
| `claude-sonnet-4` | Claude (Anthropic) | ? | ~$0.003/1K tok | Mejor calidad/precio. Razonamiento sólido. |
| `claude-haiku-4-5` | Claude (Anthropic) | ? | ~$0.00025/1K tok | Media. Funciona bien para queries simples. |
| `glm-5` | GLM (Zhipu) | ? | ? | Funcionó en test. Calidad básica. |
| `deepseek-chat-v2` | DeepSeek | ? | ? | Funcionó en test. Razonamiento decente. |
| `qwen3.6-plus` | Qwen (Alibaba) | ? | ? | Funcionó en test. |
| `kimi-k2.6` | Kimi (Moonshot) | 262K | ~$0.002/1K tok | Funcionó. Gran contexto. Bueno para I+D+I. |

## Modelos que FALLAN ❌

| Modelo ID | Problema |
|-----------|----------|
| `deepseek-v4-flash-free` | Respuesta vacía. Probable rate limit o no disponible en tier actual. |
| `qwen3.6-plus-free` | ERROR (vacío). |
| `minimax-m2.5-free` | `None` en respuesta. No funciona. |

**Pitfall:** Los modelos con sufijo `-free` en OpenCode Zen **no funcionan**. Siempre usar la versión paga.

## Modelos NO TESTADOS pero disponibles

| Modelo ID | Tipo | Contexto | Notas |
|-----------|------|----------|-------|
| `minimax-m2.7` | MiniMax | 196K | Disponible en lista. No testado aún. |
| `claude-opus-4` | Claude | ? | Premium. No testado. |
| `gpt-5.4` | GPT (OpenAI) | ? | Versión base. No testado. |

## Lista completa

356 modelos disponibles vía OpenCode Zen (lista de `/v1/models`).
Los principales proveedores: OpenAI, Anthropic, Moonshot (Kimi), MiniMax, DeepSeek, Alibaba (Qwen), Google (Gemini), Meta (Llama).

## Recomendaciones por caso de uso

| Caso | Modelo recomendado |
|------|-------------------|
| Producción barata (RAGs, queries simples) | `gpt-5.4-nano` |
| Producción calidad media | `claude-haiku-4-5` o `gpt-5.4-mini` |
| Producción calidad alta | `claude-sonnet-4` |
| I+D+I con contexto largo | `kimi-k2.6` (262K ctx) |
| I+D+I reasoning complejo | `claude-sonnet-4` o `minimax-m2.7` |
| Testing/development | `gpt-5.4-nano` (el más barato que funciona) |

## Archivo de credenciales

```bash
~/secrets/opencode.env
chmod 600
```

Contenido:
```
OPENCODE_API_KEY=sk-xxxxxxxx
OPENCODE_BASE_URL=https://opencode.ai/zen/v1
OPENCODE_MODEL=gpt-5.4-nano
```
