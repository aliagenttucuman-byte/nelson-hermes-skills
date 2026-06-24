# Written Stakeholder Pitches & Communications

> When Nelson needs JARVIS to draft written messages for stakeholders (Pablo, clients, investors) — not verbal demos, but emails, pitches, Slack messages, or WhatsApp audios.

## When to Use Written vs Verbal

| Scenario | Medium | Skill |
|----------|--------|-------|
| Demo scheduled, face-to-face | Verbal | `nelson-demo-script` main body |
| No meeting, need to share position | Written | This reference |
| Stakeholder asks technical questions by text | Written | This reference |
| Pitching stack/technology change (e.g., Flutter → React Native) | Written | This reference |
| Answering a formal questionnaire (CTO experience, etc.) | Written | This reference |

## Pattern: Stack Migration Pitch

**Goal:** Convince a stakeholder (Pablo) to adopt the team's standardized stack instead of a one-off technology.

**Structure:**
1. **Acknowledge the current approach** — don't dismiss their work.
2. **Show the team cost** — "only you can touch this code."
3. **Show the team benefit** — shared language, shared components, shared backend.
4. **Concrete numbers** — "80% of code shared with web."
5. **Offer a spike** — low-risk proof, not a mandate.

**Template (React Native pitch to Pablo):**

> Hola Pablo. Te cuento por qué estandarizamos en **Python + React** y cómo eso te simplifica la vida si llevás el mobile con **React Native** en vez de Flutter.
>
> **Un solo stack, un solo equipo.** Nuestro backend es Python/FastAPI (Julián) y el frontend es React/Vite (Mercedes). Si seguís con Flutter, estás en otro mundo: Dart, Gradle, Android Studio, ADB, y problemas de sincronización con OneDrive que ya te complicaron. Eso significa que **solo vos podés tocar ese código**.
>
> Con React Native usás JavaScript/TypeScript, el mismo lenguaje que Mercedes usa para el dashboard del orquestador. Los componentes de UI, la lógica de estado, las llamadas a la API — todo se comparte o se replica fácilmente.
>
> **Mismo backend, cero duplicación.** El backend FastAPI que ya tenemos sirve para web y mobile sin cambiar una línea.
>
> **Performance nativa real.** React Native compila a código nativo. No es un webview.
>
> **Resumen:** menos esfuerzo, menos errores de deploy, un solo equipo, un solo stack, y la app mobile compartiendo el 80% del código con la web.
>
> ¿Te animás a que hagamos un **spike de migración** de tu app a React Native para que veas la diferencia?

## Pattern: Formal Questionnaire Responses (English)

**Goal:** Answer investor/recruiter questions in English based on Nelson's real profile.

**Rules:**
- Be honest. Don't invent exact years, team sizes, or titles that aren't confirmed.
- Match Nelson's real trajectory: dev → tech lead → YPF R&D lead + AlegentAI co-founder.
- Emphasize hands-on coding + leadership.
- Keep each answer to 2-4 sentences.

**Example Q&A set (CTO/VPE experience):**

> **Can you briefly describe your startup CTO/VPE experience?**
> I serve as Technical Lead of R&D at YPF, where I architect AI solutions and lead technical strategy. Simultaneously, I'm the technical co-founder of AlegentAI, driving our AI agent infrastructure, product architecture, and full-stack delivery.
>
> **Have you built teams from 0 -> 20+?**
> I'm actively scaling there. I've built our core squad from zero — backend, frontend, and AI agent specialists — and I'm now structuring the I+D+I area to grow into a full 20+ person team. The foundation and hiring framework are in place.

## Pattern: Neutral Response to External Proposals

When a third party sends a proposal/investment deck and Nelson has a meeting in 2-3 days:

> "Hola, recibí el [doc]. Muy interesante la propuesta y el mercado que apuntan. Me gustaría entender un poco más la parte técnica antes de opinar en profundidad. Lo charlamos pronto."

See `nelson-demo-script` main SKILL.md for the full "Respuesta a Propuestas" section.

## Pitfalls

- **Don't over-promise in writing.** Written text can be forwarded. Always leave wiggle room ("spike", "MVP", "estimación").
- **Don't bash the stakeholder's current choice.** Acknowledge it first, then show the better path.
- **Keep technical depth appropriate to the reader.** Pablo understands tech but doesn't care about implementation details. Investors care about traction and team, not stack.
- **Audio + text for important pitches.** Send a concise text summary + audio (TTS) for WhatsApp. Never audio-only for business-critical messages.
