#!/usr/bin/env python3
"""
Benchmark comparativo OptiLLM vs Ollama directo.
3 problemas de razonamiento con respuestas verificables.
Uso: source /home/server/optillm-venv/bin/activate && python benchmark_optillm.py
"""
import json, time
from openai import OpenAI

OLLAMA_URL = "http://localhost:11434/v1"
OPTILLM_URL = "http://localhost:18000/v1"
MODEL = "llama3.2:3b"  # Cambiar a llama3.1:8b si se quiere probar 8B

PREGUNTAS = [
    {
        "nombre": "Lobo_Oveja_Repollo",
        "pregunta": (
            "Un granjero tiene que cruzar un rio con un lobo, una oveja y un repollo. "
            "Tiene un bote que solo cabe el granjero y una cosa mas. "
            "Si deja solos al lobo con la oveja, el lobo se come a la oveja. "
            "Si deja solos a la oveja con el repollo, la oveja se come el repollo. "
            "Explica paso a paso como transporta todo al otro lado del rio."
        )
    },
    {
        "nombre": "Interruptores_Bombillas",
        "pregunta": (
            "En una habitacion hay 3 interruptores. Afuera hay 3 bombillas, cada una controlada "
            "por un interruptor diferente. Solo puedo salir de la habitacion UNA SOLA VEZ para ver las bombillas. "
            "Como descubro con certeza que interruptor controla cada bombilla? "
            "Responde en espanol paso a paso."
        )
    },
    {
        "nombre": "Trenes_Cruzados",
        "pregunta": (
            "Un tren sale de Buenos Aires hacia Cordoba a 80 km/h. "
            "Otro tren sale de Cordoba hacia Buenos Aires a 120 km/h. "
            "La distancia entre las dos ciudades es de 700 km. "
            "A que distancia de Buenos Aires se cruzan los dos trenes? "
            "Muestra el calculo paso a paso."
        )
    }
]

def test_endpoint(client, model, pregunta):
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": pregunta}],
            max_tokens=600,
            temperature=0.3,
        )
        texto = resp.choices[0].message.content
        tokens = resp.usage.completion_tokens if resp.usage else 0
    except Exception as e:
        texto = f"ERROR: {e}"
        tokens = 0
    duracion = round(time.time() - t0, 2)
    return {"texto": texto, "tokens": tokens, "duracion": duracion}

client_ollama = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
client_optillm = OpenAI(base_url=OPTILLM_URL, api_key="sk-dummy")

variantes = [
    ("OLLAMA_DIRECTO", client_ollama, MODEL),
    ("OPTILLM_PASSTHROUGH", client_optillm, MODEL),
    ("OPTILLM_MOA", client_optillm, f"moa-{MODEL}"),
    ("OPTILLM_MCTS", client_optillm, f"mcts-{MODEL}"),
    ("OPTILLM_RE2", client_optillm, f"re2-{MODEL}"),
    ("OPTILLM_COT_REFLECTION", client_optillm, f"cot_reflection-{MODEL}"),
]

resultados = {}

for pregunta in PREGUNTAS:
    nombre_p = pregunta["nombre"]
    print(f"\n{'='*60}")
    print(f"PROBLEMA: {nombre_p}")
    print(f"{'='*60}")
    resultados[nombre_p] = {}
    for nombre_v, cli, mod in variantes:
        print(f"\n--- {nombre_v} (model={mod}) ---")
        r = test_endpoint(cli, mod, pregunta["pregunta"])
        resultados[nombre_p][nombre_v] = r
        print(f"  Tiempo: {r['duracion']}s | Tokens: {r['tokens']}")
        print(f"  Respuesta (primeros 400 chars):\n{r['texto'][:400]}...")

out_path = f"/home/server/optillm_benchmark_{MODEL.replace(':','_')}.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"\n\n{'='*60}")
print("RESUMEN DE TIEMPOS")
print(f"{'='*60}")
for nombre_p in resultados:
    print(f"\n{nombre_p}:")
    for nombre_v in resultados[nombre_p]:
        r = resultados[nombre_p][nombre_v]
        print(f"  {nombre_v:28s} -> {r['duracion']:>7.2f}s | {r['tokens']:>4} tokens")

print(f"\nResultados guardados en: {out_path}")
