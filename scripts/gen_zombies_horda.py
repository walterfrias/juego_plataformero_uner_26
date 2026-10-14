#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_zombies_horda.py  —  3 zombies de la calle que SOLO aparecen en la horda
del Nivel 1, mezclados con el personal del laboratorio. Mismo estilo que
gen_zombies_wave2.py (reusa su paleta "familia" y el _outline): 32x34,
8 frames de caminata, pies a y=33. Todos miran a la derecha (la horda
avanza hacia la derecha).

  ZombieHin — hincha. Camiseta bordó con franja, bufanda, jean. Andar:
              "alentando", los brazos arriba alternados y rebote fuerte.
  ZombieRep — repartidor. Campera gris, gorra, mochila cúbica naranja
              enorme en la espalda. Andar: encorvado por el peso, rápido.
  ZombiePol — policía. Uniforme azul oscuro, gorra con visera, cinturón.
              Andar: tieso, casi marcial, un brazo estirado al frente.

Crea, por cada uno:
  game/assets/Zombie_<X>/Zombie_<X>_Walk_1..8.png   (32x34 RGBA)
  game/assets/Zombie_<X>/zombie_<x>_walk_sheet.png  (256x34, referencia)

Uso:  python3 scripts/gen_zombies_horda.py      (desde la raíz del repo)
"""
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from gen_zombies_wave2 import (EYE, H, MOUTH, N, SKIN, SKIN_S, TAU, W,  # noqa: E402
                               _new, _outline)

JEANS, JEANS_S = (56, 62, 84, 255), (42, 46, 64, 255)
SHOE = (60, 58, 58, 255)
HAIR = (58, 48, 42, 255)
# hincha
JERSEY, JERSEY_S = (120, 44, 56, 255), (92, 32, 42, 255)
JERSEY_BAND = (206, 200, 196, 255)
SCARF, SCARF_2 = (120, 44, 56, 255), (206, 200, 196, 255)
# repartidor
JACKET, JACKET_S = (92, 96, 104, 255), (68, 72, 80, 255)
BOX, BOX_S, BOX_H = (206, 118, 50, 255), (160, 86, 36, 255), (232, 156, 88, 255)
BOX_LOGO = (240, 220, 190, 255)
CAP_R = (60, 64, 74, 255)
# policía
UNIF, UNIF_S = (40, 52, 84, 255), (28, 36, 62, 255)
BELT, BUCKLE = (30, 30, 34, 255), (186, 176, 120, 255)
VISOR = (22, 24, 32, 255)
BADGE = (196, 184, 120, 255)


def _legs(d, cx, hip_y, ph, stride, lift, pants, shoe=SHOE, width=2):
    for sign, phase in ((-1, 0.0), (1, math.pi)):
        sw = math.sin(ph + phase)
        fx = cx + sign * 2 + round(sw * stride)
        fy = 33 - round(max(0.0, sw) * lift)
        d.line([(cx + sign * 2, hip_y + 2), (fx, fy)], fill=pants, width=width)
        d.rectangle([fx - 2, fy - 1, fx + 1, fy], fill=shoe)


# ======================================================================
# ZombieHin — hincha alentando
# ======================================================================
def frame_hin(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 15
    bob = abs(math.sin(ph))
    hip_y = 21 - round(bob * 2)                 # rebote fuerte
    _legs(d, cx, hip_y, ph, 3, 4, JEANS)
    d.rectangle([cx - 3, hip_y - 1, cx + 3, hip_y + 3], fill=JEANS_S)

    sh_y = hip_y - 11
    d.polygon([(cx - 4, sh_y), (cx + 4, sh_y), (cx + 4, hip_y), (cx - 4, hip_y)], fill=JERSEY)
    d.polygon([(cx + 2, sh_y), (cx + 4, sh_y), (cx + 4, hip_y), (cx + 2, hip_y)], fill=JERSEY_S)
    d.line([(cx - 4, sh_y + 5), (cx + 4, sh_y + 5)], fill=JERSEY_BAND)      # franja
    d.line([(cx - 4, sh_y + 6), (cx + 4, sh_y + 6)], fill=JERSEY_BAND)

    # brazos arriba, alternados ("alentando")
    for k, (sign, col) in enumerate(((-1, JERSEY_S), (1, JERSEY))):
        up = math.sin(ph + k * math.pi)
        ax = cx + sign * 4
        hx = ax + sign * 2
        hy = sh_y - 5 - round(max(0.0, up) * 3)
        d.line([(ax, sh_y + 1), (hx, hy)], fill=col, width=2)
        d.rectangle([hx - 1, hy - 1, hx + 1, hy], fill=SKIN if k else SKIN_S)

    # cabeza + bufanda a rayas al cuello
    hx = cx + 1
    hy = 3 + round(bob)
    d.ellipse([hx - 3, hy, hx + 4, hy + 7], fill=SKIN)
    d.polygon([(hx - 3, hy - 1), (hx + 4, hy - 1), (hx + 4, hy + 1), (hx - 3, hy + 2)], fill=HAIR)
    d.point([(hx, hy + 3), (hx + 3, hy + 3)], fill=EYE)
    d.rectangle([hx, hy + 5, hx + 3, hy + 6], fill=MOUTH)                   # grita
    for sx in range(cx - 4, cx + 5):
        d.point([(sx, sh_y - 1), (sx, sh_y)], fill=SCARF if (sx // 2) % 2 else SCARF_2)
    d.line([(cx - 3, sh_y + 1), (cx - 3, sh_y + 4)], fill=SCARF)              # punta colgando
    _outline(img)
    return img


# ======================================================================
# ZombieRep — repartidor con mochila cúbica
# ======================================================================
def frame_rep(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 16
    bob = abs(math.sin(ph))
    hip_y = 22 - round(bob)
    _legs(d, cx, hip_y, ph, 4, 3, JEANS)          # zancada rápida
    d.rectangle([cx - 3, hip_y - 1, cx + 3, hip_y + 3], fill=JEANS_S)

    lean = 3
    sh_x, sh_y = cx + lean, hip_y - 11
    # mochila cúbica en la espalda (detrás del torso, a la izquierda)
    bx0, by0 = sh_x - 12, sh_y - 3 + round(bob)
    d.rectangle([bx0, by0, bx0 + 9, by0 + 10], fill=BOX)
    d.rectangle([bx0 + 7, by0, bx0 + 9, by0 + 10], fill=BOX_S)
    d.line([(bx0, by0), (bx0 + 9, by0)], fill=BOX_H)
    d.rectangle([bx0 + 2, by0 + 3, bx0 + 5, by0 + 6], fill=BOX_LOGO)
    # torso (campera) volcado al frente
    d.polygon([(sh_x - 4, sh_y), (sh_x + 3, sh_y), (cx + 3, hip_y), (cx - 4, hip_y)], fill=JACKET)
    d.polygon([(sh_x, sh_y), (sh_x + 3, sh_y), (cx + 3, hip_y), (cx, hip_y)], fill=JACKET_S)
    d.line([(sh_x - 3, sh_y), (bx0 + 8, by0 + 2)], fill=JACKET_S)            # tira de la mochila
    # brazos
    hxf = sh_x + 5 + round(math.sin(ph) * 2)
    hyf = sh_y + 6
    d.line([(sh_x + 2, sh_y + 1), (hxf, hyf)], fill=JACKET, width=2)
    d.rectangle([hxf - 1, hyf, hxf + 1, hyf + 1], fill=SKIN)
    hxb = sh_x - 2 + round(math.sin(ph + math.pi) * 2)
    d.line([(sh_x - 2, sh_y + 1), (hxb, sh_y + 9)], fill=JACKET_S, width=2)
    d.rectangle([hxb - 1, sh_y + 9, hxb + 1, sh_y + 10], fill=SKIN_S)
    # cabeza con gorra
    hx, hy = sh_x + 2, sh_y - 7 + round(bob)
    d.rectangle([sh_x, sh_y - 1, sh_x + 2, sh_y + 1], fill=SKIN_S)
    d.ellipse([hx - 3, hy, hx + 4, hy + 7], fill=SKIN)
    d.chord([hx - 3, hy - 2, hx + 4, hy + 4], 180, 360, fill=CAP_R)
    d.rectangle([hx + 1, hy + 1, hx + 6, hy + 1], fill=CAP_R)                # visera
    d.point([(hx + 1, hy + 3), (hx + 3, hy + 3)], fill=EYE)
    d.line([(hx + 1, hy + 5), (hx + 3, hy + 5)], fill=MOUTH)
    _outline(img)
    return img


# ======================================================================
# ZombiePol — policía, andar tieso
# ======================================================================
def frame_pol(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 15
    step = math.sin(ph)
    hip_y = 21 - round(abs(step))
    # piernas rectas y tiesas (sin rodilla), paso corto marcado
    for sign, phase in ((-1, 0.0), (1, math.pi)):
        sw = math.sin(ph + phase)
        fx = cx + sign * 2 + round(sw * 3)
        fy = 33 - round(max(0.0, sw) * 2)
        d.line([(cx + sign * 2, hip_y + 2), (fx, fy)], fill=UNIF_S, width=3)
        d.rectangle([fx - 2, fy - 1, fx + 2, fy], fill=SHOE)

    sh_y = hip_y - 12
    d.polygon([(cx - 5, sh_y), (cx + 5, sh_y), (cx + 4, hip_y + 1), (cx - 4, hip_y + 1)], fill=UNIF)
    d.polygon([(cx + 2, sh_y), (cx + 5, sh_y), (cx + 4, hip_y + 1), (cx + 2, hip_y + 1)], fill=UNIF_S)
    d.rectangle([cx - 4, hip_y - 1, cx + 4, hip_y], fill=BELT)
    d.point([(cx, hip_y - 1), (cx + 1, hip_y - 1)], fill=BUCKLE)
    d.rectangle([cx - 3, sh_y + 3, cx - 2, sh_y + 4], fill=BADGE)            # placa
    # brazo estirado al frente (rígido) y el otro pegado al cuerpo
    hx, hy = cx + 12, sh_y + 3 + round(step)
    d.line([(cx + 4, sh_y + 1), (hx, hy)], fill=UNIF, width=2)
    d.rectangle([hx, hy - 1, hx + 1, hy], fill=SKIN)
    d.line([(cx - 5, sh_y + 1), (cx - 5, sh_y + 10)], fill=UNIF_S, width=2)
    d.rectangle([cx - 6, sh_y + 10, cx - 4, sh_y + 11], fill=SKIN_S)
    # cabeza con gorra de visera
    hx, hy = cx + 1, 4 + round(abs(step))
    d.rectangle([cx, hy + 6, cx + 2, hy + 8], fill=SKIN_S)
    d.ellipse([hx - 3, hy + 1, hx + 4, hy + 8], fill=SKIN)
    d.rectangle([hx - 4, hy - 1, hx + 4, hy + 2], fill=UNIF)
    d.line([(hx - 4, hy - 1), (hx + 4, hy - 1)], fill=UNIF_S)
    d.rectangle([hx, hy + 2, hx + 6, hy + 2], fill=VISOR)
    d.point([(hx + 1, hy + 2)], fill=BADGE)
    d.point([(hx, hy + 4), (hx + 3, hy + 4)], fill=EYE)
    d.line([(hx, hy + 6), (hx + 3, hy + 6)], fill=MOUTH)
    _outline(img)
    return img


ZOMBIES = {"Hin": frame_hin, "Rep": frame_rep, "Pol": frame_pol}


def main():
    for letter, fn in ZOMBIES.items():
        out = f"game/assets/Zombie_{letter}"
        os.makedirs(out, exist_ok=True)
        frames = [fn(i) for i in range(N)]
        for i, f in enumerate(frames, 1):
            f.save(f"{out}/Zombie_{letter}_Walk_{i}.png")
        sheet = Image.new("RGBA", (W * N, H), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            sheet.paste(f, (i * W, 0))
        sheet.save(f"{out}/zombie_{letter.lower()}_walk_sheet.png")
        print(f"Zombie_{letter}: {N} frames {W}x{H}  ->  {out}/")


if __name__ == "__main__":
    assert os.path.isdir("game/assets"), "corré desde la raíz del repo"
    main()
