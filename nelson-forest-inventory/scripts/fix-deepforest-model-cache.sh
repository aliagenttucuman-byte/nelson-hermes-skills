#!/bin/bash
# fix-deepforest-model-cache.sh
# Descarga el modelo DeepForest weecology/deepforest-tree dentro del container
# usando HTTP clásico (evita el protocolo xet que falla sin HF_TOKEN).
# Ejecutar cuando el modelo tiene .incomplete o el container fue recreado.

set -e

CONTAINER="forestai-poc-celery_worker-1"
BLOB="d37a7af0b5ba2754282a80d41b4c7b66e8c7149234df5bf3f41bdaf57d329fc8"
BLOB_PATH="/root/.cache/huggingface/hub/models--weecology--deepforest-tree/blobs/$BLOB"
SNAP="/root/.cache/huggingface/hub/models--weecology--deepforest-tree/snapshots/cc21436bc5d572dde8ff5f93c1e71a32f563cace"

echo "[1/4] Limpiando incompletos..."
docker exec "$CONTAINER" sh -c "find /root/.cache/huggingface -name '*.incomplete' -delete && echo OK"

echo "[2/4] Descargando model.safetensors (~124MB, puede tardar 1-2 min)..."
docker exec "$CONTAINER" python3 -c "
import os
os.environ['HF_HUB_DISABLE_XET'] = '1'
from huggingface_hub import hf_hub_download
path = hf_hub_download(repo_id='weecology/deepforest-tree', filename='model.safetensors', local_dir='/tmp/deepforest_dl')
print('Descargado en:', path)
"

echo "[3/4] Copiando al blob cache..."
docker exec "$CONTAINER" sh -c "
cp /tmp/deepforest_dl/model.safetensors $BLOB_PATH
ls -lh $BLOB_PATH
"

echo "[4/4] Creando symlink snapshot..."
docker exec "$CONTAINER" sh -c "
ln -sf '../../blobs/$BLOB' $SNAP/model.safetensors
ls -la $SNAP
"

echo ""
echo "Verificando carga offline..."
docker exec "$CONTAINER" timeout 60 python3 -c "
import os
os.environ['HF_HUB_OFFLINE'] = '1'
from deepforest import main as df_main
model = df_main.deepforest()
model.load_model(model_name='weecology/deepforest-tree', revision='main')
print('MODELO CARGADO OK — cache local verificado')
print(type(model.model))
"

echo ""
echo "Done. Para hacerlo permanente, agregar al docker-compose.yml:"
echo "  celery_worker:"
echo "    volumes:"
echo "      - /home/server/.cache/huggingface:/root/.cache/huggingface"
