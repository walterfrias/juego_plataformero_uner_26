#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_l3_caos.py  —  banderas argentinas y caos en la calle del Nivel 3 (18/10).
Pedido del usuario: "agreguemos banderas de argentina por los monumentos y
edificios (sin ser exagerado) y autos prendidos fuego o caos en la calle".
Todo es DECORADO (sin colisión). Lo cablea wire_l3_caos.py.

Crea (game/assets/City/):
  BANDERAS (colores apagados para la noche: no tienen que competir con Lio)
    bandera_balcon_1..2.png  16x20   colgada de un balcón o ventana (bastones
                                     verticales, sol en el medio), se mece
    bandera_mastil_1..4.png  34x26   en un mástil que sale de la pared, flamea
    bandera_pie_1..4.png     24x50   en un mástil vertical (terraza, monumentos)
  CAOS EN LA CALLE (el asfalto de adelante, debajo de la vereda)
    auto_quemado.png         60x24   sedán quemado: chapa negra y óxido, sin vidrios
    fuego_auto_1..3.png      40x26   llamas que salen por las ventanillas
    luz_fuego_calle.png     130x56   el resplandor del fuego sobre el asfalto
    taxi_volcado.png         58x24   taxi porteño (negro y amarillo) panza arriba
    patrullero_1..2.png      64x28   patrullero abandonado, puerta abierta, la
                                     sirena alterna rojo / azul
    luz_sirena_1..2.png      96x44   el reflejo de la sirena en el asfalto
    colectivo.png           124x40   colectivo cruzado, vidrios rotos, el número
    humo_auto_1..6.png       40x64   humo del patrullero en llamas: bocanadas que
                                     suben y se van a la derecha, naranja abajo
                                     (el fuego) y se desvanecen arriba (loop)
    cono.png 8x10, neumatico.png 12x12, escombro.png 18x8
Uso:  python3 scripts/gen_l3_caos.py
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from gen_l3_luces import BAYER, FIRE, glow   # noqa: E402

OUT = "game/assets/City"
T = (0, 0, 0, 0)
# bandera apagada para la noche
CEL, CEL_S = (92, 138, 180, 255), (70, 108, 146, 255)
BLA, BLA_S = (186, 192, 204, 255), (146, 152, 166, 255)
SOL = (200, 160, 70, 255)
POLE, POLE_H = (90, 88, 84, 255), (130, 128, 122, 255)
OUTL = (20, 18, 24, 255)
TIRE, RIM = (24, 24, 28, 255), (90, 92, 98, 255)
GLASS_DK = (16, 18, 26, 255)


def _outline(img, col=OUTL):
    """contorno de 1 px afuera de lo opaco (como los sprites del juego)."""
    w, h = img.size
    px = img.load()
    src = [[px[x, y][3] > 0 for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if not src[y][x] and any(0 <= x + dx < w and 0 <= y + dy < h and src[y + dy][x + dx]
                                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = col


def _franja(v, sombra=False):
    """color de la bandera según la posición 0..1 a lo ancho de las franjas."""
    if v < 1 / 3 or v >= 2 / 3:
        return CEL_S if sombra else CEL
    return BLA_S if sombra else BLA


# ---------------------------------------------------------------- banderas
def bandera_balcon(k):
    """colgada: bastones VERTICALES (celeste-blanco-celeste), sol en el medio."""
    w, h = 16, 20
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    for y in range(1, h):
        sway = round(math.sin(k * math.pi + y * 0.25) * (y / h) * 1.2)       # se mece más abajo
        for x in range(1, w - 1):
            xx = x + sway
            if not 0 <= xx < w:
                continue
            fold = (x + k) % 5 == 0                                          # pliegues
            px[xx, y] = _franja((x - 1) / (w - 2), sombra=fold)
    d = ImageDraw.Draw(img)
    d.line([(0, 0), (w - 1, 0)], fill=POLE)                                  # la varilla de donde cuelga
    d.ellipse([6, 8, 9, 11], fill=SOL)
    return img


def _pano(px, x0, y0, fw, fh, k, amp=1.6):
    """paño horizontal (celeste-blanco-celeste) que flamea desde el mástil en x0."""
    for x in range(fw):
        dy = round(math.sin(x * 0.45 - k * math.pi / 2) * amp * (x / fw))
        shade = math.cos(x * 0.45 - k * math.pi / 2) < -0.5
        for y in range(fh):
            px[x0 + x, y0 + y + dy] = _franja(y / fh, sombra=shade)
    sx, sy = x0 + fw // 2, y0 + fh // 2 + round(math.sin(fw / 2 * 0.45 - k * math.pi / 2) * amp * 0.5)
    for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        px[sx + ox - 1, sy + oy - 1] = SOL


def bandera_mastil(k):
    """mástil que sale de la pared (abajo a la izquierda) en diagonal, paño a la derecha."""
    w, h = 34, 26
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    d.line([(1, h - 2), (13, 3)], fill=POLE, width=2)                        # mástil a ~55°
    d.rectangle([0, h - 4, 3, h - 1], fill=POLE_H)                           # la grampa en la pared
    _pano(img.load(), 13, 4, 19, 12, k)
    d.point((13, 2), fill=POLE_H)
    return img


def bandera_pie(k):
    """mástil vertical con base (terrazas y monumentos de la arena)."""
    w, h = 24, 50
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, 3, h - 3], fill=POLE)
    d.line([(2, 2), (2, h - 3)], fill=POLE_H)
    d.rectangle([0, h - 3, 5, h - 1], fill=(70, 68, 66, 255))               # base
    d.ellipse([1, 0, 4, 3], fill=SOL)                                         # moharra dorada
    _pano(img.load(), 4, 4, 18, 12, k)
    return img


# ---------------------------------------------------------------- autos
def _ruedas(d, xs, y, quemada=False):
    for x in xs:
        if quemada:                                                          # sin cubierta: la llanta
            d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=RIM, fill=(40, 30, 28, 255))
        else:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=TIRE)
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=RIM)


def _sedan(d, w, body, body_s, roof, glass):
    """silueta de sedán mirando a la derecha (piso del auto en y = 18)."""
    d.polygon([(2, 12), (12, 11), (18, 4), (40, 4), (48, 11), (w - 3, 12), (w - 2, 18), (1, 18)], fill=body)
    d.rectangle([1, 16, w - 2, 18], fill=body_s)                             # zócalo
    d.polygon([(19, 5), (28, 5), (28, 11), (14, 11)], fill=glass)          # ventanilla de atrás
    d.polygon([(30, 5), (39, 5), (45, 11), (30, 11)], fill=glass)          # ventanilla de adelante
    d.line([(18, 4), (40, 4)], fill=roof)


def auto_quemado():
    w, h = 60, 24
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    _sedan(d, w, (52, 46, 46, 255), (36, 32, 34, 255), (70, 62, 58, 255), GLASS_DK)
    rnd = random.Random(5)
    for _ in range(26):                                                      # óxido y chapa quemada
        x, y = rnd.randrange(3, w - 3), rnd.randrange(6, 17)
        if img.getpixel((x, y))[3] and img.getpixel((x, y))[:3] != GLASS_DK[:3]:
            d.point((x, y), fill=rnd.choice([(118, 62, 38, 255), (86, 50, 36, 255), (30, 26, 28, 255)]))
    d.line([(50, 13), (56, 13)], fill=(120, 110, 90, 255))                  # paragolpes caído
    _ruedas(d, (13, 47), 19, quemada=True)
    _outline(img)
    return img


def fuego_auto(k):
    """llamas que salen por las dos ventanillas (base = abajo de la imagen)."""
    w, h = 40, 26
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    for cx, alto in ((12, 22), (28, 25)):
        for x in range(cx - 8, cx + 9):
            e = 1 - abs(x - cx) / 9
            tongue = math.sin(x * 0.9 + k * 2.1) * 2.5 + math.sin(x * 1.7 - k * 1.3) * 1.5
            top = int(h - e ** 0.7 * alto - tongue)
            for y in range(max(0, top), h):
                t = (y - top) / max(1, h - top)
                i = min(4, int((1 - abs(t - 0.7)) * 4.2))
                px[x, y] = FIRE[max(0, i - (1 if y < top + 2 else 0))] + (255,)
    rnd = random.Random(30 + k)
    d = ImageDraw.Draw(img)
    for _ in range(5):
        d.point((rnd.randrange(2, w - 2), rnd.randrange(0, 8)), fill=FIRE[3] + (255,))
    return img


def taxi_volcado():
    """taxi porteño (negro con el techo amarillo) panza arriba: ruedas al aire."""
    w, h = 58, 24
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    negro, negro_s = (36, 36, 40, 255), (24, 24, 28, 255)
    amar, amar_s = (196, 160, 50, 255), (150, 120, 40, 255)
    # carrocería invertida: chasis arriba (y 6..12), cabina aplastada abajo (y 12..22)
    d.rectangle([2, 6, w - 3, 13], fill=negro)
    d.rectangle([2, 6, w - 3, 7], fill=(60, 58, 62, 255))                   # el chasis
    d.polygon([(10, 13), (w - 12, 13), (w - 16, 21), (14, 21)], fill=amar)   # techo amarillo, abajo
    d.line([(14, 21), (w - 16, 21)], fill=amar_s)
    d.rectangle([15, 14, 24, 16], fill=GLASS_DK)                            # ventanillas (finitas)
    d.rectangle([27, 14, w - 18, 16], fill=GLASS_DK)
    d.rectangle([w // 2 - 4, 21, w // 2 + 3, 23], fill=(210, 60, 50, 255))  # la capelina de TAXI aplastada
    d.line([(2, 12), (w - 3, 12)], fill=negro_s)
    _ruedas(d, (12, w - 13), 4)
    _outline(img)
    return img


def patrullero(k):
    """patrullero abandonado: blanco y azul, puerta de adelante abierta, sirena."""
    w, h = 64, 28
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    blanco, blanco_s = (170, 176, 186, 255), (120, 126, 138, 255)
    azul = (46, 72, 130, 255)
    d.polygon([(2, 16), (12, 15), (18, 8), (42, 8), (50, 15), (w - 3, 16), (w - 2, 22), (1, 22)], fill=blanco)
    d.rectangle([1, 17, w - 2, 19], fill=azul)                               # franja azul
    d.rectangle([1, 20, w - 2, 22], fill=blanco_s)
    d.polygon([(19, 9), (29, 9), (29, 15), (14, 15)], fill=GLASS_DK)
    d.polygon([(31, 9), (41, 9), (47, 15), (31, 15)], fill=GLASS_DK)
    d.polygon([(33, 13), (38, 9), (38, 20), (33, 22)], fill=blanco_s)      # puerta abierta hacia afuera
    on, off = ((220, 50, 50, 255), (60, 90, 170, 255)) if k == 0 else ((110, 40, 40, 255), (90, 150, 255, 255))
    d.rectangle([24, 4, 28, 7], fill=on)                                    # sirena: rojo / azul
    d.rectangle([29, 4, 33, 7], fill=off)
    d.rectangle([24, 7, 33, 7], fill=(50, 50, 56, 255))
    _ruedas(d, (14, 49), 23)
    _outline(img)
    return img


def luz_sirena(k):
    col = (230, 60, 60) if k == 0 else (70, 110, 240)
    cx = 0.40 if k == 0 else 0.60
    return glow(96, 44, col, 120, cx=cx, cy=0.55, power=1.5)


def colectivo():
    """colectivo cruzado: crema y bordó, vidrios rotos, el número en el cartel."""
    w, h = 124, 40
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    crema, crema_s = (178, 166, 140, 255), (132, 122, 104, 255)
    bordo, bordo_s = (120, 44, 50, 255), (86, 32, 38, 255)
    d.rounded_rectangle([1, 3, w - 2, 33], radius=4, fill=crema)
    d.rectangle([1, 22, w - 2, 33], fill=bordo)
    d.line([(1, 32), (w - 2, 32)], fill=bordo_s)
    d.line([(1, 21), (w - 2, 21)], fill=crema_s)
    rnd = random.Random(60)
    for x in range(8, w - 14, 14):                                          # ventanillas (algunas rotas)
        d.rectangle([x, 7, x + 10, 17], fill=GLASS_DK)
        if rnd.random() < 0.5:
            d.line([(x + 2, 8), (x + 6, 13), (x + 9, 9)], fill=(90, 100, 118, 255))
        elif rnd.random() < 0.4:
            d.rectangle([x + 1, 8, x + 9, 16], fill=(62, 72, 90, 255))        # el vidrio que queda
    d.rectangle([w - 12, 5, w - 4, 20], fill=GLASS_DK)                     # parabrisas
    d.rectangle([w - 26, 1, w - 13, 5], fill=(30, 30, 34, 255))            # cartel con el número
    for i, x in enumerate((w - 24, w - 20, w - 16)):
        d.rectangle([x, 2, x + 2, 4], fill=(230, 150, 50, 255) if i != 1 else (200, 130, 40, 255))
    d.rectangle([4, 24, 18, 31], fill=(60, 30, 34, 255))                   # puerta de atrás abierta
    _ruedas(d, (22, w - 26), 34)
    _outline(img)
    return img


def humo_auto(k, n=6):
    """bocanadas que suben en loop: cada una avanza 1/n de su recorrido por cuadro."""
    w, h = 40, 64
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    puffs = 7
    acc = [[0.0] * w for _ in range(h)]
    for i in range(puffs):
        t = ((k / n) + i / puffs) % 1.0                              # 0 = sale del auto, 1 = arriba
        cy = h - 6 - t * (h - 10)
        cx = 8 + t * 22 + math.sin(i * 2.3) * 3                     # el viento la lleva a la derecha
        r = 4 + t * 9
        a = (1 - t) ** 0.9 * min(1.0, t * 6 + 0.3)                  # aparece rápido, se desvanece arriba
        for y in range(max(0, int(cy - r)), min(h, int(cy + r) + 1)):
            for x in range(max(0, int(cx - r)), min(w, int(cx + r) + 1)):
                q = 1 - ((x - cx) ** 2 + (y - cy) ** 2) / (r * r)
                if q > 0:
                    acc[y][x] = max(acc[y][x], a * q ** 0.6)
    for y in range(h):
        warm = max(0.0, (y - h * 0.55) / (h * 0.45))                 # abajo, lo ilumina el fuego
        col = tuple(int(c0 * (1 - warm) + c1 * warm) for c0, c1 in zip((116, 110, 118), (180, 108, 60)))
        for x in range(w):
            v = acc[y][x] * 270
            q = v / 40
            base = int(q)
            v = min(255, (base + (1 if (q - base) * 16 > BAYER[y % 4][x % 4] else 0)) * 40)   # tramado
            if v:
                px[x, y] = col + (v,)
    return img


def cono():
    img = Image.new("RGBA", (8, 10), T)
    d = ImageDraw.Draw(img)
    d.polygon([(3, 0), (4, 0), (6, 8), (1, 8)], fill=(200, 96, 40, 255))
    d.line([(2, 4), (5, 4)], fill=(210, 210, 200, 255))
    d.rectangle([0, 8, 7, 9], fill=(150, 70, 30, 255))
    return img


def neumatico():
    img = Image.new("RGBA", (12, 12), T)
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, 11, 11], fill=TIRE)
    d.ellipse([3, 3, 8, 8], fill=(46, 44, 48, 255))
    d.ellipse([4, 4, 7, 7], fill=T)
    d.arc([0, 0, 11, 11], 200, 290, fill=(56, 56, 62, 255))
    return img


def escombro():
    img = Image.new("RGBA", (18, 8), T)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 7), (4, 2), (9, 3), (12, 0), (17, 5), (17, 7)], fill=(84, 80, 82, 255))
    d.polygon([(4, 7), (7, 4), (11, 6)], fill=(110, 104, 100, 255))
    d.point([(3, 5), (13, 4)], fill=(56, 52, 54, 255))
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    for k in range(2):
        bandera_balcon(k).save(f"{OUT}/bandera_balcon_{k + 1}.png")
        patrullero(k).save(f"{OUT}/patrullero_{k + 1}.png")
        luz_sirena(k).save(f"{OUT}/luz_sirena_{k + 1}.png")
    for k in range(4):
        bandera_mastil(k).save(f"{OUT}/bandera_mastil_{k + 1}.png")
        bandera_pie(k).save(f"{OUT}/bandera_pie_{k + 1}.png")
    for k in range(6):
        humo_auto(k).save(f"{OUT}/humo_auto_{k + 1}.png")
    for k in range(3):
        fuego_auto(k).save(f"{OUT}/fuego_auto_{k + 1}.png")
    auto_quemado().save(f"{OUT}/auto_quemado.png")
    taxi_volcado().save(f"{OUT}/taxi_volcado.png")
    colectivo().save(f"{OUT}/colectivo.png")
    cono().save(f"{OUT}/cono.png")
    neumatico().save(f"{OUT}/neumatico.png")
    escombro().save(f"{OUT}/escombro.png")
    glow(130, 56, (240, 120, 50), 140, cy=0.6, power=1.4).save(f"{OUT}/luz_fuego_calle.png")
    print("banderas (balcon, mastil, pie), autos (quemado, taxi, patrullero, colectivo), fuego, luces, "
          "cono, neumatico, escombro  ->", OUT)


if __name__ == "__main__":
    main()
