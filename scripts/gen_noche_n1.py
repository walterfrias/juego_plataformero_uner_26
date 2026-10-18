#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_noche_n1.py  —  iluminación de la noche del Nivel 1 (pedido el 15/10):
la escena se veía clara y sin contraste entre el fondo y lo jugable. Idea:
oscurecer todo y devolver la luz solo donde importa (luna, fuegos, faroles).
Lo cablea wire_noche_n1.py.

Mismo criterio que gen_lab_luces.py: Pillow, pixel art, transparencias con
tramado ordenado (Bayer 4x4) en pocos escalones, nada de degradés lisos.
Todo lo que se repite en horizontal es tileable (ancho múltiplo de 4 y
ruido periódico).

Crea (game/assets/N1/Noche/):
  cielo.png          4x270   cielo de arriba (casi negro) al horizonte (más
                             cálido y sucio: los incendios de la ciudad)
  nubes.png          384x80  banda de nubes finas, cantos de arriba con luz
                             de luna (pasa por delante de la Luna)
  niebla.png         256x48  bruma: transparente arriba, densa abajo, con
                             jirones (se pone sobre la base de cada skyline)
  incendio.png       96x64   resplandor naranja de un incendio lejano
  humo_1..6.png      28x110  columna de humo que sube (animación en loop)
  fuego_1..6.png     12x16   llama del tacho (animación en loop)
  fuego_glow.png     120x64  halo cálido del tacho + charco de luz en el piso
  farol_cono.png     64x52   cono de luz de sodio del farol + charco

Uso:  python3 scripts/gen_noche_n1.py   (desde la raíz del repo)
"""
import math
import os
import random

from PIL import Image

OUT = "game/assets/N1/Noche"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither(alpha, x, y, step=26):
    """cuantiza el alfa a escalones con tramado Bayer (igual que el lab)."""
    q = max(0.0, alpha) / step
    base = int(q)
    return min(255, (base + (1 if (q - base) * 16 > BAYER[y % 4][x % 4] else 0)) * step)


def dither_ch(v, x, y, step=3):
    """lo mismo para un canal de color (degradé del cielo sin bandas)."""
    q = v / step
    base = int(q)
    return min(255, (base + (1 if (q - base) * 16 > BAYER[y % 4][x % 4] else 0)) * step)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def periodic_noise(w, seed, octaves=((1, 1.0), (2, 0.5), (4, 0.25), (8, 0.12))):
    """ruido 1D tileable de período w: suma de senos con fases al azar."""
    rng = random.Random(seed)
    waves = [(k, a, rng.uniform(0, 2 * math.pi)) for k, a in octaves]
    tot = sum(a for _, a, _ in waves)
    return [0.5 + 0.5 * sum(a * math.sin(2 * math.pi * k * x / w + p) for k, a, p in waves) / tot
            for x in range(w)]


# ---------------------------------------------------------------- cielo
SKY = [(0, (7, 9, 22)), (95, (13, 16, 34)), (165, (28, 25, 46)), (269, (34, 27, 44))]


def cielo():
    img = Image.new("RGBA", (4, 270), T)
    px = img.load()
    for y in range(270):
        c = SKY[-1][1]
        for (y0, c0), (y1, c1) in zip(SKY, SKY[1:]):
            if y0 <= y <= y1:
                c = lerp(c0, c1, (y - y0) / (y1 - y0))
                break
        for x in range(4):
            px[x, y] = tuple(dither_ch(v, x, y) for v in c) + (255,)
    return img


# ---------------------------------------------------------------- nubes
CLOUD = (36, 40, 66)
CLOUD_LIT = (104, 118, 156)


def nubes():
    w, h = 384, 80
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    top = periodic_noise(w, 3, ((2, 1.0), (5, 0.6), (11, 0.3), (24, 0.15)))
    thick = periodic_noise(w, 5, ((3, 1.0), (7, 0.5), (16, 0.2)))
    mask = periodic_noise(w, 9, ((2, 1.0), (3, 0.7)))       # huecos de cielo limpio
    for x in range(w):
        if mask[x] < 0.42:
            continue
        cov = min(1, (mask[x] - 0.42) / 0.18)
        y0 = 18 + top[x] * 34
        th = 10 + thick[x] * 26 * cov
        for y in range(h):
            if y < y0 or y > y0 + th:
                continue
            t = (y - y0) / th
            a = 235 * cov * (1 - t ** 3)
            c = CLOUD_LIT if y - y0 < 1.5 and cov > 0.5 else CLOUD
            a = dither(a, x, y, 32)
            if a:
                px[x, y] = c + (a,)
    return img


# ---------------------------------------------------------------- niebla
FOG = (46, 52, 80)


def niebla():
    w, h = 256, 48
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    wisp = periodic_noise(w, 11, ((1, 0.6), (3, 1.0), (7, 0.6), (16, 0.3)))
    wisp2 = periodic_noise(w, 13, ((2, 1.0), (5, 0.5), (12, 0.4)))
    for x in range(w):
        for y in range(h):
            t = y / (h - 1)
            ramp = min(1, t / 0.65) ** 1.6
            band = 0.65 + 0.35 * wisp[x]
            # jirones: una franja más densa que ondula a media altura
            yc = 0.45 + 0.18 * (wisp2[x] - 0.5)
            jiron = 0.35 * max(0, 1 - abs(t - yc) / 0.12) * wisp2[x]
            a = dither(230 * min(1, ramp * band + jiron), x, y, 24)
            if a:
                px[x, y] = FOG + (a,)
    return img


# ---------------------------------------------------------------- incendio lejano
EMBER = (214, 92, 38)
EMBER_HOT = (255, 172, 74)


def incendio():
    w, h = 96, 64
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    cx, cy = w / 2, h - 6
    for y in range(h):
        for x in range(w):
            ex = (x + 0.5 - cx) / (w / 2)
            ey = (y + 0.5 - cy) / (h - 4)
            r = math.sqrt(ex * ex + ey * ey)
            if r < 1:
                a = dither(120 * (1 - r) ** 1.5, x, y)
                if a:
                    px[x, y] = EMBER + (a,)
    rng = random.Random(21)
    for _ in range(26):                                     # llamas sobre las terrazas
        x = int(cx + rng.gauss(0, 10))
        y = h - 1 - rng.randint(0, 6)
        if 0 <= x < w:
            px[x, y] = EMBER_HOT + (255,)
            if rng.random() < 0.5 and y > 0:
                px[x, y - 1] = EMBER + (220,)
    return img


# ---------------------------------------------------------------- humo
SMOKE = (40, 37, 46)
SMOKE_LIT = (92, 52, 36)


def humo(frame, frames=6):
    w, h = 28, 110
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    period = 44                                             # el humo sube un período por vuelta
    off = frame * period / frames
    for y in range(h):
        u = 1 - y / (h - 1)                                 # 0 abajo, 1 arriba
        yy = y + off
        drift = 3 * math.sin(2 * math.pi * yy / period) + 6 * u ** 1.5    # se inclina con el viento
        half = 2.5 + 9 * u
        dens = 0.55 + 0.45 * math.sin(2 * math.pi * yy / (period / 2) + 1.3)
        for x in range(w):
            dx = (x + 0.5 - (w / 2 - 4 + drift)) / half
            if abs(dx) >= 1:
                continue
            a = 210 * (1 - dx * dx) * (0.6 + 0.4 * dens) * (1 - u) ** 0.6
            a = dither(a, x, y, 28)
            if a:
                c = lerp(SMOKE_LIT, SMOKE, min(1, u * 3.5))
                px[x, y] = tuple(round(v) for v in c) + (a,)
    return img


# ---------------------------------------------------------------- fuego del tacho
FIRE = [(130, 30, 18), (214, 74, 26), (250, 146, 40), (255, 214, 96), (255, 246, 206)]


def fuego(frame, frames=6):
    w, h = 12, 16
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    rng = random.Random(100 + frame)
    ph = 2 * math.pi * frame / frames
    for y in range(h):
        u = 1 - y / (h - 1)                                  # 0 abajo, 1 punta
        sway = 1.4 * math.sin(ph + u * 3.2) * u
        half = 5.2 * (1 - u) ** 0.8 + 0.4
        for x in range(w):
            dx = abs(x + 0.5 - (w / 2 + sway)) / half
            heat = (1 - dx) * (1 - u * 0.85) + rng.uniform(-0.12, 0.12)
            if dx >= 1 or heat <= 0.05:
                continue
            k = min(len(FIRE) - 1, int(heat * len(FIRE) * 1.15))
            px[x, y] = FIRE[k] + (255,)
    for _ in range(2):                                       # chispas sueltas arriba
        x, y = rng.randint(3, 8), rng.randint(0, 4)
        if px[x, y][3] == 0:
            px[x, y] = FIRE[3] + (255,)
    return img


GLOW_FIRE = (255, 150, 60)


def glow_halo(w, h, cx, cy, rx, ry, peak, color, pool_y=None, pool_rx=0, pool_peak=0):
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    for y in range(h):
        for x in range(w):
            ex, ey = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            r = math.sqrt(ex * ex + ey * ey)
            a = peak * max(0, 1 - r) ** 1.4
            if pool_y is not None:
                px2, py2 = (x + 0.5 - cx) / pool_rx, (y - pool_y) / 3.5
                r2 = px2 * px2 + py2 * py2
                if r2 < 1:
                    a = max(a, pool_peak * (1 - r2))
            a = dither(a, x, y)
            if a:
                px[x, y] = color + (a,)
    return img


def fuego_glow():
    # llama (centro) en (60, 42); el piso (pie del tacho) es la última fila
    return glow_halo(120, 64, 60, 42, 58, 40, 110, GLOW_FIRE, pool_y=62, pool_rx=40, pool_peak=80)


# ---------------------------------------------------------------- cono del farol
SODIUM = (255, 196, 120)


def farol_cono():
    w, h = 64, 52
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    cx = w / 2
    top = 4                                                  # el vidrio del farol
    for y in range(h):
        if y >= top:
            t = (y - top) / (h - 1 - top)
            half = 3 + (w / 2 - 6) * t
            a_c = 62 * (1 - t) + 22 * t
            for x in range(w):
                dx = abs(x + 0.5 - cx)
                if dx <= half:
                    a = dither(a_c * (1 - (dx / half) ** 2), x, y)
                    if a:
                        px[x, y] = SODIUM + (a,)
        for x in range(w):                                   # halo chico alrededor del vidrio
            r = math.hypot(x + 0.5 - cx, y + 0.5 - top) / 9
            if r < 1:
                a = dither(120 * (1 - r) ** 1.2, x, y)
                if a > px[x, y][3]:
                    px[x, y] = SODIUM + (a,)
    for y in range(h - 4, h):                                # charco en la vereda
        for x in range(w):
            ex, ey = (x + 0.5 - cx) / (w / 2 - 2), (y - (h - 1)) / 3.5
            r = ex * ex + ey * ey
            if r < 1:
                a = dither(80 * (1 - r), x, y)
                if a > px[x, y][3]:
                    px[x, y] = SODIUM + (a,)
    return img


def main():
    cielo().save(f"{OUT}/cielo.png")
    nubes().save(f"{OUT}/nubes.png")
    niebla().save(f"{OUT}/niebla.png")
    incendio().save(f"{OUT}/incendio.png")
    for k in range(6):
        humo(k).save(f"{OUT}/humo_{k + 1}.png")
        fuego(k).save(f"{OUT}/fuego_{k + 1}.png")
    fuego_glow().save(f"{OUT}/fuego_glow.png")
    farol_cono().save(f"{OUT}/farol_cono.png")
    print(f"cielo, nubes, niebla, incendio, humo_1..6, fuego_1..6, fuego_glow, farol_cono -> {OUT}/")


if __name__ == "__main__":
    main()
