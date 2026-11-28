#!/usr/bin/env python3
"""Genera una página estática por edición (ediciones/<N>/index.html) y su imagen para compartir
(ediciones/<N>/og.jpg), y reescribe sitemap.xml.

Las ediciones viven como hash (#ed-232) en la portada, y Google no indexa lo que va después de «#».
Estas páginas le dan a cada edición su propia URL, con título, descripción, vista previa para
WhatsApp/X/Facebook y datos NewsArticle, sin JavaScript.

Uso (desde la raíz del repo):  python3 .claude/skills/nueva-edicion/scripts/generar_ediciones.py
Se corre después de cada cambio en index.html o archivo.json. Es idempotente.
"""
import html
import json
import os
import re
import sys

SITE = "https://5min-deconomia.github.io/"
RAIZ = os.getcwd()
AQUI = os.path.dirname(os.path.abspath(__file__))
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
FAVICON = ""
FLECHA = {"down": "↓", "flat": "→"}


def e(s):
    return html.escape("" if s is None else str(s), quote=True)


def iso(fecha):
    m = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+),?\s+(\d{4})", fecha or "", re.I)
    if not m or m.group(2).lower() not in MESES:
        return None
    return f"{m.group(3)}-{MESES[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"


def corta(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def cargar():
    h = open(os.path.join(RAIZ, "index.html"), encoding="utf-8").read()
    data = json.loads(re.search(r'<script type="application/json" id="site-data">(.*?)</script>', h, re.S).group(1))
    viejas = json.load(open(os.path.join(RAIZ, data.get("archivo", "archivo.json")), encoding="utf-8"))["editions"]
    eds = data["editions"] + viejas
    eds.sort(key=lambda x: x["number"], reverse=True)
    global FAVICON
    m = re.search(r'<link rel="icon"[^>]*>', h)
    FAVICON = m.group(0) if m else ""
    return eds


# ---------- imagen para compartir (1200x630) ----------

def og_imagen(ed, destino):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    W, H = 1200, 630
    img = Image.new("RGB", (W, H))
    px = img.load()
    a, b = (0x5C, 0x0E, 0x17), (0x25, 0x04, 0x08)
    for y in range(H):
        for x in range(W):
            t = min(1, (x * 0.35 + y) / (W * 0.35 + H))
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    d = ImageDraw.Draw(img)

    def fuente(nombre, tam, peso):
        f = ImageFont.truetype(os.path.join(AQUI, "fuentes", nombre), tam)
        try:
            f.set_variation_by_axes([peso])
        except Exception:
            pass
        return f

    brass, parch, coral = (200, 162, 74), (241, 231, 214), (217, 118, 90)
    p = ed["portada"]
    st = p.get("stat") or {}
    # marca y número
    d.text((72, 58), "5 min. de Economía", font=fuente("PlayfairDisplay.ttf", 34, 700), fill=parch)
    kick = f"EDICIÓN N.º {ed['number']}  ·  {ed['date'].upper()}"
    d.text((72, 112), kick, font=fuente("SpaceGrotesk.ttf", 22, 600), fill=brass)
    d.line((72, 156, 300, 156), fill=brass, width=2)
    # titular, con ajuste de tamaño para que quepa en 4 líneas
    ancho = 1056 if not st.get("value") else 760
    for tam in (58, 52, 46, 40, 36):
        f = fuente("PlayfairDisplay.ttf", tam, 700)
        lineas, linea = [], ""
        for pal in p["headline"].split():
            prueba = (linea + " " + pal).strip()
            if d.textlength(prueba, font=f) <= ancho:
                linea = prueba
            else:
                lineas.append(linea)
                linea = pal
        lineas.append(linea)
        if len(lineas) <= 4:
            break
    y = 190
    for ln in lineas[:4]:
        d.text((72, y), ln, font=f, fill=parch)
        y += int(tam * 1.22)
    # cifra destacada a la derecha
    if st.get("value"):
        fv = fuente("PlayfairDisplay.ttf", 84, 700)
        val = st["value"]
        while d.textlength(val, font=fv) > 258 and fv.size > 40:
            fv = fuente("PlayfairDisplay.ttf", fv.size - 6, 700)
        d.text((870, 230), val, font=fv, fill=coral)
        d.text((870, 230 + fv.size + 18), FLECHA.get(st.get("direction"), "↑"),
               font=fuente("SpaceGrotesk.ttf", 48, 600), fill=coral)
    d.text((72, 560), "La economía, explicada en el tiempo que dura tu café.",
           font=fuente("PlayfairDisplay.ttf", 26, 500), fill=(241, 231, 214))
    d.text((1128, 566), "5min-deconomia.github.io", font=fuente("SpaceGrotesk.ttf", 20, 500), fill=brass, anchor="ra")
    img.save(destino, "JPEG", quality=86, optimize=True, progressive=True)
    return True


# ---------- HTML ----------

def capsula(c, k, n):
    t = c.get("type")
    idx = f'<span class="idx">{e(c.get("index", ""))}</span>'
    cab = f'<div class="cap-head"><span class="tag">{e(c.get("tag"))}</span>{idx}</div>'
    pie = f'<p class="src">Fuente: {e(c.get("source"))} · {e(c.get("date"))}</p>' if c.get("source") else ""
    cuerpo = ""
    if t == "quote":
        cuerpo = (f'<blockquote><p>«{e(c.get("quote"))}»</p><footer><strong>{e(c.get("author"))}</strong>'
                  f'{" · " + e(c.get("source_label")) if c.get("source_label") else ""}</footer></blockquote>')
        return f'<article class="cap cap-quote" id="c{k}">{cab}{cuerpo}</article>'
    titulo = f'<h2>{e(c.get("title"))}</h2>'
    cuerpo += f'<p>{e(c.get("body"))}</p>' if c.get("body") else ""
    if t == "stat" and c.get("stat"):
        s = c["stat"]
        cuerpo += (f'<div class="stat"><span class="v">{e(s.get("value"))}</span> '
                   f'<span class="arrow" aria-hidden="true">{FLECHA.get(s.get("direction"), "↑")}</span>'
                   f'<span class="l">{e(s.get("label"))}</span></div>')
    if c.get("analysis"):
        cuerpo += f'<div class="analysis"><span>Breve lectura</span><p>{e(c["analysis"])}</p></div>'
    if t == "image" and c.get("image"):
        mini = re.sub(r"-web\.jpg$", "-mini.jpg", c["image"])
        if not os.path.isfile(os.path.join(RAIZ, mini)):
            mini = c["image"]
        cuerpo += (f'<a class="infog" href="../../{e(c["image"])}"><img src="../../{e(mini)}" alt="{e(c.get("alt") or c.get("title"))}" '
                   f'loading="lazy" width="560" height="700"><span>Ver la infografía en tamaño completo</span></a>')
    if t == "links":
        cuerpo += "<ul class=\"links\">" + "".join(
            f'<li><a href="{e(l.get("url"))}" rel="noopener">{e(l.get("name"))}</a> <span>{e(l.get("note"))}</span></li>'
            for l in c.get("links", [])) + "</ul>"
    if t == "youtube" and c.get("youtube"):
        cuerpo += (f'<p><a class="btn" href="https://www.youtube.com/watch?v={e(c["youtube"])}" rel="noopener">'
                   f'Ver en YouTube · {e(c.get("channel"))}</a></p>')
    if t == "video" and c.get("video"):
        cuerpo += (f'<video src="../../{e(c["video"])}" poster="../../{e(c.get("poster"))}" controls playsinline preload="none"></video>')
        if c.get("items"):
            cuerpo += "<ul class=\"items\">" + "".join(f"<li>{e(i)}</li>" for i in c["items"]) + "</ul>"
        if c.get("note"):
            cuerpo += f'<p class="note">{e(c["note"])}</p>'
    return f'<article class="cap cap-{e(t)}" id="c{k}">{cab}{titulo}{cuerpo}{pie}</article>'


CSS = """
:root{--wine:#5C0E17;--wine-deep:#3A070E;--parchment:#F1E7D6;--parch-dim:rgba(241,231,214,.72);--brass:#C8A24A;--brass-dim:rgba(200,162,74,.35);--coral:#D9765A;--ink:#151010;--line:rgba(241,231,214,.16)}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--ink);color:var(--parchment);font:16px/1.65 'Space Grotesk',system-ui,sans-serif}
a{color:var(--brass)}a:focus-visible,.btn:focus-visible{outline:2px solid var(--parchment);outline-offset:2px}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
header.top{background:#0b0909;border-bottom:1px solid var(--line)}
header.top .wrap{display:flex;justify-content:space-between;align-items:center;min-height:64px;gap:12px}
.brand{font:italic 700 20px 'Playfair Display',Georgia,serif;color:var(--parchment);text-decoration:none}
.top nav a{font-size:12px;letter-spacing:.14em;text-transform:uppercase;text-decoration:none;margin-left:16px}
.hero{background:linear-gradient(155deg,var(--wine) 0%,var(--wine-deep) 62%,#250408 100%);padding:40px 0 32px;border-bottom:1px solid var(--brass-dim)}
.kicker{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--brass)}
h1{font:700 clamp(30px,6vw,46px)/1.15 'Playfair Display',Georgia,serif;margin:12px 0 14px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 0;padding:0;list-style:none}
.chips li{font-size:11px;letter-spacing:.12em;text-transform:uppercase;border:1px solid var(--brass-dim);border-radius:99px;padding:4px 12px;color:var(--parch-dim)}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.btn{display:inline-block;padding:12px 18px;border:1px solid var(--brass);color:var(--parchment);text-decoration:none;font-weight:600;font-size:14px;border-radius:2px}
.btn.primary{background:var(--brass);color:var(--ink)}
.ind{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:28px 0 0;padding:16px 0 0;border-top:1px solid var(--line)}
.ind div{border-left:2px solid var(--brass-dim);padding:2px 12px}.ind b{display:block;font:600 20px 'Playfair Display',Georgia,serif}
.ind small{display:block;font-size:12px;color:var(--parch-dim)}.ind .k{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--parch-dim)}
.indsrc{font-size:12px;color:rgba(241,231,214,.55);margin:10px 0 0}
main{padding:24px 0 48px}
.cap{background:linear-gradient(155deg,var(--wine) 0%,var(--wine-deep) 68%,#250408 100%);border:1px solid var(--brass-dim);border-radius:6px;padding:24px clamp(18px,4vw,32px);margin:18px 0;scroll-margin-top:16px}
.cap:target{border-color:var(--brass);box-shadow:0 0 0 2px var(--brass)}
.cap-head{display:flex;justify-content:space-between;align-items:center}
.tag{background:var(--brass);color:var(--ink);font-size:12px;font-weight:700;padding:3px 12px;border-radius:99px}
.idx{font-size:12px;letter-spacing:.12em;color:var(--parch-dim)}
.cap h2{font:700 clamp(22px,4.4vw,28px)/1.25 'Playfair Display',Georgia,serif;margin:14px 0 10px}
.cap p{margin:0 0 12px;color:var(--parch-dim)}
.stat{margin:16px 0;padding-top:14px;border-top:1px solid var(--line)}
.stat .v{font:700 clamp(36px,8vw,52px)/1 'Playfair Display',Georgia,serif;color:var(--coral)}
.stat .arrow{font-size:28px;color:var(--coral)}.stat .l{display:block;font-size:13px;color:var(--parch-dim);margin-top:6px}
.analysis{border-left:3px solid var(--brass);background:rgba(21,16,16,.35);padding:14px 18px;margin:16px 0}
.analysis span{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--brass)}.analysis p{margin:6px 0 0;color:var(--parchment)}
.src{font-size:12px!important;letter-spacing:.04em;margin-top:16px!important;color:rgba(241,231,214,.6)!important}
.infog{display:block;text-decoration:none}.infog img{display:block;width:100%;max-width:420px;height:auto;border-radius:4px;margin:8px 0}
.links{padding-left:18px}.links li{margin:6px 0}.links span{color:var(--parch-dim);font-size:14px}
video{width:100%;max-width:360px;border-radius:8px;border:1px solid var(--brass-dim);background:#000;display:block;margin:10px 0}
.items{font-size:14px;color:var(--parch-dim);padding-left:18px}
blockquote{margin:16px 0 0;font:italic 600 clamp(20px,4vw,26px)/1.35 'Playfair Display',Georgia,serif}
blockquote p{color:var(--parchment)!important}blockquote footer{font:14px 'Space Grotesk',system-ui,sans-serif;color:var(--parch-dim)}
nav.eds{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:24px;margin-top:32px}
footer.site{border-top:1px solid var(--line);padding:24px 0 40px;font-size:13px;color:var(--parch-dim)}
"""


def pagina(ed, prev, sig):
    n = ed["number"]
    p = ed["portada"]
    url = f"{SITE}ediciones/{n}/"
    titulo = f'{p["headline"]} — 5 min. de Economía, edición {n}'
    desc = corta(p.get("body"), 158)
    fecha = iso(ed.get("date"))
    og = f"{url}og.jpg" if os.path.isfile(os.path.join(RAIZ, "ediciones", str(n), "og.jpg")) else f"{SITE}5min-economia-og.png"
    ld = {
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": corta(p["headline"], 110), "description": desc, "url": url, "mainEntityOfPage": url,
        "image": [og], "inLanguage": "es",
        "author": {"@type": "Person", "name": "Rafael Jerez"},
        "publisher": {"@type": "NewsMediaOrganization", "name": "5 min. de Economía", "url": SITE,
                      "logo": {"@type": "ImageObject", "url": f"{SITE}5min-economia-og.png"}},
        "isPartOf": {"@type": "CreativeWorkSeries", "name": "5 min. de Economía", "url": SITE},
        "articleSection": "Economía", "keywords": ", ".join(ed.get("tags", [])),
    }
    if fecha:
        ld["datePublished"] = ld["dateModified"] = fecha
    ind = ed.get("indicators") or {}
    ind_html = ""
    if ind.get("items"):
        ind_html = '<div class="ind" aria-label="Indicadores de la edición">' + "".join(
            f'<div><span class="k">{e(x.get("label"))}</span><b>{e(x.get("value"))}</b><small>{e(x.get("note"))}</small></div>'
            for x in ind["items"]) + "</div>"
        if ind.get("source"):
            ind_html += f'<p class="indsrc">{e(ind["source"])}</p>'
    caps = "\n".join(capsula(c, k, len(ed["capsulas"])) for k, c in enumerate(ed["capsulas"], 1))
    nav = '<nav class="eds" aria-label="Otras ediciones">'
    nav += f'<a href="../{sig["number"]}/">← Edición {sig["number"]} (anterior)</a>' if sig else "<span></span>"
    nav += f'<a href="../{prev["number"]}/">Edición {prev["number"]} (siguiente) →</a>' if prev else f'<a href="../../#archivo">Todas las ediciones →</a>'
    nav += "</nav>"
    video = ""
    if ed.get("video"):
        video = (f'<article class="cap" id="video"><div class="cap-head"><span class="tag">Video</span></div>'
                 f'<h2>Resumen de la edición {n}</h2><video src="../../{e(ed["video"])}" '
                 f'poster="../../{e(ed.get("videoPoster"))}" controls playsinline preload="none"></video></article>')
    tags = "".join(f"<li>{e(t)}</li>" for t in ed.get("tags", []))
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://gc.zgo.at; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: https:; media-src 'self'; connect-src 'self' https://5mindeconomia.goatcounter.com; object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:locale" content="es_LA">
<meta property="og:site_name" content="5 min. de Economía">
<meta property="og:title" content="{e(p['headline'])}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
{f'<meta property="article:published_time" content="{fecha}">' if fecha else ''}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@5Deconomia">
<meta name="twitter:title" content="{e(p['headline'])}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{og}">
<meta name="theme-color" content="#3A070E">
{FAVICON}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,600;1,700&family=Space+Grotesk:wght@400;600;700&display=swap">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="../../">5 min. de Economía</a>
<nav><a href="../../#archivo">Archivo</a><a href="../../#seguir">Seguir</a></nav></div></header>
<section class="hero"><div class="wrap">
<span class="kicker">Edición N.º {n} · {e(ed.get('date'))}</span>
<h1>{e(p['headline'])}</h1>
<ul class="chips" aria-label="Temas">{tags}</ul>
<div class="cta"><a class="btn primary" href="../../#ed-{n}">Ver en la página interactiva</a><a class="btn" href="../../#seguir">Seguir la cápsula</a></div>
{ind_html}
</div></section>
<main><div class="wrap">
{caps}
{video}
{nav}
</div></main>
<footer class="site"><div class="wrap">5 min. de Economía · La economía, explicada en el tiempo que dura tu café. · <a href="../../">Ir a la portada</a></div></footer>
<script data-goatcounter="https://5mindeconomia.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""


def sitemap(eds):
    hoy = iso(eds[0]["date"]) if eds else None
    filas = [f"  <url>\n    <loc>{SITE}</loc>\n" + (f"    <lastmod>{hoy}</lastmod>\n" if hoy else "") +
             "    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>"]
    for ed in eds:
        f = iso(ed["date"])
        filas.append(f"  <url>\n    <loc>{SITE}ediciones/{ed['number']}/</loc>\n" +
                     (f"    <lastmod>{f}</lastmod>\n" if f else "") + "    <priority>0.8</priority>\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(filas) + "\n</urlset>\n")


def main():
    eds = cargar()
    for i, ed in enumerate(eds):
        carpeta = os.path.join(RAIZ, "ediciones", str(ed["number"]))
        os.makedirs(carpeta, exist_ok=True)
        og_imagen(ed, os.path.join(carpeta, "og.jpg"))
        prev = eds[i - 1] if i > 0 else None          # más nueva
        sig = eds[i + 1] if i + 1 < len(eds) else None  # más vieja
        with open(os.path.join(carpeta, "index.html"), "w", encoding="utf-8") as f:
            f.write(pagina(ed, prev, sig))
    with open(os.path.join(RAIZ, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap(eds))
    print(f"{len(eds)} páginas en ediciones/ y sitemap.xml actualizado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
