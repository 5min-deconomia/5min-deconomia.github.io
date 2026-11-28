---
name: nueva-edicion
description: Use when publishing, updating or correcting an edition of 5 min. de Economía (index.html site-data JSON, archivo.json, sitemap.xml) — "nueva edición", "edición 233", "agrega una cápsula", "corrige la cápsula", "actualiza indicadores", "mueve ediciones al archivo".
---

# Nueva edición de 5 min. de Economía

## Cómo está armado el sitio

Sitio estático en GitHub Pages, sin build. Todo el contenido vive en JSON:

- `index.html` → `<script type="application/json" id="site-data">` (entre la línea `"editions": [` y `<!-- DATA END -->`). Contiene `multimedia`, `eventos`, `editions` (las **6 más recientes**, de la más nueva a la más vieja) y `"archivo": "archivo.json"`.
- `archivo.json` → `{"editions": [...]}` con las ediciones más viejas (misma forma). La página lo carga después de mostrar la portada.
- `ediciones/<N>/`: una página estática por edición, generada desde el JSON. Es la URL que se comparte y la que Google indexa.
- El JS del sitio genera solo: portada, archivo, «Infografías y videos», enlaces `#ed-232-c3` y el NewsArticle para Google. **No edites el JS ni el HTML para publicar contenido.**

## Forma de una edición (contrato)

```json
{
  "number": 233,
  "date": "1 de diciembre, 2026",
  "tags": ["Chile", "Venezuela", "EE.UU."],
  "portada": { "tag", "headline", "body", "stat", "source", "date", "analysis", "index": "01 / 10" },
  "capsulas": [ ... ],
  "indicators": { "items": [ {"label": "Dólar", "value": "$1.033,78", "note": "Cierre · 27 nov"} ], "source": "Fuentes: ..." },
  "video": "5min-economia-233-resumen.mp4",          // opcional
  "videoPoster": "5min-economia-233-video-portada.jpg" // opcional, va junto a video
}
```

- `date`: exactamente `D de mes, AAAA` (Google lo convierte a fecha ISO).
- `portada`: copia de la cápsula 1 (`headline` = `title`, mismo `body`, `stat`, `source`, `date`, `analysis`). Su `index` lleva espacios: `"01 / 10"`.
- `tags`: los temas de las cápsulas en orden de aparición, sin repetir, **sin** las secciones fijas (Infografía, Sitios de interés, Cierre, Video recomendado, Evento).
- `index` de cada cápsula: `"NN/TT"` sin espacios, con dos dígitos, consecutivo, y `TT` = total de cápsulas.

## Tipos de cápsula y orden

| type | Campos | Dónde va |
|---|---|---|
| `stat` | tag, title, body, stat{value, direction up/down, label}, source, date, analysis | Primero, las noticias (Chile → Venezuela → resto de Latam → EE.UU./Global) |
| `image` | tag `"Infografía"`, title, body, image (`*-web.jpg`), alt, source, date | Después de las noticias — ver skill `agregar-multimedia` |
| `youtube` | tag `"Video recomendado"`, youtube (id), channel, title, body, source, date | Antes de Sitios de interés |
| `video` | tag `"Evento"`, title, body, video, poster, items, note, source, date | Antes de Sitios de interés |
| `links` | tag `"Sitios de interés"`, title, body, links[{name, url, note}], source `"5 min. de economía"`, date | Penúltima |
| `quote` | tag `"Cierre"`, quote, author, source_label, source `"5 min. de economía"`, date | Siempre la última |

## Estilo editorial (lo que el lector espera)

- `body`: el hecho con cifras exactas, fecha y fuente. 3–5 oraciones. Español neutro latinoamericano, números con formato chileno (`$1.046,4`, `11,7%`, `US$5,31`).
- `analysis`: «por qué te afecta», tuteando, con un consejo concreto para el bolsillo. Sin recomendar instrumentos financieros específicos.
- `source`: medio u organismo real («INE vía BioBioChile»). **Nunca inventes cifras ni fuentes**: si no puedes verificar un dato, pregúntale al usuario.
- `stat.label`: qué mide la cifra · fecha (contexto).

## Pasos

1. Inserta la edición nueva **al inicio** de `editions` en `index.html` (justo después de `"editions": [`). Edita con un script Python que cargue y vuelva a escribir el bloque JSON con `json.dumps(..., ensure_ascii=False, indent=2)` sangrado igual que el archivo, o con Edit; nunca con `sed`.
2. Si quedan más de 6 ediciones en `index.html`, mueve las más viejas al **inicio** de `archivo.json` (orden descendente).
3. Genera las páginas propias: `python3 .claude/skills/nueva-edicion/scripts/generar_ediciones.py`. Crea o actualiza `ediciones/<N>/index.html` y `ediciones/<N>/og.jpg` (la vista previa de WhatsApp/X/Facebook) para **todas** las ediciones, y reescribe `sitemap.xml`. **No edites esos archivos a mano**: se sobrescriben. Córrelo después de **cualquier** cambio en `index.html` o `archivo.json`, también en correcciones.
4. Valida: `python3 .claude/skills/nueva-edicion/scripts/validar_sitio.py`. Debe terminar con **0 errores**. Revisa los avisos de `index.html` (los de `archivo.json` son de formato antiguo). Abre `ediciones/<N>/og.jpg` y confirma que el titular y la cifra se leen bien.
5. Mira la página: `python3 -m http.server 8000` y ábrela con Playwright en escritorio (1280 px) y celular (390 px). Revisa que la portada no se corte y que el modal de cada cápsula abra.
6. Commit (incluye `ediciones/`) con el formato del repo: `Edición 233 (1 dic 2026): nueva edición y sitemap`. Para cambios posteriores: `Edición 233: <qué cambió>`.

## Agregar o quitar una cápsula en una edición ya publicada

Renumera **todos** los `index` de esa edición y el de la portada (`TT` cambia). Es el error más común: el validador lo detecta.

## Errores comunes

| Error | Arreglo |
|---|---|
| `index` desfasado tras insertar una cápsula | Renumera todo; corre el validador |
| Portada distinta de la cápsula 1 | Cópiala de nuevo desde la cápsula 1 |
| JSON roto por comillas tipográficas o coma final | Usa `«»` dentro de textos o escapa `\"`; el validador avisa |
| Olvidar el sitemap o la página de la edición | Correr `generar_ediciones.py` |
| Editar ediciones viejas en `index.html` cuando están en `archivo.json` | Busca el número en ambos archivos |
