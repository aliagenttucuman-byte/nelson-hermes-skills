# OpenAerialMap — Ortofotos Reales Verificadas

Fuente: https://api.openaerialmap.org  
Campo URL: `uuid` (el campo `download` siempre es null)  
Fecha verificación: mayo 2026

## API de búsqueda

```bash
# Por bounding box Argentina
curl -s "https://api.openaerialmap.org/meta?limit=50&bbox=-73,-55,-53,-22" -o /tmp/oam_ar.json

# Genérico por tipo + tamaño chico
curl -s "https://api.openaerialmap.org/meta?limit=50&type=image%2Ftiff" -o /tmp/oam.json
```

## URLs Verificadas — Argentina (mayo 2026)

Todas descargables sin login, prefijo `https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/...`

| Nombre | Tamaño | Descripción | URL |
|--------|--------|-------------|-----|
| INTA San Salvador AER | 13MB | Entre Ríos — AER INTA, vegetación agrícola | `https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/660ac227fca0b60001ebc58c/0/660ac227fca0b60001ebc58d.tif` |
| Chapadmalal Buenos Aires | 8MB | Buenos Aires — costa atlántica, parque INTA Chapadmalal | `https://oin-hotosm-temp.s3.amazonaws.com/62ab78f5a896280006b0a6ae/0/62ab78f5a896280006b0a6af.tif` |
| Golondrinas Patagonia | 24MB | Patagonia — vegetación nativa | `https://oin-hotosm-temp.s3.amazonaws.com/5e40d48b56992d0006e589df/0/5e40d48b56992d0006e589e0.tif` |
| Lotes Silvopastoriles Chaco | 32MB | Gran Chaco — sistemas silvopastoriles | `https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/660aa4b8fca0b60001ebc576/0/660aa4b8fca0b60001ebc577.tif` |
| Club Terra Rosario | 17MB | Isla la Invernada, Rosario — vegetación riparia | `https://oin-hotosm-temp.s3.amazonaws.com/5be6f924a6df5900063b121c/0/5be6f924a6df5900063b121d.tif` |
| SR La Leonesa Chaco | 32MB | Chaco — lotes forestales, algarrobo | `https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/660b1858fca0b60001ebc59e/0/660b1858fca0b60001ebc59f.tif` |
| Bajamar | 10MB | Buenos Aires — zona costera | `https://oin-hotosm-temp.s3.amazonaws.com/623a760fcb82d300081432bb/0/623a760fcb82d300081432bc.tif` |

## URLs Verificadas — Resto del Mundo (mayo 2026)

| Nombre | Tamaño | País | URL |
|--------|--------|------|-----|
| Bricenio Ecuador | 5MB | Ecuador | `https://oin-hotosm-temp.s3.amazonaws.com/572b2552cd0663bb003c32a2/0/572b25b82b67227a79b4fbf1.tif` |
| Tacloban Filipinas | 14MB | Filipinas | `https://oin-hotosm-temp.s3.amazonaws.com/1/0/55c36a162b67227a79b4f4d9.tif` |
| Ruinas Rumicucho Ecuador | 15MB | Ecuador | `https://oin-hotosm-temp.s3.amazonaws.com/58d86fafca8ed70011209f81/0/113fb2f2-d8dc-425a-97c2-20050a580192.tif` |

## Script de descarga masiva

```bash
# Descarga + upload directo al sistema ForestAI
for entry in \
  "INTA San Salvador AER|https://oin-hotosm-temp.s3.us-east-1.amazonaws.com/660ac227fca0b60001ebc58c/0/660ac227fca0b60001ebc58d.tif" \
  "Chapadmalal Buenos Aires|https://oin-hotosm-temp.s3.amazonaws.com/62ab78f5a896280006b0a6ae/0/62ab78f5a896280006b0a6af.tif" \
  "Golondrinas Patagonia|https://oin-hotosm-temp.s3.amazonaws.com/5e40d48b56992d0006e589df/0/5e40d48b56992d0006e589e0.tif"; do
  name=$(echo $entry | cut -d'|' -f1)
  url=$(echo $entry | cut -d'|' -f2)
  tmpfile="/tmp/oam_$(echo $name | tr ' ' '_').tif"
  wget -q --timeout=90 "$url" -O "$tmpfile" && echo "OK $name"
  curl -s -X POST "http://localhost:8010/api/analyses" \
    -F "file=@${tmpfile};type=image/tiff" \
    -F "name=${name}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('analysis_id','ERR')[:8], d.get('status',''))"
done
```

## Resultados de análisis ForestAI (mayo 2026)

| Ortofoto | Árboles detectados | Notas |
|----------|-------------------|-------|
| INTA San Salvador AER | 30 | Vegetación agrícola + árboles dispersos |
| Chapadmalal Buenos Aires | 122 | Parque con vegetación densa — mejor resultado AR |
| Golondrinas Patagonia | procesando | Tiempo variable por tamaño 24MB |
| Lotes Silvopastoriles Chaco | procesando | Tiempo variable por tamaño 32MB |

## Nota sobre GeoTIFFs sintéticos

Generar imágenes con `numpy.random` produce GeoTIFFs válidos georreferenciados pero con 0 árboles detectados. Útiles solo para demostrar:
- Flujo de upload y procesamiento
- Ubicación geográfica correcta en el mapa (mini mapa + overlay)

Para demos con detección real de árboles → usar siempre ortofotos reales de OAM o los tiles NEON.
