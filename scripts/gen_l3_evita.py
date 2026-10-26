#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_l3_evita.py — el edificio del ex Ministerio de Obras Públicas, sobre la
9 de Julio, con el mural de Evita (25/10, pedido del usuario: "detrás del
Obelisco a la derecha, que sea crema y tenga un mural").

Referencias en la raíz del repo: obelisco_fondo_edificio_mural.webp (la torre
crema con la antena, detrás del Obelisco) y evita_mural.jpg (el mural de líneas
negras: Evita de perfil hablando al micrófono, dentro de un marco).

El mural se saca de la foto como el esclavo de L1 (gen_grafitis_n1.py): se
recorta el dibujo, se reduce a MURAL_W px y se umbraliza; después se borran
los puntos sueltos (las ventanas que se ven detrás del mural en la foto) y el
marco se dibuja prolijo. El edificio es de noche: crema apagado con luz de
luna desde la izquierda, grilla de ventanas (algunas prendidas), el escalonado
del costado derecho, el remate y la antena con su luz roja.

Salida: game/assets/City/edificio_evita.png
Uso:  python3 scripts/gen_l3_evita.py [--preview DIR]   (con --preview no toca
      game/assets: escribe ahí la imagen y una ampliación x4 para mirar)
"""
import os
import random
import sys

from PIL import Image, ImageDraw

REF = "evita_mural.jpg"
REF_CROP = (160, 183, 390, 480)      # el mural (con su marco) dentro de la foto de 600x600
OUT = "game/assets/City"

MURAL_W, UMBRAL = 50, 120
W, H = 64, 186
ANTENA_H, REMATE_H = 22, 12
FACHADA_X0, FACHADA_X1 = 3, 55       # cuerpo principal
COSTADO_X1 = 61                      # escalonado del costado derecho
MURAL_Y = ANTENA_H + REMATE_H + 6

T = (0, 0, 0, 0)
OUTL = (24, 24, 34, 255)
CREMA = [(132, 118, 96, 255), (164, 148, 120, 255), (194, 178, 146, 255), (218, 203, 168, 255)]
LINEA = (34, 30, 38, 255)             # el hierro del mural
VENTANA = (66, 64, 76, 255)
VENTANA_LUZ = (232, 192, 120, 255)
ANTENA = (150, 152, 166, 255)          # gris con luna: si es oscura se pierde contra los edificios
LUZ_ROJA = (255, 70, 60, 255)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def crema(t, x, y):
    """t 0..1 (oscuro..claro) con tramado, como el Obelisco."""
    t = max(0.0, min(0.999, t)) * (len(CREMA) - 1)
    i, f = int(t), t - int(t)
    return CREMA[min(i + 1, len(CREMA) - 1)] if f * 16 > BAYER[y % 4][x % 4] else CREMA[i]


def mural():
    """el dibujo de la foto reducido a líneas de 1 px: lista de (x, y) a pintar."""
    ref = Image.open(REF).convert("L").crop(REF_CROP)
    h = round(MURAL_W * ref.size[1] / ref.size[0])
    m = ref.resize((MURAL_W, h), Image.LANCZOS).point(lambda v: 1 if v < UMBRAL else 0)
    px = m.load()
    puntos = {(x, y) for y in range(h) for x in range(MURAL_W) if px[x, y]}
    # fuera el marco de la foto (se dibuja aparte) y los puntos sueltos (ventanas)
    puntos = {(x, y) for x, y in puntos if 2 <= x < MURAL_W - 2 and 2 <= y < h - 2}
    for _ in range(2):
        puntos = {(x, y) for x, y in puntos
                  if sum((x + a, y + b) in puntos for a in (-1, 0, 1) for b in (-1, 0, 1)) >= 3}
    return puntos, h


def edificio():
    rnd = random.Random(1951)
    puntos, mh = mural()
    img = Image.new("RGBA", (W, H), T)
    px = img.load()
    d = ImageDraw.Draw(img)

    # cuerpo principal y escalonado: luna desde la izquierda, más oscuro abajo
    for y in range(ANTENA_H + REMATE_H, H):
        for x in range(FACHADA_X0, COSTADO_X1):
            costado = x >= FACHADA_X1
            if costado and y < ANTENA_H + REMATE_H + 8:
                continue                                     # el escalón arranca más abajo
            t = 0.78 - 0.5 * (x - FACHADA_X0) / (FACHADA_X1 - FACHADA_X0) - 0.25 * (y / H)
            if costado:
                t = 0.22 - 0.1 * (y / H)
            px[x, y] = crema(t, x, y)
    # remate (los pisos de arriba, más angosto) y la antena reticulada
    for y in range(ANTENA_H, ANTENA_H + REMATE_H):
        for x in range(14, 46):
            px[x, y] = crema(0.62 - 0.4 * (x - 14) / 32, x, y)
    for y in range(ANTENA_H + 3, ANTENA_H + REMATE_H - 2, 4):
        for x in range(17, 44, 4):
            px[x, y] = VENTANA
    # antena reticulada: dos patas que se abren hacia abajo y cruces cada 5 px
    cx = 29
    def half(y):
        return (y * 4) // ANTENA_H
    for y in range(2, ANTENA_H):
        px[cx - half(y), y] = ANTENA
        px[cx + half(y), y] = ANTENA
    for y in range(6, ANTENA_H - 1, 5):
        d.line([(cx - half(y), y), (cx + half(y + 4), y + 4)], fill=ANTENA)
        d.line([(cx + half(y), y), (cx - half(y + 4), y + 4)], fill=ANTENA)
    d.line([(cx, 0), (cx, 2)], fill=ANTENA)
    px[cx, 0] = LUZ_ROJA

    # grilla de ventanas en toda la fachada (también detrás del mural, como en la foto)
    for y in range(ANTENA_H + REMATE_H + 3, H - 2, 4):
        for x in range(FACHADA_X0 + 3, COSTADO_X1 - 2, 4):
            if x >= FACHADA_X1 - 1 and y < ANTENA_H + REMATE_H + 10:
                continue
            en_mural = MURAL_Y <= y < MURAL_Y + mh
            c = VENTANA_LUZ if (not en_mural and rnd.random() < 0.07) else VENTANA
            px[x, y] = c
            px[x + 1, y] = c

    # el mural: marco y líneas
    mx = FACHADA_X0 + (FACHADA_X1 - FACHADA_X0 - MURAL_W) // 2
    d.rectangle([mx, MURAL_Y, mx + MURAL_W - 1, MURAL_Y + mh - 1], outline=LINEA)
    for x, y in puntos:
        px[mx + x, MURAL_Y + y] = LINEA

    # contorno de 1 px, como el resto de los objetos del juego
    src = img.copy().load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3] == 0 and any(0 <= x + a < W and 0 <= y + b < H and src[x + a, y + b][3]
                                         for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = OUTL
    return img


def main():
    img = edificio()
    if "--preview" in sys.argv:
        out = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(out, exist_ok=True)
        img.save(f"{out}/edificio_evita.png")
        img.resize((W * 4, H * 4), Image.NEAREST).save(f"{out}/edificio_evita_x4.png")
        print(f"vista previa en {out}")
        return
    img.save(f"{OUT}/edificio_evita.png")
    print(f"edificio_evita.png ({W}x{H}) -> {OUT}/")


if __name__ == "__main__":
    main()
