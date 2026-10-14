#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_player.py  —  personaje principal ("Val", el/la sobreviviente inmune).

Mismo estilo que los zombies (32x34, contorno 1px, paleta noche), pero
humano: piel cálida, campera naranja óxido (resalta sobre el fondo azul),
jean oscuro, botas.

20 frames repartidos en 6 animaciones:
  Idle  : 4   (respiración sutil)
  Run   : 6   (ciclo de carrera con inclinación y rebote)
  Jump  : 4   (agache -> impulso estirado -> subida -> pico)  <- cuidado acá
  Fall  : 2   (caída con piernas abiertas -> pre-aterrizaje)
  Hit   : 1   (retroceso)
  Death : 3   (tambaleo -> se dobla -> en el piso)

Archivos:
  game/assets/Player/Player_Idle_1..4.png
  game/assets/Player/Player_Run_1..6.png
  game/assets/Player/Player_Jump_1..4.png
  game/assets/Player/Player_Fall_1..2.png
  game/assets/Player/Player_Hit_1.png
  game/assets/Player/Player_Death_1..3.png
  game/assets/Player/player_sheet.png   (referencia, 20 frames en fila)

Ancla top-left (como todo GDevelop). En las animaciones con los pies en
el piso, los pies quedan en y~33. En Jump/Fall el personaje está en el
aire: el cuerpo se dibuja algo más arriba pero centrado, para que la
transición desde Idle/Run no pegue un salto.

Tech: Python 3 + Pillow.
Uso:  python3 scripts/gen_player.py    (desde la raíz del repo)
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/Player"
os.makedirs(OUT, exist_ok=True)

W, H = 32, 34
CX = 15
TAU = math.tau

OUTL   = (24, 24, 34, 255)
SKIN   = (226, 178, 140, 255)
SKIN_S = (183, 138, 108, 255)
HAIR   = (72, 52, 42, 255)
JACK   = (198, 106, 62, 255)
JACK_S = (150, 74, 44, 255)
SHIRT  = (206, 202, 190, 255)
JEAN   = (58, 68, 96, 255)
JEAN_S = (40, 48, 72, 255)
BOOT   = (44, 40, 46, 255)
EYE    = (30, 30, 40, 255)


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
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128 \
                        and px[nx, ny] != OUTL:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = OUTL


def _blank():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def limb(d, a, b, c, col, w=2):
    d.line([a, b], fill=col, width=w)
    d.line([b, c], fill=col, width=w)


def draw_figure(d, *, hip, sho, head, footL, footR, handL, handR,
                kneeL=None, kneeR=None, elbL=None, elbR=None, face_dx=1,
                sw=3, hw=3):
    """sw / hw = medio-ancho de hombros y cadera (squash: subir / stretch: bajar)."""
    hx, hy = hip
    sx, sy = sho
    hdx, hdy = head
    kneeL = kneeL or ((hx + footL[0]) // 2 - 1, (hy + footL[1]) // 2)
    kneeR = kneeR or ((hx + footR[0]) // 2 + 1, (hy + footR[1]) // 2)
    elbL = elbL or ((sx + handL[0]) // 2, (sy + handL[1]) // 2)
    elbR = elbR or ((sx + handR[0]) // 2, (sy + handR[1]) // 2)

    # pierna trasera / brazo trasero (más oscuros)
    limb(d, (hx - 1, hy), kneeL, footL, JEAN_S, 3)
    d.rectangle([footL[0] - 2, footL[1] - 1, footL[0] + 1, footL[1]], fill=BOOT)
    limb(d, (sx - 1, sy + 1), elbL, handL, JACK_S, 2)
    d.rectangle([handL[0] - 1, handL[1] - 1, handL[0], handL[1]], fill=SKIN_S)

    # torso (campera)
    d.polygon([(sx - sw, sy), (sx + sw, sy), (hx + hw, hy + 1), (hx - hw, hy + 1)], fill=JACK)
    d.polygon([(sx, sy), (sx + sw, sy), (hx + hw, hy + 1), (hx, hy + 1)], fill=JACK_S)
    d.line([(sx - 1, sy + 1), (hx - 1, hy)], fill=SHIRT)          # cierre / remera

    # pierna delantera / brazo delantero
    limb(d, (hx + 1, hy), kneeR, footR, JEAN, 3)
    d.rectangle([footR[0] - 2, footR[1] - 1, footR[0] + 2, footR[1]], fill=BOOT)

    # cabeza (compacta: casquete de pelo + cara, cuello corto)
    d.rectangle([sx - 1, sy - 1, sx, sy], fill=SKIN_S)             # cuello 1px
    hcx, hcy = sx + hdx, sy - 4 + hdy
    d.ellipse([hcx - 3, hcy - 3, hcx + 2, hcy + 3], fill=SKIN)     # cara r~3
    d.ellipse([hcx - 3, hcy - 4, hcx + 2, hcy + 0], fill=HAIR)     # casquete (chato)
    d.point([(hcx - 3, hcy), (hcx - 3, hcy + 1),
             (hcx + 2, hcy), (hcx + 2, hcy + 1)], fill=HAIR)       # patillas cortas
    d.point([(hcx + face_dx, hcy)], fill=EYE)                      # ojo (3/4)

    limb(d, (sx + 1, sy + 1), elbR, handR, JACK, 2)
    d.rectangle([handR[0] - 1, handR[1] - 1, handR[0] + 1, handR[1]], fill=SKIN)


# ---------------- animaciones ----------------

def idle(i):
    d = ImageDraw.Draw(img := _blank())
    br = [0, -1, 0, -1][i]                       # respiración
    hy = 21 + (0 if br == 0 else 0)
    draw_figure(
        d, hip=(CX + 1, hy), sho=(CX + 1, 12 + br), head=(1, br),
        footL=(CX - 2, 33), footR=(CX + 3, 33),
        handL=(CX - 2, 20 + br), handR=(CX + 4, 20 + br))
    _outline(img)
    return img


def run(i):
    """6 keyframes: CONTACTO-D, EMPUJE-D, AIRE, CONTACTO-I, EMPUJE-I, AIRE.
    (ref: SLYNYRD Pixelblog 8 + sprite-ai). En AIRE ningún pie toca el
    piso y el cuerpo está en su punto más alto; el brazo que va adelante
    sube 'de trompada' para maximizar la acción. Inclinación 3px.
    """
    d = ImageDraw.Draw(img := _blank())
    # por frame: hipY, shoY, pie_adelante, pie_atras, mano_adelante, mano_atras
    F = [
        (21, 12, (CX + 5, 33), (CX - 3, 31), (CX + 6, 14), (CX - 3, 20)),
        (19, 10, (CX + 1, 33), (CX - 4, 27), (CX + 2, 17), (CX - 1, 15)),
        (18,  9, (CX + 3, 26), (CX - 2, 24), (CX + 7, 12), (CX - 2, 18)),
        (21, 12, (CX - 3, 32), (CX + 5, 31), (CX - 3, 14), (CX + 6, 20)),
        (19, 10, (CX - 1, 33), (CX + 4, 27), (CX - 2, 17), (CX + 1, 15)),
        (18,  9, (CX - 2, 26), (CX + 3, 24), (CX - 3, 12), (CX + 7, 18)),
    ][i]
    hipY, shoY, footF, footB, handF, handB = F
    right_leads = i < 3          # frames 0-2: pierna/pie derecho adelante
    draw_figure(
        d, hip=(CX + 1, hipY), sho=(CX + 3, shoY), head=(2, 0), face_dx=2,
        footR=footF if right_leads else footB,
        footL=footB if right_leads else footF,
        handR=handF if right_leads else handB,
        handL=handB if right_leads else handF)
    _outline(img)
    return img


def jump(i):
    """4 frames: anticipación (squash) -> impulso (stretch) -> subida ->
    pico. (ref: squash -2px + ancho; stretch +2px + angosto).
    """
    d = ImageDraw.Draw(img := _blank())
    if i == 0:      # ANTICIPACIÓN: se aplasta y ensancha, rodillas afuera
        draw_figure(
            d, hip=(CX + 1, 26), sho=(CX + 1, 20), head=(0, 2), sw=4, hw=4,
            footL=(CX - 4, 33), footR=(CX + 4, 33),
            kneeL=(CX - 6, 29), kneeR=(CX + 6, 29),
            handL=(CX - 5, 28), handR=(CX + 6, 27))
    elif i == 1:    # IMPULSO: máximo stretch, cuerpo alto y angosto, brazos rectos arriba
        draw_figure(
            d, hip=(CX + 1, 22), sho=(CX + 1, 7), head=(0, -2), sw=2, hw=2,
            footL=(CX - 2, 33), footR=(CX + 1, 31),
            kneeL=(CX - 3, 28), kneeR=(CX + 2, 27),
            handL=(CX - 2, 1), handR=(CX + 3, 0),
            elbL=(CX - 3, 4), elbR=(CX + 4, 4))
    elif i == 2:    # SUBIDA: piernas recogiéndose, brazos bajando de arriba
        draw_figure(
            d, hip=(CX + 1, 19), sho=(CX + 1, 9), head=(0, -1), sw=2,
            footL=(CX - 3, 25), footR=(CX + 4, 22),
            kneeL=(CX - 5, 21), kneeR=(CX + 6, 18),
            handL=(CX - 5, 6), handR=(CX + 6, 5))
    else:           # PICO: hang time, relajado, brazos abiertos al medio
        draw_figure(
            d, hip=(CX + 1, 19), sho=(CX + 1, 10), head=(0, 0),
            footL=(CX - 3, 27), footR=(CX + 3, 26),
            kneeL=(CX - 4, 23), kneeR=(CX + 5, 22),
            handL=(CX - 6, 16), handR=(CX + 7, 15))
    _outline(img)
    return img


def fall(i):
    d = ImageDraw.Draw(img := _blank())
    if i == 0:      # CAÍDA: cuerpo estirado, piernas EXTENDIDAS buscando el piso
        draw_figure(
            d, hip=(CX + 1, 19), sho=(CX + 1, 9), head=(0, 1), sw=2,
            footL=(CX - 3, 32), footR=(CX + 4, 31),
            kneeL=(CX - 4, 26), kneeR=(CX + 5, 25),
            handL=(CX - 6, 12), handR=(CX + 7, 11))
    else:           # PRE-ATERRIZAJE: piernas juntas y flexionadas para amortiguar
        draw_figure(
            d, hip=(CX + 1, 23), sho=(CX + 1, 15), head=(0, 1), sw=4, hw=4,
            footL=(CX - 2, 33), footR=(CX + 3, 33),
            kneeL=(CX - 4, 29), kneeR=(CX + 5, 29),
            handL=(CX - 4, 20), handR=(CX + 6, 19))
    _outline(img)
    return img


def hit():
    d = ImageDraw.Draw(img := _blank())
    draw_figure(
        d, hip=(CX, 21), sho=(CX - 1, 13), head=(-2, -1),      # cabeza hacia atrás
        footL=(CX - 4, 33), footR=(CX + 2, 33),
        handL=(CX - 4, 9), handR=(CX + 3, 8), face_dx=-2)      # brazos defensa
    _outline(img)
    return img


def death(i):
    d = ImageDraw.Draw(img := _blank())
    if i == 0:      # tambaleo
        draw_figure(
            d, hip=(CX - 1, 21), sho=(CX - 2, 12), head=(-3, -1),
            footL=(CX - 5, 33), footR=(CX + 3, 33),
            handL=(CX - 6, 10), handR=(CX + 5, 9), face_dx=-2)
    elif i == 1:    # se dobla
        draw_figure(
            d, hip=(CX - 1, 26), sho=(CX - 3, 20), head=(-4, 2),
            footL=(CX - 4, 33), footR=(CX + 4, 33),
            kneeL=(CX - 6, 30), kneeR=(CX + 6, 30),
            handL=(CX - 6, 26), handR=(CX + 4, 27), face_dx=-2)
    else:           # en el piso (tirado a lo ancho)
        dd = ImageDraw.Draw(img)
        dd.polygon([(4, 30), (26, 30), (26, 33), (4, 33)], fill=JACK)
        dd.rectangle([18, 29, 26, 33], fill=JEAN)
        dd.ellipse([2, 27, 8, 33], fill=SKIN)                  # cabeza de costado
        dd.ellipse([1, 26, 7, 31], fill=HAIR)
    _outline(img)
    return img


ANIMS = {
    "Idle":  [idle(i) for i in range(4)],
    "Run":   [run(i) for i in range(6)],
    "Jump":  [jump(i) for i in range(4)],
    "Fall":  [fall(i) for i in range(2)],
    "Hit":   [hit()],
    "Death": [death(i) for i in range(3)],
}


def main():
    total = 0
    seq = []
    for name, frames in ANIMS.items():
        for k, f in enumerate(frames, 1):
            f.save(f"{OUT}/Player_{name}_{k}.png")
            seq.append(f)
            total += 1
        print(f"  {name}: {len(frames)} frames")
    sheet = Image.new("RGBA", (W * total, H), (0, 0, 0, 0))
    for k, f in enumerate(seq):
        sheet.paste(f, (k * W, 0))
    sheet.save(f"{OUT}/player_sheet.png")
    print(f"total {total} frames  ->  {OUT}/")


if __name__ == "__main__":
    main()
