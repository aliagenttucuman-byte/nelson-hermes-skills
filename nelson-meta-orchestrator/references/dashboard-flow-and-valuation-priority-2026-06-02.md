# Dashboard flow + PM valuation priority (2026-06-02)

## Context
Two concrete UX/operational corrections were applied in the Orchestrator dashboard and project views:

1) **Mission input placement**
- User feedback: "Objetivo de la misión" input was buried in the middle of the page.
- Fix: move mission input block to the top (right after mission-mode header), before operational/diagnostic cards.

2) **Valuation source selection bug**
- Symptom: ForestAI/Fleet showed low values inconsistent with project scale.
- Root cause: project card selected first keyword match, often a `brainstorming` item (spike/idea) instead of the canonical `project` entry.
- Fix in selection logic: prioritize source type in this order:
  - `project` (highest)
  - `github`
  - `brainstorming` (lowest)

## Practical rule
When rendering project-level executive valuation cards:
- Never use naive "first keyword hit".
- Rank candidates by source trust for business numbers (`project > github > brainstorming`).
- Allow manual valuation overrides for executive alignment when strategic scope exceeds auto-estimation.

## Validation checklist
- Confirm selected card source is `type=project` for flagship initiatives.
- Confirm valuation mode displayed (`manual`/`documented`/`auto`) matches intended governance.
- Confirm UX flow order starts with objective entry, then plan/execute, then telemetry/ops blocks.