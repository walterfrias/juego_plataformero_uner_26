#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_zombies_lab.py  —  3 zombies del laboratorio (Nivel 2): personal del lugar
donde empezó el brote. Mismo estilo que gen_zombies_wave2.py (reusa su paleta
"familia" y el _outline): 32x34, 8 frames de caminata, pies a y=33.

  ZombieMed — médico (M). Guardapolvo largo abierto sobre ambo turquesa,
              estetoscopio colgando. Andar: el zombie "clásico", los dos
              brazos estirados al frente, paso regular.
  ZombieEnf — enfermera (F). Ambo verde agua, gorro de quirófano, barbijo
              colgando del cuello. Andar: se tambalea de lado a lado, un
              brazo cuelga muerto.
  ZombieInv — investigador (M). Guardapolvo, antiparras y un matraz con
              líquido verde en la mano de adelante. Andar: encorvado,
              arrastra los pies, lento.

Crea, por cada uno:
  game/assets/Zombie_<X>/Zombie_<X>_Walk_1..8.png   (32x34 RGBA)
  game/assets/Zombie_<X>/zombie_<x>_walk_sheet.png  (256x34, referencia)

Uso:  python3 scripts/gen_zombies_lab.py      (desde la raíz del repo)
"""
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from gen_zombies_wave2 import (EYE, H, MOUTH, N, SKIN, SKIN_S, TAU, W,  # noqa: E402
                               _new, _outline)

# guardapolvo: "blanco" de noche (no blanco puro, para no romper la paleta)
COAT, COAT_S, COAT_H = (190, 198, 202, 255), (140, 150, 158, 255), (220, 226, 228, 255)
SCRUB, SCRUB_S = (72, 140, 140, 255), (52, 108, 110, 255)         # ambo turquesa
SCRUB2, SCRUB2_S = (110, 168, 150, 255), (80, 130, 116, 255)      # ambo verde agua
SHOE = (70, 74, 80, 255)
STETH = (48, 52, 60, 255)
STETH_M = (170, 176, 182, 255)
HAIR = (70, 58, 50, 255)
CAP = (96, 150, 150, 255)
MASK = (150, 190, 206, 255)
GOGGLE, GOGGLE_H = (60, 90, 100, 255), (150, 210, 220, 255)
GLOVE = (170, 150, 90, 255)
FLASK, LIQUID = (170, 200, 205, 255), (90, 200, 100, 255)


def _legs(d, cx, hip_y, ph, stride, lift, pants, shoe=SHOE):
    for sign, phase in ((-1, 0.0), (1, math.pi)):
        sw = math.sin(ph + phase)
        fx = cx + sign * 2 + round(sw * stride)
        fy = 33 - round(max(0.0, sw) * lift)
        d.line([(cx + sign * 2, hip_y + 2), (fx, fy)], fill=pants, width=2)
        d.rectangle([fx - 2, fy - 1, fx + 1, fy], fill=shoe)


# ======================================================================
# ZombieMed — médico, brazos al frente
# ======================================================================
def frame_med(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 15
    bob = abs(math.sin(ph))
    hip_y = 21 - round(bob)
    _legs(d, cx, hip_y, ph, 3, 3, SCRUB_S)

    sh_y = hip_y - 11
    # guardapolvo: largo hasta la rodilla, abierto adelante (se ve el ambo)
    d.polygon([(cx - 5, sh_y), (cx + 5, sh_y), (cx + 6, hip_y + 4), (cx - 6, hip_y + 4)], fill=COAT)
    d.polygon([(cx + 2, sh_y), (cx + 5, sh_y), (cx + 6, hip_y + 4), (cx + 3, hip_y + 4)], fill=COAT_S)
    d.polygon([(cx - 1, sh_y + 1), (cx + 2, sh_y + 1), (cx + 2, hip_y + 3), (cx - 1, hip_y + 3)],
              fill=SCRUB)
    d.line([(cx - 5, sh_y + 1), (cx - 5, hip_y + 3)], fill=COAT_H)
    # bolsillo con lapicera
    d.rectangle([cx - 4, sh_y + 5, cx - 2, sh_y + 7], fill=COAT_S)
    d.point([(cx - 3, sh_y + 4)], fill=STETH)
    # estetoscopio
    d.line([(cx - 2, sh_y), (cx - 2, sh_y + 4), (cx, sh_y + 6)], fill=STETH)
    d.line([(cx + 3, sh_y), (cx + 3, sh_y + 5)], fill=STETH)
    d.rectangle([cx + 2, sh_y + 5, cx + 4, sh_y + 6], fill=STETH_M)

    # brazos estirados al frente (los dos), suben y bajan apenas
    for k, (col, dy) in enumerate(((COAT_S, 3), (COAT, 0))):
        ay = sh_y + 2 + k
        hx = cx + 12
        hy = ay + dy + round(math.sin(ph + k) * 1)
        d.line([(cx + 3, ay), (hx, hy)], fill=col, width=2)
        d.rectangle([hx, hy - 1, hx + 1, hy], fill=SKIN if k else SKIN_S)

    # cabeza
    hx = cx + 1 + round(math.sin(ph) * 0.5)
    hy = 4 + round(bob)
    d.rectangle([cx, hy + 5, cx + 2, hy + 7], fill=SKIN_S)
    d.ellipse([hx - 3, hy, hx + 4, hy + 7], fill=SKIN)
    d.polygon([(hx - 3, hy), (hx + 3, hy - 1), (hx + 4, hy + 1), (hx - 3, hy + 2)], fill=HAIR)
    d.point([(hx, hy + 3), (hx + 3, hy + 3)], fill=EYE)
    d.line([(hx, hy + 5), (hx + 3, hy + 5)], fill=MOUTH)
    _outline(img)
    return img


# ======================================================================
# ZombieEnf — enfermera, tambaleo lateral
# ======================================================================
def frame_enf(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 16
    sway = math.sin(ph)                      # tambaleo de lado a lado
    bob = abs(math.sin(ph))
    hip_y = 21 - round(bob)
    _legs(d, cx, hip_y, ph, 2, 3, SCRUB2_S)
    d.rectangle([cx - 3, hip_y - 1, cx + 3, hip_y + 3], fill=SCRUB2_S)

    sh_y = hip_y - 11
    tx = round(sway * 2)
    d.polygon([(cx - 4 + tx, sh_y), (cx + 4 + tx, sh_y), (cx + 3, hip_y + 1), (cx - 3, hip_y + 1)],
              fill=SCRUB2)
    d.polygon([(cx + 1 + tx, sh_y), (cx + 4 + tx, sh_y), (cx + 3, hip_y + 1), (cx + 1, hip_y + 1)],
              fill=SCRUB2_S)
    d.line([(cx - 1 + tx, sh_y), (cx + tx, sh_y + 3), (cx + 1 + tx, sh_y)], fill=SCRUB2_S)  # escote V

    # brazo muerto (cuelga y se balancea con el cuerpo)
    axb = cx - 4 + tx
    hxb = axb - round(sway * 2)
    d.line([(axb, sh_y + 1), (hxb, sh_y + 10)], fill=SKIN_S, width=2)
    # brazo adelante, a media altura
    axf = cx + 4 + tx
    hxf = axf + 5
    hyf = sh_y + 5 + round(math.sin(ph * 2))
    d.line([(axf, sh_y + 1), (hxf, hyf)], fill=SKIN, width=2)

    # cabeza ladeada según el tambaleo, gorro y barbijo colgando
    hx = cx + tx + round(sway)
    hy = 5 + round(bob)
    d.rectangle([cx + tx, hy + 5, cx + tx + 2, hy + 7], fill=SKIN_S)
    d.ellipse([hx - 3, hy, hx + 4, hy + 7], fill=SKIN)
    d.chord([hx - 4, hy - 3, hx + 5, hy + 4], 180, 360, fill=CAP)
    d.rectangle([hx - 4, hy, hx + 5, hy + 1], fill=CAP)
    d.point([(hx, hy + 3), (hx + 3, hy + 3)], fill=EYE)
    d.line([(hx, hy + 5), (hx + 2, hy + 5)], fill=MOUTH)
    d.rectangle([hx - 1, hy + 7, hx + 3, hy + 8], fill=MASK)       # barbijo en el cuello
    _outline(img)
    return img


# ======================================================================
# ZombieInv — investigador, encorvado con un matraz
# ======================================================================
def frame_inv(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 14
    bob = abs(math.sin(ph)) * 0.5
    hip_y = 21
    _legs(d, cx, hip_y, ph, 2, 1, SHOE)       # arrastra los pies: casi no levanta

    lean = 4
    sh_x, sh_y = cx + lean, hip_y - 11 + round(bob)
    # guardapolvo largo, torso volcado al frente
    d.polygon([(sh_x - 5, sh_y), (sh_x + 4, sh_y), (cx + 5, hip_y + 8), (cx - 6, hip_y + 8)], fill=COAT)
    d.polygon([(sh_x + 1, sh_y), (sh_x + 4, sh_y), (cx + 5, hip_y + 8), (cx + 2, hip_y + 8)],
              fill=COAT_S)
    d.line([(sh_x - 4, sh_y + 1), (cx - 5, hip_y + 7)], fill=COAT_H)

    # brazo de atrás colgando, guante
    d.line([(sh_x - 4, sh_y + 1), (sh_x - 5, sh_y + 10)], fill=COAT_S, width=2)
    d.rectangle([sh_x - 6, sh_y + 10, sh_x - 4, sh_y + 11], fill=GLOVE)
    # brazo adelante sosteniendo el matraz
    fx, fy = sh_x + 6, sh_y + 6 + round(math.sin(ph) * 1)
    d.line([(sh_x + 3, sh_y + 1), (fx, fy)], fill=COAT, width=2)
    d.rectangle([fx - 1, fy - 1, fx + 1, fy + 1], fill=GLOVE)
    d.rectangle([fx + 1, fy - 5, fx + 2, fy - 2], fill=FLASK)          # cuello del matraz
    d.polygon([(fx - 1, fy + 2), (fx + 4, fy + 2), (fx + 2, fy - 2), (fx + 1, fy - 2)], fill=FLASK)
    d.line([(fx, fy + 1), (fx + 3, fy + 1)], fill=LIQUID)
    d.point([(fx + 1, fy), (fx + 2, fy)], fill=LIQUID)

    # cabeza baja y adelante, pelado con flequillo, antiparras
    hx = sh_x + 2
    hy = sh_y - 6
    d.rectangle([sh_x, sh_y - 1, sh_x + 2, sh_y + 1], fill=SKIN_S)
    d.ellipse([hx - 3, hy, hx + 4, hy + 7], fill=SKIN)
    d.line([(hx - 3, hy + 1), (hx - 1, hy)], fill=HAIR)
    d.rectangle([hx - 1, hy + 2, hx + 4, hy + 4], fill=GOGGLE)
    d.point([(hx + 1, hy + 3), (hx + 3, hy + 3)], fill=EYE)
    d.point([(hx, hy + 2)], fill=GOGGLE_H)
    d.line([(hx - 3, hy + 3), (hx - 1, hy + 3)], fill=GOGGLE)          # correa
    d.line([(hx + 1, hy + 6), (hx + 3, hy + 6)], fill=MOUTH)
    _outline(img)
    return img


ZOMBIES = {"Med": frame_med, "Enf": frame_enf, "Inv": frame_inv}


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
