#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_n1_platforms.py  —  elementos de plataformeo diegéticos del Nivel 1
(calle / costanera). Mobiliario urbano porteño con colisión, se resuelven
sólo con saltar + stomp (sin trepar / dash / doble salto).

Genera en game/assets/N1/:
  BancoPlaza.png     28x15  — banco de plaza (hierro + tablas). Jumpthru.
  Toldo.png          46x34  — puesto de feria entero (columnas + mesada + hule
                              + techo) en 1 sprite. Sólo el techo (~5px de
                              arriba) tiene colisión jumpthru; el resto es
                              decoración y el player lo atraviesa.
  FarolRepisa.png    12x4   — ménsula de hierro del farol. Atravesable.
  Colchon.png        30x10  — colchón tirado en la vereda. Sólido + rebote.

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_n1_platforms.py
"""
from PIL import Image, ImageDraw
import os

OUT = "game/assets/N1"
os.makedirs(OUT, exist_ok=True)

OUTL = (20, 22, 32, 255)
IRON = (46, 58, 54, 255)
IRON_HI = (68, 82, 76, 255)
IRON_DK = (30, 38, 36, 255)
WOOD = (104, 90, 70, 255)
WOOD_HI = (126, 110, 86, 255)
WOOD_DK = (78, 66, 50, 255)
CANVAS_A = (140, 82, 72, 255)     # lona toldo, franja A (rojo apagado)
CANVAS_B = (156, 148, 126, 255)   # franja B (crema sucio)
CANVAS_DK = (104, 60, 54, 255)
MATTRESS = (150, 148, 136, 255)
MATTRESS_HI = (168, 166, 154, 255)
MATTRESS_DK = (120, 118, 108, 255)
TICKING = (92, 104, 124, 255)     # rayas del colchón
STAIN = (96, 86, 66, 255)


def _outline(img, col=OUTL):
    px = img.load()
    w, h = img.size
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128 and px[nx, ny] != col:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = col


def _img(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def banco_plaza():
    w, h = 28, 15
    im, d = _img(w, h)
    # patas / apoyabrazos de hierro en las puntas
    for ex in (2, w - 5):
        d.rectangle([ex, 3, ex + 2, h - 1], fill=IRON)
        d.rectangle([ex, 3, ex, h - 1], fill=IRON_HI)
        d.line([(ex, 3), (ex + 4, 1), (ex + 3, 4)], fill=IRON)          # voluta del apoyabrazo
    d.rectangle([2, h - 2, w - 3, h - 1], fill=IRON_DK)                 # travesaño bajo
    # tablas del asiento (superficie sólida arriba)
    for ty, c in ((2, WOOD_HI), (4, WOOD), (6, WOOD_DK)):
        d.rectangle([4, ty, w - 5, ty + 1], fill=c)
    # respaldo
    for ty, c in ((8, WOOD), (10, WOOD_DK)):
        d.rectangle([5, ty, w - 6, ty + 1], fill=c)
    _outline(im)
    im.save(f"{OUT}/BancoPlaza.png")


# Franja superior del sprite del Toldo que SÍ tiene colisión (el resto es
# sólo dibujo — el player lo atraviesa). Ver ROOF_MASK_H en el wire.
ROOF_MASK_H = 5


def toldo():
    """Puesto de feria entero en UN solo sprite: columnas de metal + mesada
    con hule + cajón + techo de lona rayado. UN objeto.
    Sólo el techo (los primeros ~5 px) lleva colisión (jumpthru) — la
    estructura de abajo es decoración, el player la cruza sin chocar.
    """
    w, h = 46, 34
    im, d = _img(w, h)

    # ---- estructura (decoración, sin colisión) ----
    # columnas: 2 atrás finas/oscuras (profundidad), 2 adelante
    for px in (8, w - 10):
        d.rectangle([px, 9, px + 1, h - 3], fill=IRON_DK)
    for px in (3, w - 5):
        d.rectangle([px, 8, px + 2, h - 1], fill=IRON)
        d.rectangle([px, 8, px, h - 1], fill=IRON_HI)
        d.rectangle([px - 1, h - 2, px + 3, h - 1], fill=IRON_DK)          # patita
    # cajón de fruta sobre la mesada
    d.rectangle([w - 18, 11, w - 9, 16], fill=WOOD)
    for fx in range(w - 16, w - 9, 2):
        d.point([(fx, 12), (fx, 13)], fill=(150, 96, 70, 255))
    # mesada: tablón + canto
    d.rectangle([2, 15, w - 3, 17], fill=WOOD_HI)
    d.rectangle([2, 17, w - 3, 18], fill=WOOD)
    d.rectangle([2, 18, w - 3, 19], fill=WOOD_DK)
    # hule / mantel rayado colgando del frente
    hem = 30
    d.rectangle([4, 19, w - 5, hem], fill=CANVAS_B)
    for sx in range(5, w - 5, 6):
        d.line([(sx, 19), (sx, hem)], fill=CANVAS_A)
    for sx in range(4, w - 5, 3):                                          # ruedo ondulado
        d.polygon([(sx, hem), (sx + 3, hem), (sx + 1, hem + 2)], fill=CANVAS_DK)

    # ---- techo de lona (los ~5px de arriba llevan colisión) ----
    d.rectangle([0, 0, w - 1, 1], fill=IRON_HI)                            # caballete (se pisa)
    for sx in range(1, w - 1, 5):
        col = CANVAS_A if (sx // 5) % 2 == 0 else CANVAS_B
        d.polygon([(sx, 2), (sx + 5, 2), (sx + 5, 8), (sx, 8)], fill=col)
    d.rectangle([1, 2, w - 2, 3], fill=CANVAS_DK)
    for sx in range(1, w - 2, 4):                                          # faldón festoneado
        d.polygon([(sx, 8), (sx + 4, 8), (sx + 2, 10)], fill=CANVAS_DK)

    _outline(im)
    im.save(f"{OUT}/Toldo.png")


def farol_repisa():
    w, h = 12, 4
    im, d = _img(w, h)
    d.rectangle([0, 1, w - 1, 2], fill=IRON)
    d.rectangle([0, 0, w - 1, 0], fill=IRON_HI)
    d.rectangle([0, 3, w - 1, 3], fill=IRON_DK)
    d.line([(1, 3), (4, 1)], fill=IRON)                                # ménsula diagonal
    _outline(im)
    im.save(f"{OUT}/FarolRepisa.png")


def colchon():
    w, h = 30, 10
    im, d = _img(w, h)
    # cuerpo, panza hundida al medio
    d.polygon([(1, 2), (w - 2, 2), (w - 2, h - 1), (1, h - 1)], fill=MATTRESS)
    d.polygon([(1, 2), (w - 2, 2), (w - 2, 3), (1, 3)], fill=MATTRESS_HI)
    d.polygon([(6, 2), (w - 7, 2), (w - 9, 4), (8, 4)], fill=MATTRESS_DK)   # hundido
    # rayas de colchón
    for sx in range(4, w - 3, 6):
        d.line([(sx, 3), (sx, h - 2)], fill=TICKING)
    # botones / capitoné
    for bx in (7, 15, 23):
        d.point([(bx, 5)], fill=MATTRESS_DK)
    d.ellipse([w - 12, 6, w - 6, 9], fill=STAIN)                       # mancha
    _outline(im)
    im.save(f"{OUT}/Colchon.png")


def main():
    banco_plaza()
    toldo()
    farol_repisa()
    colchon()
    # hoja de contacto para revisar
    names = ["BancoPlaza", "Toldo", "FarolRepisa", "Colchon"]
    x = 2
    sheet = Image.new("RGBA", (sum(Image.open(f"{OUT}/{n}.png").width + 6 for n in names) + 4, 24),
                      (16, 20, 40, 255))
    for n in names:
        im = Image.open(f"{OUT}/{n}.png")
        sheet.alpha_composite(im, (x, 22 - im.height))
        x += im.width + 6
    sheet.save(f"{OUT}/_contact_sheet.png")
    print("N1 platforms ->", OUT)


if __name__ == "__main__":
    assert os.path.isdir("game/assets"), "corré desde la raíz del repo"
    main()
