# ForestAI — Extensión ML con NetFlora

ForestAI base usa image analytics sin ML (OpenCV + Rasterio + OBIA).
La capa de clasificación de especies se integra via `nelson-netflora` (YOLOv7 + Embrapa Acre).

## Tab integrada
- View key: `"netflora"`
- Componente: `src/components/NetFloraPanel.tsx`
- Skill de referencia: `nelson-netflora`

## Patrón para agregar tabs nuevas en App.tsx
Ver `nelson-netflora/references/forestai-tab-integration.md` — documenta los 5 pasos
exactos con los 3 lugares donde hay que actualizar el tipo TypeScript de `view`.

## Modelos disponibles (NetFlora / Embrapa)
| Categoría | Modelo | Especies |
|---|---|---|
| Açaí | ACAI_Embrapa00.pt | 2 |
| Palmeiras | PALMEIRAS_Embrapa00.pt | 11 |
| PFNMs | NM_Embrapa00.pt | 23 |
| PMFS | PMFS_Embrapa00.pt | 23 |
| Castanheira | ❌ sin modelo público | 1 |
| Ecológico | ❌ sin modelo público | 3 |

## Estado (sesión 2026-05-30)
- NetFloraPanel.tsx: UI completa con mock/demo
- Backend real (tiles.py + detect.py + results.py): pendiente de implementar
- Endpoint target: POST /api/netflora/detect → job_id → polling GET /api/netflora/jobs/{job_id}
