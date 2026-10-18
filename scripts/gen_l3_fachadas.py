#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_l3_fachadas.py  —  fachadas porteñas para el Nivel 3 (18/10). El usuario
quería que el recorrido sea "entre edificios, ya dentro de la ciudad, no en la
costanera": los frentes van pegados detrás de la vereda, entre el fondo de la
ciudad (BG_city) y el plano de juego. Solo decorado (no colisionan).

Cuatro módulos (la fila de abajo de cada imagen apoya en el piso, y = 150):
  fachada_frances.png   112x168  piedra, 3 pisos de ventanales con balcones de
                                 hierro, mansarda con buhardilla
  fachada_deptos.png     96x150  edificio de los 60: ventanas con persianas,
                                 aire acondicionado, local con cortina metálica
  fachada_ph.png         80x84   PH / casa chorizo: puerta con moldura, rejas,
                                 baranda de balaustres. Bajo: deja ver el cielo
  fachada_bar.png       104x120  bar de esquina: vidrieras iluminadas por
                                 dentro (luz cálida), toldo, piso de arriba
  calle_subsuelo.png     32x80   debajo de la vereda: asfalto, caños y tierra
                                 (reemplaza al muro de la costanera de L1)
  calle_pozo.png         32x96   interior de los pozos de la calle: el corte de
                                 calle hundido y en sombra
Apocalipsis: ventanas tapiadas, vidrios rotos, cruz roja de cuarentena en las
puertas. Noche: tonos bajos para no competir con el plano de juego, canto
izquierdo iluminado por la luna, alguna ventana prendida (cálida o de TV).

Mismo criterio que el resto del arte: Pillow, tramado Bayer en los degradés.
Uso:  python3 scripts/gen_l3_fachadas.py   (crea en game/assets/City/)
"""
from PIL import Image, ImageDraw
import random
import os

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)
OUTL = (24, 24, 34, 255)
GLASS = (20, 26, 44, 255)
GLASS_HI = (44, 54, 80, 255)
LIT = (214, 166, 92, 255)          # ventana prendida (cálida)
LIT_DK = (150, 104, 56, 255)
TV = (96, 136, 190, 255)           # luz de tele
WOOD = (92, 68, 46, 255)
WOOD_DK = (60, 44, 32, 255)
IRON = (34, 34, 42, 255)
CROSS = (176, 40, 44, 255)         # cruz de cuarentena
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def wall(img, x0, y0, x1, y1, tones, rnd, stains=6):
    """paño de pared con un degradé leve (más oscuro abajo) y manchas."""
    px = img.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            t = (y - y0) / max(1, y1 - y0)
            i = 1 if t * 16 > BAYER[y % 4][x % 4] + 6 else 2
            px[x, y] = tones[i]
    d = ImageDraw.Draw(img)
    d.line([(x0, y0), (x0, y1 - 1)], fill=tones[3])                 # canto con luz de luna
    d.line([(x1 - 1, y0), (x1 - 1, y1 - 1)], fill=tones[0])
    for _ in range(stains):                                          # manchas de humedad
        x, y = rnd.randrange(x0 + 2, x1 - 3), rnd.randrange(y0 + 2, y1 - 3)
        d.line([(x, y), (x, y + rnd.randint(2, 6))], fill=tones[0])


def window(img, x, y, w, h, rnd, kind=None, frame=(0, 0, 0, 0)):
    """ventana: oscura, prendida, con tele, tapiada o rota (al azar si kind es None)."""
    d = ImageDraw.Draw(img)
    kind = kind or rnd.choices(["dark", "dark", "dark", "lit", "tv", "board", "broken"],
                               [5, 5, 5, 2, 1, 2, 2])[0]
    d.rectangle([x - 1, y - 1, x + w, y + h], fill=frame)
    if kind == "lit":
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=LIT)
        d.rectangle([x, y + h // 2, x + w - 1, y + h - 1], fill=LIT_DK)   # cortina a media altura
    elif kind == "tv":
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=GLASS)
        d.rectangle([x + 1, y + h - 4, x + w - 2, y + h - 2], fill=TV)
    else:
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=GLASS)
        d.line([(x, y), (x + w // 2, y)], fill=GLASS_HI)                # reflejo
    if kind == "board":                                                 # tapiada con tablas
        for yy in range(y, y + h, 4):
            d.rectangle([x - 1, yy, x + w, yy + 2], fill=WOOD)
            d.line([(x - 1, yy + 2), (x + w, yy + 2)], fill=WOOD_DK)
    if kind == "broken":                                                # vidrio roto
        d.line([(x + 1, y + 1), (x + w - 2, y + h - 3)], fill=GLASS_HI)
        d.line([(x + w // 2, y + 2), (x + 2, y + h - 2)], fill=GLASS_HI)
    if w >= 6 and kind not in ("board",):
        d.line([(x + w // 2, y), (x + w // 2, y + h - 1)], fill=frame)  # parante


def cross(img, x, y, s=6):
    d = ImageDraw.Draw(img)
    d.line([(x, y), (x + s, y + s)], fill=CROSS, width=2)
    d.line([(x + s, y), (x, y + s)], fill=CROSS, width=2)


def frances():
    W, H = 112, 168
    rnd = random.Random(11)
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    stone = [(54, 52, 58, 255), (78, 74, 78, 255), (96, 92, 94, 255), (128, 124, 122, 255)]
    roof = [(34, 38, 52, 255), (48, 54, 70, 255), (62, 70, 88, 255), (84, 92, 110, 255)]
    # mansarda (techo de pizarra) con buhardilla
    for y in range(0, 30):
        inset = max(0, 12 - y // 2)
        for x in range(inset, W - inset):
            img.putpixel((x, y), roof[1 if (x + y) % 6 else 0])
    d.rectangle([48, 6, 63, 26], fill=stone[2])
    window(img, 52, 10, 8, 12, rnd, "lit", IRON)
    d.line([(0, 30), (W, 30)], fill=stone[3])                            # cornisa
    d.rectangle([0, 31, W - 1, 33], fill=stone[0])
    wall(img, 0, 34, W, H, stone, rnd, 10)
    # 3 pisos de ventanales con balcón de hierro
    for y in (42, 74, 106):
        for x in (12, 46, 80):
            window(img, x, y, 18, 22, rnd, frame=stone[0])
            d.rectangle([x - 3, y + 22, x + 20, y + 23], fill=stone[3])  # repisa
            for bx in range(x - 2, x + 20, 3):                            # baranda
                d.line([(bx, y + 18), (bx, y + 22)], fill=IRON)
            d.line([(x - 2, y + 18), (x + 19, y + 18)], fill=IRON)
        d.line([(0, y + 28), (W, y + 28)], fill=stone[0])                 # línea de piso
    # planta baja: portón con moldura y la cruz de cuarentena
    d.rectangle([44, 136, 67, H - 1], fill=WOOD_DK)
    d.rectangle([46, 138, 65, H - 1], fill=WOOD)
    d.line([(55, 138), (55, H - 1)], fill=WOOD_DK)
    d.arc([42, 128, 69, 148], 180, 360, fill=stone[3])
    cross(img, 52, 146, 7)
    for x in (12, 80):
        window(img, x, 140, 18, 20, rnd, frame=IRON)
        for rx in range(x, x + 18, 3):                                    # rejas
            d.line([(rx, 140), (rx, 159)], fill=IRON)
    return img


def deptos():
    W, H = 96, 150
    rnd = random.Random(23)
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    conc = [(48, 52, 60, 255), (66, 70, 80, 255), (82, 86, 96, 255), (112, 116, 126, 255)]
    wall(img, 0, 0, W, H, conc, rnd, 8)
    d.rectangle([0, 0, W - 1, 3], fill=conc[0])                          # carga del techo
    d.line([(10, 0), (10, -4)], fill=IRON)
    for y in range(8, 112, 26):                                          # 4 pisos
        d.rectangle([0, y + 20, W - 1, y + 21], fill=conc[0])            # losa
        for x in (6, 30, 54, 78):
            kind = rnd.choice(["dark", "dark", "lit", "board", "broken", "tv", "persiana"])
            if kind == "persiana":                                       # persiana baja
                d.rectangle([x, y, x + 13, y + 15], fill=conc[0])
                for yy in range(y, y + 15, 2):
                    d.line([(x, yy), (x + 13, yy)], fill=conc[1])
            else:
                window(img, x, y, 14, 16, rnd, kind, conc[0])
            if rnd.random() < 0.3:                                       # aire acondicionado
                d.rectangle([x + 2, y + 17, x + 9, y + 20], fill=conc[3])
                d.point((x + 3, y + 18), fill=conc[0])
    # planta baja: local con cortina metálica (y graffiti)
    d.rectangle([6, 118, 89, H - 1], fill=conc[0])
    for yy in range(120, H, 3):
        d.line([(8, yy), (87, yy)], fill=(92, 96, 104, 255))
    d.line([(20, 128), (30, 124), (38, 132), (50, 126)], fill=(150, 70, 140, 255), width=2)  # graffiti
    d.line([(56, 136), (70, 130)], fill=(90, 170, 120, 255), width=2)
    cross(img, 76, 124, 6)
    return img


def ph():
    W, H = 80, 84
    rnd = random.Random(37)
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    plaster = [(66, 58, 56, 255), (92, 80, 74, 255), (110, 96, 88, 255), (142, 126, 112, 255)]
    # baranda de balaustres arriba
    d.rectangle([0, 0, W - 1, 3], fill=plaster[3])
    for x in range(2, W - 2, 5):
        d.rectangle([x, 4, x + 2, 11], fill=plaster[2])
    d.rectangle([0, 12, W - 1, 14], fill=plaster[3])
    wall(img, 0, 15, W, H, plaster, rnd, 6)
    # puerta con moldura y cruz
    d.rectangle([30, 36, 49, H - 1], fill=plaster[3])
    d.rectangle([32, 38, 47, H - 1], fill=WOOD)
    d.line([(39, 38), (39, H - 1)], fill=WOOD_DK)
    window(img, 34, 40, 4, 8, rnd, "dark", WOOD_DK)
    window(img, 41, 40, 4, 8, rnd, "lit", WOOD_DK)
    cross(img, 36, 60, 7)
    for x in (6, 56):                                                     # ventanas con rejas
        window(img, x, 34, 16, 30, rnd, frame=plaster[3])
        for rx in range(x, x + 16, 3):
            d.line([(rx, 34), (rx, 63)], fill=IRON)
        d.line([(x, 48), (x + 15, 48)], fill=IRON)
    return img


def bar():
    W, H = 104, 120
    rnd = random.Random(41)
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    brick = [(60, 40, 38, 255), (86, 54, 48, 255), (104, 66, 56, 255), (136, 92, 74, 255)]
    wall(img, 0, 0, W, H, brick, rnd, 4)
    for y in range(4, 70, 4):                                            # ladrillos
        off = 0 if (y // 4) % 2 else 4
        for x in range(off, W, 8):
            d.point((x, y), fill=brick[0])
        d.line([(0, y), (W - 1, y)], fill=brick[1])
    for x in (8, 40, 72):                                                # piso de arriba
        window(img, x, 14, 22, 26, rnd, frame=brick[0])
    d.rectangle([0, 50, W - 1, 56], fill=(40, 70, 56, 255))              # toldo verde
    for x in range(0, W, 8):
        d.rectangle([x, 50, x + 3, 56], fill=(176, 170, 150, 255))
    d.line([(0, 57), (W - 1, 57)], fill=(30, 50, 40, 255))
    # vidrieras iluminadas por dentro: la isla de luz cálida del tramo
    for x in (6, 58):
        d.rectangle([x, 64, x + 39, H - 10], fill=LIT_DK)
        d.rectangle([x + 2, 66, x + 37, H - 22], fill=LIT)
        for sx in (x + 8, x + 24):                                       # sillas y mesa
            d.rectangle([sx, H - 20, sx + 4, H - 14], fill=WOOD_DK)
        d.line([(x + 2, 66), (x + 37, 66)], fill=(250, 214, 150, 255))
        d.rectangle([x - 1, 63, x + 40, 63], fill=IRON)
    d.rectangle([47, 70, 56, H - 1], fill=WOOD_DK)                       # puerta de la esquina
    d.rectangle([0, H - 10, W - 1, H - 1], fill=brick[0])                # zócalo
    return img


def calle_subsuelo():
    """debajo de la vereda: asfalto, caños (agua, gas) y tierra."""
    W, H = 32, 80
    img = Image.new("RGBA", (W, H), T)
    px = img.load()
    for y in range(H):
        for x in range(W):
            if y < 6:
                c = (40, 42, 50, 255) if (x * 7 + y * 3) % 5 else (56, 58, 66, 255)   # asfalto
            elif y < 8:
                c = (28, 28, 34, 255)
            else:
                t = (y - 8) / (H - 8)
                base = (46, 36, 30) if t * 16 < BAYER[y % 4][x % 4] + 4 else (34, 26, 22)
                c = tuple(int(v * (1 - 0.6 * t)) for v in base) + (255,)        # tierra, más oscura abajo
            px[x, y] = c
    d = ImageDraw.Draw(img)
    d.rectangle([0, 20, W - 1, 24], fill=(70, 74, 86, 255))              # caño de agua
    d.line([(0, 20), (W - 1, 20)], fill=(104, 110, 124, 255))
    d.rectangle([0, 36, W - 1, 38], fill=(150, 130, 40, 255))            # caño de gas (amarillo)
    d.line([(0, 36), (W - 1, 36)], fill=(196, 174, 70, 255))
    for x in (3, 17, 26):                                                # piedritas
        d.point((x, 50 + x % 9), fill=(70, 58, 50, 255))
    return img


def calle_pozo():
    """interior de los pozos de la calle (y 150..246): el corte de calle hundido y
    en sombra, a negro hacia el fondo. Sin esto se veía el fondo de la ciudad
    (estrellas y edificios) por el pozo, como un agujero al cielo."""
    sub = calle_subsuelo()
    W, H = 32, 96
    img = Image.new("RGBA", (W, H), (6, 6, 9, 255))
    img.paste(sub, (0, 10))
    px = img.load()
    for y in range(H):
        k = 0.5 * (1 - y / H) ** 1.2 + 0.06
        for x in range(W):
            r, g, b, _ = px[x, y]
            px[x, y] = (int(r * k + 3), int(g * k + 3), int(b * k + 5), 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, 9], fill=(14, 15, 20, 255))         # canto de la vereda cortada
    return img


def main():
    for name, fn in (("fachada_frances", frances), ("fachada_deptos", deptos),
                     ("fachada_ph", ph), ("fachada_bar", bar), ("calle_subsuelo", calle_subsuelo),
                     ("calle_pozo", calle_pozo)):
        fn().save(f"{OUT}/{name}.png")
    print("fachada_frances, fachada_deptos, fachada_ph, fachada_bar, calle_subsuelo, calle_pozo  ->", OUT)


if __name__ == "__main__":
    main()
