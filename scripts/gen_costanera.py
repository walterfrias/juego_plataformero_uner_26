#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_costanera.py  —  la Costanera del Río de la Plata: muro de hormigón +
caños de desagüe grandes que vierten agua + el río abajo.

Genera (game/assets/City/, paleta de palette_night.py):
  - embankment.png   48x64   muro de hormigón del malecón (tilea horizontal)
  - river.png        64x48   agua del río (tilea horizontal; se scrollea por evento)
  - river_foam.png   32x8    línea de espuma en la orilla (tilea horizontal)
  - drain_pipe.png   48x48   boca de caño redonda (3x), rejilla + gotera
  - drain_stream.png 4x (36x27)  chorro de agua ancho y corto + salpica (frames sueltos)
  - drain_splash.png 4x (48x14)  anillos de salpicadura sobre el agua (frames sueltos)
  - rebar_spikes.png 32x46   hierros expuestos saliendo del agua (tilea horizontal)
  - gap_debris.png   48x44   montículo de cascotes + hierros para los bordes del hueco
  - barbed_wire.png  48x14   2 hebras finas con púas, para tender sobre el hueco (tilea horiz)
  - wall_break_l/r.png 16x60 borde dentado del muro roto (izq / der del hueco)

Lo cablea `wire_costanera.py`.
Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_costanera.py
"""
from PIL import Image
import random
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palette_night import (  # noqa: E402
    CONCRETE_HI, CONCRETE, CONCRETE_DK, CONCRETE_STAIN, FORMLINE,
    WATER_DEEP, WATER, WATER_HI, WATER_GLINT, FOAM, FOAM_DIM,
    PIPE_RIM_LIT, PIPE_RIM, PIPE_RIM_DK, PIPE_HOLE, PIPE_HOLE_HI,
    STREAM_CORE, STREAM, STREAM_EDGE, SPLASH,
    REBAR, REBAR_HI, REBAR_DK, RUBBLE,
)

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)


def embankment():
    W, H = 48, 64
    rng = random.Random(7)
    im = Image.new("RGBA", (W, H), CONCRETE)
    px = im.load()
    for y in range(H):
        for x in range(W):
            r = rng.random()
            if r < 0.05:
                px[x, y] = CONCRETE_HI
            elif r < 0.13:
                px[x, y] = CONCRETE_DK
    for vx in (0, 16, 32):
        for y in range(H):
            px[vx, y] = FORMLINE
            px[(vx + 1) % W, y] = CONCRETE_DK
    for x in range(W):
        px[x, 22] = FORMLINE
        px[x, 23] = CONCRETE_HI if rng.random() < 0.3 else CONCRETE_DK
    for _ in range(6):
        sx, w, top = rng.randint(2, W - 3), rng.randint(1, 3), rng.randint(0, 20)
        for y in range(top, H):
            for x in range(sx, min(sx + w, W)):
                if rng.random() < 0.6:
                    px[x, y] = CONCRETE_STAIN
    im.save(f"{OUT}/embankment.png")
    print("embankment.png", im.size)


def river():
    W, H = 64, 48
    rng = random.Random(11)
    im = Image.new("RGBA", (W, H), WATER)
    px = im.load()
    for y in range(H):
        for x in range(W):
            # bandas suaves, menos contrastadas que antes
            n = math.sin(y * 0.5) + 0.4 * math.sin(x * 0.2 + y)
            px[x, y] = WATER_DEEP if n < -0.9 else (WATER_HI if n > 1.1 else WATER)
    for _ in range(55):
        y, x, ln = rng.randint(0, H - 1), rng.randint(0, W - 1), rng.randint(2, 7)
        for i in range(ln):
            if rng.random() < 0.8:
                px[(x + i) % W, y] = WATER_HI
    for _ in range(10):
        px[rng.randint(0, W - 1), rng.randint(0, H - 1)] = WATER_GLINT
    im.save(f"{OUT}/river.png")
    print("river.png", im.size)


def river_foam():
    W, H = 32, 8
    rng = random.Random(3)
    im = Image.new("RGBA", (W, H), T)
    px = im.load()
    for x in range(W):
        px[x, 0] = FOAM_DIM
        px[x, 1] = FOAM if rng.random() < 0.7 else FOAM_DIM
        if rng.random() < 0.55:
            px[x, 2] = FOAM if rng.random() < 0.4 else FOAM_DIM
        if rng.random() < 0.3:
            px[x, 3] = FOAM_DIM
        if rng.random() < 0.12:
            px[x, 4] = FOAM_DIM
    im.save(f"{OUT}/river_foam.png")
    print("river_foam.png", im.size)


def drain_pipe():
    """48x48: boca redonda con reborde de hormigón, 3 barrotes y gotera."""
    W, H = 48, 48
    im = Image.new("RGBA", (W, H), T)
    px = im.load()
    cx, cy, R = 23.5, 23.5, 22.0
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy)
            if d <= R:
                if d > R - 4:
                    px[x, y] = PIPE_RIM_LIT if (y - cy) < -abs(x - cx) * 0.5 else PIPE_RIM
                elif d > R - 8:
                    px[x, y] = PIPE_RIM if (y < cy) else PIPE_RIM_DK
                else:
                    # interior: leve degradé, más claro arriba
                    px[x, y] = PIPE_HOLE_HI if (y - cy) < -6 else PIPE_HOLE
    # barrotes verticales de la rejilla
    for bx in (int(cx) - 8, int(cx), int(cx) + 8):
        for y in range(H):
            if math.hypot(bx - cx, y - cy) <= R - 8:
                px[bx, y] = PIPE_RIM_DK
                px[bx + 1, y] = PIPE_RIM
    # gotera permanente en el labio inferior
    for y in range(int(cy + R) - 2, H):
        px[int(cx), y] = STREAM
        px[int(cx) + 1, y] = STREAM_CORE
    im.save(f"{OUT}/drain_pipe.png")
    print("drain_pipe.png", im.size)


def drain_stream():
    """4 frames de 36x27: chorro ancho y corto que ondula y salpica abajo."""
    FW, FH, N = 36, 27, 4
    rng = random.Random(5)
    for f in range(N):
        fr = Image.new("RGBA", (FW, FH), T)
        px = fr.load()
        phase = f * 1.7
        for y in range(FH):
            spread = 6.0 + (y / FH) * 9.0                 # medio-ancho: se abre hacia abajo
            wob = 2.0 * math.sin(y / 4.0 + phase) * (1 - y / FH)
            cx = FW / 2 + wob
            for x in range(int(cx - spread), int(cx + spread + 1)):
                if 0 <= x < FW:
                    dx = abs(x - cx)
                    px[x, y] = STREAM_CORE if dx < spread * 0.35 else (
                        STREAM if dx < spread * 0.8 else STREAM_EDGE)
        # salpicadura ancha en la base
        for _ in range(40):
            sx = int(FW / 2 + rng.uniform(-15, 15))
            sy = rng.randint(FH - 6, FH - 1)
            if 0 <= sx < FW:
                px[sx, sy] = SPLASH if rng.random() < 0.5 else STREAM_CORE
        fr.save(f"{OUT}/drain_stream_{f + 1}.png")
    print(f"drain_stream_1..{N}.png ({FW}x{FH})")


def drain_splash():
    """4 frames de 48x14: anillos que se expanden donde el chorro pega el agua."""
    FW, FH, N = 48, 14, 4
    for f in range(N):
        fr = Image.new("RGBA", (FW, FH), T)
        px = fr.load()
        cx = FW / 2
        rad = 3 + f * 5                                    # anillo que crece
        for x in range(FW):
            dx = abs(x - cx)
            for r, col in ((rad, SPLASH), (rad - 4, FOAM_DIM)):
                if r > 0:
                    yy = FH - 2 - int(max(0, (r ** 2 - dx ** 2)) ** 0.5 * 0.28)
                    if 0 <= yy < FH and dx <= r:
                        px[x, yy] = col
        # espuma en el centro los primeros frames
        if f < 2:
            for x in range(int(cx) - 3, int(cx) + 3):
                px[x, FH - 2] = SPLASH
                px[x, FH - 1] = FOAM_DIM
        fr.save(f"{OUT}/drain_splash_{f + 1}.png")
    print(f"drain_splash_1..{N}.png ({FW}x{FH})")


def rebar_spikes():
    """32x46 tileable: hierros doblados saliendo del agua, apuntando bien arriba.
    Base (y>38) transparente para clavar en la línea de agua."""
    W, H = 32, 46
    rng = random.Random(19)
    im = Image.new("RGBA", (W, H), T)
    px = im.load()
    # cascotes de hormigón medio hundidos en la base
    for _ in range(14):
        cx, cy = rng.randint(0, W - 1), rng.randint(H - 12, H - 1)
        for dx in range(-2, 3):
            for dy in range(-2, 2):
                if 0 <= cx + dx < W and 0 <= cy + dy < H and rng.random() < 0.7:
                    px[cx + dx, cy + dy] = RUBBLE
    # varillas cada ~4px, altas y curvadas (empalizada de hierros)
    for bx in range(1, W + 1, 4):
        bx += rng.randint(-1, 1)
        top = rng.randint(0, 8)
        lean = rng.uniform(-0.45, 0.45)
        for y in range(top, H):
            x = int(bx + lean * (y - top))
            for xx in (x, x + 1):
                if 0 <= xx < W:
                    if y <= top + 1:
                        px[xx, y] = REBAR_HI            # punta oxidada
                    elif rng.random() < 0.18:
                        px[xx, y] = REBAR_HI
                    else:
                        px[xx, y] = REBAR if xx == x else REBAR_DK
    im.save(f"{OUT}/rebar_spikes.png")
    print("rebar_spikes.png", im.size)


def gap_debris():
    """48x44: montículo de cascotes de hormigón + hierros, para los bordes
    del hueco. Reaching up casi hasta la línea del cordón."""
    W, H = 48, 44
    rng = random.Random(31)
    im = Image.new("RGBA", (W, H), T)
    px = im.load()
    # silueta de montículo (más alto al centro)
    for x in range(W):
        peak = int(H - 6 - 22 * math.sin(math.pi * x / W) + rng.randint(-3, 3))
        for y in range(max(0, peak), H):
            r = rng.random()
            px[x, y] = CONCRETE_HI if r < 0.10 else (
                CONCRETE_STAIN if r < 0.22 else RUBBLE)
    # bloques rectangulares sueltos encima
    for _ in range(7):
        bw, bh = rng.randint(5, 11), rng.randint(4, 8)
        bx, by = rng.randint(0, W - bw), rng.randint(4, H - bh - 2)
        for x in range(bx, bx + bw):
            for y in range(by, by + bh):
                edge = (x in (bx, bx + bw - 1)) or (y in (by, by + bh - 1))
                px[x, y] = FORMLINE if edge else (
                    CONCRETE_HI if (x + y) % 7 == 0 else CONCRETE_DK)
    # hierros saliendo en ángulo
    for _ in range(5):
        sx, sy = rng.randint(4, W - 4), rng.randint(6, H - 8)
        dx, dy = rng.choice([-1, 1]), -1
        for i in range(rng.randint(6, 14)):
            x, y = sx + dx * i, sy + dy * i - int(0.2 * i)
            if 0 <= x < W and 0 <= y < H:
                px[x, y] = REBAR_HI if i > 4 else REBAR
    im.save(f"{OUT}/gap_debris.png")
    print("gap_debris.png", im.size)


def barbed_wire():
    """48x14 tileable: 2 hebras finas onduladas con púas espaciadas. Para tender
    sobre el hueco casi al ras del cordón. Ondas periódicas (tilea sin costura)."""
    W, H = 48, 14
    im = Image.new("RGBA", (W, H), T)
    px = im.load()

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            px[x % W, y] = c

    for si, (sy, k) in enumerate(((4, 2.0), (9, 2.0))):
        phase = si * math.pi
        ys = []
        for x in range(W):
            y = sy + 1.6 * math.sin(2 * math.pi * k * x / W + phase)
            iy = int(round(y))
            ys.append(iy)
            put(x, iy, REBAR)
            put(x, iy + 1, REBAR_DK)
            if x % 6 == si:
                put(x, iy, REBAR_HI)
        # púas cada 12px: una X chica de 4 puntas sobre la hebra
        for bx in range(3 + si * 6, W, 12):
            by = ys[bx % W]
            for dx, dy in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
                put(bx + dx, by + dy, REBAR)
            for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                put(bx + dx, by + dy, REBAR_HI)
    im.save(f"{OUT}/barbed_wire.png")
    print("barbed_wire.png", im.size)


def wall_break(side):
    """16x60: el borde dentado del muro donde se rompió, con un par de hierros."""
    W, H = 16, 60
    rng = random.Random(23 if side == "l" else 29)
    im = Image.new("RGBA", (W, H), T)
    px = im.load()
    # perfil dentado vertical (para lado 'l' el muro está a la izquierda)
    for y in range(H):
        jag = int(3 * math.sin(y * 0.4) + rng.randint(-2, 2))
        if side == "l":
            edge = W - 4 + jag
            xr = range(0, min(W, edge))
        else:
            edge = 4 + jag
            xr = range(max(0, edge), W)
        for x in xr:
            r = rng.random()
            px[x, y] = CONCRETE_HI if r < 0.06 else (
                CONCRETE_DK if r < 0.16 else CONCRETE)
        # línea de encofrado
        if y % 12 == 0:
            for x in xr:
                px[x, y] = FORMLINE
    # hierros salientes cerca del tope
    for hy in (rng.randint(4, 10), rng.randint(16, 24)):
        length = rng.randint(4, 8)
        for i in range(length):
            x = (i) if side == "l" else (W - 1 - i)
            yy = hy + int(i * 0.5)
            if 0 <= x < W and 0 <= yy < H:
                px[x, yy] = REBAR_HI if i == length - 1 else REBAR
    im.save(f"{OUT}/wall_break_{side}.png")
    print(f"wall_break_{side}.png", im.size)


if __name__ == "__main__":
    embankment()
    river()
    river_foam()
    drain_pipe()
    drain_stream()
    drain_splash()
    rebar_spikes()
    gap_debris()
    barbed_wire()
    wall_break("l")
    wall_break("r")
