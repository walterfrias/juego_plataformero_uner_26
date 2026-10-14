#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_font.py  —  fuente bitmap del HUD (puntaje, antídotos, jefe, récord).

Genera (game/assets/UI/):
  - hud_font.png  atlas con los glifos (relleno claro + contorno oscuro)
  - hud_font.fnt  descriptor BMFont en formato texto (lo lee el objeto
                  BitmapText de GDevelop)

Glifos 5x7 (algunos más angostos), mayúsculas + dígitos + acentos
españoles. El relleno es blanco con las 2 filas de abajo apenas más
oscuras: el color final se da con el tint del objeto (multiplicativo),
así una sola fuente sirve para el dorado del puntaje, el verde de los
antídotos y el rojo del jefe.

Misma tipografía que el menú y la pausa: los glifos que ya existen en
gen_menu_ui.py (GLYPHS) se toman de ahí; acá solo se agregan los que
faltan (dígitos 1-9, K Q W Y, signos, acentos). Monoespaciada de 5 px
con contorno 8-vecino y sombra de 1 px abajo, como outlined() del menú,
así el puntaje no "baila" al cambiar.

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_font.py
"""
from PIL import Image
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_menu_ui import GLYPHS as MENU_GLYPHS  # noqa: E402

OUT = "game/assets/UI"
os.makedirs(OUT, exist_ok=True)

T = (0, 0, 0, 0)
FILL = (255, 255, 255, 255)
FILL_DK = (196, 200, 214, 255)   # 2 filas de abajo: da volumen con el tint
OUTLINE = (12, 14, 22, 255)      # mismo contorno que los textos del juego

ACC = 2      # filas reservadas arriba para acentos
GH = 7       # alto del glifo
CELL_H = ACC + GH + 3   # + contorno arriba/abajo + sombra

G = {
    "0": [" XXX ", "X   X", "X  XX", "X X X", "XX  X", "X   X", " XXX "],
    "1": ["  X  ", " XX  ", "  X  ", "  X  ", "  X  ", "  X  ", " XXX "],
    "2": [" XXX ", "X   X", "    X", "   X ", "  X  ", " X   ", "XXXXX"],
    "3": ["XXXX ", "    X", "    X", " XXX ", "    X", "    X", "XXXX "],
    "4": ["   X ", "  XX ", " X X ", "X  X ", "XXXXX", "   X ", "   X "],
    "5": ["XXXXX", "X    ", "XXXX ", "    X", "    X", "X   X", " XXX "],
    "6": [" XXX ", "X    ", "X    ", "XXXX ", "X   X", "X   X", " XXX "],
    "7": ["XXXXX", "    X", "   X ", "  X  ", "  X  ", "  X  ", "  X  "],
    "8": [" XXX ", "X   X", "X   X", " XXX ", "X   X", "X   X", " XXX "],
    "9": [" XXX ", "X   X", "X   X", " XXXX", "    X", "    X", " XXX "],
    "A": [" XXX ", "X   X", "X   X", "XXXXX", "X   X", "X   X", "X   X"],
    "B": ["XXXX ", "X   X", "X   X", "XXXX ", "X   X", "X   X", "XXXX "],
    "C": [" XXX ", "X   X", "X    ", "X    ", "X    ", "X   X", " XXX "],
    "D": ["XXXX ", "X   X", "X   X", "X   X", "X   X", "X   X", "XXXX "],
    "E": ["XXXXX", "X    ", "X    ", "XXXX ", "X    ", "X    ", "XXXXX"],
    "F": ["XXXXX", "X    ", "X    ", "XXXX ", "X    ", "X    ", "X    "],
    "G": [" XXX ", "X   X", "X    ", "X XXX", "X   X", "X   X", " XXXX"],
    "H": ["X   X", "X   X", "X   X", "XXXXX", "X   X", "X   X", "X   X"],
    "I": ["XXX", " X ", " X ", " X ", " X ", " X ", "XXX"],
    "J": ["  XXX", "   X ", "   X ", "   X ", "   X ", "X  X ", " XX  "],
    "K": ["X   X", "X  X ", "X X  ", "XX   ", "X X  ", "X  X ", "X   X"],
    "L": ["X    ", "X    ", "X    ", "X    ", "X    ", "X    ", "XXXXX"],
    "M": ["X   X", "XX XX", "X X X", "X X X", "X   X", "X   X", "X   X"],
    "N": ["X   X", "XX  X", "X X X", "X  XX", "X   X", "X   X", "X   X"],
    "O": [" XXX ", "X   X", "X   X", "X   X", "X   X", "X   X", " XXX "],
    "P": ["XXXX ", "X   X", "X   X", "XXXX ", "X    ", "X    ", "X    "],
    "Q": [" XXX ", "X   X", "X   X", "X   X", "X X X", "X  X ", " XX X"],
    "R": ["XXXX ", "X   X", "X   X", "XXXX ", "X X  ", "X  X ", "X   X"],
    "S": [" XXXX", "X    ", "X    ", " XXX ", "    X", "    X", "XXXX "],
    "T": ["XXXXX", "  X  ", "  X  ", "  X  ", "  X  ", "  X  ", "  X  "],
    "U": ["X   X", "X   X", "X   X", "X   X", "X   X", "X   X", " XXX "],
    "V": ["X   X", "X   X", "X   X", "X   X", "X   X", " X X ", "  X  "],
    "W": ["X   X", "X   X", "X   X", "X X X", "X X X", "XX XX", "X   X"],
    "X": ["X   X", "X   X", " X X ", "  X  ", " X X ", "X   X", "X   X"],
    "Y": ["X   X", "X   X", " X X ", "  X  ", "  X  ", "  X  ", "  X  "],
    "Z": ["XXXXX", "    X", "   X ", "  X  ", " X   ", "X    ", "XXXXX"],
    " ": ["   "] * 7,
    "/": ["    X", "    X", "   X ", "  X  ", " X   ", "X    ", "X    "],
    ":": [" ", "X", "X", " ", "X", "X", " "],
    ".": [" ", " ", " ", " ", " ", "X", "X"],
    "!": ["X", "X", "X", "X", "X", " ", "X"],
    "¡": ["X", " ", "X", "X", "X", "X", "X"],
    "+": ["     ", "  X  ", "  X  ", "XXXXX", "  X  ", "  X  ", "     "],
    "-": ["    ", "    ", "    ", "XXXX", "    ", "    ", "    "],
    "x": ["     ", "     ", "X   X", " X X ", "  X  ", " X X ", "X   X"],
    # carteles del tutorial y de fin de nivel (wire_pixel_texts.py)
    "[": ["XXX", "X  ", "X  ", "X  ", "X  ", "X  ", "XXX"],
    "]": ["XXX", "  X", "  X", "  X", "  X", "  X", "XXX"],
    "(": [" X", "X ", "X ", "X ", "X ", "X ", " X"],
    ")": ["X ", " X", " X", " X", " X", " X", "X "],
    ",": ["  ", "  ", "  ", "  ", "  ", " X", "X "],
    "?": [" XXX ", "X   X", "    X", "   X ", "  X  ", "     ", "  X  "],
    "¿": ["  X  ", "     ", "  X  ", " X   ", "X    ", "X   X", " XXX "],
    "←": ["     ", "  X  ", " X   ", "XXXXX", " X   ", "  X  ", "     "],
    "→": ["     ", "  X  ", "   X ", "XXXXX", "   X ", "  X  ", "     "],
}

# La fuente del menú manda: sus glifos pisan a los de arriba.
G.update({k: [r.replace("0", " ").replace("1", "X") for r in v]
          for k, v in MENU_GLYPHS.items() if k not in "<>^v"})
# flechas arriba/abajo: las mismas del menú
G["↑"] = [r.replace("0", " ").replace("1", "X") for r in MENU_GLYPHS["^"]]
G["↓"] = [r.replace("0", " ").replace("1", "X") for r in MENU_GLYPHS["v"]]
# monoespaciada: los glifos angostos se centran en 5 px
G = {k: [r.center(5) for r in v] if len(v[0]) < 5 else v for k, v in G.items()}

# Acentos: glifo base + marca en las 2 filas de arriba (columna centrada).
ACCENTED = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N"}


def glyph_rows(ch):
    """Devuelve las 9 filas (2 de acento + 7) del glifo."""
    if ch in ACCENTED:
        base = G[ACCENTED[ch]]
        w = len(base[0])
        if ch == "Ñ":
            mark = [" XX X", "X XX "]
        else:
            c = w // 2
            mark = [" " * (c + 1) + "X" + " " * (w - c - 2), " " * c + "X" + " " * (w - c - 1)]
            mark = [m[:w] for m in mark]
        return mark + base
    return [" " * len(G[ch][0])] * ACC + G[ch]


def draw(ch):
    rows = glyph_rows(ch)
    w = len(rows[0])
    im = Image.new("RGBA", (w + 2, CELL_H), T)
    px = im.load()
    on = set()
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != " ":
                on.add((x + 1, y + 1))
    # sombra 1 px abajo (como outlined() del menú) + contorno 8-vecino
    for (x, y) in on:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1, 2):
                q = (x + dx, y + dy)
                if q not in on and 0 <= q[0] < w + 2 and 0 <= q[1] < CELL_H:
                    px[q] = OUTLINE
    for (x, y) in on:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q not in on and 0 <= q[0] < w + 2 and 0 <= q[1] < CELL_H:
                    px[q] = OUTLINE
    for (x, y) in on:
        px[x, y] = FILL_DK if y - 1 >= ACC + GH - 2 else FILL
    return im


def main():
    chars = list(G.keys()) + list(ACCENTED.keys())
    imgs = {c: draw(c) for c in chars}
    # atlas en filas de ~128 px
    W = 128
    x = y = 0
    pos = {}
    for c in chars:
        im = imgs[c]
        if x + im.width > W:
            x, y = 0, y + CELL_H + 1
        pos[c] = (x, y)
        x += im.width + 1
    H = y + CELL_H
    atlas = Image.new("RGBA", (W, H), T)
    for c in chars:
        atlas.paste(imgs[c], pos[c])
    atlas.save(os.path.join(OUT, "hud_font.png"))

    lines = [
        'info face="PZHud" size=%d bold=0 italic=0 charset="" unicode=1 '
        'stretchH=100 smooth=0 aa=1 padding=0,0,0,0 spacing=1,1' % CELL_H,
        "common lineHeight=%d base=%d scaleW=%d scaleH=%d pages=1 packed=0"
        % (CELL_H + 1, CELL_H - 1, W, H),
        'page id=0 file="hud_font.png"',
        "chars count=%d" % len(chars),
    ]
    for c in chars:
        im = imgs[c]
        px, py = pos[c]
        # xadvance = 6 = 5 px + 1 de separación, igual que text_mask(gap=1)
        lines.append(
            "char id=%d x=%d y=%d width=%d height=%d xoffset=0 yoffset=0 "
            "xadvance=6 page=0 chnl=15" % (ord(c), px, py, im.width, im.height)
        )
    with open(os.path.join(OUT, "hud_font.fnt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("hud_font.png %dx%d, %d glifos" % (W, H, len(chars)))


if __name__ == "__main__":
    main()
