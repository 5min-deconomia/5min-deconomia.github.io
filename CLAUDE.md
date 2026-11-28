# 5 min. de Economía

Sitio estático (GitHub Pages, sin build). El contenido vive en JSON: `index.html` (`<script id="site-data">`, las 6 ediciones más recientes) y `archivo.json` (las anteriores).

- Publicar o corregir ediciones: skill `nueva-edicion`.
- Infografías, videos, portadas y eventos: skill `agregar-multimedia`.
- Antes de cada commit: `python3 .claude/skills/nueva-edicion/scripts/validar_sitio.py` (0 errores).
- Commits en español: `Edición 233 (1 dic 2026): …` / `Edición 233: …`.
