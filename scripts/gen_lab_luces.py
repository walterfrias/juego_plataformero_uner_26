#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_lab_luces.py  —  iluminación de "película de terror clase B" del
laboratorio (L2/L3, pedido el 14/10): tubos fluorescentes del techo, su cono
de luz fría y la sombra de las zonas a oscuras. Lo cablea wire_lab_luces.py
(que también los hace parpadear).

Mismo criterio que el resto del arte: Pillow, pixel art. Las transparencias
del cono van con tramado ordenado (Bayer 4x4) en pocos niveles, así se ve
como luz de juego retro y no como un degradé liso.

Crea (game/assets/Lab/):
  lamp_fixture.png  40x5    carcasa del tubo (siempre visible, apagada)
  lamp_glow.png     130x172 tubo encendido + cono de luz + charco en el piso
                            (lo que prende y apaga el evento)
  lab_sombra.png    64x8    oscuridad de zona: sólida al medio y con los
                            extremos esfumados (se estira al ancho de la zona)

Uso:  python3 scripts/gen_lab_luces.py   (desde la raíz del repo)
"""
from PIL import Image, ImageDraw
import os

OUT = "game/assets/Lab"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)

LIGHT = (196, 238, 228)          # fluorescente frío, apenas verdoso (como los tanques)
TUBE = (236, 255, 250, 255)
HOUSING = (58, 68, 76, 255)
HOUSING_HI = (84, 96, 104, 255)
HOUSING_DK = (30, 36, 42, 255)
DARK = (6, 10, 14)

GW, GH = 130, 172                # cono: de la carcasa (y=-62) al piso (y=110)
TOP_W = 34
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
STEP = 26                        # alfa en escalones de 26 (≈ 5 niveles)


def dither(alpha, x, y):
    """cuantiza el alfa a escalones con tramado Bayer."""
    q = alpha / STEP
    base = int(q)
    return min(255, (base + (1 if (q - base) * 16 > BAYER[y % 4][x % 4] else 0)) * STEP)


def fixture():
    img = Image.new("RGBA", (40, 5), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 39, 2], fill=HOUSING)
    d.line([(0, 0), (39, 0)], fill=HOUSING_HI)
    d.rectangle([3, 3, 36, 4], fill=HOUSING_DK)      # tubo apagado
    d.point([(0, 2), (39, 2)], fill=HOUSING_DK)
    return img


def glow():
    img = Image.new("RGBA", (GW, GH), T)
    px = img.load()
    cx = GW / 2
    for y in range(GH):
        t = y / (GH - 1)
        half = (TOP_W / 2) + (GW / 2 - TOP_W / 2) * t      # trapecio
        a_center = 105 * (1 - t) + 30 * t                  # se apaga hacia abajo
        for x in range(GW):
            dx = abs(x + 0.5 - cx)
            if dx > half:
                continue
            edge = 1 - (dx / half) ** 2                     # más luz al centro
            a = dither(a_center * edge, x, y)
            if a:
                px[x, y] = LIGHT + (a,)
    # charco de luz en el piso (elipse chata al pie del cono)
    for y in range(GH - 8, GH):
        for x in range(GW):
            ex = (x + 0.5 - cx) / (GW / 2 - 4)
            ey = (y - (GH - 2)) / 6
            r = ex * ex + ey * ey
            if r < 1:
                a = dither(70 * (1 - r), x, y)
                if a > px[x, y][3]:
                    px[x, y] = LIGHT + (a,)
    # el tubo encendido, arriba del todo (calza en la carcasa: fixture y+3)
    x0 = int(cx - 17)
    for x in range(x0, x0 + 34):
        px[x, 0] = TUBE
        px[x, 1] = LIGHT + (230,)
    return img


def sombra():
    w, h = 64, 8
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    for x in range(w):
        ramp = min(1, x / 16, (w - 1 - x) / 16)            # 16 px de cada lado esfumados
        for y in range(h):
            px[x, y] = DARK + (round(255 * ramp),)
    return img


def main():
    fixture().save(f"{OUT}/lamp_fixture.png")
    glow().save(f"{OUT}/lamp_glow.png")
    sombra().save(f"{OUT}/lab_sombra.png")
    print(f"lamp_fixture 40x5, lamp_glow {GW}x{GH}, lab_sombra 64x8  ->  {OUT}/")


if __name__ == "__main__":
    main()
