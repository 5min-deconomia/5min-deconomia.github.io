---
name: agregar-multimedia
description: Use when adding or replacing an infographic, a summary video, a poster image, a YouTube recommendation or an event video on 5 min. de Economía — "infografía", "video resumen", "portada del video", "comprime el video", "la imagen pesa mucho", "evento".
---

# Infografías y videos en 5 min. de Economía

Los archivos van en la **raíz** del repo. Nombres siempre en minúsculas, sin tildes, con guiones:
`5min-economia-<tema>-<alcance>[-<año>]-web.jpg`, `5min-economia-<N>-resumen.mp4`.

## Infografía (cápsula `image`)

1. **Imágenes** (desde el original que entrega el usuario):
   ```bash
   # versión web: ancho 2160 px como máximo, JPG calidad 85, sin metadatos
   convert original.png -resize '2160x>' -strip -interlace Plane -quality 85 5min-economia-bigmac-latam-web.jpg
   # miniatura obligatoria: 560x700 (4:5), recortada desde arriba
   convert 5min-economia-bigmac-latam-web.jpg -resize 560x -gravity north -crop 560x700+0+0 +repage -strip -quality 82 5min-economia-bigmac-latam-mini.jpg
   ```
   La página muestra la `-mini.jpg` en las grillas y abre la `-web.jpg` en el modal. Sin miniatura, cada lector descarga ~1 MB extra. Objetivo: web < 1 MB, mini < 90 KB.
2. **Cápsula**, antes de «Sitios de interés»:
   ```json
   {
     "tag": "Infografía", "type": "image",
     "title": "¿Cuánto cuesta un Big Mac en Latinoamérica?",
     "body": "2–3 oraciones con la conclusión y la cifra de Chile.",
     "image": "5min-economia-infografia-bigmac-latam-web.jpg",
     "alt": "Infografía: <tema>, <fecha>. <TODAS las cifras que muestra la imagen, país por país>.",
     "source": "The Economist, índice Big Mac (julio 2026); cálculo propio",
     "date": "jul 2026"
   }
   ```
   El `alt` transcribe todos los datos: es lo que leen los lectores de pantalla y Google.
3. Renumera los `index` de la edición y la portada (`01 / TT`) — ver skill `nueva-edicion`.
4. Valida con `python3 .claude/skills/nueva-edicion/scripts/validar_sitio.py`.
5. Commit: `Edición 232: infografía Big Mac en Latinoamérica`.

## Video resumen de la edición

Formato vertical 1080×1920. Comprime siempre antes de subir (los actuales pesan 2–6 MB):
```bash
ffmpeg -i entrada.mp4 -c:v libx264 -preset slow -crf 28 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
  -r 30 -c:a aac -b:a 96k -movflags +faststart 5min-economia-233-resumen.mp4
# portada: un cuadro representativo (segundo 1), JPG < 150 KB
ffmpeg -ss 1 -i 5min-economia-233-resumen.mp4 -frames:v 1 -q:v 4 5min-economia-233-video-portada.jpg
```
`-movflags +faststart` hace que empiece a reproducirse antes de descargarse completo. Luego en la edición:
`"video": "5min-economia-233-resumen.mp4", "videoPoster": "5min-economia-233-video-portada.jpg"`.
No es una cápsula: aparece solo en «Infografías y videos».

## Otros

- **Video que no es de una edición** (promo, institucional): agrégalo a `multimedia.extraVideos` con `{ed, title, video, poster}`.
- **YouTube recomendado**: cápsula `youtube` con solo el id (`"X7C4f9CM_Mg"`), `channel` y un `body` que diga con qué cápsula se relaciona.
- **Evento** (con video propio): cápsula `video` con tag `"Evento"`, o una entrada en `eventos` (`id, tag, title, body, video, poster, link, linkLabel, source, date`). Quita los eventos ya realizados.

## Errores comunes

| Error | Arreglo |
|---|---|
| Subir el PNG original de 5 MB | Generar `-web.jpg` y `-mini.jpg` |
| Video sin `+faststart` | Recomprimir con el comando de arriba |
| `alt` genérico («infografía del Big Mac») | Transcribir todas las cifras |
| Reemplazar una imagen manteniendo el nombre | El navegador puede mostrar la vieja: usa un nombre nuevo (p. ej. `-2025`) y actualiza el JSON |
