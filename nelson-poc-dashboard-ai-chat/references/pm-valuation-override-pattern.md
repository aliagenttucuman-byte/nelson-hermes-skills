# PM Valuation Override Pattern (Nelson dashboard)

## Trigger
Use when PM page has project selector and user needs non-static valuation that updates per selection.

## Data contract
Each project item should expose:

```json
{
  "id": "project:xyz",
  "project_valuation": {
    "mode": "documented|auto|manual",
    "mvp_total_investment_usd": 5374,
    "development_cost_usd": 4830,
    "operational_cost_4m_usd": 544,
    "monthly_avg_usd": 1343.5,
    "revenue_scenarios": [
      {"name":"Base","gross_revenue_usd":80000}
    ],
    "source_files": ["/path/doc.md"],
    "note": "..."
  }
}
```

## Source precedence
1. `manual` override persisted by project_id.
2. `documented` valuation from project-local evidence.
3. `auto` valuation from technical signals and project size.

## API workflow
- Force recalc all PM data:
  - `POST /pm/instances/reindex`
- Generate selected project valuation:
  - `POST /pm/projects/valuation/generate` with `{ "project_id": "..." }`
- Freeze current valuation as manual:
  - `POST /pm/projects/valuation/override/set` with `{ "project_id": "...", "valuation": {...optional...} }`
- Unfreeze:
  - `POST /pm/projects/valuation/override/clear` with `{ "project_id": "..." }`

## UI behavior
- Show card "Valuación de la iniciativa" only from selected project.
- Show three headline values:
  - Valor actual estimado = `mvp_total_investment_usd`
  - Escenario base = `revenue_scenarios[Base].gross_revenue_usd`
  - Reparto 55/45 from base gross
- Show source label: Documentada / Auto JARVIS / Manual (fijada)

## Verification recipe
1) Open PM, select project A and project B → card values must change.
2) Set override for A.
3) Reindex PM.
4) Select A again → mode remains `manual`.
5) Clear override for A.
6) Reindex PM.
7) Select A → mode returns to `documented` or `auto`.
