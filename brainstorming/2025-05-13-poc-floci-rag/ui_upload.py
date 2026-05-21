from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import boto3
import os
from pathlib import Path

app = FastAPI(title="RAG Upload - PoC I+D+i")

# Configuracion S3 (floci local)
S3_ENDPOINT = "http://localhost:4566"
S3_BUCKET = "rag-documents"
AWS_KEY = "test"
AWS_SECRET = "test"
REGION = "us-east-1"

s3 = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET,
    region_name=REGION
)

# Crear directorio para templates
template_dir = Path(__file__).parent / "templates"
template_dir.mkdir(exist_ok=True)

# Template HTML simple
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>PoC RAG - Subir Documentos</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .upload-area { border: 3px dashed #007bff; border-radius: 10px; padding: 40px; text-align: center; margin: 20px 0; background: #f8f9fa; }
        .upload-area:hover { background: #e9ecef; }
        input[type="file"] { display: none; }
        .btn { background: #007bff; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #0056b3; }
        .file-list { margin-top: 20px; }
        .file-item { background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 5px; display: flex; justify-content: space-between; }
        .success { color: green; }
        .error { color: red; }
        .info { color: #666; font-size: 14px; margin-top: 20px; padding: 15px; background: #e7f3ff; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 PoC RAG - Area I+D+i</h1>
        <p>Suba documentos PDF para el sistema de Retrieval Augmented Generation</p>
        
        <div class="info">
            <strong>Infraestructura:</strong><br>
            🗂️ S3 (floci local) → bucket: <code>rag-documents</code><br>
            🤖 Embeddings: Ollama local (nomic-embed-text)<br>
            🔍 Vector DB: Qdrant local<br>
            🧠 LLM: llama3.2:3b / gemma3:4b
        </div>
        
        <form action="/upload" method="post" enctype="multipart/form-data">
            <div class="upload-area" onclick="document.getElementById('file').click()">
                <p style="font-size: 48px; margin: 0;">📁</p>
                <p style="font-size: 18px; color: #666;">Click para seleccionar PDF</p>
                <input type="file" id="file" name="file" accept=".pdf" onchange="this.form.submit()">
            </div>
        </form>
        
        {% if message %}
        <div class="{{ status }}">
            <strong>{{ message }}</strong>
        </div>
        {% endif %}
        
        <div class="file-list">
            <h3>📋 Documentos subidos ({{ files|length }}):</h3>
            {% for f in files %}
            <div class="file-item">
                <span>📄 {{ f.name }} ({{ f.size }} bytes)</span>
                <span style="color: #666;">{{ f.date }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

# Guardar template
template_file = template_dir / "index.html"
template_file.write_text(html_template)

templates = Jinja2Templates(directory=str(template_dir))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Listar archivos del bucket
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET)
        files = []
        for obj in response.get('Contents', []):
            files.append({
                'name': obj['Key'],
                'size': obj['Size'],
                'date': obj['LastModified'].strftime('%Y-%m-%d %H:%M')
            })
    except Exception as e:
        files = []
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "files": files,
        "message": None,
        "status": None
    })

@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...)):
    message = ""
    status = ""
    
    try:
        # Validar que sea PDF
        if not file.filename.endswith('.pdf'):
            message = "Solo se permiten archivos PDF"
            status = "error"
        else:
            # Subir a S3
            content = await file.read()
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=file.filename,
                Body=content,
                ContentType='application/pdf'
            )
            message = f"✅ '{file.filename}' subido exitosamente a S3"
            status = "success"
    except Exception as e:
        message = f"❌ Error: {str(e)}"
        status = "error"
    
    # Listar archivos actualizados
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET)
        files = []
        for obj in response.get('Contents', []):
            files.append({
                'name': obj['Key'],
                'size': obj['Size'],
                'date': obj['LastModified'].strftime('%Y-%m-%d %H:%M')
            })
    except:
        files = []
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "files": files,
        "message": message,
        "status": status
    })

@app.get("/health")
async def health():
    return {"status": "ok", "s3_endpoint": S3_ENDPOINT, "bucket": S3_BUCKET}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
