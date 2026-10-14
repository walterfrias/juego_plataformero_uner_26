#!/usr/bin/env python3
"""
gen_menu_ui.py — arte procedural del MainMenu (mismo criterio que el resto
del repo: Pillow, sin fuentes externas, paleta noche).

Genera en game/assets/Menu/:
  menu_sky.png         cielo 480x270: degradé noche, estrellas, luna enferma
                       y bruma verde (el virus) sobre el horizonte.
  luna.png             luna sola (54x54, con halo) para Level1.
  menu_logo.png        "PACIENTE ZERO" en pixel font propia, ZERO en verde
                       tóxico con chorreado.
  menu_sub.png         subtítulo chico.
  menu_panel.png       panel del menú (hormigón oscuro semitransparente).
  menu_<item>_{n,s}.png  ítems JUGAR/OPCIONES/SALIR normal/seleccionado.
  menu_opt_*.png       título y etiquetas del panel de opciones.
  menu_bar_<0..10>.png barra de volumen (11 estados, 10% c/u).
  menu_hint*.png       ayudas de teclado.
  pause_*.png          menú de pausa de Level1/2/3 (wire_pause_panel.py).

La pixel font es 5x7 dibujada a mano acá abajo (solo los glifos usados).
Uso:  python3 scripts/gen_menu_ui.py   (desde la raíz del repo)
"""
import os
import random
from PIL import Image, ImageDraw

from palette_night import BG, CONCRETE, CONCRETE_LIT, FORMLINE, PIPE_HOLE

OUT = "game/assets/Menu"
W, H = 480, 270

INK = PIPE_HOLE                 # contorno (12,14,22)
WHITE = (236, 238, 230, 255)
DIM = (128, 138, 164, 255)      # ítem no seleccionado
TOXIC = (132, 214, 92, 255)     # verde virus
TOXIC_HI = (196, 244, 150, 255)
TOXIC_DK = (70, 140, 60, 255)
AMBER = (255, 206, 110, 255)    # luz de farol (acento)

GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00001", "00001", "00001", "10001", "10001", "01110"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10011", "10101", "10101", "11001", "10001", "01110"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00000", "00100"],
    ":": ["00000", "00100", "00000", "00000", "00000", "00100", "00000"],
    "<": ["00010", "00100", "01000", "10000", "01000", "00100", "00010"],
    ">": ["01000", "00100", "00010", "00001", "00010", "00100", "01000"],
    "^": ["00100", "01110", "10101", "00100", "00100", "00100", "00000"],
    "v": ["00000", "00100", "00100", "00100", "10101", "01110", "00100"],
    " ": ["00000"] * 7,
}


def text_mask(txt, scale=1, gap=1):
    """máscara 'L' del texto en la pixel font (sin contorno)."""
    cw = 5 * scale
    w = len(txt) * (cw + gap * scale) - gap * scale
    m = Image.new("L", (max(w, 1), 7 * scale), 0)
    d = ImageDraw.Draw(m)
    for i, ch in enumerate(txt):
        g = GLYPHS[ch]
        ox = i * (cw + gap * scale)
        for y, row in enumerate(g):
            for x, b in enumerate(row):
                if b == "1":
                    d.rectangle([ox + x * scale, y * scale,
                                 ox + (x + 1) * scale - 1, (y + 1) * scale - 1], fill=255)
    return m


def outlined(mask, fill, outline=INK, shadow=True, pad=2):
    """pinta la máscara con relleno (color o función y->color), contorno 1px y sombra."""
    w, h = mask.size
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2 + (1 if shadow else 0)), (0, 0, 0, 0))
    px = mask.load()
    out = im.load()
    solid = [(x, y) for y in range(h) for x in range(w) if px[x, y]]
    solid_set = set(solid)
    ring = set()
    for x, y in solid:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (x + dx, y + dy) not in solid_set:
                    ring.add((x + dx, y + dy))
    if shadow:
        for x, y in solid_set | ring:
            out[x + pad, y + pad + 1] = outline
    for x, y in ring:
        out[x + pad, y + pad] = outline
    for x, y in solid:
        out[x + pad, y + pad] = fill(y, h) if callable(fill) else fill
    return im


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(4))


def sky():
    rnd = random.Random(27)
    im = Image.new("RGBA", (W, H), BG)
    px = im.load()
    top, horizon = (8, 10, 22, 255), (30, 36, 60, 255)
    for y in range(H):
        t = min(1, y / 190)
        c = lerp(top, horizon, t ** 1.4)
        # bruma verde (virus) pegada al horizonte
        haze = max(0.0, 1 - abs(y - 175) / 45) ** 2 * 0.35
        c = lerp(c, (60, 110, 60, 255), haze)
        for x in range(W):
            px[x, y] = c
    # dithering suave entre bandas para que no se vean escalones
    for y in range(0, 190):
        for x in range((y % 2), W, 2):
            if rnd.random() < 0.08:
                px[x, y] = lerp(px[x, y], horizon, 0.15)
    # estrellas
    for _ in range(90):
        x, y = rnd.randrange(W), rnd.randrange(150)
        b = rnd.choice([(70, 80, 110), (110, 120, 150), (170, 180, 200)])
        px[x, y] = b + (255,)
    for _ in range(8):  # estrellas grandes en cruz
        x, y = rnd.randrange(4, W - 4), rnd.randrange(4, 110)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            px[x + dx, y + dy] = (200, 205, 220, 255) if (dx, dy) == (0, 0) else (100, 110, 140, 255)
    # luna enferma (verdosa) con halo, arriba a la derecha
    lu = moon()
    im.alpha_composite(lu, (404 - lu.width // 2, 44 - lu.height // 2))
    return im


def moon():
    """luna enferma (verdosa) con halo. Sprite propio: la usan el cielo del
    menú y Level1 (al lado del obelisco, wire_luna_level1.py)."""
    s = 54
    m = s // 2
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    for r, a in ((26, 18), (21, 30), (17, 45)):
        halo = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        ImageDraw.Draw(halo).ellipse([m - r, m - r, m + r, m + r], fill=(150, 200, 120, a))
        im.alpha_composite(halo)
    d = ImageDraw.Draw(im)
    d.ellipse([m - 12, m - 12, m + 12, m + 12], fill=(206, 222, 176, 255))
    for cx, cy, cr in ((m - 4, m - 3, 3), (m + 5, m + 4, 2), (m - 1, m + 6, 2), (m + 4, m - 6, 1)):
        d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(170, 192, 140, 255))
    return im


def logo():
    top = outlined(text_mask("PACIENTE", scale=3),
                   lambda y, h: lerp(WHITE, (170, 182, 200, 255), y / h))
    zero_m = text_mask("ZERO", scale=4)
    # chorreado: gotas que bajan desde la base de algunas columnas
    rnd = random.Random(0)
    zw, zh = zero_m.size
    drip = Image.new("L", (zw, zh + 12), 0)
    drip.paste(zero_m, (0, 0))
    dd = ImageDraw.Draw(drip)
    zp = zero_m.load()
    bottoms = [x for x in range(zw) if zp[x, zh - 1]]
    # 5 gotas cortas: hilo de 1px y gota de 2x2 al final
    for x in rnd.sample(bottoms[::3], 5):
        ln = rnd.randint(2, 6)
        dd.rectangle([x, zh, x, zh + ln], fill=255)
        dd.rectangle([x, zh + ln, x + 1, zh + ln + 1], fill=255)
    zero = outlined(drip, lambda y, h: TOXIC_HI if y < 4 else (TOXIC if y < zh - 6 else TOXIC_DK))
    w = max(top.width, zero.width)
    im = Image.new("RGBA", (w, top.height + zero.height + 2), (0, 0, 0, 0))
    im.alpha_composite(top, ((w - top.width) // 2, 0))
    im.alpha_composite(zero, ((w - zero.width) // 2, top.height + 2))
    return im


def panel(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=INK[:3] + (255,))
    d.rectangle([1, 1, w - 2, h - 2], fill=CONCRETE_LIT[:3] + (255,))
    d.rectangle([2, 2, w - 3, h - 3], fill=FORMLINE[:3] + (255,))
    d.rectangle([3, 3, w - 4, h - 4], fill=(14, 17, 30, 205))
    # franja de peligro (cinta de cuarentena) arriba
    for x in range(3, w - 3):
        c = AMBER if ((x // 4) % 2 == 0) else INK
        d.point((x, 3), fill=c[:3] + (255,))
        d.point((x, 4), fill=c[:3] + (200,))
    # remaches
    for x, y in ((5, 7), (w - 6, 7), (5, h - 6), (w - 6, h - 6)):
        d.point((x, y), fill=CONCRETE_LIT)
        d.point((x + 1, y + 1), fill=CONCRETE)
    return im


def item(txt, sel):
    m = text_mask(txt, scale=2)
    if sel:
        return outlined(m, lambda y, h: TOXIC_HI if y < h // 2 else TOXIC)
    return outlined(m, DIM, shadow=False)


def bar(level):
    """barra de 10 celdas estilo jeringa/medidor."""
    cw, gap, hgt = 8, 2, 8
    w = 10 * (cw + gap) + 3
    im = Image.new("RGBA", (w, hgt + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, hgt + 3], fill=INK)
    for i in range(10):
        x = 2 + i * (cw + gap)
        on = i < level
        d.rectangle([x, 2, x + cw - 1, hgt + 1], fill=(TOXIC if on else FORMLINE))
        if on:
            d.line([x, 2, x + cw - 1, 2], fill=TOXIC_HI)
        else:
            d.line([x, hgt + 1, x + cw - 1, hgt + 1], fill=CONCRETE)
    return im


def lines(rows, color):
    """varias líneas de texto chico centradas en una sola imagen."""
    ims = [outlined(text_mask(r), color, shadow=False) for r in rows]
    w = max(i.width for i in ims)
    im = Image.new("RGBA", (w, sum(i.height for i in ims) - 2 * (len(ims) - 1)), (0, 0, 0, 0))
    y = 0
    for i in ims:
        im.alpha_composite(i, ((w - i.width) // 2, y))
        y += i.height - 2
    return im


def pause_art():
    """menú de pausa (Level1/2/3): mismo panel que el MainMenu, velo oscuro
    y filas etiqueta+barra en una sola imagen (11 estados c/u)."""
    out = {}
    dim = Image.new("RGBA", (8, 8), (6, 8, 16, 150))   # se estira a 480x270
    out["pause_dim.png"] = dim
    out["pause_panel.png"] = panel(PAUSE_W, 124)
    out["pause_title.png"] = outlined(text_mask("PAUSA", scale=2), AMBER)
    row_w = PAUSE_W - 24
    for key, txt in (("music", "MUSICA"), ("sfx", "SFX")):
        lbl = outlined(text_mask(txt), WHITE, shadow=False)
        for i in range(11):
            b = bar(i)
            im = Image.new("RGBA", (row_w, b.height), (0, 0, 0, 0))
            im.alpha_composite(lbl, (0, (b.height - lbl.height) // 2))
            im.alpha_composite(b, (row_w - b.width, 0))
            out[f"pause_{key}_{i}.png"] = im
    out["pause_hint.png"] = pause_hint()
    return out


PAUSE_W = 200
MOCHILA_ICON = "game/assets/UI/mochila_worn.png"   # gen_mochila.py


def pause_hint():
    """ayudas de la pausa; la fila de la mochila lleva el sprite de la
    mochila puesta (14x16) a la izquierda del texto."""
    top = lines(["< > MUSICA    ^ v SFX", "R: REINICIAR    M: MENU"], DIM)
    txt = outlined(text_mask("I: MOCHILA"), DIM, shadow=False)
    icon = Image.open(MOCHILA_ICON).convert("RGBA")
    mid = Image.new("RGBA", (icon.width + 3 + txt.width, max(icon.height, txt.height)), (0, 0, 0, 0))
    mid.alpha_composite(icon, (0, (mid.height - icon.height) // 2))
    mid.alpha_composite(txt, (icon.width + 3, (mid.height - txt.height) // 2))
    bot = outlined(text_mask("ESC / P: REANUDAR"), DIM, shadow=False)
    rows = [top, mid, bot]
    w = max(r.width for r in rows)
    im = Image.new("RGBA", (w, sum(r.height for r in rows) - 2), (0, 0, 0, 0))
    y = 0
    for r in rows:
        im.alpha_composite(r, ((w - r.width) // 2, y))
        y += r.height - 1
    return im


def main():
    assert os.path.isdir("game"), "corré desde la raíz del repo"
    os.makedirs(OUT, exist_ok=True)
    out = {}
    out["menu_sky.png"] = sky()
    out["menu_logo.png"] = logo()
    out["luna.png"] = moon()
    out["menu_sub.png"] = outlined(text_mask("BUENOS AIRES - NOCHE CERO"), DIM, shadow=False)
    out["menu_panel.png"] = panel(172, 92)
    for key, txt in (("jugar", "JUGAR"), ("opciones", "OPCIONES"), ("salir", "SALIR")):
        out[f"menu_{key}_n.png"] = item(txt, False)
        out[f"menu_{key}_s.png"] = item(txt, True)
    out["menu_opt_title.png"] = outlined(text_mask("OPCIONES", scale=2), AMBER)
    out["menu_opt_music.png"] = outlined(text_mask("MUSICA"), WHITE, shadow=False)
    out["menu_opt_sfx.png"] = outlined(text_mask("SFX"), WHITE, shadow=False)
    for i in range(11):
        out[f"menu_bar_{i}.png"] = bar(i)
    out["menu_hint.png"] = outlined(text_mask("^ v ELEGIR    ENTER: ACEPTAR    O: OPCIONES"),
                                    DIM, shadow=False)
    out["menu_opt_hint.png"] = outlined(text_mask("< > MUSICA    ^ v SFX    ESC: VOLVER"),
                                        DIM, shadow=False)
    out.update(pause_art())
    for name, im in out.items():
        im.save(os.path.join(OUT, name))
        print(f"{name:22s} {im.size}")


if __name__ == "__main__":
    main()
