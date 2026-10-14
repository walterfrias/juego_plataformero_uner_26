#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_trees.py  —  2 variedades de árbol para la calle / costanera del N1.
Decoración (sin comportamiento). Paleta noche.

Son árboles DISTINTOS: no comparten paleta.
  ArbolBajo.png   42x44  — árbol de plaza podado. Copa redonda y baja.
                           Follaje oliva/verde cálido.
  ArbolAlto.png   48x82  — árbol alto. Copa GRANDE, REDONDA y SIMÉTRICA.
                           Follaje verde-azulado frío.

Ambos con volumen: luz de luna arriba-izquierda, sombra abajo-derecha,
panza en sombra y sombra proyectada de la copa sobre el tronco.

Pie al ras del borde inferior: se coloca con  y = alturaPiso - altoSprite.
Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_trees.py
"""
from PIL import Image, ImageDraw
import random
import os

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)

RIM = (18, 22, 30, 255)
LIGHT_DIR = (-0.60, -0.72)   # de dónde viene la luz (arriba-izquierda)

# --- ArbolBajo: oliva / verde cálido ---
BAJO = dict(
    base=(54, 64, 44, 255), dark=(40, 48, 32, 255), xdark=(28, 34, 22, 255),
    light=(84, 92, 60, 255), xlight=(112, 118, 80, 255),
    bark=(58, 48, 38, 255), bark_l=(82, 68, 54, 255), bark_d=(38, 30, 24, 255),
)
# --- ArbolAlto: verde-azulado / frío ---
ALTO = dict(
    base=(38, 58, 56, 255), dark=(26, 42, 42, 255), xdark=(18, 30, 30, 255),
    light=(58, 86, 82, 255), xlight=(88, 116, 110, 255),
    bark=(48, 44, 48, 255), bark_l=(72, 66, 68, 255), bark_d=(30, 28, 32, 255),
)


def _outline(img):
    px = img.load()
    w, h = img.size
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128 and px[nx, ny] != RIM:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = RIM


def _lobes(d, lobes, color):
    for cx, cy, r in lobes:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def _shade_crown(img, cx, cy, rx, ry, pal, seed):
    """Sombreado de volumen sobre el follaje ya pintado (color pal['base'])."""
    px = img.load()
    w, h = img.size
    lx, ly = LIGHT_DIR
    for y in range(h):
        for x in range(w):
            if px[x, y][:3] != pal["base"][:3]:
                continue
            nx = (x - cx) / rx
            ny = (y - cy) / ry
            edge = nx * nx + ny * ny          # 0 centro .. ~1 borde
            dot = nx * lx + ny * ly           # >0 hacia la luz (arriba-izq)
            c = pal["base"]
            if ny > 0.50 or (dot < -0.15 and edge > 0.28):
                c = pal["dark"]               # abajo / lado en sombra
            if dot < -0.50 and edge > 0.42:
                c = pal["xdark"]              # canto en sombra fuerte
            if ny > 0.70:
                c = pal["xdark"]              # panza / cara de abajo
            if dot > 0.28 and edge > 0.16:
                c = pal["light"]              # zona iluminada (arriba-izq)
            if dot > 0.58 and edge > 0.40:
                c = pal["xlight"]             # brillo del canto
            px[x, y] = c
    # textura mínima: unos grumos, sin romper el volumen
    rnd = random.Random(seed)
    for _ in range(70):
        x, y = rnd.randrange(w), rnd.randrange(h)
        p = px[x, y]
        if p == pal["base"] and rnd.random() < 0.5:
            px[x, y] = pal["dark"] if rnd.random() < 0.5 else pal["light"]


def _trunk(d, cx, y0, y1, half_top, half_bot, pal):
    d.polygon([(cx - half_bot, y1), (cx + half_bot, y1),
               (cx + half_top, y0), (cx - half_top, y0)], fill=pal["bark"])
    d.line([(cx - half_top + 1, y1 - 1), (cx - half_top + 1, y0)], fill=pal["bark_l"])
    d.line([(cx + half_top - 1, y1 - 1), (cx + half_top - 1, y0)], fill=pal["bark_d"])
    d.point([(cx - half_bot, y1), (cx + half_bot, y1)], fill=pal["bark_d"])


def _cast_shadow_on_trunk(img, cx, y0, half, pal):
    """Sombra de la copa sobre los primeros px del tronco."""
    px = img.load()
    for y in range(y0, y0 + 7):
        for x in range(cx - half, cx + half + 1):
            if 0 <= x < img.size[0] and 0 <= y < img.size[1] and px[x, y][:3] == pal["bark"][:3]:
                px[x, y] = pal["bark_d"]


def arbol_bajo():
    w, h = 42, 44
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = 21
    _trunk(d, cx, 26, h - 1, 3, 5, BAJO)
    # copa redonda y baja: elipse + un lóbulo centrado arriba (simétrico)
    cy, rx, ry = 16, 17, 13
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=BAJO["base"])
    _lobes(d, [(cx, 8, 8)], BAJO["base"])
    _shade_crown(img, cx, cy, rx, ry + 2, BAJO, seed=11)
    _cast_shadow_on_trunk(img, cx, 26, 3, BAJO)
    _outline(img)
    img.save(f"{OUT}/ArbolBajo.png")


def arbol_alto():
    w, h = 48, 82
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = 24
    _trunk(d, cx, 44, h - 1, 3, 6, ALTO)
    # copa GRANDE, REDONDA y SIMÉTRICA: una sola elipse + remate centrado arriba
    cy, rx, ry = 27, 21, 25
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=ALTO["base"])
    _lobes(d, [(cx, 10, 10)], ALTO["base"])
    _shade_crown(img, cx, cy, rx, ry, ALTO, seed=7)
    _cast_shadow_on_trunk(img, cx, 44, 3, ALTO)
    _outline(img)
    img.save(f"{OUT}/ArbolAlto.png")


def main():
    arbol_bajo()
    arbol_alto()
    a, b = Image.open(f"{OUT}/ArbolBajo.png"), Image.open(f"{OUT}/ArbolAlto.png")
    sheet = Image.new("RGBA", (a.width + b.width + 12, max(a.height, b.height) + 4), (16, 20, 40, 255))
    sheet.alpha_composite(a, (4, sheet.height - a.height - 2))
    sheet.alpha_composite(b, (a.width + 8, sheet.height - b.height - 2))
    sheet.save(f"{OUT}/_trees_contact.png")
    print(f"ArbolBajo {a.size}  |  ArbolAlto {b.size}  ->  {OUT}/")


if __name__ == "__main__":
    assert os.path.isdir("game/assets"), "corré desde la raíz del repo"
    main()
