#!/bin/bash
# robotocore-health-check.sh — Verifica rápidamente si robotocore está operativo
# Uso: bash robotocore-health-check.sh [HOST] [PORT]
# Default: localhost 4566

HOST="${1:-localhost}"
PORT="${2:-4566}"
ENDPOINT="http://${HOST}:${PORT}"

set -euo pipefail

echo "=== robotocore Health Check ==="
echo "Endpoint: $ENDPOINT"
echo ""

# 1. Health endpoint
echo -n "1. Health endpoint (/health): "
if curl -sf "${ENDPOINT}/_robotocore/health" > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL — robotocore no responde. ¿Está el contenedor levantado?"
    exit 1
fi

# 2. STS GetCallerIdentity (sanity check de credenciales)
echo -n "2. STS GetCallerIdentity: "
if python3 -c "
import boto3, sys
try:
    sts = boto3.client('sts', endpoint_url='${ENDPOINT}',
                       aws_access_key_id='123456789012',
                       aws_secret_access_key='test',
                       region_name='us-east-1')
    id = sts.get_caller_identity()
    print(f'OK (Account: {id[\"Account\"]})')
except Exception as e:
    print(f'FAIL: {e}')
    sys.exit(1)
" 2>/dev/null; then
    true
else
    echo "FAIL — boto3 no puede conectar o credenciales rechazadas"
    exit 1
fi

# 3. S3 bucket create + list (flujo completo)
echo -n "3. S3 create/list bucket: "
if python3 -c "
import boto3, uuid, sys
try:
    s3 = boto3.client('s3', endpoint_url='${ENDPOINT}',
                      aws_access_key_id='123456789012',
                      aws_secret_access_key='test',
                      region_name='us-east-1')
    bucket = f'health-check-{uuid.uuid4().hex[:8]}'
    s3.create_bucket(Bucket=bucket)
    buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]
    s3.delete_bucket(Bucket=bucket)
    if bucket in buckets:
        print(f'OK (created & deleted {bucket})')
    else:
        print('FAIL — bucket no aparece en list_buckets')
        sys.exit(1)
except Exception as e:
    print(f'FAIL: {e}')
    sys.exit(1)
" 2>/dev/null; then
    true
else
    echo "FAIL — operación S3 falló"
    exit 1
fi

echo ""
echo "=== robotocore está operativo ==="
