# Demo Package: {{NOMBRE_PROYECTO}}
## Comparativa {{VARIANTE_A}} vs {{VARIANTE_B}} vs {{VARIANTE_C}}

**Fecha:** {{YYYY-MM-DD}}
**Autor:** Equipo Nelson (Tony/JARVIS)
**Estado:** {{Funcionando / En desarrollo / Archivado}}

---

## Que es esto

{{Descripcion de 2-3 lineas del sistema que se esta comparando. Explicar en lenguaje no-tecnico para que Pablo lo entienda.}}

**Caso de uso:** {{Ejemplo concreto de como lo usaria un cliente.}}

---

## Las {{N}} Versiones (Deployadas en Paralelo)

| Variante | Tecnologia | {{Caracteristica clave 1}} | {{Caracteristica clave 2}} |
|----------|-----------|----------------------------|----------------------------|
| **{{Variante A}}** | {{Tech A}} | {{Valor A1}} | {{Valor A2}} |
| **{{Variante B}}** | {{Tech B}} | {{Valor B1}} | {{Valor B2}} |
| **{{Variante C}}** | {{Tech C}} | {{Valor C1}} | {{Valor C2}} |

---

## URLs de Acceso (Funcionando Ahora)

| Variante | Interfaz Web | API Backend |
|----------|-------------|-------------|
| **{{Variante A}}** | {{URL_FRONTEND_A}} | {{URL_BACKEND_A}} |
| **{{Variante B}}** | {{URL_FRONTEND_B}} | {{URL_BACKEND_B}} |
| **{{Variante C}}** | {{URL_FRONTEND_C}} | {{URL_BACKEND_C}} |

> **Nota:** Estas URLs son temporales (tuneles de Cloudflare). Si se reinicia el servidor, las URLs cambian.

---

## Como Probarlo (Flujo End-to-End)

### Paso 1: Abrir la UI
Elegi cualquiera de las URLs de Frontend arriba.

### Paso 2: Subir un Documento / Configurar
{{Instrucciones especificas del sistema.}}

**Datos de prueba ya cargados:**
- {{Dato 1}}
- {{Dato 2}}

### Paso 3: Ejecutar la accion principal
{{Ejemplo concreto de que hacer.}}

### Paso 4: Ver el resultado
{{Que deberia ver el usuario.}}

---

## Arquitectura Tecnica

```
Usuario (celular/PC)
    |
    v
Cloudflare Tunnel (URL publica temporal)
    |
    v
[Frontend {{Stack Frontend}}]
    |
    |  fetch()
    v
[Backend {{Stack Backend}}]
    |
    +--------+--------+--------+
    |        |        |        |
    v        v        v        v
 {{Var A}}  {{Var B}} {{Var C}} {{Otras deps}}
```

**Todo corre en nuestro servidor Linux local.** No dependemos de APIs externas salvo los tuneles de Cloudflare para el acceso remoto.

---

## Stack Completo

| Capa | Tecnologia | Version |
|------|-----------|---------|
| Frontend | {{Tech}} | {{Ver}} |
| Backend | {{Tech}} | {{Ver}} |
| {{Capa A}} | {{Tech}} | {{Ver}} |
| {{Capa B}} | {{Tech}} | {{Ver}} |
| Infra | Docker Compose | Latest |
| Acceso remoto | Cloudflared | Quick tunnels |

---

## Comparativa Detallada

| Caracteristica | {{Variante A}} | {{Variante B}} | {{Variante C}} |
|----------------|----------------|----------------|----------------|
| {{Metrica 1}} | {{Valor}} | {{Valor}} | {{Valor}} |
| {{Metrica 2}} | {{Valor}} | {{Valor}} | {{Valor}} |
| {{Metrica 3}} | {{Valor}} | {{Valor}} | {{Valor}} |

---

## Decisiones para el Cliente

| Si el cliente... | Recomendamos |
|------------------|--------------|
| {{Condicion A}} | **{{Variante A}}** |
| {{Condicion B}} | **{{Variante B}}** |
| {{Condicion C}} | **{{Variante C}}** |

---

## Lecciones Aprendidas (Pitfalls)

1. **{{Pitfall 1}}:** {{Descripcion}} **Solucion:** {{Fix}}
2. **{{Pitfall 2}}:** {{Descripcion}} **Solucion:** {{Fix}}
3. **{{Pitfall 3}}:** {{Descripcion}} **Solucion:** {{Fix}}

---

## Costos

| Componente | Costo |
|-----------|-------|
| Servidor Linux local | $0 (ya lo tenemos) |
| {{Dep 1}} | $0 (open source / local) |
| {{Dep 2}} | $0 (open source / local) |
| Cloudflare tunnels | $0 (quick tunnels, sin cuenta) |
| **Total** | **$0** |

---

## Proximos Pasos (Para Discutir con Pablo)

- [ ] Validar que Pablo puede acceder a las URLs desde su celular
- [ ] Decidir con que variante seguimos
- [ ] Definir el primer cliente piloto
- [ ] {{Otro item}}

---

## Documentacion Tecnica del Equipo

- Skill: `{{skill-name}}`
- Repositorio: `github.com/aliagenttucuman-byte/nelson-hermes-skills`
