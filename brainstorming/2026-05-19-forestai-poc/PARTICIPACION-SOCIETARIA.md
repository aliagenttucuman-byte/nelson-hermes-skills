# ForestAI · Análisis de Participación Societaria

> Fecha: 2026-05-20
> Autor: JARVIS (para Nelson Acosta)
> Estado: BORRADOR — Solo para uso interno del equipo Nelson
> Contexto: Startup nueva con equipo de drones (hardware) + equipo Nelson (software)

---

## 1. Contexto del Deal

| Parte | Aporte |
|-------|--------|
| **Equipo Nelson (Tony + Pablo + equipo)** | Software ForestAI (PoC lista), desarrollo futuro, arquitectura, mantenimiento |
| **Equipo Drones** | Hardware (drones), operación en campo, conocimiento del negocio forestal, clientes potenciales |

La startup no tiene producto vendible sin el software. El software no tiene distribución ni operación sin los drones. Es un deal de complementarios puros.

---

## 2. Valuación del Aporte de Software

### 2a. PoC ya construida (valor ya entregado)

| Componente | Horas | Rate | Valor |
|-----------|-------|------|-------|
| Backend FastAPI + OBIA + alometría INTA | 180 h | $30/h | $5.400 |
| Frontend React + MapLibre + GeoPanel | 160 h | $30/h | $4.800 |
| Integración WFS MAyDS + Sentinel-2 CDSE | 60 h | $30/h | $1.800 |
| Arquitectura + Docker + DevOps | 60 h | $40/h | $2.400 |
| Research + pruebas + datos INTA | 80 h | $30/h | $2.400 |
| **Total PoC** | **540 h** | — | **$16.800** |

### 2b. Desarrollo futuro comprometido (para llevar a producción)

Ver ESTIMACION.md — **$28.000** adicionales en 6-7 semanas.

### 2c. Valor total del aporte software (entry equity)

| Concepto | Valor |
|----------|-------|
| PoC ya entregada | $16.800 |
| Desarrollo a producción (comprometido) | $28.000 |
| **Total aporte software** | **$44.800** |

---

## 3. Valuación del Aporte de Drones

### Estimación referencial hardware

| Concepto | Valor estimado |
|----------|---------------|
| Drone fotogramétrico profesional (ej. DJI Matrice, senseFly eBee) | $15.000–35.000 por unidad |
| Cámara multiespectral (MicaSense, Parrot Sequoia) — si tienen | $5.000–15.000 |
| Equipamiento de campo (baterías, transporte, calibración) | $3.000–8.000 |
| **Hardware estimado (1 drone)** | **$23.000–58.000** |

### Intangibles del equipo de drones

| Concepto | Valor (difícil de cuantificar) |
|----------|-------------------------------|
| Conocimiento operativo del negocio forestal | Alto |
| Red de contactos con empresas forestales / gobiernos | Alto |
| Certificaciones de piloto drone (ANAC) | Medio |
| Capacidad de escalar operación en campo | Alto |

---

## 4. Análisis de Equity — Rango Justo

### Metodología: contribución relativa al valor total

| Parte | Aporte tangible | Aporte intangible | Peso total estimado |
|-------|----------------|-------------------|---------------------|
| Equipo Nelson (software) | $44.800 dev | Diferenciación tecnológica, escalabilidad del producto | **35–45%** |
| Equipo Drones | $23.000–58.000 hardware | Red comercial, operación, mercado | **55–65%** |

### Escenarios de negociación

| Escenario | Nelson | Drones | Cuándo aplica |
|-----------|--------|--------|---------------|
| **Mínimo aceptable** | 30% | 70% | Solo si ellos ponen capital + operación + clientes desde el día 1 |
| **Justo** | 40% | 60% | Deal equilibrado, software ya funcionando, desarrollo futuro comprometido |
| **Favorable a Nelson** | 45% | 55% | Si el software es claramente el diferenciador y ellos no tienen clientes concretos aún |
| **No aceptar** | < 30% | > 70% | Perdés influencia en decisiones técnicas y el incentivo económico no justifica el esfuerzo |

---

## 5. Estructura Recomendada

### 5a. Distribución inicial

```
Equipo Nelson:   40% (Tony + Pablo — a dividir internamente)
Equipo Drones:   60%
```

### 5b. Vesting — OBLIGATORIO para todos

Sin vesting, alguien puede irse en 6 meses con el equity completo. Proponer:

| Parámetro | Valor sugerido |
|-----------|---------------|
| Período de vesting | 24–36 meses |
| Cliff (mínimo para ganar algo) | 6 meses |
| Tipo | Mensual después del cliff |

Ejemplo: 40% de Nelson vesta en 24 meses. Si Nelson se va a los 12 meses sin cliff, gana 0. Con cliff de 6 meses y vesting mensual: a los 12 meses tiene 25% de su 40% = 10% real.

### 5c. Cláusulas clave a incluir

| Cláusula | Por qué importa |
|----------|----------------|
| **Tag-along** | Si los de drones venden su parte, Nelson tiene derecho a vender en las mismas condiciones |
| **Derecho de primera oferta** | Si alguien quiere vender, los socios tienen primera opción de compra |
| **Decisiones técnicas** | El equipo Nelson tiene veto en decisiones de arquitectura y tecnología |
| **Propiedad del código** | El código pertenece a la sociedad, no a ningún socio individualmente (acordar antes) |
| **Dedicación mínima** | Qué horas semanales se compromete cada parte — evitar el "socio fantasma" |

---

## 6. Cómo Presentarlo en la Negociación

### Argumento central

> "El software es el corazón del producto. Los drones sin el sistema de análisis son solo una herramienta de captura de imágenes — lo que hace la diferencia en el mercado es la inteligencia que convierte esas imágenes en inventario, NDVI, biomasa y reportes. Ya lo construimos, ya funciona, y vamos a seguir desarrollándolo. Pedimos el 40% como reconocimiento de ese valor diferencial."

### Si piden menos del 35%

> "No tiene sentido para nosotros. El riesgo que asumimos en el desarrollo, más el costo de oportunidad de no dedicar esas horas a otro proyecto, no se justifica por debajo del 35%. Podemos hacer el software como servicio (contrato de desarrollo + suscripción mensual) y mantener el equity separado."

### Palanca: la alternativa externa

Si hay riesgo de que el deal no cierre, recordar que el software funciona solo — se puede buscar otro operador de drones o venderlo directamente a empresas forestales que ya tienen flota.

---

## 7. División Interna del Equity de Nelson

| Integrante | % del 40% total | % de la empresa |
|-----------|----------------|-----------------|
| Tony (Líder técnico + arquitectura) | 55–60% del bloque | 22–24% |
| Pablo (Comercial + negocio) | 25–30% del bloque | 10–12% |
| Equipo dev (Julián + Mercedes) | 15–20% del bloque | 6–8% (pool) |

> Nota: esto es una propuesta. Tony y Pablo definen la distribución interna.

---

## 8. Próximos Pasos

- [ ] Tony valida los números y el rango de equity
- [ ] Reunión con el equipo de drones para presentar la propuesta
- [ ] Acordar estructura de vesting antes de hablar de porcentajes
- [ ] Consultar con abogado comercial para el acuerdo societario formal
- [ ] Definir modelo de gobernanza (quién toma decisiones sobre qué)

---

**NO compartir con el equipo de drones sin aprobación previa de Tony.**

*Generado por JARVIS — 2026-05-20*
