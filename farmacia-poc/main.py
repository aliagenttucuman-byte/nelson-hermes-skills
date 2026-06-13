"""
Farmacia PoC - Backend FastAPI
Dashboard para farmacia con datos mock y asistente IA
Puerto: 8030
"""

import random
import json
import asyncio
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

# ─── Seed reproducible ────────────────────────────────────────────────────────
random.seed(42)
TODAY = date.today()
NOW = datetime.now()

# ─── DATA MOCK ────────────────────────────────────────────────────────────────

LABORATORIOS = [
    "Bayer", "Roche", "Pfizer", "Novartis", "Abbott",
    "GlaxoSmithKline", "AstraZeneca", "Merck", "Sanofi", "Lilly"
]

CATEGORIAS = ["antibióticos", "analgésicos", "cardiología", "dermatología", "vitaminas"]

FARMACEUTICOS = ["Ana García", "Carlos López", "María Rodríguez", "José Martínez", "Laura Sánchez"]

PRODUCTOS_NOMBRES = {
    "antibióticos": [
        "Amoxicilina 500mg", "Azitromicina 250mg", "Ciprofloxacino 500mg",
        "Cefalexina 500mg", "Doxiciclina 100mg", "Claritromicina 500mg",
        "Ampicilina 500mg", "Levofloxacino 500mg", "Metronidazol 500mg", "Trimetoprim 160mg"
    ],
    "analgésicos": [
        "Ibuprofeno 400mg", "Paracetamol 500mg", "Naproxeno 500mg",
        "Diclofenaco 50mg", "Ketorolaco 10mg", "Tramadol 50mg",
        "Metamizol 500mg", "Celecoxib 200mg", "Meloxicam 15mg", "Aspirina 500mg"
    ],
    "cardiología": [
        "Atorvastatina 20mg", "Losartán 50mg", "Amlodipino 5mg",
        "Metoprolol 50mg", "Enalapril 10mg", "Bisoprolol 5mg",
        "Ramipril 5mg", "Carvedilol 25mg", "Valsartán 80mg", "Furosemida 40mg"
    ],
    "dermatología": [
        "Hidrocortisona 1% crema", "Betametasona 0.05% crema", "Ketoconazol 2% crema",
        "Tretinoína 0.025% crema", "Clotrimazol 1% crema", "Mupirocina 2% crema",
        "Adapaleno 0.1% gel", "Permetrina 5% crema", "Terbinafina 1% crema", "Aciclovir 5% crema"
    ],
    "vitaminas": [
        "Vitamina C 1000mg", "Vitamina D3 2000UI", "Complejo B forte",
        "Omega 3 1000mg", "Zinc 50mg", "Magnesio 400mg",
        "Hierro 325mg", "Calcio 600mg + D3", "Vitamina E 400UI", "Biotina 10000mcg"
    ]
}


def generar_productos():
    productos = []
    pid = 1
    for cat, nombres in PRODUCTOS_NOMBRES.items():
        for nombre in nombres:
            precio_compra = round(random.uniform(3.50, 45.00), 2)
            margen = random.uniform(0.20, 0.55)
            precio_venta = round(precio_compra * (1 + margen), 2)
            stock_minimo = random.randint(5, 20)
            # Algunos productos con bajo stock para alertas
            if pid % 7 == 0:
                stock_actual = random.randint(0, stock_minimo - 1)
            else:
                stock_actual = random.randint(stock_minimo, stock_minimo * 5)

            # Vencimientos: algunos próximos a vencer
            if pid % 9 == 0:
                dias_venc = random.randint(5, 28)  # vence en <30 días
            elif pid % 11 == 0:
                dias_venc = random.randint(1, 7)   # vence muy pronto
            else:
                dias_venc = random.randint(45, 540)  # normal

            vencimiento = TODAY + timedelta(days=dias_venc)
            ventas_30d = random.randint(2, 120)

            bajo_stock = stock_actual < stock_minimo
            dias_para_vencer = (vencimiento - TODAY).days
            por_vencer = dias_para_vencer <= 30

            alerta = None
            if bajo_stock and por_vencer:
                alerta = "crítico"
            elif bajo_stock:
                alerta = "stock"
            elif por_vencer:
                alerta = "vencimiento"

            productos.append({
                "id": pid,
                "nombre": nombre,
                "laboratorio": random.choice(LABORATORIOS),
                "categoria": cat,
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
                "precio_compra": precio_compra,
                "precio_venta": precio_venta,
                "vencimiento": vencimiento.isoformat(),
                "dias_para_vencer": dias_para_vencer,
                "ventas_30d": ventas_30d,
                "bajo_stock": bajo_stock,
                "por_vencer": por_vencer,
                "alerta": alerta,
                "rotacion": round(ventas_30d / max(stock_actual, 1), 2)
            })
            pid += 1
    return productos


def generar_ventas(productos):
    ventas = []
    horas_disponibles = list(range(8, 21))  # 8am a 8pm
    for i in range(1, 31):
        producto = random.choice(productos)
        hora = f"{random.choice(horas_disponibles):02d}:{random.randint(0,59):02d}"
        cantidad = random.randint(1, 5)
        importe = round(producto["precio_venta"] * cantidad, 2)
        ventas.append({
            "id": i,
            "hora": hora,
            "producto": producto["nombre"],
            "categoria": producto["categoria"],
            "cantidad": cantidad,
            "precio_unitario": producto["precio_venta"],
            "importe": importe,
            "farmaceutico": random.choice(FARMACEUTICOS)
        })
    # Ordenar por hora
    ventas.sort(key=lambda x: x["hora"])
    return ventas


def generar_proveedores():
    nombres = [
        "Distribuidora Farma Norte S.A.",
        "MediSupply Argentina",
        "Laboratorios Unidos S.R.L.",
        "PharmaDist Centro",
        "Grupo Salud Mayorista"
    ]
    proveedores = []
    for i, nombre in enumerate(nombres, 1):
        ultimo_pedido = TODAY - timedelta(days=random.randint(3, 45))
        proveedores.append({
            "id": i,
            "nombre": nombre,
            "contacto": f"contacto{i}@{nombre.lower().replace(' ', '').replace('.', '')[:15]}.com",
            "telefono": f"+54 11 {random.randint(4000,6999)}-{random.randint(1000,9999)}",
            "deuda_pendiente": round(random.uniform(5000, 85000), 2),
            "ultimo_pedido": ultimo_pedido.isoformat(),
            "dias_desde_pedido": (TODAY - ultimo_pedido).days,
            "pedidos_mes": random.randint(1, 8),
            "condicion_pago": random.choice(["30 días", "60 días", "contado", "15 días"])
        })
    return proveedores


def calcular_kpis(productos, ventas):
    ventas_dia = sum(v["importe"] for v in ventas)
    costo_dia = sum(
        next((p["precio_compra"] for p in productos if p["nombre"] == v["producto"]), 0) * v["cantidad"]
        for v in ventas
    )
    margen_bruto = ventas_dia - costo_dia
    margen_pct = round((margen_bruto / ventas_dia * 100) if ventas_dia > 0 else 0, 1)

    bajo_stock = [p for p in productos if p["bajo_stock"]]
    por_vencer = [p for p in productos if p["por_vencer"]]
    rotacion_prom = round(sum(p["rotacion"] for p in productos) / len(productos), 2)

    # Producto más vendido del día
    ventas_por_producto = {}
    for v in ventas:
        ventas_por_producto[v["producto"]] = ventas_por_producto.get(v["producto"], 0) + v["importe"]
    top_producto = max(ventas_por_producto, key=ventas_por_producto.get) if ventas_por_producto else "N/A"

    return {
        "ventas_dia": round(ventas_dia, 2),
        "margen_bruto": round(margen_bruto, 2),
        "margen_porcentaje": margen_pct,
        "transacciones": len(ventas),
        "ticket_promedio": round(ventas_dia / len(ventas), 2) if ventas else 0,
        "productos_bajo_stock": len(bajo_stock),
        "productos_por_vencer": len(por_vencer),
        "rotacion_promedio": rotacion_prom,
        "top_producto_dia": top_producto,
        "alertas_criticas": len([p for p in productos if p["alerta"] == "crítico"]),
        "fecha": TODAY.isoformat(),
        "hora_actualizacion": NOW.strftime("%H:%M")
    }


# ─── Inicializar datos ─────────────────────────────────────────────────────────
PRODUCTOS = generar_productos()
VENTAS = generar_ventas(PRODUCTOS)
PROVEEDORES = generar_proveedores()
KPIS = calcular_kpis(PRODUCTOS, VENTAS)

# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title="Farmacia PoC API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Cliente IA ───────────────────────────────────────────────────────────────
ai_client = AsyncOpenAI(
    api_key="freellmapi-0b0b33d6a9c82a2b15ec6e2006867256e26e7b244e71a57d",
    base_url="http://localhost:3101/v1"
)

AI_MODEL = "deepseek-ai/deepseek-v4-flash"


def get_proveedores_txt():
    lines = []
    for p in PROVEEDORES:
        lines.append(f"- {p['nombre']}: ${p['deuda_pendiente']:,.2f} ({p['condicion_pago']})")
    return "\n".join(lines)


def build_system_prompt():
    bajo_stock = [p for p in PRODUCTOS if p["bajo_stock"]]
    por_vencer = [p for p in PRODUCTOS if p["por_vencer"]]
    criticos = [p for p in PRODUCTOS if p["alerta"] == "crítico"]

    alertas_txt = ""
    if criticos:
        nombres_criticos = ", ".join(p["nombre"] for p in criticos)
        alertas_txt += f"\n⚠️ CRÍTICOS (bajo stock Y por vencer): {nombres_criticos}"
    if bajo_stock:
        items_stock = ", ".join(p["nombre"] + " (stock: " + str(p["stock_actual"]) + ", mín: " + str(p["stock_minimo"]) + ")" for p in bajo_stock)
        alertas_txt += f"\n📦 Bajo stock mínimo: {items_stock}"
    if por_vencer:
        items_venc = ", ".join(p["nombre"] + " (vence en " + str(p["dias_para_vencer"]) + " días)" for p in por_vencer)
        alertas_txt += f"\n⏰ Por vencer en 30 días: {items_venc}"

    return f"""Eres el asistente virtual de una farmacia. Tienes acceso al estado actual del negocio en tiempo real.

📊 ESTADO ACTUAL DE LA FARMACIA ({TODAY.strftime('%d/%m/%Y')}):
- Ventas del día: ${KPIS['ventas_dia']:,.2f}
- Margen bruto: ${KPIS['margen_bruto']:,.2f} ({KPIS['margen_porcentaje']}%)
- Transacciones: {KPIS['transacciones']} ventas
- Ticket promedio: ${KPIS['ticket_promedio']:,.2f}
- Productos bajo stock mínimo: {KPIS['productos_bajo_stock']}
- Productos por vencer (≤30 días): {KPIS['productos_por_vencer']}
- Rotación promedio: {KPIS['rotacion_promedio']}x
- Producto más vendido hoy: {KPIS['top_producto_dia']}
- Alertas críticas: {KPIS['alertas_criticas']}

🚨 ALERTAS ACTIVAS:{alertas_txt if alertas_txt else ' Ninguna crítica por el momento.'}

📦 PROVEEDORES CON DEUDA:
{get_proveedores_txt()}

Responde en español, de forma concisa y útil. Usa emojis apropiados. Si te preguntan sobre productos específicos, usa los datos reales proporcionados arriba. Cuando hagas recomendaciones, basa las en los datos reales del inventario."""


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "farmacia-poc", "timestamp": NOW.isoformat()}


@app.get("/api/kpis")
async def get_kpis():
    return KPIS


@app.get("/api/productos")
async def get_productos(
    categoria: str = None,
    alerta: str = None,
    buscar: str = None
):
    productos = PRODUCTOS.copy()
    if categoria:
        productos = [p for p in productos if p["categoria"] == categoria.lower()]
    if alerta:
        productos = [p for p in productos if p["alerta"] == alerta.lower()]
    if buscar:
        productos = [p for p in productos if buscar.lower() in p["nombre"].lower()]
    return {
        "total": len(productos),
        "productos": productos,
        "categorias": CATEGORIAS
    }


@app.get("/api/ventas")
async def get_ventas():
    total = sum(v["importe"] for v in VENTAS)
    return {
        "fecha": TODAY.isoformat(),
        "total_ventas": round(total, 2),
        "cantidad_transacciones": len(VENTAS),
        "ventas": VENTAS
    }


@app.get("/api/proveedores")
async def get_proveedores():
    deuda_total = sum(p["deuda_pendiente"] for p in PROVEEDORES)
    return {
        "deuda_total": round(deuda_total, 2),
        "proveedores": PROVEEDORES
    }


class ChatRequest(BaseModel):
    message: str
    history: list = []


@app.post("/api/chat")
async def chat(req: ChatRequest):
    system_prompt = build_system_prompt()

    messages = [{"role": "system", "content": system_prompt}]
    # Agregar historial previo (max últimos 10 mensajes)
    for msg in req.history[-10:]:
        messages.append(msg)
    messages.append({"role": "user", "content": req.message})

    async def stream_response() -> AsyncGenerator[str, None]:
        try:
            stream = await ai_client.chat.completions.create(
                model=AI_MODEL,
                messages=messages,
                stream=True,
                max_tokens=800,
                temperature=0.7
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ─── Servir Frontend ──────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent / "frontend"
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"

# Si existe build de Vite, servir desde dist/
if FRONTEND_DIST.exists():
    # Montar assets estáticos de Vite
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Intentar servir el archivo exacto primero
        static_file = FRONTEND_DIST / full_path
        if static_file.exists() and static_file.is_file():
            return FileResponse(str(static_file))
        # SPA fallback
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"error": "Frontend not built"}

elif (FRONTEND_DIR / "index.html").exists():
    # Fallback: HTML standalone
    @app.get("/")
    async def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_static(full_path: str, request: Request):
        static_file = FRONTEND_DIR / full_path
        if static_file.exists() and static_file.is_file():
            return FileResponse(str(static_file))
        # SPA fallback
        return FileResponse(str(FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8030, log_level="info")
