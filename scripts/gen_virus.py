#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_virus.py  —  obstáculo aéreo del Nivel 1: virus flotante estilo
coronavirus (bola con espigas), que el jugador tiene que esquivar.

Diseño:
  - paleta única de 4 tonos, todos la misma familia rosa/roja de la
    espiga (a pedido del usuario 2026-09-13: "que no haya tanto
    contraste, todo del color de las puntas, pero con sombra/luz") —
    el centro ya NO es un rojo más oscuro aparte, usa los mismos 4
    tonos que las espigas (SHADE/BASE/LIGHT/TIP), solo que repartidos
    distinto para dar volumen.
  - más espigas (14, antes 9) y de largo variable — chicas/medianas/
    grandes mezcladas por spike (nunca más grandes que antes, la
    variedad es hacia abajo) para que la silueta se vea más orgánica,
    no como una flor pareja.
  - animación de 6 frames: el cuerpo "respira" (pulso de radio) y las
    espigas se mueven con un jitter individual por frame — no es un
    sprite estático, lee como si estuviera flotando/vibrando en el aire.
  - se lee por silueta + color, mismo criterio que zombies/antidoto/mochila.
  - no tiene animación de "muerte": es un obstáculo, no se puede eliminar
    (a diferencia de los zombies, que se matan con stomp).

Crea (game/assets/Virus/):
  virus_1..6.png    16x16  RGBA
  virus_sheet.png   96x16  referencia

Tech: Python 3 + Pillow, sin IA de imagen.  Uso:  python3 scripts/gen_virus.py
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/Virus"
os.makedirs(OUT, exist_ok=True)

W = H = 16
N = 6

OUTL  = (18, 12, 26, 255)
# 1 sola familia de color (rosa/rojo), 4 pasos de luz -> sombra a luz
SHADE = (176, 58, 74, 255)
BASE  = (206, 82, 96, 255)
LIGHT = (232, 114, 124, 255)
TIP   = (250, 156, 164, 255)

cx, cy = W / 2, H / 2
base_r = 4.5
n_spikes = 14
# largo de cada espiga por índice: mezcla chica/mediana/grande, nunca
# más grande que el máximo viejo (~2.85px) — variedad hacia abajo.
SPIKE_LEN = [1.1, 2.0, 1.5, 2.6, 1.2, 1.8, 1.0, 2.4,
             1.4, 1.9, 1.1, 2.5, 1.6, 2.1]


def _outline(img):
    px = img.load()
    w, h = img.size
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128:
                    edge.append((x, y))
                    break
    for (x, y) in edge:
        px[x, y] = OUTL
    return img


def draw_frame(i):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pulse = math.sin(i / N * 2 * math.pi) * 0.5
    r = base_r + pulse
    rot = i / N * (2 * math.pi / n_spikes)

    for s in range(n_spikes):
        ang = rot + s * (2 * math.pi / n_spikes)
        jitter = math.sin(i / N * 2 * math.pi + s * 1.7) * 0.4
        length = SPIKE_LEN[s % len(SPIKE_LEN)] + jitter
        x0 = cx + math.cos(ang) * r
        y0 = cy + math.sin(ang) * r
        x1 = cx + math.cos(ang) * (r + length)
        y1 = cy + math.sin(ang) * (r + length)
        d.line([x0, y0, x1, y1], fill=SHADE, width=1)
        d.ellipse([x1 - 1.0, y1 - 1.0, x1 + 1.0, y1 + 1.0], fill=BASE)
        d.ellipse([x1 - 0.5, y1 - 0.5, x1 + 0.5, y1 + 0.5], fill=TIP)

    # cuerpo: mismos 4 tonos, repartidos como sombra (abajo-der) / base / luz (arriba-izq)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BASE)
    d.ellipse([cx - r, cy - r * 0.15, cx + r, cy + r], fill=SHADE)
    d.ellipse([cx - r * 0.55, cy - r * 0.7, cx + r * 0.15, cy - r * 0.05], fill=LIGHT)
    d.ellipse([cx - r * 0.3, cy - r * 0.5, cx - r * 0.05, cy - r * 0.25], fill=TIP)
    for (dx, dy, rr) in [(-1.1, 0.6, 0.85), (1.4, 1.1, 0.7), (0.3, -1.3, 0.6)]:
        d.ellipse([cx + dx - rr, cy + dy - rr, cx + dx + rr, cy + dy + rr], fill=SHADE)

    return _outline(img)


def main():
    frames = [draw_frame(i) for i in range(N)]
    for i, f in enumerate(frames, start=1):
        f.save(f"{OUT}/virus_{i}.png")

    sheet = Image.new("RGBA", (W * N, H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * W, 0), f)
    sheet.save(f"{OUT}/virus_sheet.png")
    print(f"ok: {N} frames {W}x{H} -> {OUT}/")


if __name__ == "__main__":
    main()
