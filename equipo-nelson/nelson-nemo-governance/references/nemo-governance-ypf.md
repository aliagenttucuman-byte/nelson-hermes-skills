# NemoHermes Governance — Documentación YPF (jun 2026)

## Contexto
YPF tiene NemoHermes implementado como capa de routing NVIDIA.
Necesitan gobierno para múltiples VPs sin intervención dev.
SSO: Microsoft EntraID ya en uso en toda YPF.

## Casos de Uso Detectados YPF

| VP / Área | Caso de Uso | Skills necesarias |
|-----------|-------------|-------------------|
| Finanzas | Análisis OPEX/barril mensual | fin-costos, fin-benchmark |
| Operaciones | Reporte de producción diario | ops-produccion, ops-alertas |
| IT | Monitoreo de infraestructura | it-infra-check, it-alertas |
| Comercial | Análisis de precios y márgenes | com-precios, com-margenes |
| RRHH | Reportes de dotación (sin PII) | rrhh-dotacion-anonimizada |
| Presidencia | Dashboard ejecutivo cross-área | cruce: finanzas + operaciones |

## Documentos Generados
- Diagrama PNG: generado con drawio CLI en `/tmp/nemo-governance.png`
- Doc completo: `/tmp/nemo-governance/NEMO_HERMES_GOVERNANCE.md`

## Próximos Pasos con YPF
1. Validar roles y áreas exactas con equipo IT
2. Inventariar skills/prompts actuales en NemoHermes
3. Definir VPs piloto para Fase 1
4. Estimar costos GCP según volumen de usuarios

## Stafa que circulan (contexto de la sesión)
Nelson recibió consulta de Gino/Pablo sobre apps de "IA que genera dinero" que
circulan en anuncios de Taboola en El País. Son estafas de libro:
- Dominio: webcrewstat.com (red de afiliados spam)
- Patrón: foto de celeb argentina + depósito inicial $250 USD + dinero no recuperable
- Sin regulación CNV/SEC
AlegentAI != esas apps. Nosotros automatizamos procesos reales.
