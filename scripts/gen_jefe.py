#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_jefe.py  —  Paciente Zero definitivo (18/10): el jefe deja de ser el
zombie T agrandado. Es una masa viral (la paleta del virus del juego, con su
corona de espículas) con el paciente original fundido adelante: cara, un
brazo que se estira, restos de la bata del hospital y la pulsera de
internación. En vez de piernas, seudópodos que se arrastran. Mutado, no
humanoide (decisión del usuario).

Sprite nativo de 64x68 (el tamaño con el que se jugaba el jefe, así no
cambian la colisión ni que no se pueda saltar: Lio salta 37). Mira a la
DERECHA (los eventos lo espejan con FlipX cuando va a la izquierda). Los pies
tocan la última fila.

Animaciones (cada una cuenta en qué estado de la pelea está):
  jefe_walk_1..6      se arrastra hacia Lio (estado 0 y la embestida)
  jefe_carga_1..3     se hincha y estira las espículas antes de embestir
                      (estado 1: el aviso se lee en la forma, no solo en el contorno)
  jefe_expuesto_1..4  aturdido: espículas caídas, ojos en cruz y un NÚCLEO VERDE
                      abierto arriba que late: "pisame acá" (estado 3, la única
                      ventana de pisotón)

Paleta: contorno y piel = zombies del juego; masa = virus_1.png; verde = el
de los tanques y los halos del lab. Sombreado con tramado Bayer 4x4.
Uso:  python3 scripts/gen_jefe.py   (crea game/assets/Jefe/)
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/Jefe"
os.makedirs(OUT, exist_ok=True)
W, H = 64, 68
T = (0, 0, 0, 0)
OUTLINE = (24, 24, 34, 255)
# masa viral (virus_1.png) de sombra a luz
VIR = [(96, 30, 44, 255), (140, 44, 60, 255), (176, 58, 74, 255), (206, 82, 96, 255),
       (232, 114, 124, 255), (250, 156, 164, 255)]
VEIN = (78, 22, 36, 255)
PUS = (196, 210, 120, 255)                 # pústulas (amarillo verdoso)
# paciente (piel de los zombies)
SKIN = [(70, 96, 74, 255), (108, 150, 116, 255), (150, 190, 150, 255), (186, 214, 180, 255)]
EYE = (214, 74, 74, 255)
EYE_HI = (255, 170, 150, 255)
MOUTH = (60, 20, 26, 255)
TOOTH = (220, 214, 190, 255)
GOWN = [(96, 116, 138, 255), (136, 158, 180, 255), (176, 196, 214, 255)]   # bata celeste
BAND = (236, 236, 228, 255)                # pulsera de internación
BAND_TAG = (214, 74, 74, 255)
CORE = [(40, 110, 60, 255), (70, 170, 90, 255), (140, 230, 140, 255), (220, 255, 210, 255)]
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def shade(levels, t, x, y):
    """t en 0..1 → color de la lista con tramado entre escalones."""
    t = max(0.0, min(0.999, t))
    q = t * (len(levels) - 1)
    i = int(q)
    frac = q - i
    j = min(i + 1, len(levels) - 1)
    return levels[j] if frac * 16 > BAYER[y % 4][x % 4] else levels[i]


def outline(img):
    """contorno de 1 px alrededor de todo lo opaco (como los zombies)."""
    src = img.copy()
    px, sp = img.load(), src.load()
    for y in range(H):
        for x in range(W):
            if sp[x, y][3] == 0 and any(
                    0 <= x + dx < W and 0 <= y + dy < H and sp[x + dx, y + dy][3] > 0
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = OUTLINE
    return img


def body(img, cx, cy, rx, ry):
    """masa viral: elipse sombreada (luz arriba-izquierda), venas y pústulas."""
    px = img.load()
    for y in range(H):
        for x in range(W):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            r = dx * dx + dy * dy
            if r <= 1:
                # luz arriba-izquierda; abajo-derecha en sombra (volumen). El centro
                # cae en un solo escalón (menos ruido de tramado)
                light = 0.50 - 0.38 * dx - 0.50 * dy - 0.30 * r
                px[x, y] = shade(VIR, light, x, y)
    d = ImageDraw.Draw(img)
    # venas oscuras
    for pts in ([(cx - 12, cy - 4), (cx - 6, cy + 2), (cx - 8, cy + 9)],
                [(cx - 2, cy - 12), (cx + 3, cy - 6), (cx + 1, cy)],
                [(cx - 14, cy + 6), (cx - 9, cy + 12)]):
        d.line(pts, fill=VEIN)
    # pústulas
    for (x, y) in ((cx - 10, cy - 8), (cx - 15, cy + 2), (cx - 4, cy + 10), (cx + 2, cy - 14)):
        d.point((x, y), fill=PUS)
        d.point((x + 1, y), fill=VIR[5])


def spikes(img, cx, cy, rx, ry, length, droop=0.0, pulse=0):
    """corona de espículas (como el virus): tallo + bulbo, en la mitad de atrás y arriba."""
    d = ImageDraw.Draw(img)
    for k in range(9):
        a = math.radians(100 + k * 24)                 # de arriba (100°) hacia atrás y abajo
        L = length + (pulse if k % 2 else 0)
        ex, ey = cx + math.cos(a) * rx, cy - math.sin(a) * ry
        # caídas: la punta baja (aturdido)
        tx = ex + math.cos(a) * L
        ty = ey - math.sin(a) * L + droop * L
        d.line([(ex, ey), (tx, ty)], fill=VIR[1], width=2)
        d.rectangle([tx - 1, ty - 1, tx + 1, ty + 1], fill=VIR[4])
        d.point((tx - 1, ty - 1), fill=VIR[5])


def tentacles(img, cx, base_y, phase, spread=1.0):
    """seudópodos: 4 de la base de la masa al piso, ondulando (desfasados)."""
    px = img.load()
    for k, ox in enumerate((-15, -6, 3, 12)):
        x0 = cx + ox * spread
        for y in range(int(base_y), H):
            t = (y - base_y) / max(1, H - 1 - base_y)
            sway = math.sin(phase + k * 1.6) * 4 * t
            w = 4.5 - 2.5 * t
            xc = x0 + sway + (3 if k >= 2 else -3) * t      # se abren hacia afuera
            for x in range(int(xc - w / 2), int(xc + w / 2) + 1):
                if 0 <= x < W:
                    px[x, y] = shade(VIR, 0.45 - 0.3 * t + (0.15 if x < xc else 0), x, y)


def patient(img, cx, cy, eyes="rojo", arm=0.0, mouth=1.0):
    """el paciente fundido adelante (derecha): cara, bata, brazo con la pulsera."""
    d = ImageDraw.Draw(img)
    px = img.load()
    fx, fy = cx + 15, cy - 9                            # centro de la cara
    # restos de la bata: tela que envuelve el frente de la masa, con el borde de
    # abajo roto (dientes) y dos jirones colgando; arriba se pierde en la masa
    rnd = [0, 2, 1, 3, 0, 2, 4, 1, 2, 0, 3, 1, 2, 0, 1, 3]
    for i in range(16):
        x = cx + 1 + i
        top = cy + 2 - i // 3
        bot = cy + 11 - i // 4 - rnd[i]                  # borde roto
        for yy in range(top, bot):
            if 0 <= x < W and 0 <= yy < H and px[x, yy][3]:
                fold = 0.18 if (x + yy // 3) % 5 == 0 else 0.0  # pliegues
                px[x, yy] = shade(GOWN, 0.72 - (yy - top) * 0.05 - fold, x, yy)
        if i in (3, 10):                                 # jirones
            for yy in range(bot, bot + 4):
                if 0 <= yy < H:
                    px[x, yy] = GOWN[0]
    for (x, y) in ((cx + 4, cy + 4), (cx + 9, cy + 3), (cx + 13, cy + 1)):  # estampado de la bata
        d.point((x, y), fill=GOWN[0])
    # cara (óvalo) que sale de la masa
    for y in range(fy - 8, fy + 8):
        for x in range(fx - 6, fx + 7):
            ex, ey = (x + 0.5 - fx) / 6.5, (y + 0.5 - fy) / 8
            if ex * ex + ey * ey <= 1:
                px[x, y] = shade(SKIN, 0.75 - 0.35 * ex - 0.4 * ey, x, y)
    # ojos
    for ox in (-2, 3):
        x, y = fx + ox, fy - 2
        if eyes == "cruz":
            d.line([(x - 1, y - 1), (x + 1, y + 1)], fill=MOUTH)
            d.line([(x - 1, y + 1), (x + 1, y - 1)], fill=MOUTH)
        else:
            d.rectangle([x - 1, y - 1, x + 1, y], fill=EYE)
            if eyes == "brillo":
                d.point((x, y - 1), fill=EYE_HI)
                d.point((x - 1, y - 1), fill=EYE_HI)
    # boca abierta con dientes
    mh = max(1, round(3 * mouth))
    d.rectangle([fx - 2, fy + 3, fx + 3, fy + 3 + mh], fill=MOUTH)
    d.point((fx - 1, fy + 3), fill=TOOTH)
    d.point((fx + 2, fy + 3), fill=TOOTH)
    # brazo: del hombro (frente de la masa) hacia adelante y abajo, con garras
    sx, sy = cx + 18, cy + 4
    hx, hy = sx + 10 + round(3 * arm), sy + 12 - round(4 * arm)
    d.line([(sx, sy), (hx, hy)], fill=SKIN[1], width=4)
    d.line([(sx, sy - 1), (hx, hy - 1)], fill=SKIN[2], width=1)
    d.rectangle([hx - 2, hy - 2, hx + 1, hy + 1], fill=SKIN[1])        # mano
    for gx in (-1, 1, 3):                                              # garras
        d.line([(hx + gx, hy + 1), (hx + gx + 1, hy + 4)], fill=TOOTH)
    # pulsera de internación en la muñeca
    bx, by = (sx + hx) // 2 + 3, (sy + hy) // 2 + 3
    d.rectangle([bx - 1, by - 2, bx + 1, by + 1], fill=BAND)
    d.point((bx, by - 1), fill=BAND_TAG)


def core(img, cx, top_y, beat):
    """núcleo verde abierto arriba (solo en Expuesto): el blanco del pisotón."""
    d = ImageDraw.Draw(img)
    r = 5 + beat
    d.ellipse([cx - r - 1, top_y - 2, cx + r + 1, top_y + 6], fill=VEIN)        # herida
    d.ellipse([cx - r, top_y - 1, cx + r, top_y + 5], fill=CORE[1])
    d.ellipse([cx - r + 2, top_y, cx + r - 2, top_y + 3], fill=CORE[2])
    d.point((cx - 1, top_y + 1), fill=CORE[3])
    d.point((cx, top_y + 1), fill=CORE[3])


def frame(kind, k):
    img = Image.new("RGBA", (W, H), T)
    cx, cy, rx, ry = 27, 36, 21, 20
    if kind == "walk":
        bob = round(math.sin(k / 6 * 2 * math.pi) * 1)
        cy += bob
        spikes(img, cx, cy, rx, ry, 6, pulse=1 if k % 3 == 0 else 0)
        body(img, cx, cy, rx, ry)
        tentacles(img, cx, cy + ry - 4, k / 6 * 2 * math.pi)
        patient(img, cx, cy, eyes="rojo", arm=math.sin(k / 6 * 2 * math.pi), mouth=0.6 + 0.4 * (k % 2))
    elif kind == "carga":
        grow = k                                        # se hincha cuadro a cuadro
        rx2, ry2 = rx + grow, ry + grow
        spikes(img, cx, cy - grow, rx2, ry2, 7 + 2 * k)
        body(img, cx, cy - grow, rx2, ry2)
        tentacles(img, cx, cy - grow + ry2 - 4, 0.5, spread=1.0 + 0.08 * k)
        patient(img, cx - grow // 2, cy - grow, eyes="brillo", arm=-1.0, mouth=1.4)
    else:                                               # expuesto: aplastado, aturdido
        sq = 3
        cy2, ry2, rx2 = cy + sq, ry - sq, rx + 2
        spikes(img, cx, cy2, rx2, ry2, 4, droop=0.9)
        body(img, cx, cy2, rx2, ry2)
        tentacles(img, cx, cy2 + ry2 - 3, math.pi / 2, spread=1.25)
        patient(img, cx, cy2 + 2, eyes="cruz", arm=-0.6, mouth=0.4)
        core(img, cx - 2, cy2 - ry2 + 2, beat=1 if k % 2 else 0)
    return outline(img)


def main():
    for kind, n in (("walk", 6), ("carga", 3), ("expuesto", 4)):
        for k in range(n):
            frame(kind, k).save(f"{OUT}/jefe_{kind}_{k + 1}.png")
    print(f"jefe_walk_1..6, jefe_carga_1..3, jefe_expuesto_1..4  ->  {OUT}/")


if __name__ == "__main__":
    main()
