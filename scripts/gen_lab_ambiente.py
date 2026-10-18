#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_lab_ambiente.py  —  luces de ambiente del laboratorio (sprint de arte del
18/10): que las zonas oscuras de L2 y la arena de L3 tengan islas de luz con
color en vez de un velo gris parejo. Lo cablea wire_lab_ambiente.py.

Mismo criterio que gen_lab_luces.py (de ahí sale el tramado): Pillow, alfa
en escalones con tramado Bayer 4x4, así se ve como luz de juego retro.

Crea (game/assets/Lab/):
  luz_tanque.png    64x72  resplandor verde de un par de tanques del fondo
                           (lab_near.png, x 58..106 del tile) + charco en el piso
  luz_monitor.png   34x26  resplandor cian de un monitor (lab_near, x 132/162)
  baliza.png        10x6   baliza de alarma en la pared (cúpula roja)
  baliza_haz.png    70x150 haz rojo de la baliza (el evento lo hace barrer
                           de lado a lado rotándolo desde la punta de arriba)
  alarma_tinte.png  64x8   tinte rojo de zona, extremos esfumados (se estira
                           al ancho de la zona; el evento lo hace latir)

Uso:  python3 scripts/gen_lab_ambiente.py   (desde la raíz del repo)
"""
from PIL import Image, ImageDraw
import os

from gen_lab_luces import dither

OUT = "game/assets/Lab"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)
GREEN = (140, 230, 140)          # = LIQUID_HI de gen_lab.py
CYAN = (110, 210, 180)           # = SCREEN_HI de gen_lab.py
RED = (255, 64, 52)
RED_DK = (120, 24, 24, 255)
HOUSING = (58, 68, 76, 255)
HOUSING_DK = (30, 36, 42, 255)


def luz_tanque():
    """Los dos tanques del tile de lab_near quedan en x 8..24 y 36..52 del
    sprite (el sprite va en x_tile + 52); el líquido en y 30..60; el piso en
    la fila 68."""
    w, h = 64, 72
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    for y in range(h):
        for x in range(w):
            a = 0.0
            for cx in (16.5, 44.5):                    # centro de cada tanque
                dx = (x + 0.5 - cx) / 16
                dy = (y + 0.5 - 46) / 26
                r = (dx * dx + dy * dy) ** 0.5
                a = max(a, max(0.0, 1 - r) ** 1.4 * 110)
            # charco en el piso, delante de los tanques
            ex, ey = (x + 0.5 - 32) / 31, (y + 0.5 - 68) / 4
            r = ex * ex + ey * ey
            if r < 1:
                a = max(a, 115 * (1 - r))
            v = dither(a, x, y)
            if v:
                px[x, y] = GREEN + (v,)
    img.save(f"{OUT}/luz_tanque.png")


def luz_monitor():
    """La pantalla (20x13) queda en x 7..27, y 5..18 del sprite (el sprite va
    en x_monitor - 5, y_near + 15)."""
    w, h = 34, 26
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    for y in range(h):
        for x in range(w):
            dx = max(0, abs(x + 0.5 - 17) - 9) / 8
            dy = max(0, abs(y + 0.5 - 11.5) - 6) / 7
            r = (dx * dx + dy * dy) ** 0.5
            a = max(0.0, 1 - r) ** 1.5 * 80
            v = dither(a, x, y)
            if v:
                px[x, y] = CYAN + (v,)
    img.save(f"{OUT}/luz_monitor.png")


def baliza():
    img = Image.new("RGBA", (10, 6), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 9, 1], fill=HOUSING)            # soporte contra la pared
    d.rectangle([2, 2, 7, 5], fill=RED_DK)              # cúpula
    d.rectangle([3, 2, 6, 4], fill=RED + (255,))
    d.point((4, 3), fill=(255, 190, 170, 255))          # brillo
    d.line([(1, 5), (8, 5)], fill=HOUSING_DK)
    img.save(f"{OUT}/baliza.png")


def baliza_haz():
    """Cono que nace en la punta de arriba al centro (35, 0): ahí van el
    origen y el centro de rotación del sprite."""
    w, h = 70, 150
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    cx = w / 2
    for y in range(h):
        t = y / (h - 1)
        half = 3 + (w / 2 - 3) * t
        a_center = 110 * (1 - t) ** 1.2 + 12
        for x in range(w):
            dx = abs(x + 0.5 - cx)
            if dx > half:
                continue
            v = dither(a_center * (1 - (dx / half) ** 2), x, y)
            if v:
                px[x, y] = RED + (v,)
    for y in range(3):                                   # el foco, en la punta
        for x in range(int(cx) - 2, int(cx) + 2):
            px[x, y] = (255, 170, 150, 230)
    img.save(f"{OUT}/baliza_haz.png")


def alarma_tinte():
    w, h = 64, 8
    img = Image.new("RGBA", (w, h), T)
    px = img.load()
    for x in range(w):
        ramp = min(1, x / 16, (w - 1 - x) / 16)          # = lab_sombra: 16 px esfumados
        for y in range(h):
            px[x, y] = (200, 28, 28, round(255 * ramp))
    img.save(f"{OUT}/alarma_tinte.png")


def main():
    luz_tanque()
    luz_monitor()
    baliza()
    baliza_haz()
    alarma_tinte()
    print(f"luz_tanque, luz_monitor, baliza, baliza_haz, alarma_tinte  ->  {OUT}/")


if __name__ == "__main__":
    main()
