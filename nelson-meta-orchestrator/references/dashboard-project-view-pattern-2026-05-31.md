# Dashboard Vista por Proyecto — Patrón ProjectView

Fecha: 2026-05-31
Archivo: `/home/server/nelson/orchestrator-dashboard/src/pages/ProjectView.tsx`

## Patrón

Componente genérico `ProjectView` parametrizado por `projectKey` que renderiza una vista dedicada por proyecto. Exports separados por proyecto (`ForestAIPage`, `FleetPage`).

## Config por proyecto (hardcoded + dinámico)

```typescript
type ProjectConfig = {
  id: string
  label: string
  icon: React.ElementType
  color: string          // tailwind color name (emerald, indigo)
  accent: string         // texto del color (text-emerald-400)
  keywords: string[]     // para hacer match contra el índice PM
  repoUrl?: string
  tunnelUrl?: string
  description: string
  stack: string[]
  milestones: { name: string; done: boolean }[]  // hitos hardcodeados
}
```

Los hitos se hardcodean (estado real del proyecto). La valuación y próximos pasos vienen del índice PM dinámicamente via `usePmInstances`.

## Match contra PM

```typescript
const match = allProjects.find((p) =>
  cfg.keywords.some((kw) => p.name.toLowerCase().includes(kw))
)
```

Keywords del proyecto buscan en el nombre de la instancia PM. Si no hay match, mostrar alerta "no encontrado en índice PM, hacer Actualizar datos del PM".

## Pitfall: TypeScript — no usar `as Array<...>()`

```typescript
// MAL — syntax error TS1005:
const allProjects = (data?.projects || []) as Array<{
  id: string
  ...
}>()   // <-- el () final es inválido

// BIEN — definir type interno primero:
type PMProject = {
  id: string
  ...
}
const allProjects = (data?.projects || []) as PMProject[]
```

## Sidebar con dividers — items heterogéneos

```typescript
const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { divider: true, label: 'Proyectos' },   // divider item
  { to: '/forestai', icon: TreePine, label: 'ForestAI' },
  // ...
]

// Render:
nav.map((item, idx) => {
  if ('divider' in item && item.divider) {
    return <div key={`div-${idx}`}>...</div>
  }
  const { to, icon: Icon, label } = item as { to: string; icon: React.ElementType; label: string }
  return <NavLink key={to} ...>
})
```

## Colores dinámicos Tailwind — pitfall

No usar template literals para clases Tailwind:
```typescript
// MAL:
className={`bg-${cfg.color}-500/15`}  // Tailwind no puede tree-shake esto

// OK para PoCs internos, pero en producción usar un mapa:
const colorMap = {
  emerald: 'bg-emerald-500/15',
  indigo: 'bg-indigo-500/15',
}
```

## Estructura de rutas

```typescript
// App.tsx
<Route path="/forestai" element={<ForestAIPage />} />
<Route path="/fleet"    element={<FleetPage />}    />
```
