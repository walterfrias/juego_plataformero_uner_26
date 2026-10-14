#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_hud.py  —  arte de HUD / meta del Nivel 1 (Tier 1).

Genera (game/assets/UI/):
  - heart.png     11x10  corazón pixel para el contador de vidas
  - sign_lab.png  28x46  entrada al laboratorio (meta del nivel), apoya en y=46

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_hud.py
"""
from PIL import Image
import os

OUT = "game/assets/UI"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)

HEART = (206, 74, 74, 255)
HEART_HI = (232, 128, 128, 255)
HEART_DK = (150, 44, 52, 255)
HEART_OL = (40, 20, 28, 255)

CONC = (52, 57, 72, 255)
CONC_HI = (74, 80, 98, 255)
CONC_DK = (34, 37, 48, 255)
DOOR = (14, 18, 20, 255)
GLOW = (120, 200, 140, 255)      # verde enfermizo del laboratorio
GLOW_DIM = (60, 110, 80, 255)


def heart():
    W, H = 11, 10
    im = Image.new("RGBA", (W, H), T)
    px = im.load()
    shape = [
        "  XX XX  ",
        " XXXXXXX ",
        "XXXXXXXXX",
        "XXXXXXXXX",
        "XXXXXXXXX",
        " XXXXXXX ",
        "  XXXXX  ",
        "   XXX   ",
        "    X    ",
    ]
    for y, row in enumerate(shape):
        for x, ch in enumerate(row):
            if ch == "X":
                px[x + 1, y + 1] = HEART
    # brillo arriba-izq, sombra abajo-der, contorno
    for x in range(W):
        for y in range(H):
            if px[x, y] == HEART:
                if px[x, y - 1] == T and y > 0:
                    px[x, y] = HEART_HI
                for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + ox, y + oy
                    if 0 <= nx < W and 0 <= ny < H and px[nx, ny] == T:
                        px[nx, ny] = HEART_OL
    px[3, 7] = HEART_HI
    px[7, 6] = HEART_DK
    im.save(f"{OUT}/heart.png")
    print("heart.png", im.size)


def sign_lab():
    W, H = 28, 46
    im = Image.new("RGBA", (W, H), T)
    px = im.load()
    # marco de hormigón
    for y in range(4, H):
        for x in range(W):
            border = x < 4 or x >= W - 4 or y < 8
            px[x, y] = CONC_HI if (border and (x < 4 or y < 8)) else (
                CONC if border else DOOR)
    # dintel más marcado
    for x in range(W):
        px[x, 4] = CONC_DK
        px[x, 7] = CONC_DK
    # cartel iluminado sobre la puerta
    for x in range(6, W - 6):
        px[x, 1] = GLOW_DIM
        px[x, 2] = GLOW
        px[x, 3] = GLOW_DIM
    # resplandor verde saliendo de la puerta (parte baja)
    for y in range(H - 14, H):
        for x in range(6, W - 6):
            if (x + y) % 3 == 0:
                px[x, y] = GLOW_DIM
    for x in range(9, W - 9):
        px[x, H - 2] = GLOW
    im.save(f"{OUT}/sign_lab.png")
    print("sign_lab.png", im.size)


if __name__ == "__main__":
    heart()
    sign_lab()
