#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_zombie_drag.py  —  4to zombie: mujer demacrada que ARRASTRA un pie.
Mismo estilo/proporciones que el ZombieT (alto, flaco, linework limpio,
paleta familia), pero otra silueta y otra caminata.

Diseño:
  - mujer alta y consumida. Cárdigan tejido gastado (mostaza sucio) con el
    ruedo deshilachado, vestido oscuro debajo. Melena larga y apelmazada
    tapándole media cara, asimétrica. Piel verde + ojos rojos.
  - caminata de ARRASTRE: la pierna izquierda queda muerta, el pie no se
    despega del piso nunca — se raspa y va a los tirones detrás del cuerpo.
    La derecha hace todo el trabajo: pisa, planta y tira del cuerpo, que
    avanza a sacudones. 8 frames.
  - ancla fija en la cadera. Pies al borde inferior (y=33).

Crea:
  game/assets/Zombie_D/Zombie_D_Walk_1..8.png   (32x34, RGBA)
  game/assets/Zombie_D/zombie_d_walk_sheet.png  (256x34, referencia)

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_zombie_drag.py
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/Zombie_D"
os.makedirs(OUT, exist_ok=True)

W, H = 32, 34
N = 8
TAU = math.tau

OUTL       = (24, 24, 34, 255)
SKIN       = (150, 190, 150, 255)
SKIN_S     = (108, 150, 116, 255)
CARDIGAN   = (150, 130, 82, 255)
CARDIGAN_S = (110, 96, 58, 255)
DRESS      = (58, 54, 66, 255)
DRESS_S    = (42, 39, 50, 255)
HAIR       = (54, 46, 42, 255)
HAIR_S     = (38, 32, 30, 255)
EYE        = (214, 74, 74, 255)
MOUTH      = (120, 40, 44, 255)


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
    ph = t * TAU
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = 16

    push = max(0.0, math.sin(ph))                 # fase de empuje de la pierna sana
    hitch = round(1.4 * push)                     # el cuerpo se va para adelante a sacudones
    dip = round(1.2 * push)
    hip_y = 21 + dip

    # ---- pierna que arrastra (izq): el pie NO se despega, va detrás ----
    drag_x = cx - 3 + round(2 * math.sin(ph * 0.5 - 0.6))
    d.line([(cx - 2, hip_y + 2), (drag_x - 2, 30), (drag_x, 33)], fill=SKIN_S, width=2)
    d.line([(cx - 2, hip_y + 2), (drag_x - 1, 30)], fill=DRESS_S, width=2)
    d.rectangle([drag_x - 2, 32, drag_x + 2, 33], fill=DRESS_S)   # pie raspando, plano

    # ---- pierna sana (der): pisa y tira ----
    s = math.sin(ph + 0.2)
    gx = cx + 2 + round(s * 4)
    gy = 33 - round(max(0.0, s) * 3)
    d.line([(cx + 2, hip_y + 2), (gx, gy)], fill=SKIN_S, width=2)
    d.line([(cx + 2, hip_y + 2), (gx, min(gy, 30))], fill=DRESS, width=2)
    d.rectangle([gx - 2, gy - 1, gx + 1, gy], fill=DRESS_S)

    # ---- vestido oscuro / cadera ----
    d.polygon([(cx - 3, hip_y - 2), (cx + 3, hip_y - 2),
               (cx + 3, hip_y + 4), (cx - 3, hip_y + 4)], fill=DRESS)

    # ---- cárdigan angosto y largo (silueta consumida), ruedo deshilachado ----
    sh_y = hip_y - 13
    tx = hitch
    hem = hip_y + 4 + dip
    d.polygon([(cx - 4 + tx, sh_y), (cx + 4 + tx, sh_y),
               (cx + 3, hem), (cx - 3, hem)], fill=CARDIGAN)
    d.polygon([(cx + 1 + tx, sh_y), (cx + 4 + tx, sh_y),
               (cx + 3, hem), (cx + 1, hem)], fill=CARDIGAN_S)
    d.line([(cx - 1 + tx, sh_y + 1), (cx - 1, hem - 1)], fill=CARDIGAN_S)  # abertura
    for jx in (cx - 3, cx, cx + 3):                                       # jirones del ruedo
        d.point([(jx, hem), (jx, hem + 1)], fill=CARDIGAN_S)

    # ---- brazo colgando (atrás en z) ----
    axb = cx - 4 + tx
    hxb = axb - 1 + round(2 * math.sin(ph + math.pi))
    hyb = sh_y + 12 + dip
    d.line([(axb, sh_y + 1), (hxb, hyb)], fill=CARDIGAN_S, width=2)
    d.rectangle([hxb - 1, hyb, hxb + 1, hyb + 2], fill=SKIN_S)

    # ---- cabeza chica inclinada; la cara se ve, el pelo la enmarca ----
    hx = cx + tx + round(math.sin(ph) * 0.6)
    hy = 6 + dip + round(math.sin(ph) * 0.8)
    d.rectangle([cx + tx, hy + 3, cx + tx + 2, hy + 6], fill=SKIN_S)      # cuello
    # pelo detrás (casquete + una mecha larga cae por el lado izq hasta el hombro)
    d.polygon([(hx - 3, hy - 3), (hx + 4, hy - 3), (hx + 4, hy + 1),
               (hx + 3, hy + 4), (hx - 4, hy + 4), (hx - 4, hy - 1)], fill=HAIR)
    d.polygon([(hx - 4, hy + 1), (hx - 2, hy + 1), (hx - 2, hy + 9),
               (hx - 4, hy + 7)], fill=HAIR)                              # mecha larga izq
    d.point([(hx - 3, hy + 10), (hx - 2, hy + 11)], fill=HAIR_S)
    # cara
    d.ellipse([hx - 2, hy - 1, hx + 3, hy + 4], fill=SKIN)
    d.point([(hx + 1, hy + 1)], fill=EYE)                                 # un ojo (el otro bajo el pelo)
    d.line([(hx, hy + 3), (hx + 2, hy + 3)], fill=MOUTH)

    _outline(img)
    return img


def main():
    frames = [frame(i) for i in range(N)]
    for i, f in enumerate(frames, 1):
        f.save(f"{OUT}/Zombie_D_Walk_{i}.png")
    sheet = Image.new("RGBA", (W * N, H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * W, 0))
    sheet.save(f"{OUT}/zombie_d_walk_sheet.png")
    print(f"{N} frames {W}x{H}  ->  {OUT}/Zombie_D_Walk_1..{N}.png")


if __name__ == "__main__":
    main()
