# Patrón ProjectView genérico — Dashboard por iniciativa

## Cuándo usar

Cuando el orchestrator dashboard necesita una vista dedicada por proyecto/iniciativa
(ForestAI, Fleet, etc.) que muestre: progreso de hitos, valuación económica, escenario
financiero base y próximas acciones desde el índice PM.

## Estructura del componente

```tsx
// src/pages/ProjectView.tsx

type ProjectConfig = {
  id: string
  label: string
  icon: React.ElementType
  color: string          // 'emerald' | 'indigo' | 'amber'
  accent: string         // 'text-emerald-400' etc
  keywords: string[]     // para buscar en el índice PM
  tunnelUrl?: string     // URL del demo si existe
  description: string
  stack: string[]
  milestones: { name: string; done: boolean }[]
}

const PROJECTS: Record<string, ProjectConfig> = {
  forestai: { ... },
  fleet: { ... },
}

// Componente genérico — recibe la key del proyecto
export function ProjectView({ projectKey }: { projectKey: string }) { ... }

// Exports específicos (sin lógica propia)
export function ForestAIPage() { return <ProjectView projectKey="forestai" /> }
export function FleetPage()    { return <ProjectView projectKey="fleet" />    }
```

## Cómo agregar un proyecto nuevo

1. Agregar entrada en `PROJECTS` con su config
2. Agregar export específico al final del archivo
3. Agregar ruta en `App.tsx`: `<Route path="/nuevo" element={<NuevoPage />} />`
4. Agregar item al sidebar en `Sidebar.tsx` bajo la sección "Proyectos"

## Búsqueda en el índice PM

El componente busca la instancia PM por keywords:

```tsx
const match = allProjects.find((p) =>
  cfg.keywords.some((kw) => p.name.toLowerCase().includes(kw))
)
```

Si no encuentra match, muestra un aviso para hacer re-index desde Resumen PM.

## Sidebar con secciones

```tsx
// Sidebar.tsx — nav con dividers
const nav = [
  { to: '/',             icon: LayoutDashboard, label: 'Dashboard'       },
  { to: '/orchestrator', icon: BrainCircuit,    label: 'Orquestador'     },
  { divider: true, label: 'Proyectos' },
  { to: '/forestai',    icon: TreePine,         label: 'ForestAI'        },
  { to: '/fleet',       icon: Truck,            label: 'Fleet Optimizer' },
  { divider: true, label: 'Gestión' },
  { to: '/budget',      icon: DollarSign,       label: 'Presupuesto'     },
  ...
]

// Render con soporte de dividers:
{nav.map((item, idx) => {
  if ('divider' in item && item.divider) {
    return <div key={`div-${idx}`} className="pt-3 pb-1 px-3">
      <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest">{item.label}</p>
    </div>
  }
  const { to, icon: Icon, label } = item as { to: string; icon: React.ElementType; label: string }
  return <NavLink key={to} to={to} ... />
})}
```

## Archivos involucrados

- `src/pages/ProjectView.tsx` — componente genérico + exports
- `src/components/layout/Sidebar.tsx` — nav con dividers
- `src/App.tsx` — rutas `/forestai` y `/fleet`
