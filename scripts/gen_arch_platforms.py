#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_arch_platforms.py  —  2 SECCIONES DE EDIFICIO completas (de la azotea a
la calle), cada una con un elemento donde apoyarse arriba. Reemplazan a la
Cornisa flotante. Distintas en forma y paleta, ambas con luz y sombra.
Pensadas para usarse también como REFUGIO (tienen puerta a la calle).

  Balcon.png            46x80  — edificio con balcón: baranda de hierro que
                                 SUBE desde la losa (no cuelga), puerta
                                 ventana atrás, ventanas con postigo, y
                                 puerta de calle abajo (más alta que un
                                 zombie). Fachada ocre (cálida).
  EscaleraIncendio.png  46x80  — edificio con descanso de escalera de
                                 incendios: reja + baranda + escalerita que
                                 baja, ventanas, puerta de calle. Ladrillo
                                 gris + acero oxidado (fría).

Sólo la losa / reja lleva colisión (el wire pone máscara custom en esa
franja); el resto del edificio es dibujo — el player camina por delante y
sólo se apoya arriba saltando.
Pie al ras del borde inferior: se coloca con  y = alturaPiso - altoSprite.

Tech: Python 3 + Pillow.  Uso:  python3 scripts/gen_arch_platforms.py
"""
from PIL import Image, ImageDraw
import os

OUT = "game/assets/N1"
os.makedirs(OUT, exist_ok=True)
RIM = (18, 22, 28, 255)
W, H = 46, 80

# --- Balcon: fachada ocre + hierro verde-negro ---
WALL   = (128, 102, 72, 255)
WALL_D = (96, 76, 52, 255)
WALL_L = (152, 122, 86, 255)
IRON   = (44, 52, 46, 255)
IRON_D = (26, 32, 28, 255)
IRON_L = (72, 82, 72, 255)
DOOR   = (46, 38, 34, 255)
DOOR_L = (70, 58, 50, 255)
SLAB   = (140, 136, 124, 255)
SLAB_L = (172, 166, 150, 255)
SLAB_D = (100, 96, 86, 255)
GLASS  = (40, 46, 58, 255)
GLASS_L = (58, 66, 82, 255)

# --- EscaleraIncendio: ladrillo gris + acero oxidado ---
BRICK   = (66, 66, 74, 255)
BRICK_D = (48, 48, 56, 255)
BRICK_L = (90, 88, 94, 255)
STEEL   = (102, 82, 64, 255)
STEEL_D = (64, 52, 42, 255)
STEEL_L = (136, 108, 80, 255)
GRATE   = (76, 64, 58, 255)
GRATE_D = (48, 42, 38, 255)


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
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128 and px[nx, ny] != RIM:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = RIM


def _facade(d, base, dark, light, brick_step):
    """fachada plana con canto iluminado a la izq y sombra a la der + hiladas."""
    d.rectangle([2, 2, W - 1, H - 1], fill=base)
    for y in range(4, H - 1, brick_step):
        d.line([(2, y), (W - 1, y)], fill=dark)
    d.rectangle([2, 2, 3, H - 1], fill=light)          # canto iluminado (luna)
    d.rectangle([W - 3, 2, W - 1, H - 1], fill=dark)   # sombra lado derecho


def _window(d, x0, y0, x1, y1, frame, glass, glass_l):
    d.rectangle([x0, y0, x1, y1], fill=frame)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=glass)
    d.line([(x0 + 1, y0 + 1), (x1 - 2, y0 + 1)], fill=glass_l)     # reflejo arriba
    d.line([((x0 + x1) // 2, y0), ((x0 + x1) // 2, y1)], fill=frame)
    d.line([(x0, (y0 + y1) // 2), (x1, (y0 + y1) // 2)], fill=frame)


def _street_door(d, frame, dark, light):
    # portal de entrada: ~38px de alto (un poco más que un zombie de 34) y 17 de ancho
    dx0, dx1, dy0, dy1 = 14, 31, H - 40, H - 1
    d.rectangle([dx0 - 2, dy0 - 3, dx1 + 2, dy1], fill=frame)      # marco
    d.rectangle([dx0, dy0, dx1, dy1], fill=dark)                   # hueco
    d.line([(dx0, dy0 + 1), (dx1, dy0 + 1)], fill=light)          # dintel iluminado
    d.line([(dx0, dy0 + 5), (dx1, dy0 + 5)], fill=frame)         # travesaño / fanlight
    d.line([((dx0 + dx1) // 2, dy0 + 5), ((dx0 + dx1) // 2, dy1)], fill=(24, 20, 20, 255))
    for hy in (dy0 + 12, dy0 + 22):                               # tableros de las hojas
        d.line([(dx0 + 2, hy), ((dx0 + dx1) // 2 - 1, hy)], fill=(24, 20, 20, 255))
        d.line([((dx0 + dx1) // 2 + 1, hy), (dx1 - 2, hy)], fill=(24, 20, 20, 255))
    d.point([(dx0 + 4, dy1 - 8), ((dx0 + dx1) // 2 + 3, dy1 - 8)], fill=light)  # picaportes
    d.rectangle([dx0 - 4, dy1 - 1, dx1 + 4, dy1], fill=frame)      # umbral / escalón


def balcon():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _facade(d, WALL, WALL_D, WALL_L, brick_step=4)
    # cornisa de arriba
    d.rectangle([1, 0, W - 1, 1], fill=WALL_L)

    # --- puerta ventana del balcón (atrás, en la fachada) ---
    d.rectangle([17, 3, 29, 16], fill=DOOR)
    for yy in range(5, 16, 3):
        d.line([(18, yy), (28, yy)], fill=DOOR_L)
    # --- baranda de hierro que SUBE desde la losa ---
    d.line([(4, 4), (41, 4)], fill=IRON_L)                        # pasamanos (arriba)
    for bx in range(5, 41, 4):
        d.line([(bx, 4), (bx, 14)], fill=IRON)                    # barrotes verticales
    d.line([(5, 9), (40, 9)], fill=IRON_D)                        # travesaño
    # --- losa del balcón (SUPERFICIE — franja landable) ---
    d.rectangle([2, 14, 40, 16], fill=SLAB)
    d.rectangle([2, 13, 40, 13], fill=SLAB_L)                     # canto con luz de luna
    d.rectangle([2, 16, 40, 17], fill=SLAB_D)
    d.rectangle([2, 17, 40, 18], fill=DOOR)                       # sombra proyectada abajo
    # ménsulas bajo la losa
    d.line([(5, 17), (9, 22)], fill=IRON_D)
    d.line([(37, 17), (33, 22)], fill=IRON_D)

    # --- resto del edificio hacia la calle (fachada más alta) ---
    _window(d, 6, 23, 18, 33, WALL_D, GLASS, GLASS_L)
    _window(d, 28, 23, 40, 33, WALL_D, GLASS, GLASS_L)
    _window(d, 5, 44, 12, 58, WALL_D, GLASS, GLASS_L)     # angostas, al lado del portal
    _window(d, 34, 44, 41, 58, WALL_D, GLASS, GLASS_L)
    _street_door(d, WALL_D, DOOR, WALL_L)

    _outline(im)
    im.save(f"{OUT}/Balcon.png")


def escalera_incendio():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _facade(d, BRICK, BRICK_D, BRICK_L, brick_step=3)
    d.rectangle([1, 0, W - 1, 1], fill=BRICK_L)                    # parapeto

    # --- baranda del descanso, sube desde la reja ---
    d.line([(3, 3), (37, 3)], fill=STEEL_L)                       # pasamanos
    for bx in range(4, 37, 4):
        d.line([(bx, 3), (bx, 13)], fill=STEEL)
    d.line([(4, 8), (36, 8)], fill=STEEL_D)
    # escalerita que SUBE (fuera de cuadro) a la derecha
    for ry in range(0, 12, 3):
        d.line([(38, ry), (43, ry)], fill=STEEL)
    d.line([(38, 0), (38, 13)], fill=STEEL_D)
    d.line([(43, 0), (43, 13)], fill=STEEL_D)
    # --- reja del descanso (SUPERFICIE — franja landable) ---
    d.rectangle([2, 13, 37, 16], fill=GRATE)
    for x in range(4, 37, 3):
        d.line([(x, 14), (x, 15)], fill=GRATE_D)
    d.rectangle([2, 12, 37, 12], fill=STEEL_L)                    # canto con luz
    d.rectangle([2, 16, 37, 17], fill=STEEL_D)
    # ménsulas diagonales a la pared
    for sx in (5, 22):
        d.line([(sx, 16), (sx + 12, 30)], fill=STEEL)
    # escalerita que BAJA al frente
    for ry in range(18, 34, 3):
        d.line([(8, ry), (16, ry)], fill=STEEL_D)
    d.line([(8, 17), (8, 34)], fill=STEEL)
    d.line([(16, 17), (16, 34)], fill=STEEL)

    # --- resto del edificio hacia la calle (fachada más alta) ---
    _window(d, 6, 22, 18, 32, BRICK_D, GLASS, GLASS_L)
    _window(d, 24, 22, 38, 32, BRICK_D, GLASS, GLASS_L)
    _window(d, 5, 44, 12, 58, BRICK_D, GLASS, GLASS_L)    # angostas, al lado del portal
    _window(d, 34, 44, 41, 58, BRICK_D, GLASS, GLASS_L)
    _street_door(d, BRICK_D, DOOR, BRICK_L)

    _outline(im)
    im.save(f"{OUT}/EscaleraIncendio.png")


def main():
    balcon()
    escalera_incendio()
    a, b = Image.open(f"{OUT}/Balcon.png"), Image.open(f"{OUT}/EscaleraIncendio.png")
    sheet = Image.new("RGBA", (a.width + b.width + 12, max(a.height, b.height) + 4), (16, 20, 40, 255))
    sheet.alpha_composite(a, (4, 2))
    sheet.alpha_composite(b, (a.width + 8, 2))
    sheet.save(f"{OUT}/_arch_contact.png")
    print(f"Balcon {a.size}  |  EscaleraIncendio {b.size}  ->  {OUT}/  "
          f"(franja landable: losa ~y13-17 / reja ~y12-16 ; portal de calle ~y40-79)")


if __name__ == "__main__":
    assert os.path.isdir("game/assets"), "corré desde la raíz del repo"
    main()
