#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_mochila.py  —  pickup del Nivel 1: mochila de repartidor.

Diseño:
  - mochila cúbica térmica de delivery, naranja vivo con parche blanco
    ovalado y una "R" naranja al frente (estética de mochila de
    repartidor tipo Rappi), correas negras arriba.
  - da la habilidad de planeo (caída lenta) por el resto del nivel al
    agarrarla — ver wire_mochila.py.
  - se lee por silueta + color, no por animación fina, igual criterio
    que antidoto_*.
  - 6 frames: bob de 2 px (flota) + un glint que barre el parche en
    2 frames + una correa que se mece apenas.
  - ancla al centro (pickup flotante, no apoya en piso).

Crea (game/assets/UI/):
  mochila_1..6.png    18x20  RGBA
  mochila_sheet.png   108x20 referencia
  mochila_worn.png    14x16  RGBA (versión estática, sin halo/bob, para
                       dibujar puesta en la espalda del jugador una vez
                       que la agarra — ver wire_mochila.py)

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_mochila.py
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/UI"
os.makedirs(OUT, exist_ok=True)

W, H = 18, 20
N = 6
T = (0, 0, 0, 0)

OUTL     = (26, 22, 34, 255)
ORANGE   = (255, 90, 0, 255)      # naranja Rappi
ORANGE_S = (204, 62, 0, 255)      # sombra
ORANGE_HI = (255, 140, 60, 255)   # brillo
STRAP    = (34, 30, 40, 255)
STRAP_HI = (60, 54, 66, 255)
PATCH    = (250, 246, 238, 255)   # parche blanco
PATCH_S  = (214, 208, 196, 255)
R_MARK   = ORANGE
GLOW     = (255, 130, 40, 60)


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

    bob = round(math.sin(ph) * 1.5)
    cx = 9
    top = 3 + bob

    # ---- halo naranja tenue ----
    d.ellipse([cx - 7, top + 1, cx + 6, top + 17], fill=GLOW)

    # ---- correas (se mecen apenas) ----
    sway = 1 if i in (1, 4) else 0
    d.line([(cx - 4 + sway, top - 1), (cx - 4, top + 4)], fill=STRAP, width=2)
    d.line([(cx + 4 - sway, top - 1), (cx + 4, top + 4)], fill=STRAP, width=2)
    d.point([(cx - 4, top - 1)], fill=STRAP_HI)
    d.point([(cx + 4, top - 1)], fill=STRAP_HI)

    # ---- cuerpo cúbico (mochila térmica) ----
    body = [cx - 6, top + 2, cx + 6, top + 15]
    d.rounded_rectangle(body, radius=2, fill=ORANGE)
    d.rounded_rectangle([cx - 6, top + 10, cx + 6, top + 15], radius=2, fill=ORANGE_S)

    # ---- solapa superior ----
    d.rounded_rectangle([cx - 6, top + 1, cx + 6, top + 4], radius=2, fill=ORANGE_HI)

    # ---- parche blanco ovalado con "R" ----
    d.ellipse([cx - 4, top + 5, cx + 4, top + 11], fill=PATCH)
    d.ellipse([cx - 4, top + 9, cx + 4, top + 11], fill=PATCH_S)
    # letra R simplificada (3x5 px)
    rx, ry = cx - 1, top + 5
    d.line([(rx, ry), (rx, ry + 4)], fill=R_MARK)          # palo vertical
    d.line([(rx, ry), (rx + 2, ry)], fill=R_MARK)          # techo
    d.line([(rx + 2, ry), (rx + 2, ry + 1)], fill=R_MARK)  # lado panza
    d.line([(rx, ry + 2), (rx + 2, ry + 2)], fill=R_MARK)  # medio
    d.line([(rx + 1, ry + 2), (rx + 2, ry + 4)], fill=R_MARK)  # pata

    # ---- brillo / glint que barre el parche (frames 2 y 3) ----
    if i == 2:
        d.line([(cx - 2, top + 9), (cx + 1, top + 6)], fill=(255, 255, 255, 200))
    elif i == 3:
        d.line([(cx, top + 10), (cx + 3, top + 7)], fill=(255, 255, 255, 200))

    _outline(img)
    return img


def frame_worn():
    """Version estatica, chica, sin halo/bob/glint — para dibujar puesta
    en la espalda del jugador (compañera fija, no pickup flotante)."""
    ww, wh = 14, 16
    img = Image.new("RGBA", (ww, wh), T)
    d = ImageDraw.Draw(img)
    cx, top = 7, 1

    d.line([(cx - 3, top - 1), (cx - 3, top + 3)], fill=STRAP, width=2)
    d.line([(cx + 3, top - 1), (cx + 3, top + 3)], fill=STRAP, width=2)

    body = [cx - 5, top + 1, cx + 5, top + 12]
    d.rounded_rectangle(body, radius=2, fill=ORANGE)
    d.rounded_rectangle([cx - 5, top + 8, cx + 5, top + 12], radius=2, fill=ORANGE_S)
    d.rounded_rectangle([cx - 5, top, cx + 5, top + 3], radius=2, fill=ORANGE_HI)

    d.ellipse([cx - 3, top + 4, cx + 3, top + 9], fill=PATCH)
    rx, ry = cx - 1, top + 4
    d.line([(rx, ry), (rx, ry + 3)], fill=R_MARK)
    d.line([(rx, ry), (rx + 1, ry)], fill=R_MARK)
    d.line([(rx + 1, ry), (rx + 1, ry + 1)], fill=R_MARK)
    d.line([(rx, ry + 1), (rx + 1, ry + 1)], fill=R_MARK)
    d.line([(rx + 1, ry + 1), (rx + 1, ry + 3)], fill=R_MARK)

    _outline(img)
    return img


def main():
    frames = [frame(i) for i in range(N)]
    for i, f in enumerate(frames, 1):
        f.save(f"{OUT}/mochila_{i}.png")
    sheet = Image.new("RGBA", (W * N, H), T)
    for i, f in enumerate(frames):
        sheet.paste(f, (i * W, 0))
    sheet.save(f"{OUT}/mochila_sheet.png")
    print(f"{N} frames {W}x{H}  ->  {OUT}/mochila_1..{N}.png")

    frame_worn().save(f"{OUT}/mochila_worn.png")
    print(f"1 frame 14x16  ->  {OUT}/mochila_worn.png")


if __name__ == "__main__":
    main()
