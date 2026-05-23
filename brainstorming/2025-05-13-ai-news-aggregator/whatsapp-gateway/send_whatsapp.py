#!/usr/bin/env python3
"""
Script Python para enviar mensajes de WhatsApp vía el Gateway local.
El gateway debe estar corriendo en http://localhost:3001

Uso:
  python3 send_whatsapp.py --to 5493816240691 --message "Hola mundo"
  python3 send_whatsapp.py --to 5493816240691,5493811234567 --message "Broadcast"
"""

import argparse
import json
import urllib.request

GATEWAY_URL = "http://localhost:3001"

# Contactos de la consultora
CONTACTS = {
    "pablo": "5493816240691",
    "pablo terian": "5493816240691",
    "terian": "5493816240691",
    "mi socio": "5493816240691",
    "socio": "5493816240691",
}


def resolve_contact(name_or_number: str) -> str:
    """Resuelve un nombre de contacto a número, o devuelve el número tal cual."""
    key = name_or_number.strip().lower()
    if key in CONTACTS:
        return CONTACTS[key]
    return name_or_number.strip().replace("+", "").replace(" ", "").replace("-", "")


def send_message(to: str, message: str):
    """Envía un mensaje a un número."""
    data = json.dumps({"to": to, "message": message}).encode("utf-8")
    req = urllib.request.Request(
        f"{GATEWAY_URL}/send",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def send_batch(recipients: list[dict], delay_ms: int = 2000):
    """Envía mensajes a múltiples números."""
    data = json.dumps({"recipients": recipients, "delayMs": delay_ms}).encode("utf-8")
    req = urllib.request.Request(
        f"{GATEWAY_URL}/send-batch",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def main():
    parser = argparse.ArgumentParser(description="Enviar mensajes WhatsApp vía Gateway")
    parser.add_argument("--to", required=True, help="Número(s) o nombre(s) destino, separados por coma. Ej: 5493816240691, pablo, terian")
    parser.add_argument("--message", required=True, help="Mensaje a enviar")
    parser.add_argument("--batch", action="store_true", help="Usar modo batch (más seguro para múltiples)")
    parser.add_argument("--delay", type=int, default=2000, help="Delay entre mensajes en ms (default: 2000)")
    args = parser.parse_args()

    raw_targets = [n.strip() for n in args.to.split(",")]
    numbers = [resolve_contact(t) for t in raw_targets]
    
    # Mostrar resolución
    for raw, resolved in zip(raw_targets, numbers):
        if raw.lower() != resolved:
            print(f"📋 {raw} -> {resolved}")

    if len(numbers) == 1 and not args.batch:
        result = send_message(numbers[0], args.message)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        recipients = [{"to": n, "message": args.message} for n in numbers]
        result = send_batch(recipients, args.delay)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
