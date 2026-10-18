#!/usr/bin/env python3
"""
gen_lab_subsuelo.py  —  el "bloque negro" debajo del piso del laboratorio
(Nivel 2 / arena del Nivel 3) pasa a ser el corte del edificio: losa,
entretecho de servicios (ducto de ventilación, cañerías, vigas) y una sala de
contención con coronavirus encerrados en tubos de vidrio.

Mismo criterio que gen_lab.py: Pillow, sin IA de imagen ni packs; paleta del
lab (los colores se repiten acá para no importar gen_lab, que al importarse
regeneraría todo).

Qué crea (en game/assets/Lab/):
  - lab_subsuelo.png    128x80 : corte bajo el piso, tileable en X. Va sobre el
                                 cuerpo del Ground (filas 16..95 de
                                 lab_floor.png), del mismo ancho que cada
                                 tramo de piso.
  - contencion_0..3.png  24x40 : tubo de contención con líquido verde y un
                                 virus que flota adentro (4 cuadros: el virus
                                 sube y baja y gira).
  - contencion_rota_0..3.png   : el mismo tubo con el vidrio rajado y el
                                 líquido más bajo (los que se rompen).
  - contencion_vacia.png  24x40 : el tubo roto después de estallar (sin virus,
                                 vidrio partido, charco en el fondo).
  - contencion_glow.png  48x56 : halo verde detrás del tubo.
  - escotilla_borde.png   4x16 : franja de peligro a los lados de la boca del
                                 ducto jugable (Nivel 2).

Uso:  python3 scripts/gen_lab_subsuelo.py      (desde la raíz del repo)
"""
from PIL import Image, ImageDraw
import random
import os

OUT = "game/assets/Lab"
os.makedirs(OUT, exist_ok=True)

# --- paleta del lab (= gen_lab.py) ---
WALL_DK = (22, 34, 40, 255)
WALL = (30, 45, 52, 255)
SEAM = (16, 25, 30, 255)
STRIPE = (54, 92, 88, 255)
METAL_LIT = (120, 132, 140, 255)
METAL = (78, 88, 98, 255)
METAL_DK = (44, 50, 58, 255)
TANK_GLASS = (60, 90, 96, 255)
LIQUID = (70, 170, 90, 255)
LIQUID_HI = (140, 230, 140, 255)
FLOOR_GAP = (56, 64, 70, 255)

# --- propios del subsuelo (más oscuros: está "abajo", sin luz de la sala) ---
CAV = (12, 18, 22, 255)          # fondo del entretecho
CAV_HI = (18, 26, 31, 255)
SLAB = (40, 48, 54, 255)         # canto inferior de la losa
SLAB_DK = (28, 34, 40, 255)
DUCT_LIT = (92, 102, 110, 255)
DUCT = (60, 68, 76, 255)
DUCT_DK = (36, 42, 50, 255)
PIPE_TOX = (52, 96, 64, 255)     # caño de residuos (verde)
PIPE_TOX_HI = (88, 150, 96, 255)
PIPE_RED = (98, 44, 48, 255)     # caño de incendio
PIPE_RED_HI = (150, 70, 70, 255)
HAZ_Y = (170, 140, 36, 255)      # franja de peligro (= wet_sign oscuro)
HAZ_K = (20, 20, 24, 255)
GRATE = (34, 40, 46, 255)
GLOW_G = (70, 170, 90)

VIRUS = "game/assets/Virus/virus_1.png"


def lerp(a, b, t):
    return tuple(int(x * (1 - t) + y * t) for x, y in zip(a[:3], b[:3])) + (255,)


def lab_subsuelo():
    w, h = 128, 80
    rnd = random.Random(2610)
    img = Image.new("RGBA", (w, h), CAV)
    d = ImageDraw.Draw(img)

    # fondo del entretecho: paneles con juntas, más oscuro hacia abajo
    for y in range(h):
        t = min(1.0, y / (h - 1))
        d.line([(0, y), (w, y)], fill=lerp(CAV_HI, (6, 9, 12), t))
    for x in range(0, w, 32):
        d.line([(x, 8), (x, h)], fill=SEAM)

    # losa: continúa el piso de arriba (lab_floor fila 16 = WALL_DK)
    d.rectangle([0, 0, w, 5], fill=SLAB)
    d.line([(0, 0), (w, 0)], fill=WALL_DK)
    d.line([(0, 5), (w, 5)], fill=SLAB_DK)
    for x in range(4, w, 16):            # bulones de la losa
        d.point((x, 3), fill=METAL)

    # vigas doble T cada 64 px (de la losa al piso de rejilla)
    for bx in (20, 84):
        d.rectangle([bx - 3, 6, bx + 3, 7], fill=METAL_DK)
        d.rectangle([bx - 1, 8, bx + 1, 66], fill=METAL_DK)
        d.line([(bx - 1, 8), (bx - 1, 66)], fill=METAL)
        d.rectangle([bx - 3, 66, bx + 3, 67], fill=METAL_DK)

    # ducto de ventilación grande (y 9..24), secciones de 32 px con brida
    d.rectangle([0, 9, w, 24], fill=DUCT)
    d.line([(0, 9), (w, 9)], fill=DUCT_LIT)
    d.line([(0, 10), (w, 10)], fill=DUCT_LIT)
    d.line([(0, 23), (w, 23)], fill=DUCT_DK)
    d.line([(0, 24), (w, 24)], fill=SEAM)
    for x in range(0, w, 32):
        d.rectangle([x, 8, x + 1, 25], fill=DUCT_DK)
        d.point((x, 12), fill=DUCT_LIT)
        d.point((x, 21), fill=DUCT_LIT)
    # rejilla del ducto (deja ver adentro, oscuro)
    for gx in (44, 108):
        d.rectangle([gx, 13, gx + 11, 20], fill=SEAM)
        for yy in range(14, 20, 2):
            d.line([(gx + 1, yy), (gx + 10, yy)], fill=DUCT_DK)

    # cañerías (y 28 y 32): residuos verde y red de incendio
    d.line([(0, 28), (w, 28)], fill=PIPE_TOX_HI)
    d.rectangle([0, 29, w, 30], fill=PIPE_TOX)
    d.line([(0, 33), (w, 33)], fill=PIPE_RED_HI)
    d.line([(0, 34), (w, 34)], fill=PIPE_RED)
    for x in (10, 74):                    # abrazaderas
        d.rectangle([x, 27, x + 1, 35], fill=METAL_DK)
    # válvula en el caño verde
    d.rectangle([56, 26, 60, 31], fill=METAL)
    d.line([(55, 25), (61, 25)], fill=METAL_LIT)

    # franja de peligro sobre la sala de contención
    for x in range(w):
        d.line([(x, 38), (x, 40)], fill=HAZ_Y if ((x // 4) % 2 == 0) else HAZ_K)
    d.line([(0, 41), (w, 41)], fill=SEAM)

    # piso de rejilla de la sala (y 66..69) y debajo, oscuro
    d.rectangle([0, 66, w, 69], fill=GRATE)
    d.line([(0, 66), (w, 66)], fill=METAL_DK)
    for x in range(0, w, 3):
        d.point((x, 68), fill=SEAM)
    for y in range(70, h):
        t = (y - 70) / (h - 70)
        d.line([(0, y), (w, y)], fill=lerp((10, 14, 18), (4, 6, 8), t))

    # goteras / manchas (detalle chico, determinístico)
    for _ in range(10):
        x, y = rnd.randrange(w), rnd.randrange(43, 64)
        d.point((x, y), fill=CAV_HI)
    img.save(f"{OUT}/lab_subsuelo.png")


def _tube(rota=False):
    """Tubo vacío (sin virus). 24x40: tapa 0..4, vidrio 5..33, base 34..39."""
    w, h = 24, 40
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # vidrio + líquido
    top_liq = 15 if rota else 9
    d.rectangle([3, 5, 20, 33], fill=TANK_GLASS[:3] + (150,))
    d.rectangle([4, top_liq, 19, 33], fill=LIQUID[:3] + (210,))
    d.line([(4, top_liq), (19, top_liq)], fill=LIQUID_HI)
    # burbujas
    for (bx, by) in ((7, 28), (15, 22), (10, 17), (16, 30)):
        if by > top_liq + 1:
            d.point((bx, by), fill=LIQUID_HI)
    # bordes del vidrio + reflejo
    d.line([(3, 5), (3, 33)], fill=METAL_DK)
    d.line([(20, 5), (20, 33)], fill=METAL_DK)
    d.line([(5, 6), (5, 31)], fill=(190, 230, 220, 150))
    # tapa y base metálicas
    d.rectangle([1, 0, 22, 4], fill=METAL)
    d.line([(1, 0), (22, 0)], fill=METAL_LIT)
    d.line([(1, 4), (22, 4)], fill=METAL_DK)
    d.rectangle([0, 34, 23, 39], fill=METAL)
    d.line([(0, 34), (23, 34)], fill=METAL_LIT)
    d.rectangle([0, 38, 23, 39], fill=METAL_DK)
    d.point((4, 36), fill=(200, 60, 60, 255))     # lucecita de estado
    d.point((19, 36), fill=LIQUID_HI)
    if rota:
        crack = (220, 240, 235, 255)
        pts = [(14, 6), (12, 10), (15, 13), (11, 18), (13, 21)]
        d.line(pts, fill=crack)
        d.line([(12, 10), (8, 12)], fill=crack)
        d.line([(15, 13), (18, 15)], fill=crack)
        d.point((16, 7), fill=crack)
        d.point((7, 20), fill=crack)
        # charquito verde que gotea por la base
        d.line([(15, 34), (15, 37)], fill=LIQUID_HI)
    return img


def contencion():
    vir = Image.open(VIRUS).convert("RGBA")
    # 4 cuadros: el virus flota (dy) y gira (rot) dentro del líquido
    frames = [(0, 0), (-1, 90), (-2, 180), (-1, 270)]
    for rota in (False, True):
        base = _tube(rota)
        for i, (dy, rot) in enumerate(frames):
            img = base.copy()
            v = vir.rotate(rot)
            # el virus se ve a través del líquido: un poco apagado
            px = v.load()
            for yy in range(v.height):
                for xx in range(v.width):
                    r, g, b, a = px[xx, yy]
                    if a:
                        px[xx, yy] = (int(r * .85), int(g * .9 + 10), int(b * .85), a)
            img.alpha_composite(v, (4, 17 + dy + (2 if rota else 0)))
            name = "contencion_rota" if rota else "contencion"
            img.save(f"{OUT}/{name}_{i}.png")


def contencion_vacia():
    """El tubo roto después de estallar: sin virus, vidrio partido arriba,
    charco de líquido en el fondo."""
    w, h = 24, 40
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # vidrio que quedó: solo la mitad de abajo, con borde dentado
    jag = [22, 19, 24, 20, 17, 21, 25, 18, 22, 20, 23, 19, 21, 24, 20, 22, 18, 21]
    for i, x in enumerate(range(3, 21)):
        d.line([(x, jag[i]), (x, 33)], fill=TANK_GLASS[:3] + (110,))
        d.point((x, jag[i]), fill=(200, 235, 228, 220))
    d.line([(3, 22), (3, 33)], fill=METAL_DK)
    d.line([(20, 20), (20, 33)], fill=METAL_DK)
    # restos de líquido en el fondo
    d.rectangle([4, 30, 19, 33], fill=LIQUID[:3] + (200,))
    d.line([(4, 30), (19, 30)], fill=LIQUID_HI)
    # tapa (torcida) y base
    d.rectangle([1, 1, 22, 4], fill=METAL)
    d.line([(1, 1), (22, 0)], fill=METAL_LIT)
    d.line([(1, 4), (22, 4)], fill=METAL_DK)
    d.rectangle([0, 34, 23, 39], fill=METAL)
    d.line([(0, 34), (23, 34)], fill=METAL_LIT)
    d.rectangle([0, 38, 23, 39], fill=METAL_DK)
    d.point((4, 36), fill=(255, 70, 60, 255))     # alarma en rojo
    d.point((19, 36), fill=(255, 70, 60, 255))
    # vidrios en el piso de rejilla, a los costados
    for (x, y) in ((-0, 39), (2, 38), (21, 38), (23, 39)):
        d.point((x, y), fill=(200, 235, 228, 255))
    img.save(f"{OUT}/contencion_vacia.png")


def escotilla_borde():
    """Borde de la boca del ducto jugable (Nivel 2): franja de peligro
    vertical de 4x16 sobre el canto de la baldosa, a cada lado del agujero.
    Distingue la entrada (se puede caer, no mata) de los huecos con vidrios."""
    w, h = 4, 16
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.line([(0, y), (w - 1, y)], fill=HAZ_Y if ((y // 3) % 2 == 0) else HAZ_K)
    d.line([(0, 0), (w - 1, 0)], fill=(222, 190, 60, 255))
    img.save(f"{OUT}/escotilla_borde.png")


def contencion_glow():
    w, h = 48, 56
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    cx, cy = w / 2, h * 0.55
    bayer = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    for y in range(h):
        for x in range(w):
            dx, dy = (x - cx) / (w / 2), (y - cy) / (h / 2)
            r = (dx * dx + dy * dy) ** 0.5
            a = max(0.0, 1 - r) ** 1.6 * 110
            # alfa en escalones con tramado (como lamp_glow)
            step = int(a / 22) * 22 + (22 if (a % 22) / 22 * 16 > bayer[y % 4][x % 4] else 0)
            if step > 0:
                px[x, y] = GLOW_G + (min(step, 110),)
    img.save(f"{OUT}/contencion_glow.png")


if __name__ == "__main__":
    lab_subsuelo()
    contencion()
    contencion_vacia()
    contencion_glow()
    escotilla_borde()
    print("ok: lab_subsuelo, contencion[_rota]_0..3, contencion_vacia, contencion_glow, escotilla_borde")
