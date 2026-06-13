# Patrones de Extracción de Metadata — Evaluaciones Rápidas

> Referencia operativa para el patrón "Evaluación Rápida de Repos / Modelos / Productos Externos" definido en el SKILL.md de nelson-brainstorming. Comandos curl exactos, endpoints API, y pitfalls por fuente.

## Regla de oro

**`browser_navigate` falla en este servidor** — Chrome tira "No usable sandbox" (AppArmor userns deshabilitado en Ubuntu 23.10+). **Siempre usar `curl` + parsing con `sed`/`jq`/`python`.** Más rápido, más confiable, sin dependencies.

## HuggingFace — Modelos

**API JSON oficial:** `https://huggingface.co/api/models/{org}/{name}`

```bash
curl -sL "https://huggingface.co/api/models/nvidia/LocateAnything-3B" | head -100
```

**Campos clave en el JSON:**
- `id`, `private`, `gated`, `disabled`, `license` (spdx_id via `cardData.license_name`)
- `downloads`, `downloadsAllTime`, `likes`, `lastModified`, `createdAt`
- `pipeline_tag` (image-text-to-text, text-generation, feature-extraction, etc.)
- `library_name`, `tags[]`, `safetensors.parameters.BF16`
- `model-index` → null suele indicar que NO hay eval formal
- `cardData.base_model[]` → modelos base
- `transformersInfo.auto_model`, `transformersInfo.custom_class` → patrón de uso
- `siblings[]` → archivos del repo (buscar `modeling_*.py` para custom code)
- `spaces[]` → demos comunitarios
- `tag_objs[].extra.paperTitle` → títulos de papers

**Página HTML (para descripción humana):**
```bash
curl -sL "https://huggingface.co/nvidia/LocateAnything-3B" \
  -A "Mozilla/5.0" \
  | sed 's/<[^>]*>//g' \
  | grep -iE "(locate|prompt|model|description|vision|grounding|task|usage)" \
  | head -60
```

**Pitfalls HF:**
- `model-index: null` ≠ modelo malo, pero no hay benchmark formal
- `gated: true` → requiere aprobación manual para descargar
- `custom_code: true` + archivos `modeling_*.py` → trust_remote_code requerido, revisar el código
- `license_name: "other"` o sin SPDX → leer el LICENSE manualmente, suele ser restrictiva
- Tags `arxiv:*` → link al paper, leer al menos el abstract

## GitHub — Repos

**API JSON oficial:** `https://api.github.com/repos/{owner}/{repo}`

```bash
curl -sL "https://api.github.com/repos/tashfeenahmed/freellmapi" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({k:d.get(k) for k in ['name','description','language','stargazers_count','forks_count','open_issues_count','license','updated_at','pushed_at','size','topics','archived','disabled']}, indent=2, default=str))"
```

**Campos clave:**
- `stargazers_count`, `forks_count`, `watchers_count`, `open_issues_count`
- `pushed_at` → si >6 meses, marcar como "abandoned warning" (no necesariamente muerto, pero es señal)
- `license.spdx_id` → MIT, Apache-2.0, GPL-3.0, etc. None = todos los derechos reservados
- `size` en KB
- `topics[]`, `language`, `default_branch`
- `archived: true` → mantenimiento oficial terminado
- `disabled: true` → repo bloqueado por GitHub (ToS violation, etc.)

**Tree de archivos:**
```bash
curl -sL "https://api.github.com/repos/{owner}/{repo}/contents/" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f['type'], f['name'], f.get('size','')) for f in d]"
```

**README raw:**
```bash
curl -sL "https://raw.githubusercontent.com/{owner}/{repo}/main/README.md" | head -200
```

**Pitfalls GitHub:**
- `pushed_at` ≠ `updated_at`. El pushed es lo que importa (último commit real)
- Stars inflados por marketing no significan calidad (siempre chequear issues, PRs, último release)
- `license.spdx_id: null` → NO es MIT, no es open source. Buscar LICENSE file manualmente
- Repos de un solo autor con >1k stars en <3 meses → verificar si es genuino o artificial
- `private: true` o 404 → no accesible, no se puede evaluar

## arxiv — Papers

**API oficial:** `http://export.arxiv.org/api/query?search_query=all:{query}&max_results=5`

**Mejor:** buscar el PDF directo:
```bash
curl -sL "https://arxiv.org/abs/{paper_id}" \
  | sed 's/<[^>]*>//g' \
  | grep -A 2 -iE "(abstract|authors|title)"
```

**Campos clave en abstract:**
- Task (detection, segmentation, grounding, etc.)
- Datasets usados (COCO, LVIS, custom)
- Métricas reportadas (mAP, AP50, etc.)
- Limitaciones declaradas
- Licencia del código/modelo (a veces el paper no la menciona — verificar repo)

**Pitfalls arxiv:**
- Paper reciente (<6 meses) → sin peer review, leer con cuidado las claims
- "State of the art on X" sin tabla comparativa → desconfiar
- Benchmarks custom sin release público → irreproducible
- Datasets no estándar → no comparable con la literature

## npm — Paquetes Node

```bash
curl -sL "https://registry.npmjs.org/{package}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); v=d.get('dist-tags',{}).get('latest'); m=d['versions'][v] if v else {}; print(json.dumps({k:m.get(k) for k in ['name','version','description','license','homepage','repository']}, indent=2))"
```

**Campos clave:**
- `license` → tipo SPDX
- `repository.url` → link al source
- `dependencies` → qué más se necesita
- `time` → última release
- `maintainers` → cuántos mantienen el package

## PyPI — Paquetes Python

```bash
curl -sL "https://pypi.org/pypi/{package}/json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); i=d['info']; print(json.dumps({k:i.get(k) for k in ['name','version','summary','license','home_page','project_urls']}, indent=2))"
```

**Pitfalls PyPI:**
- `license: None` o string vacío → no es open source
- `classifiers` con `License :: OSI Approved :: MIT License` → confiable
- `Development Status :: 4 - Beta` o `3 - Alpha` → no usar en producción

## Productos SaaS

No hay API estándar. Para productos, scrapear:
- Pricing page (curl + grep)
- ToS page (buscar "non-commercial", "redistribution", "automated access")
- Status page (uptime histórico)
- Reviews en G2, Capterra, HN

**Pitfalls SaaS:**
- Free tier atractivo que cambia a pago agresivo cuando crecés
- ToS que prohíbe automatización (mata casos como FreeLLMAPI-style proxies)
- "Self-hosted" como upsell que cuesta 10x más que el SaaS
- Vendor lock-in via formatos propietarios

## Patrones transversales

### Licencias que bloquean producción comercial
- `CC BY-NC-*` (non-commercial)
- `NVIDIA License` (research only)
- `Research Use Only`
- Cualquiera que diga "academic and non-profit research purposes only"

### Licencias OK para producción
- `MIT`, `BSD-2-Clause`, `BSD-3-Clause`, `Apache-2.0`, `ISC`, `MPL-2.0`
- `GPL-3.0` → OK si tu código también es GPL (copyleft)
- `LGPL-3.0` → OK para linking

### Señales de proyecto abandonado
- `pushed_at` > 6 meses sin activity
- `open_issues` >> `closed_issues` (ratio > 3:1)
- Última release > 1 año
- Issues sin respuesta de maintainers
- Dependencias con CVEs sin parchar

### Señales de proyecto serio
- CI verde (badge en README)
- Releases con semver (tags v*)
- Changelog mantenido
- Multi-arch Docker (linux/amd64 + arm64)
- Tests con coverage > 70%
- Documentación completa (no solo README)
- Discord/Slack/Discourse activo

## Comando one-liner para repo completo

```bash
# Combinado: API + tree + README
REPO="owner/repo"
curl -sL "https://api.github.com/repos/$REPO" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Stars: {d['stargazers_count']} | Forks: {d['forks_count']} | License: {d.get('license',{}).get('spdx_id','NONE')} | Last push: {d['pushed_at']} | Archived: {d['archived']}\")"
```

## Anti-patrones a evitar

- **NO** tomar el título del README como verdad — leer al menos la sección de arquitectura/limitaciones
- **NO** saltar el `LICENSE` — la license es lo que define si sirve o no
- **NO** ignorar el `pushed_at` — un repo con 10k stars pero 2 años sin push es código muerto
- **NO** confiar en el contador de stars como proxy de calidad — chequear ratio issues/PRs/last activity
- **NO** decir "popular project" sin dar el número — siempre el número concreto
- **NO** recomendar un repo con `trust_remote_code` sin haber leído el código custom
