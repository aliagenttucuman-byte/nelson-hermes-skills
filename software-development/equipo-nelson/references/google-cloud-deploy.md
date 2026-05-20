# Google Cloud Deploy — Proyecto latam-flight-delay

## Configuración actual

- **Proyecto:** `latam-flight-delay`
- **Cuenta de servicio:** `github-actions@latam-flight-delay.iam.gserviceaccount.com`
- **Credenciales:** `~/.gcp-service-account.json`
- **CLI:** Instalado en `~/google-cloud-sdk/`

## Comandos útiles

```bash
# Activar credenciales
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
gcloud auth activate-service-account --key-file=$HOME/.gcp-service-account.json
gcloud config set project latam-flight-delay

# Deploy a Cloud Run (ejemplo)
gcloud run deploy nelson-backend \
  --source ./backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Deploy frontend estático a Cloud Storage + CDN
gsutil -m cp -r ./frontend/dist/* gs://BUCKET_NAME/
```

## Notas

- Para deploy real, habilitar **Cloud Resource Manager API** desde la consola de Google Cloud (puede estar deshabilitada en proyectos nuevos/free).
- Este es un plano — ajustar región, nombres de servicios y variables de entorno según el proyecto.
