# Simulación física realista para Fleet Optimizer AR

Patrón para datos simulados con física real — aplicable a cualquier PoC de flota o activos con consumo dinámico.

## TARA y campos por activo

```python
{
    "tara_kg": 9500,             # peso propio del vehículo vacío
    "capacidad_carga_kg": 22500, # máximo legal de carga
    "peso_carga_kg": 18200,      # carga actual del viaje
    "tanque_litros": 600,        # capacidad total del tanque
    "consumo_base_l100km": 28.0, # consumo vacío (L/100km)
    # Cubiertas
    "cubiertas_km_vida": 120000,       # vida estimada del juego
    "cubiertas_km_recorridos": 42500,  # km desde último cambio
    # Vida útil
    "vida_util_km": 1000000,     # vida típica tracto larga distancia
}
```

## Fórmula de consumo dinámico

El consumo real varía según cuánto pesa lo que llevás:

```python
factor_carga = 1 + 0.3 * (peso_carga_kg / capacidad_carga_kg)
consumo_real_l100km = consumo_base_l100km * factor_carga

# Ejemplos reales:
# Scania R450 cargado al 100%: 27.0 * 1.30 = 35.1 L/100km
# Volvo FM 380 cargado al 34%: 25.5 * 1.10 = 28.1 L/100km
# DAF CF 400 cargado al 100%: 30.0 * 1.30 = 39.0 L/100km
```

## Conversión km/h → consumo por tick (30s)

```python
km_tick = velocidad_kmh * 30 / 3600          # km recorridos en 30s
litros_consumidos = consumo_real * km_tick / 100
pct_consumido = (litros_consumidos / tanque_litros) * 100
combustible = max(0, combustible - pct_consumido)
```

## Autonomía en tiempo real

```python
autonomia_km = (combustible / 100) * tanque_litros / consumo_real * 100
```

## Desgaste de cubiertas

```python
cubiertas_km_recorridos += km_tick   # se acumula con cada movimiento
km_restantes = cubiertas_km_vida - cubiertas_km_recorridos
pct_vida = (1 - cubiertas_km_recorridos / cubiertas_km_vida) * 100

# Alerta crítica < 5.000 km restantes
if km_restantes < 5000:
    alerta = f"🔴 Cubiertas: {int(km_restantes):,} km para cambio"
```

## Vida útil del camión

```python
vida_util_pct = (km_total / vida_util_km) * 100
km_restantes_vida = vida_util_km - km_total
```

## Valores reales de referencia (Argentina, 2026)

| Modelo              | TARA (kg) | Cap. carga (kg) | Consumo base | Tanque |
|---------------------|-----------|-----------------|--------------|--------|
| Mercedes Actros 2651| 9.500     | 22.500          | 28 L/100     | 600 L  |
| Scania R450         | 8.800     | 23.200          | 27 L/100     | 620 L  |
| Volvo FH 460        | 8.600     | 23.400          | 26 L/100     | 600 L  |
| DAF XF 480          | 8.900     | 23.100          | 27 L/100     | 580 L  |
| Iveco Stralis 480   | 9.200     | 22.800          | 28 L/100     | 600 L  |
| Mercedes Actros 1848| 9.100     | 22.900          | 29 L/100     | 600 L  |
| Scania G410         | 8.700     | 23.300          | 27.5 L/100   | 620 L  |
| Volvo FM 380        | 8.400     | 23.600          | 25.5 L/100   | 600 L  |
| DAF CF 400          | 9.300     | 22.700          | 30 L/100     | 580 L  |
| Iveco Trakker 480   | 9.800     | 22.200          | 29.5 L/100   | 620 L  |

Vida cubiertas promedio flota pesada AR: 120.000 km (varía 110.000-130.000 según uso).
Vida útil tracto larga distancia: ~1.000.000 km.
