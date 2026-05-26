#!/usr/bin/env python3
"""Sanitiza una respuesta antes de entregarla al usuario."""
import re
import sys

def sanitize(text: str) -> str:
    # Rutas del sistema
    text = re.sub(r'/home/[^/\s]+', '/home/<USER>', text)
    text = re.sub(r'/Users/[^/\s]+', '/Users/<USER>', text)
    text = re.sub(r'/tmp/[^\s\n]+', '/tmp/<FILE>', text)
    # IPs privadas
    text = re.sub(r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b', '<INTERNAL_IP>', text)
    # Hostnames internos comunes
    text = re.sub(r'\b[a-zA-Z0-9-]+\.local\b', '<HOST>.local', text)
    return text

if __name__ == "__main__":
    text = sys.stdin.read()
    print(sanitize(text))
