# Configuración de Cron Jobs en Hermes

## Paso a paso

1. **Crear script Python** en `~/brainstorming/YYYY-MM-DD-proyecto/scripts/`
2. **Probar manualmente:** `python3 scripts/mi_script.py`
3. **Crear wrapper shell** en `~/.hermes/scripts/mi-job.sh`:
   ```bash
   #!/bin/bash
   cd /home/server/brainstorming/YYYY-MM-DD-proyecto || exit 1
   python3 scripts/mi_script.py
   ```
4. **Hacer ejecutable:** `chmod +x ~/.hermes/scripts/mi-job.sh`
5. **Registrar cron job** (desde Hermes, no crontab del sistema):
   ```
   schedule: "0 9,18 * * *"
   script: "mi-job.sh"
   deliver: "origin"
   no_agent: true
   ```

## Reglas críticas

- El campo `script` debe ser **solo el nombre del archivo**, sin paths. Hermes lo busca en `~/.hermes/scripts/`
- **NO** usar paths absolutos ni `~/` en el campo `script`
- `no_agent: true` es obligatorio para jobs de datos puros (evita consumir tokens de LLM)
- El output del script llega como mensaje al usuario vía `deliver: "origin"`

## Formato de schedule (cron)

- `0 9,18 * * *` → 9:00 y 18:00 todos los días
- `0 8 * * 1` → lunes a las 8:00
- `*/30 * * * *` → cada 30 minutos

## Troubleshooting

- Si el job no aparece, verificar que el script wrapper tenga permisos de ejecución
- Si el output no llega, verificar que el script no esté escribiendo a stderr sin redirigir
- El state file (JSON) debe vivir fuera del repo para persistir entre ejecuciones
