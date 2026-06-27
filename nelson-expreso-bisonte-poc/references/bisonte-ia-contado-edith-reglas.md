# IA CONTADO — Reglas de Negocio (transcripción Edith, jun 2026)

Video: Google Drive file_id `1sw6PahPF1EA51TjokD5qDnXB2IEDxgYK`, 57 min, 454MB.
Transcripción: `/tmp/bisonte/transcripcion.txt` (Whisper small CPU, ~30 min procesamiento).

## Flujo diario de Edith

Mínimo 4x/semana, objetivo todos los días al mediodía (después que la chica de cuentas corrientes
ingresa todas las acreditaciones — transferencias del día anterior que impactan al día siguiente).

1. Transoft: Operativos → Informes Generales → Detalle Guías por Sucursal → "Contado con Estado de Guía" → Exportar Excel
2. Pegar en hoja nueva del día en su Excel acumulado (el INICIAL)
3. Vincular con BUSCARV desde hoja anterior: trae JUSTIFICACIÓN, REFERENTE, OBSERVACIÓN
4. Eliminar duplicados (pagos a cuenta + nota de crédito sobre misma guía → se queda con la primera)
5. Filtrar solo estado ED (entregadas pendientes de cobro) — el resto va a otras matrices
6. Asignar REFERENTE a las NDS/NDE (nuevas sin asignar) usando succobro como base
7. Pintar en rojo las urgentes según tolerancia de días
8. Agregar observaciones manuales (VER DIF, RETENCION, etc.)
9. Subir al Dropbox → equipo cuentas corrientes trabaja encima

## Estructura del informe Transoft

Informe: "GF Pendientes de Cobro - CONTADO C/ESTADO DE GUIA"

SISTEMA tiene ~14 columnas (descarga pura de Transoft):
- nro, guiafec, razsocc, clase, **fechaedit**, sucori, sucdest, importe, saldo, succobro, tiporec, sucursal, nrogen_a, estado

INICIAL tiene las mismas + 4 columnas manuales que agrega Edith:
- JUSTIFICACIÓN (ej: "SGCP 6562")
- REFERENTE (ej: "BA", "CC", "HM")
- ESTADO (ED, DT, TT, RL, RT, DO, DI, OB, NR)
- OBSERVACIÓN (ej: "VER DIF", "RETENCION", "SALDO PENDIENTE")

## Columna DIAS_ATRASO — fuente correcta

**Fuente: `fechaedit` (datetime de openpyxl) — confirmado con Edith jun 2026.**

- `fechaedit` = última edición en Transoft, que en la práctica corresponde a la fecha de entrega
- `guiafec` = fecha de EMISIÓN de la guía (cuando se creó), NO de entrega — NO usar para DIAS_ATRASO

Cálculo:
```python
from datetime import datetime, timezone, timedelta
ar_tz = timezone(timedelta(hours=-3))
hoy = datetime.now(ar_tz).date()
dias = (hoy - fechaedit.date()).days
```

## Estados de guía

| Código | Significado |
|--------|-------------|
| ED | Entregada pendiente de cobro — el ÚNICO que trabaja en esta matriz |
| DT | Despachada en tránsito |
| TT | En tránsito |
| RL | Recibida en depósito local |
| RT | Retornada |
| DO | Devuelta al origen |
| DI | Documentación incompleta |
| OB | Observada |
| NR | No retirada |

Solo se trabaja ED en la planilla IA CONTADO. El resto van a otras matrices.

## REFERENTE — sucursal/comercial responsable del cobro

| Código | Significado |
|--------|-------------|
| BA | Buenos Aires |
| CC | Casa Central (Tucumán) |
| JU | Jujuy |
| RO | Rosario |
| SA | Salta |
| HM / HMS | Héctor M. (comercial) |
| MRA | Comercial MRA |
| FN | Federico Nacif (comercial) |
| POSVENTA | Área de posventa |
| NDS / NDE | Sin asignar — filtro para encontrar las nuevas del día |

Regla: REFERENTE = succobro del sistema. 90% correlación directa.
Excepción: si la negociación la hizo un comercial de Tucumán aunque el cobro figure en otra sucursal.

Cuentas híbridas: clientes sin cuenta corriente pero con margen de 7 días de gracia.
Cobranza en origen: la sucursal se queda con la guía original y manda el duplicado — pueden cobrar
sin que llegue la documentación física a Casa Central.

## OBSERVACIÓN — valores más usados

| Valor | Significado |
|-------|-------------|
| VER DIF | Saldo ≠ importe, diferencia sin explicar — urgente |
| RETENCION | Diferencia es retención impositiva, la sucursal la gestiona (esp. BA) |
| SI + número | Solicitud de Indemnización (ligada a área posventa) |
| SGCP + número | Número de gestión de cobro asignada |
| PAGA DD/MM | Ya fue pagada en esa fecha (transferencia procesada al día siguiente) |
| SALDO PENDIENTE | Saldo con causa justificada (mudanza, espera, acuerdo especial) |
| nota de crédito | Diferencia es nota de crédito — sacar VER DIF cuando se confirma |
| judicial / gerencia | Guía en juicio — no gestionar, escalar |

## Tolerancias de días de atraso

- **Casa Central (CC)**: 0 días de tolerancia — cualquier guía no entregada el mismo día ya es rojo. Edith: "De casa central es inmediato del día anterior."
- **Sucursales (BA, JU, RO, SA, etc.)**: 7 días de tolerancia — tiempo para que la caja mande docs. >7 días → rojo.

Nota sobre transferencias: muchos pagos llegan como transferencia bancaria. La chica de cuentas
corrientes los procesa primera hora de la mañana siguiente. Por eso una guía puede aparecer como
pendiente aunque ya esté cobrada — desaparece recién al mediodía después del ingreso.

## Regla de pintado — IMPORTANTE: solo la celda/columna, NUNCA la fila entera

**Nelson (jun 2026): "no pintemos todas las filas, sino pintemos la columna correspondiente a la regla".**

Pintar la fila entera confunde. Cada color va en la celda o columna que lo origina:
- DIAS_ATRASO → colorear solo la celda DIAS_ATRASO (rojo si supera tolerancia)
- ESTADO_CAMBIO → colorear solo la celda ESTADO de SISTEMA (rojo si cambió vs INICIAL)
- NUEVOS → colorear solo la celda del campo que falta completar (amarillo)

## Regla de pintado rojo — ambas condiciones activan rojo (OR)

1. Estado cambió en Transoft entre INICIAL y SISTEMA (ej: TT → ED, RL → ED) → celda ESTADO roja
2. Días de atraso supera tolerancia → celda DIAS_ATRASO roja:
   - succobro == "CC" → tolerancia 0 días (cualquier día de atraso → rojo)
   - resto → tolerancia 7 días (>7 → rojo)

## Regla de pintado amarillo

Registros nuevos (solo en SISTEMA) que están DENTRO de tolerancia → celda DIAS_ATRASO amarilla.
Significa: guía nueva del día que Edith y el equipo deben completar manualmente.

## Orden de prioridad que usa Edith para revisar

1. **Sin gestión de cobro asignada** (NDS/NDE en REFERENTE) — asignar urgente
2. **Pintadas de rojo** (atrasadas) — investigar y presionar
3. **VER DIF** (diferencias sin explicar) — identificar causa
4. **RETENCION** (retenciones impositivas) — la sucursal debe reclamarla

## Colaboración via Dropbox

- Edith sube el FINAL al Dropbox
- El equipo de cuentas corrientes abre el archivo, completa los 4 campos manuales en las filas amarillas
- Edith supervisa y aprueba
- Objetivo a futuro: que el equipo de cuentas corrientes ejecute el proceso ellos mismos, Edith solo revisa el dashboard

## Merge INICIAL + SISTEMA = FINAL — reglas verificadas con datos reales

Con el IA_CONTADO.xlsx de prueba (jun 2026):
- 281 existentes preservados con anotaciones de Edith
- 93 nuevos en amarillo (carga manual pendiente)
- 88 eliminados (cobrados/cerrados en Transoft)
- Rojos: todos los que cambiaron estado + todos los que superan tolerancia de días

IMPORTANTE: el SISTEMA se filtra por estado=ED y se deduplicada ANTES del merge.
Los duplicados (pago a cuenta + nota de crédito sobre misma guía) se eliminan quedando con la primera ocurrencia.

## Descarga del video de Edith

```bash
pip install gdown
gdown "https://drive.google.com/uc?id=1sw6PahPF1EA51TjokD5qDnXB2IEDxgYK" -O /tmp/bisonte/edith_explicacion.mp4
ffmpeg -i /tmp/bisonte/edith_explicacion.mp4 -ar 16000 -ac 1 -c:a pcm_s16le /tmp/bisonte/edith_audio.wav -y
python3 -c "
import whisper
model = whisper.load_model('small', device='cpu')
result = model.transcribe('/tmp/bisonte/edith_audio.wav', language='es', verbose=False)
open('/tmp/bisonte/transcripcion.txt','w').write(result['text'])
print('LISTO:', len(result['text']), 'chars')
"
```

Nota: 57 min de audio en CPU con modelo `small` tarda ~30 min. Usar `background=True` en terminal.
