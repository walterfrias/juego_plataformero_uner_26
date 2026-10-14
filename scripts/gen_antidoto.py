#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_antidoto.py  —  pickup del Nivel 1: vial de antídoto.

Diseño:
  - frasco de vidrio chico, cuerpo redondeado y cuello corto, tapón de
    corcho. Líquido verde fosforescente (mismo verde enfermizo del
    laboratorio / sign_lab.png: familia 120,200,140) lleno ~2/3, con
    menisco más claro y un par de burbujas que suben.
  - reflejo vertical de vidrio sobre el lado izquierdo.
  - se lee por silueta + color, no por animación fina.
  - 6 frames: bob de 2 px (sin) + un "glint" diagonal que barre el vidrio
    en 2 de los frames + burbujas que suben en loop.
  - ancla al centro (es un pickup flotante, no apoya en piso).

Crea (game/assets/UI/):
  antidoto_1..6.png    14x18  RGBA
  antidoto_sheet.png   84x18  referencia

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_antidoto.py
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/UI"
os.makedirs(OUT, exist_ok=True)

W, H = 14, 18
N = 6
T = (0, 0, 0, 0)

OUTL      = (26, 22, 34, 255)
GLASS     = (150, 176, 178, 90)      # vidrio, semitransparente
GLASS_HI  = (232, 244, 240, 235)     # reflejo
CORK      = (150, 108, 66, 255)
CORK_S    = (110, 78, 46, 255)
LIQ       = (96, 200, 128, 255)      # verde antídoto
LIQ_HI    = (168, 240, 176, 255)     # menisco / brillo
LIQ_S     = (52, 140, 92, 255)       # fondo del líquido
BUBBLE    = (208, 250, 210, 255)
GLOW      = (120, 220, 150, 70)      # halo tenue


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
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128 and px[nx, ny] != OUTL:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = OUTL


def frame(i):
    t = i / N
    ph = t * math.tau
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)

    bob = round(math.sin(ph) * 1.5)          # -1..1 -> flota
    cx = 7
    top = 3 + bob                            # y del hombro del frasco

    # ---- halo verde tenue ----
    d.ellipse([cx - 6, top + 1, cx + 5, top + 15], fill=GLOW)

    # ---- cuerpo de vidrio (cuello + panza redondeada) ----
    neck = [(cx - 2, top), (cx + 2, top), (cx + 2, top + 3), (cx - 2, top + 3)]
    body = [cx - 4, top + 3, cx + 4, top + 13]
    d.polygon(neck, fill=GLASS)
    d.ellipse(body, fill=GLASS)

    # ---- líquido: llena la panza ~2/3 desde abajo ----
    liq_top = top + 5
    d.ellipse([cx - 4, liq_top, cx + 4, top + 13], fill=LIQ)
    d.ellipse([cx - 4, top + 10, cx + 4, top + 13], fill=LIQ_S)      # poso más oscuro abajo
    d.ellipse([cx - 4, liq_top, cx + 4, liq_top + 2], fill=LIQ_HI)   # menisco
    d.point([(cx - 2, top + 8), (cx + 1, top + 10)], fill=LIQ_HI)    # brillos internos

    # ---- burbujas que suben (loop segun fase) ----
    for k, off in enumerate((0.0, 0.5)):
        bp = (t + off) % 1.0
        by = int(top + 12 - bp * 6)
        bx = cx - 1 + k * 2
        if by > liq_top:
            d.point([(bx, by)], fill=BUBBLE)

    # ---- tapon de corcho ----
    d.rectangle([cx - 2, top - 3, cx + 2, top], fill=CORK)
    d.rectangle([cx - 2, top - 3, cx + 2, top - 2], fill=CORK_S)
    d.rectangle([cx - 3, top - 1, cx + 3, top], fill=CORK_S)         # borde saliente

    # ---- reflejo de vidrio (lado izq) ----
    d.line([(cx - 3, top + 5), (cx - 3, top + 10)], fill=GLASS_HI)
    d.point([(cx - 2, top + 4)], fill=GLASS_HI)

    # ---- glint diagonal que barre el vidrio (frames 2 y 3) ----
    if i == 2:
        d.line([(cx - 1, top + 8), (cx + 2, top + 3)], fill=GLASS_HI)
    elif i == 3:
        d.line([(cx + 1, top + 9), (cx + 4, top + 4)], fill=GLASS_HI)

    _outline(img)
    return img


def main():
    frames = [frame(i) for i in range(N)]
    for i, f in enumerate(frames, 1):
        f.save(f"{OUT}/antidoto_{i}.png")
    sheet = Image.new("RGBA", (W * N, H), T)
    for i, f in enumerate(frames):
        sheet.paste(f, (i * W, 0))
    sheet.save(f"{OUT}/antidoto_sheet.png")
    print(f"{N} frames {W}x{H}  ->  {OUT}/antidoto_1..{N}.png")


if __name__ == "__main__":
    main()
