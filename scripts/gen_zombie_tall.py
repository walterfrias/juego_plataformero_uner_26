#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_zombie_tall.py  —  3er zombie: oficinista alto y demacrado. Otro carácter
que el ZombieM (ancho, encorvado, renguera): éste es flaco y estirado, camina
tieso como marchando, con balanceo lateral y la cabeza colgando.

Diseño (para diferenciarlo de los otros):
  - alto, flaco, llena casi todo el canvas a lo alto. Camisa blanca sucia con
    corbata manchada, pantalón de vestir oscuro. Calvicie incipiente, anteojos
    torcidos colgando de una oreja. Piel verde + ojos rojos (familia).
  - marcha tiesa: las dos piernas quedan casi rectas, alternan el paso sin
    doblar la rodilla; el cuerpo se mece de lado a lado (transferencia de
    peso). Un brazo cuelga muerto y pendulea, el otro va estirado al frente.
  - cabeza caída hacia adelante, cabecea 1 vez por ciclo.
  - ancla fija en la cadera. Pies al borde inferior (y=33).

Crea:
  game/assets/Zombie_T/Zombie_T_Walk_1..8.png   (32x34, RGBA)
  game/assets/Zombie_T/zombie_t_walk_sheet.png  (256x34, referencia)

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_zombie_tall.py
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/Zombie_T"
os.makedirs(OUT, exist_ok=True)

W, H = 32, 34
N = 8
TAU = math.tau

OUTL     = (24, 24, 34, 255)
SKIN     = (150, 190, 150, 255)
SKIN_S   = (108, 150, 116, 255)
SHIRT    = (176, 178, 170, 255)
SHIRT_S  = (128, 132, 126, 255)
TIE      = (112, 48, 52, 255)      # corbata manchada
TIE_S    = (78, 34, 40, 255)
PANTS    = (54, 55, 66, 255)
PANTS_S  = (38, 39, 50, 255)
HAIR     = (66, 58, 50, 255)
GLASS    = (40, 42, 52, 255)
EYE      = (214, 74, 74, 255)
MOUTH    = (120, 40, 44, 255)


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
    cx = 15

    rock = 1.6 * math.sin(ph)                 # mecida lateral (peso)
    bob = abs(math.sin(ph * 2))               # rebote sutil
    hip_y = 21 - round(bob)
    lean = 1                                  # inclinado un pelo al frente

    # ---- piernas tiesas que alternan (sin doblar rodilla) ----
    for sign, phase in ((-1, 0.0), (1, math.pi)):
        sw = math.sin(ph + phase)
        foot_x = cx + sign * 2 + round(sw * 3)
        lift = max(0.0, sw) * 2
        foot_y = 33 - round(lift)
        hipx = cx + sign * 2 + round(rock * 0.4)
        d.line([(hipx, hip_y + 2), (foot_x, foot_y)], fill=SKIN_S, width=2)
        d.line([(hipx, hip_y + 2), (foot_x, min(foot_y, 30))], fill=PANTS, width=2)
        d.rectangle([foot_x - 2, foot_y - 1, foot_x + 1, foot_y], fill=PANTS_S)

    # ---- cadera / cinturón ----
    d.rectangle([cx - 3, hip_y - 1, cx + 4, hip_y + 3], fill=PANTS)
    d.line([(cx - 3, hip_y), (cx + 4, hip_y)], fill=PANTS_S)

    # ---- torso flaco y largo (camisa) ----
    sh_y = hip_y - 13
    tx = round(rock)                          # el torso sigue la mecida
    d.polygon([(cx - 3 + tx, sh_y), (cx + 4 + tx, sh_y),
               (cx + 4, hip_y - 1), (cx - 3, hip_y - 1)], fill=SHIRT)
    d.polygon([(cx + 1 + tx, sh_y), (cx + 4 + tx, sh_y),
               (cx + 4, hip_y - 1), (cx + 1, hip_y - 1)], fill=SHIRT_S)
    # corbata: cae del cuello, pendulea un poco
    knot_x = cx + tx + lean
    tip_x = knot_x + round(1.2 * math.sin(ph + 0.7))
    d.line([(knot_x, sh_y), (knot_x, sh_y + 3), (tip_x, hip_y - 2)], fill=TIE, width=2)
    d.point([(tip_x, hip_y - 2)], fill=TIE_S)

    # ---- brazo muerto que pendulea (atrás en z) ----
    sxb = cx - 3 + tx
    hxb = sxb - 1 + round(2 * math.sin(ph + math.pi))
    hyb = sh_y + 12 + round(bob)
    d.line([(sxb, sh_y + 1), (hxb, hyb)], fill=SHIRT_S, width=2)
    d.rectangle([hxb - 1, hyb, hxb + 1, hyb + 2], fill=SKIN_S)

    # ---- cabeza colgando + calvicie + anteojos torcidos ----
    hx = cx + tx + lean + round(math.sin(ph) * 0.6)
    hy = 5 + round(bob) + round(math.sin(ph) * 1.0)
    d.rectangle([cx + tx, hy + 3, cx + tx + 2, hy + 6], fill=SKIN_S)          # cuello
    d.ellipse([hx - 3, hy - 2, hx + 4, hy + 5], fill=SKIN)                   # cara alargada
    d.arc([hx - 3, hy - 4, hx + 4, hy + 3], 180, 360, fill=HAIR)            # pelo (solo laterales/atrás)
    d.point([(hx - 3, hy + 1), (hx + 4, hy + 1)], fill=HAIR)
    d.point([(hx - 1, hy + 2), (hx + 2, hy + 2)], fill=EYE)                  # ojos
    d.line([(hx - 3, hy + 2), (hx - 1, hy + 3)], fill=GLASS)                 # anteojo torcido
    d.point([(hx + 3, hy + 3)], fill=GLASS)
    d.line([(hx - 1, hy + 4), (hx + 2, hy + 4)], fill=MOUTH)                 # boca floja

    # ---- brazo estirado al frente (adelante en z) ----
    sxf = cx + 4 + tx
    hxf = cx + 9
    hyf = sh_y + 4 + round(1.4 * math.sin(ph))
    d.line([(sxf, sh_y + 1), (cx + 7, sh_y + 2), (hxf, hyf)], fill=SHIRT, width=2)
    d.rectangle([hxf - 1, hyf - 1, hxf + 1, hyf + 1], fill=SKIN)

    _outline(img)
    return img


def main():
    frames = [frame(i) for i in range(N)]
    for i, f in enumerate(frames, 1):
        f.save(f"{OUT}/Zombie_T_Walk_{i}.png")
    sheet = Image.new("RGBA", (W * N, H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * W, 0))
    sheet.save(f"{OUT}/zombie_t_walk_sheet.png")
    print(f"{N} frames {W}x{H}  ->  {OUT}/Zombie_T_Walk_1..{N}.png")


if __name__ == "__main__":
    main()
