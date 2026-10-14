#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_zombies_wave2.py  —  4 zombies nuevos (2 F, 2 M), cada uno con OTRA silueta
y OTRA caminata que los que ya estan (ZombieF/M base, ZombieT marcha tiesa,
ZombieD arrastra un pie). Mismo estilo: 32x34, paleta "familia" (piel verde,
ojos rojos, linework limpio con _outline), ancla en la cadera, pies a y=33.

  ZombieN — adolescente (F). Buzo con capucha caida, mochila en un hombro.
            Andar: pasitos cortos y RAPIDOS + tics — cabeza y hombros dan
            sacudones espasmodicos fuera de ritmo con las piernas.
  ZombieV — anciana (F). Muy encorvada (casi doblada), panuelo en la cabeza,
            bata larga que barre el piso. Andar: LENTISIMO, pasos minimos,
            el cuerpo doblado se bambolea adelante-atras, un brazo tantea.
  ZombieO — obrero (M). Casco, chaleco reflectivo mugriento, corpulento.
            Andar: renguera PESADA — una pierna tiesa que planta y arrastra
            el talon, el cuerpo se tira encima con un pisoton y gran
            balanceo de hombros.
  ZombieJ — corredor (M). Ropa deportiva, vincha. Torso volcado ~25 al frente
            como si fuera a caerse. Andar: zancada ANCHA y rapida, brazos
            descoordinados, rebote fuerte. El mas rapido.

Crea, por cada uno:
  game/assets/Zombie_<X>/Zombie_<X>_Walk_1..8.png   (32x34 RGBA)
  game/assets/Zombie_<X>/zombie_<x>_walk_sheet.png  (256x34, referencia)

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_zombies_wave2.py
"""
from PIL import Image, ImageDraw
import math
import os

W, H, N = 32, 34, 8
TAU = math.tau

# --- paleta familia (compartida con ZombieT / ZombieD) ---
OUTL   = (24, 24, 34, 255)
SKIN   = (150, 190, 150, 255)
SKIN_S = (108, 150, 116, 255)
EYE    = (214, 74, 74, 255)
MOUTH  = (120, 40, 44, 255)


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


def _new():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


# ======================================================================
# ZombieN — adolescente, pasitos rapidos + tics
# ======================================================================
HOODIE, HOODIE_S = (122, 98, 132, 255), (92, 72, 102, 255)
JEANS = (52, 56, 74, 255)
SNEAK = (182, 182, 174, 255)
PACK, PACK_S = (120, 72, 66, 255), (92, 54, 50, 255)
N_HAIR = (60, 50, 44, 255)


def frame_n(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 16
    stride = math.sin(ph)
    bob = abs(math.sin(ph * 2))
    hip_y = 22 - round(bob)
    tw = round(math.sin(ph * 3 + 0.5))            # espasmo: -1/0/1 fuera de ritmo

    # piernas: paso corto, cadencia rapida
    for sign, phase in ((-1, 0.0), (1, math.pi)):
        sw = math.sin(ph + phase)
        fx = cx + sign * 2 + round(sw * 2)
        fy = 33 - round(max(0.0, sw) * 3)
        hipx = cx + sign * 2
        d.line([(hipx, hip_y + 2), (fx, fy)], fill=SKIN_S, width=2)
        d.line([(hipx, hip_y + 2), (fx, min(fy, 29))], fill=JEANS, width=2)
        d.rectangle([fx - 2, fy - 1, fx + 1, fy], fill=SNEAK)

    d.rectangle([cx - 3, hip_y - 1, cx + 3, hip_y + 3], fill=JEANS)

    sh_y = hip_y - 12
    tx = round(stride * 0.6) + tw                 # el torso tiembla
    d.polygon([(cx - 4 + tx, sh_y), (cx + 4 + tx, sh_y),
               (cx + 3, hip_y), (cx - 3, hip_y)], fill=HOODIE)
    d.polygon([(cx + 1 + tx, sh_y), (cx + 4 + tx, sh_y),
               (cx + 3, hip_y), (cx + 1, hip_y)], fill=HOODIE_S)
    # capucha caida en la espalda (bulto atras del cuello)
    d.polygon([(cx - 4 + tx, sh_y), (cx - 1 + tx, sh_y - 1),
               (cx - 1 + tx, sh_y + 4), (cx - 4 + tx, sh_y + 3)], fill=HOODIE_S)
    # mochila en el hombro derecho
    d.rectangle([cx + 3 + tx, sh_y + 1, cx + 6 + tx, sh_y + 8], fill=PACK)
    d.rectangle([cx + 3 + tx, sh_y + 1, cx + 4 + tx, sh_y + 8], fill=PACK_S)
    d.line([(cx + 1 + tx, sh_y), (cx + 3 + tx, sh_y + 7)], fill=PACK_S)

    # brazo atras
    axb = cx - 4 + tx
    hxb = axb - round(2 * math.sin(ph))
    hyb = sh_y + 9 + round(bob)
    d.line([(axb, sh_y + 1), (hxb, hyb)], fill=HOODIE_S, width=2)
    d.rectangle([hxb - 1, hyb, hxb + 1, hyb + 1], fill=SKIN_S)
    # brazo adelante (+ tic)
    axf = cx + 4 + tx
    hxf = axf + round(2 * math.sin(ph + math.pi)) + tw
    hyf = sh_y + 9 + round(bob)
    d.line([(axf, sh_y + 1), (hxf, hyf)], fill=HOODIE, width=2)
    d.rectangle([hxf - 1, hyf, hxf + 1, hyf + 1], fill=SKIN)

    # cabeza (algo grande), cola de caballo, snap con el tic
    hx = cx + tx + tw + round(math.sin(ph) * 0.4)
    hy = 5 + round(bob * 0.5)
    d.rectangle([cx + tx, hy + 4, cx + tx + 2, hy + 7], fill=SKIN_S)
    d.ellipse([hx - 3, hy - 1, hx + 4, hy + 6], fill=SKIN)
    d.polygon([(hx - 3, hy - 2), (hx + 4, hy - 2), (hx + 4, hy + 2), (hx - 3, hy + 2)], fill=N_HAIR)
    d.polygon([(hx + 3, hy), (hx + 6, hy + 1), (hx + 5, hy + 6), (hx + 3, hy + 4)], fill=N_HAIR)
    d.point([(hx - 1, hy + 2), (hx + 2, hy + 2)], fill=EYE)
    d.line([(hx, hy + 4), (hx + 2, hy + 4)], fill=MOUTH)

    _outline(img)
    return img


# ======================================================================
# ZombieV — anciana encorvada, lentisima
# ======================================================================
ROBE, ROBE_S = (128, 110, 118, 255), (96, 80, 90, 255)
SCARF = (84, 72, 84, 255)


def frame_v(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 15
    sway = math.sin(ph)                            # el cuerpo doblado se mece
    hip_y = 20
    lean = 6 + round(sway * 1.5)                   # cuanto se proyecta el torso al frente

    # piernas cortas bajo la bata, casi verticales, apenas despegan
    for sign, phase in ((-1, 0.0), (1, math.pi)):
        sw = math.sin(ph + phase)
        fx = cx + sign * 2 + round(sw * 1.5)
        fy = 33 - round(max(0.0, sw) * 1.5)
        d.line([(cx + sign, hip_y + 2), (fx, fy)], fill=ROBE_S, width=3)
        d.rectangle([fx - 2, fy - 1, fx + 1, fy], fill=ROBE_S)

    # bata larga que barre el piso
    d.polygon([(cx - 4, hip_y), (cx + 4, hip_y), (cx + 5, 33), (cx - 5, 33)], fill=ROBE)
    d.polygon([(cx + 1, hip_y), (cx + 4, hip_y), (cx + 5, 33), (cx + 1, 33)], fill=ROBE_S)

    # espalda doblada: joroba redonda de la cadera hacia un "hombro" adelante
    sh_x = cx + lean
    sh_y = hip_y - 7
    d.polygon([(cx - 3, hip_y), (cx + 1, hip_y - 4), (sh_x, sh_y - 1),
               (sh_x + 1, sh_y + 3), (cx - 1, hip_y + 2)], fill=ROBE)
    d.polygon([(cx - 1, hip_y - 3), (cx + 2, hip_y - 4), (sh_x, sh_y - 1),
               (sh_x - 2, sh_y + 1)], fill=ROBE_S)

    # brazo que tantea al frente
    hxf = sh_x + 5 + round(sway * 1.5)
    hyf = sh_y + 5
    d.line([(sh_x, sh_y + 1), (hxf - 2, sh_y + 3), (hxf, hyf)], fill=ROBE, width=2)
    d.rectangle([hxf - 1, hyf - 1, hxf + 1, hyf + 1], fill=SKIN)
    # brazo que cuelga
    hxb = sh_x - 3
    d.line([(sh_x - 1, sh_y + 1), (hxb, sh_y + 7)], fill=ROBE_S, width=2)
    d.rectangle([hxb - 1, sh_y + 7, hxb + 1, sh_y + 8], fill=SKIN_S)

    # cabeza baja y adelante, panuelo
    hx = sh_x + 2
    hy = sh_y + 1
    d.rectangle([sh_x - 1, sh_y, sh_x + 1, sh_y + 2], fill=SKIN_S)
    d.ellipse([hx - 2, hy - 2, hx + 3, hy + 3], fill=SKIN)
    d.polygon([(hx - 3, hy - 3), (hx + 3, hy - 3), (hx + 3, hy + 1),
               (hx + 1, hy + 3), (hx - 3, hy + 2)], fill=SCARF)
    d.point([(hx + 1, hy + 1)], fill=EYE)
    d.line([(hx, hy + 2), (hx + 2, hy + 2)], fill=MOUTH)

    _outline(img)
    return img


# ======================================================================
# ZombieO — obrero, renguera pesada
# ======================================================================
O_SHIRT, O_SHIRT_S = (74, 82, 96, 255), (54, 60, 72, 255)
VEST, VEST_S = (150, 146, 86, 255), (112, 108, 58, 255)
O_PANTS = (78, 74, 58, 255)
BELT = (52, 44, 36, 255)
BOOT = (46, 42, 40, 255)
# casco de obrero: amarillo mugriento (saturación baja, familia de la paleta)
HAT, HAT_S = (194, 178, 104, 255), (150, 136, 74, 255)
HAT_H = (222, 208, 150, 255)


def frame_o(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 15
    lurch = max(0.0, math.sin(ph))                 # peso cayendo sobre la pierna tiesa
    rock = 2.5 * math.sin(ph)
    bob = round(3 * lurch)
    hip_y = 20 + bob

    # pierna tiesa (der): casi vertical, planta, arrastra el talon
    pgx = cx + 3 + round(rock * 0.3)
    d.line([(cx + 2, hip_y + 2), (pgx, 33)], fill=O_PANTS, width=3)
    d.rectangle([pgx - 1, 31, pgx + 3, 33], fill=BOOT)
    # pierna que da el paso (izq)
    sw = math.sin(ph + math.pi)
    lgx = cx - 3 + round(sw * 4)
    lgy = 33 - round(max(0.0, sw) * 4)
    d.line([(cx - 2, hip_y + 2), (lgx, lgy)], fill=O_PANTS, width=3)
    d.rectangle([lgx - 2, lgy - 1, lgx + 2, lgy], fill=BOOT)

    d.rectangle([cx - 4, hip_y - 1, cx + 5, hip_y + 3], fill=O_PANTS)
    d.rectangle([cx - 4, hip_y + 1, cx + 5, hip_y + 2], fill=BELT)

    sh_y = hip_y - 13
    tx = round(rock)
    d.polygon([(cx - 5 + tx, sh_y), (cx + 6 + tx, sh_y),
               (cx + 5, hip_y - 1), (cx - 4, hip_y - 1)], fill=O_SHIRT)
    # chaleco: dos panos claros con la abertura oscura al medio
    d.polygon([(cx - 4 + tx, sh_y + 1), (cx - 1 + tx, sh_y + 1),
               (cx - 1, hip_y - 1), (cx - 4, hip_y - 1)], fill=VEST)
    d.polygon([(cx + 2 + tx, sh_y + 1), (cx + 5 + tx, sh_y + 1),
               (cx + 5, hip_y - 1), (cx + 2, hip_y - 1)], fill=VEST)
    d.line([(cx - 3 + tx, sh_y + 3), (cx - 3, hip_y - 2)], fill=VEST_S)
    d.line([(cx + 4 + tx, sh_y + 3), (cx + 4, hip_y - 2)], fill=VEST_S)

    # brazos con gran balanceo de hombros
    axb = cx - 5 + tx
    hxb = axb - 2 + round(3 * math.sin(ph))
    hyb = sh_y + 13 + bob
    d.line([(axb, sh_y + 1), (hxb, hyb)], fill=O_SHIRT_S, width=3)
    d.rectangle([hxb - 2, hyb, hxb + 1, hyb + 2], fill=SKIN_S)
    axf = cx + 6 + tx
    hxf = axf + 1 + round(3 * math.sin(ph + math.pi))
    hyf = sh_y + 12 + bob
    d.line([(axf, sh_y + 1), (hxf, hyf)], fill=O_SHIRT, width=3)
    d.rectangle([hxf - 1, hyf, hxf + 2, hyf + 2], fill=SKIN)

    # cabeza hundida entre los hombros + casco
    hx = cx + tx + round(math.sin(ph) * 0.5)
    hy = 4 + bob + round(lurch * 1.5)
    d.rectangle([cx + tx, hy + 4, cx + tx + 3, hy + 6], fill=SKIN_S)
    d.ellipse([hx - 3, hy, hx + 4, hy + 6], fill=SKIN)
    d.point([(hx - 1, hy + 3), (hx + 2, hy + 3)], fill=EYE)
    d.line([(hx - 1, hy + 5), (hx + 2, hy + 5)], fill=MOUTH)
    # casco tipo caparazón: domo liso y redondo, sin cresta cónica
    d.chord([hx - 5, hy - 4, hx + 6, hy + 5], 180, 360, fill=HAT)
    d.rectangle([hx - 6, hy, hx + 7, hy + 1], fill=HAT_S)
    d.point([(hx + 2, hy - 1), (hx + 3, hy - 1), (hx + 3, hy)], fill=HAT_S)  # sombra lateral
    d.point([(hx - 2, hy - 2), (hx - 1, hy - 3), (hx, hy - 3)], fill=HAT_H)  # brillo

    _outline(img)
    return img


# ======================================================================
# ZombieJ — corredor volcado al frente, zancada ancha
# ======================================================================
JACKET, JACKET_S = (58, 64, 82, 255), (42, 46, 60, 255)
STRIPE = (158, 66, 66, 255)
J_SHORTS = (48, 52, 64, 255)
SHOE = (182, 178, 170, 255)
J_HAIR = (52, 46, 42, 255)
BAND = (150, 70, 70, 255)


def frame_j(i):
    ph = i / N * TAU
    img, d = _new()
    cx = 14
    pitch = 6                                       # inclinacion fija al frente
    bob = abs(math.sin(ph * 2))
    hip_y = 22 - round(bob * 2)

    # piernas: zancada ancha y rapida, la de atras patea hacia arriba
    for sign, phase in ((-1, 0.0), (1, math.pi)):
        sw = math.sin(ph + phase)
        fx = cx + sign + round(sw * 6)
        fy = 33 - round(max(0.0, -sw) * 5)
        knee_x = cx + sign + round(sw * 3)
        knee_y = hip_y + 6
        d.line([(cx + sign, hip_y + 2), (knee_x, knee_y)], fill=J_SHORTS, width=3)
        d.line([(knee_x, knee_y), (fx, fy)], fill=SKIN_S, width=2)
        d.rectangle([fx - 2, fy - 1, fx + 2, fy], fill=SHOE)

    d.rectangle([cx - 3, hip_y - 1, cx + 3, hip_y + 3], fill=J_SHORTS)

    sh_x = cx + pitch
    sh_y = hip_y - 12
    d.polygon([(sh_x - 3, sh_y), (sh_x + 4, sh_y), (cx + 3, hip_y), (cx - 3, hip_y)], fill=JACKET)
    d.polygon([(sh_x + 1, sh_y), (sh_x + 4, sh_y), (cx + 3, hip_y), (cx + 1, hip_y)], fill=JACKET_S)
    d.line([(sh_x - 2, sh_y + 2), (cx - 1, hip_y - 1)], fill=STRIPE)

    # brazos descoordinados (fases distintas, no opuestas)
    hxf = sh_x + 5 + round(2 * math.sin(ph))
    hyf = sh_y + round(3 * math.sin(ph))
    d.line([(sh_x + 3, sh_y + 1), (hxf, hyf)], fill=JACKET, width=2)
    d.rectangle([hxf - 1, hyf - 1, hxf + 1, hyf + 1], fill=SKIN)
    hxb = sh_x - 4 + round(3 * math.sin(ph + 2.3))
    hyb = sh_y + 8 + round(2 * math.sin(ph + 2.3))
    d.line([(sh_x - 2, sh_y + 1), (hxb, hyb)], fill=JACKET_S, width=2)
    d.rectangle([hxb - 1, hyb, hxb + 1, hyb + 1], fill=SKIN_S)

    # cabeza volcada, mirando el piso, vincha
    hx = sh_x + 2 + round(math.sin(ph) * 0.5)
    hy = sh_y - 3 + round(bob)
    d.rectangle([sh_x, sh_y - 1, sh_x + 2, sh_y + 1], fill=SKIN_S)
    d.ellipse([hx - 3, hy - 2, hx + 3, hy + 4], fill=SKIN)
    d.polygon([(hx - 3, hy - 3), (hx + 3, hy - 3), (hx + 3, hy - 1), (hx - 3, hy - 1)], fill=J_HAIR)
    d.line([(hx - 3, hy - 1), (hx + 3, hy - 1)], fill=BAND)
    d.point([(hx - 1, hy + 1), (hx + 2, hy + 1)], fill=EYE)
    d.line([(hx, hy + 3), (hx + 2, hy + 3)], fill=MOUTH)

    _outline(img)
    return img


ZOMBIES = {
    "N": frame_n,
    "V": frame_v,
    "O": frame_o,
    "J": frame_j,
}


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
