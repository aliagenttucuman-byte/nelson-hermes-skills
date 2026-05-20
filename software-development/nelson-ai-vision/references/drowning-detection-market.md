# Detección de Ahogamiento en Piletas — Investigación de Mercado

**Fecha:** Mayo 2026  
**Contexto:** Idea de proyecto I+D+I para Argentina. Nelson (Tony) lo planteó como PoC potencial.

## Mercado Internacional — Competidores

| Empresa | País | Tecnología | Precio estimado | Instalaciones |
|---------|------|------------|-----------------|---------------|
| Poseidon Technologies | Francia/USA | Visión 3D subacuática | 20–60k EUR | 3,000+ en 35 países |
| AngelEye | Italia | Cámaras subacuáticas + IA | 8–25k EUR | 4,000+ en Europa |
| Lynxight | Israel | IA deep learning + sub | 15–40k USD/año | 500+, JCC USA, Cruz Roja Americana |
| Aqua Alert | Australia | Cámaras aéreas + pose | 5–15k AUD | 200+ |
| Sentry Aquatic | Canadá | Sonar subacuático + IA | n/d | 100+ |
| Seal Innovation | Corea del Sur | Cámaras térmicas + IA | n/d | Asia |

## Mercado Argentina

- **No hay nadie haciendo esto con IA localmente** (Mayo 2026)
- ~12,000 piletas comerciales estimadas (range 8k–22k): countries, hoteles, clubes, complejos sindicales
- Estimativo económico a USD 900 por integración + USD 300/año mantenimiento:
  - 1% mercado (120 clientes) → USD 108k instalación + USD 36k/año
  - 2% mercado (240 clientes) → USD 216k instalación + USD 72k/año
  - 5% mercado (600 clientes) → USD 540k instalación + USD 180k/año

## Stack Técnico Recomendado

- **Detección de personas:** YOLOv8 / YOLOv11 (Ultralytics)
- **Estimación de pose:** MediaPipe Pose
- **Tracking multi-persona:** ByteTrack
- **Lógica temporal:** persona inmóvil > 20 segundos = alerta
- **Backend:** Python + FastAPI
- **Alertas:** WebSocket + push notifications
- **Cámaras:** IP subacuáticas + cámaras de borde

## Recursos Open Source

- GitHub: buscar "drowning detection YOLO"
- Datasets: https://universe.roboflow.com (buscar "drowning detection")
- Papers: IEEE Xplore + arXiv cs.CV — "Drowning Detection Using Computer Vision and Deep Learning"

## Plan de 3 Fases (PoC)

**Fase 1 (2 semanas):** Prototipo con 1 cámara + YOLO + regla: persona bajo agua >20s = alarma  
**Fase 2:** Fine-tuning con videos reales, reducir falsos positivos, agregar MediaPipe pose  
**Fase 3:** Panel web React, alertas mobile, soporte multi-cámara, historial de incidentes

## Diferencial Local

- Precio en pesos argentinos (8–40x más barato que competidores internacionales)
- Soporte local
- Adaptado a normativas argentinas de seguridad en piletas
- Primer player con IA en Argentina = ventana de oportunidad
