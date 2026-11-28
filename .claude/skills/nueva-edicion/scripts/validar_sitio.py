#!/usr/bin/env python3
"""Valida los datos del sitio 5 min. de Economía antes de hacer commit.

Uso (desde la raíz del repo):  python3 .claude/skills/nueva-edicion/scripts/validar_sitio.py
Sale con código 1 si encuentra errores. Las advertencias no bloquean.
"""
import json
import os
import re
import sys

RAIZ = os.getcwd()
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
CAMPOS = {
    "stat": ["tag", "type", "title", "body", "stat", "source", "date", "analysis", "index"],
    "image": ["tag", "type", "title", "body", "image", "alt", "source", "date", "index"],
    "links": ["tag", "type", "title", "body", "links", "source", "date", "index"],
    "quote": ["tag", "type", "quote", "author", "source", "date", "index"],
    "youtube": ["tag", "type", "youtube", "title", "body", "source", "date", "index"],
    "video": ["tag", "type", "title", "body", "video", "poster", "source", "date", "index"],
}
NO_PAIS = {"Infografía", "Sitios de interés", "Cierre", "Video recomendado", "Evento"}
MAX_INLINE = 6

errores, avisos = [], []


def err(m):
    errores.append(m)


def aviso(m):
    avisos.append(m)


def existe(f, donde):
    if f and not os.path.isfile(os.path.join(RAIZ, f)):
        err(f"{donde}: no existe el archivo «{f}»")


def iso(fecha):
    m = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+),?\s+(\d{4})", fecha or "", re.I)
    if not m or m.group(2).lower() not in MESES:
        return None
    return f"{m.group(3)}-{MESES[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"


def revisar_edicion(ed, origen, estricto=True):
    # Las ediciones de archivo.json usan a veces un formato antiguo: solo avisan.
    global err
    err_real = err
    if not estricto:
        err = aviso
    try:
        _revisar(ed, origen)
    finally:
        err = err_real


def _revisar(ed, origen):
    n = ed.get("number")
    pre = f"[{origen}] edición {n}"
    if not iso(ed.get("date")):
        err(f"{pre}: fecha «{ed.get('date')}» no sigue el formato «27 de noviembre, 2026»")
    caps = ed.get("capsulas") or []
    total = len(caps)
    if not total:
        err(f"{pre}: no tiene cápsulas")
        return
    for i, c in enumerate(caps, 1):
        t = c.get("type")
        if t not in CAMPOS:
            err(f"{pre} cápsula {i}: tipo desconocido «{t}»")
            continue
        falta = [k for k in CAMPOS[t] if k not in c]
        if falta:
            err(f"{pre} cápsula {i} ({t}): faltan campos {falta}")
        esperado = f"{i:02d}/{total:02d}"
        if c.get("index") != esperado:
            err(f"{pre} cápsula {i}: index «{c.get('index')}», debería ser «{esperado}»")
        if t == "stat" and c.get("stat", {}).get("direction") not in ("up", "down", "flat", None):
            aviso(f"{pre} cápsula {i}: stat.direction «{c['stat'].get('direction')}» inusual")
        if t == "image":
            existe(c.get("image"), f"{pre} cápsula {i}")
            img = c.get("image") or ""
            if img.endswith("-web.jpg"):
                mini = img[:-8] + "-mini.jpg"
                if not os.path.isfile(os.path.join(RAIZ, mini)):
                    aviso(f"{pre} cápsula {i}: falta la miniatura «{mini}» (la página cargará la imagen pesada)")
            if len(c.get("alt", "")) < 80:
                aviso(f"{pre} cápsula {i}: el alt es muy corto; debe describir todas las cifras")
        if t == "video":
            existe(c.get("video"), f"{pre} cápsula {i}")
            existe(c.get("poster"), f"{pre} cápsula {i}")
    if caps[-1].get("type") != "quote":
        aviso(f"{pre}: la última cápsula no es la cita de «Cierre»")
    p = ed.get("portada")
    if not p:
        err(f"{pre}: falta portada")
    else:
        if p.get("index") != f"01 / {total:02d}":
            err(f"{pre}: portada.index «{p.get('index')}», debería ser «01 / {total:02d}»")
        c0 = caps[0]
        if p.get("headline") != c0.get("title") or p.get("body") != c0.get("body"):
            aviso(f"{pre}: la portada no coincide con la cápsula 1 (headline/title o body)")
    paises = []
    for c in caps:
        tg = c.get("tag")
        if tg not in NO_PAIS and tg not in paises:
            paises.append(tg)
    if ed.get("tags") != paises:
        aviso(f"{pre}: tags {ed.get('tags')} no coinciden con los temas de las cápsulas {paises}")
    if ed.get("video"):
        existe(ed["video"], pre)
        existe(ed.get("videoPoster"), pre)
    if not (ed.get("indicators") or {}).get("items"):
        aviso(f"{pre}: sin indicadores")


def main():
    html = open(os.path.join(RAIZ, "index.html"), encoding="utf-8").read()
    m = re.search(r'<script type="application/json" id="site-data">(.*?)</script>', html, re.S)
    if not m:
        print("ERROR: no encontré <script id=\"site-data\"> en index.html")
        return 1
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"ERROR: el JSON de site-data no es válido: {e}")
        return 1
    try:
        archivo = json.load(open(os.path.join(RAIZ, data.get("archivo", "archivo.json")), encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: archivo.json no se pudo leer: {e}")
        return 1

    inline = data.get("editions") or []
    viejas = archivo.get("editions") or []
    nums = [e.get("number") for e in inline]
    if nums != sorted(nums, reverse=True):
        err(f"index.html: las ediciones no están de la más nueva a la más vieja: {nums}")
    if len(set(nums) | {e.get('number') for e in viejas}) != len(nums) + len(viejas):
        err("una edición aparece a la vez en index.html y en archivo.json")
    if viejas and nums and max(e["number"] for e in viejas) >= min(nums):
        err("archivo.json tiene ediciones más nuevas que alguna de index.html")
    if len(inline) > MAX_INLINE:
        aviso(f"index.html tiene {len(inline)} ediciones; mueve las más viejas a archivo.json (máximo {MAX_INLINE})")

    for e in inline:
        revisar_edicion(e, "index.html")
    for e in viejas:
        revisar_edicion(e, "archivo.json", estricto=False)
    for v in (data.get("multimedia") or {}).get("extraVideos", []):
        existe(v.get("video"), "multimedia.extraVideos")
        existe(v.get("poster"), "multimedia.extraVideos")
    for ev in data.get("eventos") or []:
        existe(ev.get("video"), f"evento {ev.get('id')}")
        existe(ev.get("poster"), f"evento {ev.get('id')}")

    if inline:
        fecha = iso(inline[0].get("date"))
        sm = open(os.path.join(RAIZ, "sitemap.xml"), encoding="utf-8").read()
        lm = re.search(r"<lastmod>([^<]+)</lastmod>", sm)
        if fecha and (not lm or lm.group(1) < fecha):
            err(f"sitemap.xml: lastmod «{lm.group(1) if lm else '—'}» es anterior a la última edición ({fecha})")

    grandes = [f for f in os.listdir(RAIZ) if f.endswith(".mp4") and os.path.getsize(f) > 8 * 1024 * 1024]
    for f in grandes:
        aviso(f"{f} pesa más de 8 MB; comprímelo (ver skill agregar-multimedia)")

    for a in avisos:
        print("AVISO:", a)
    for e in errores:
        print("ERROR:", e)
    print(f"\n{len(inline)} ediciones en index.html, {len(viejas)} en archivo.json · "
          f"{len(errores)} errores, {len(avisos)} avisos")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
