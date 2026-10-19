#!/usr/bin/env python3
"""
gen_l3_calle.py  —  piezas nuevas del Nivel 3 (recorrido por el centro y la
arena del Obelisco, 18/10). Casi todo el nivel reusa el kit de L1; esto es
lo poco que faltaba. Lo usa wire_l3_recorrido.py.

Mismo criterio que el resto: Pillow, paleta noche.

Crea (game/assets/City/):
  valla.png          16x16  valla de contención metálica, tileable en Y: la
                            barricada que se cierra detrás de Lio al entrar
                            a la arena
  andamio_tablon.png 64x8   tablón de andamio: reemplaza al estante del lab
                            como plataforma de la arena (mismo tamaño)
  andamio_poste.png   4x8   caño del andamio, tileable en Y: sostiene los
                            tablones (si no, flotarían como las camillas)
  estatua_columna_izq/der.png 102x130 pirámide monolito de basalto (tope = y 70)
                            con la losa de granito adelante (y 122); hasta el 18/10
                            era una columna con la Libertad
  estatua_busto_izq/der.png   64x80  pedestal alto (y 96) con el busto de un
                            prócer con barbijo (las plataformas de la arena)
  obelisco_cerca.png 48x176 el Obelisco de la arena: pedestal con cinta de
                            cuarentena, fuste, punta y ventanita; luna desde la
                            izquierda y reflector cálido desde abajo

Uso:  python3 scripts/gen_l3_calle.py   (desde la raíz del repo)
"""
from PIL import Image, ImageDraw
import os

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)
STEEL_LIT = (128, 136, 150, 255)
STEEL = (86, 92, 106, 255)
STEEL_DK = (46, 50, 62, 255)
SEAM = (22, 24, 32, 255)
BLUE = (60, 96, 160, 255)              # franja de la valla policial
WOOD_LIT = (150, 116, 78, 255)
WOOD = (112, 84, 56, 255)
WOOD_DK = (70, 52, 36, 255)


def valla():
    w, h = 16, 16
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1, h - 1], fill=STEEL_LIT)          # parantes
    d.rectangle([14, 0, 15, h - 1], fill=STEEL_DK)
    for x in range(3, 13, 3):                              # barrotes
        d.line([(x, 0), (x, h - 1)], fill=STEEL)
        d.point((x + 1, 0), fill=STEEL_DK)
    d.rectangle([0, 6, 15, 9], fill=BLUE)                  # franja azul
    d.line([(0, 6), (15, 6)], fill=(110, 150, 210, 255))
    d.line([(0, 9), (15, 9)], fill=SEAM)
    img.save(f"{OUT}/valla.png")


def tablon():
    w, h = 64, 8
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, 4], fill=WOOD)               # tabla (se pisa la fila 0)
    d.line([(0, 0), (w - 1, 0)], fill=WOOD_LIT)
    d.line([(0, 4), (w - 1, 4)], fill=WOOD_DK)
    for x in (9, 23, 41, 55):                              # vetas
        d.line([(x, 2), (x + 4, 2)], fill=WOOD_DK)
    d.rectangle([0, 5, w - 1, 6], fill=STEEL)              # caño horizontal debajo
    d.line([(0, 7), (w - 1, 7)], fill=SEAM)
    for x in (2, w - 6):                                   # abrazaderas
        d.rectangle([x, 4, x + 3, 7], fill=STEEL_LIT)
    img.save(f"{OUT}/andamio_tablon.png")


def poste():
    w, h = 4, 8
    img = Image.new("RGBA", (w, h), T)
    d = ImageDraw.Draw(img)
    d.line([(0, 0), (0, h - 1)], fill=STEEL_LIT)
    d.line([(1, 0), (1, h - 1)], fill=STEEL)
    d.line([(2, 0), (2, h - 1)], fill=STEEL)
    d.line([(3, 0), (3, h - 1)], fill=SEAM)
    img.save(f"{OUT}/andamio_poste.png")


# --- Obelisco de la arena (18/10): reemplaza al sprite de fondo agrandado al doble ---
OB_W, OB_H = 48, 176          # del piso (fila 175) hasta casi el borde de arriba de la cámara
CONC = [(58, 60, 78, 255), (92, 96, 116, 255), (136, 142, 160, 255),
        (178, 184, 198, 255), (214, 218, 226, 255)]
WARM = (236, 176, 112)        # reflector de abajo (luz cálida de sodio)
TAPE_Y, TAPE_K = (222, 190, 60, 255), (24, 24, 30, 255)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def _shade(t, x, y):
    t = max(0.0, min(0.999, t)) * (len(CONC) - 1)
    i, f = int(t), t - int(t)
    return CONC[min(i + 1, len(CONC) - 1)] if f * 16 > BAYER[y % 4][x % 4] else CONC[i]


def obelisco():
    """Obelisco en primer plano de fondo: pedestal, fuste que se afina, punta
    (piramidión) y la ventanita de arriba. Luz de luna desde la izquierda y el
    reflector cálido desde el piso, que se apaga hacia arriba. Cinta de
    cuarentena alrededor del pedestal."""
    img = Image.new("RGBA", (OB_W, OB_H), T)
    px = img.load()
    cx = OB_W / 2
    base_h, tip_h = 16, 12
    for y in range(OB_H):
        if y >= OB_H - base_h:                          # pedestal (2 escalones)
            half = 22 if y >= OB_H - 7 else 19
        elif y >= tip_h:                                # fuste: de 26 a 18 px de ancho
            t = (y - tip_h) / (OB_H - base_h - tip_h)
            half = 9 + 4 * t
        else:                                           # piramidión
            half = 9 * (y / tip_h)
        for x in range(OB_W):
            dx = (x + 0.5 - cx) / max(half, 0.5)
            if abs(dx) > 1:
                continue
            light = 0.66 - 0.52 * dx                     # luna desde la izquierda: cara en sombra a la derecha
            if y < tip_h:
                light += 0.12 if dx < 0 else -0.1       # caras de la punta bien marcadas
            c = _shade(light, x, y)
            # reflector: entibia la parte de abajo (se apaga hacia arriba)
            warm = max(0.0, 1 - (OB_H - y) / 110) * 0.45
            if warm > 0 and BAYER[y % 4][x % 4] / 16 < warm * 1.6:
                c = tuple(int(a * (1 - warm) + b * warm) for a, b in zip(c[:3], WARM)) + (255,)
            px[x, y] = c
    d = ImageDraw.Draw(img)
    # juntas de los paneles del fuste: pocas y cortas (si cruzan todo el ancho y
    # coinciden con el afinamiento, el fuste parece una torre de pisos)
    for y in range(tip_h + 30, OB_H - base_h - 10, 34):
        d.line([(cx - 4, y), (cx + 2, y)], fill=CONC[2])
    # ventanita cerca de la punta
    d.rectangle([cx - 1, tip_h + 7, cx, tip_h + 10], fill=CONC[0])
    d.point((cx - 1, tip_h + 7), fill=(255, 220, 150, 255))          # alguien dejó la luz prendida
    # canto del pedestal y cinta de cuarentena
    d.line([(cx - 19, OB_H - base_h), (cx + 18, OB_H - base_h)], fill=CONC[4])
    for x in range(int(cx - 22), int(cx + 22)):
        for y in (OB_H - 11, OB_H - 10):
            px[x, y] = TAPE_Y if ((x + y) // 3) % 2 == 0 else TAPE_K
    d.line([(cx + 21, OB_H - 10), (cx + 23, OB_H - 6)], fill=TAPE_Y)      # punta suelta
    # contorno oscuro de 1 px (como el resto de los objetos del juego)
    src = img.copy()
    sp = src.load()
    for y in range(OB_H):
        for x in range(OB_W):
            if sp[x, y][3] == 0 and any(0 <= x + a < OB_W and 0 <= y + b < OB_H and sp[x + a, y + b][3]
                                        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = (24, 24, 34, 255)
    img.save(f"{OUT}/obelisco_cerca.png")


# --- estatuas de la arena (18/10): las plataformas de la pelea con el jefe pasan a ser
# monumentos de la vía pública (pedido del usuario). Las superficies coinciden EXACTO con
# las 6 plataformas que ya estaban (alturas 122 / 96 / 70 del mundo, 64 px de ancho):
# la pelea no cambia. Coordenadas de cada imagen relativas a su esquina (ver wire).
GRAN = [(54, 56, 66, 255), (78, 80, 92, 255), (104, 106, 118, 255), (138, 140, 150, 255)]   # granito
BRON = [(30, 56, 52, 255), (50, 92, 84, 255), (76, 130, 116, 255), (120, 176, 154, 255)]    # bronce con pátina


def _block(img, x0, y0, x1, y1, tones):
    """bloque de piedra con luz de luna de la izquierda, junta y canto de arriba."""
    px = img.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            t = (x - x0) / max(1, x1 - x0)
            i = 2 if t * 16 < 10 - BAYER[y % 4][x % 4] * 0.5 else 1
            px[x, y] = tones[i]
    d = ImageDraw.Draw(img)
    d.line([(x0, y0), (x1 - 1, y0)], fill=tones[3])            # canto de arriba (se pisa)
    d.line([(x0, y0 + 1), (x1 - 1, y0 + 1)], fill=tones[2])
    d.line([(x0, y0), (x0, y1 - 1)], fill=tones[3])
    d.line([(x1 - 1, y0), (x1 - 1, y1 - 1)], fill=tones[0])


def _outline(img):
    src = img.copy()
    sp, px = src.load(), img.load()
    W, H = img.size
    for y in range(H):
        for x in range(W):
            if sp[x, y][3] == 0 and any(0 <= x + a < W and 0 <= y + b < H and sp[x + a, y + b][3]
                                        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = (24, 24, 34, 255)


# Las estatuas con columna pasaron a ser PIRÁMIDES ESTILO MONOLITO (18/10, pedido del usuario;
# los bustos quedan). Mismas superficies: tope plano (y 70, x 0..64) y la losa de adelante
# (y 122, x 10..74). Los faldones bajan PIR_PAD px más allá a cada lado (la imagen se ensancha
# y wire_l3_recorrido.py la corre PIR_PAD a la izquierda): son decorado, no se pisan.
PIR_PAD = 14
BASALTO = [(18, 18, 26, 255), (30, 30, 42, 255), (46, 46, 62, 255), (96, 100, 122, 255)]
RUNA = (110, 200, 80, 255)
RUNA_S = (52, 92, 46, 255)


def estatua_columna():
    """(74 + 2·PIR_PAD)x130, esquina en el mundo (30 − PIR_PAD, 20) a la izquierda: pirámide
    truncada de basalto negro (tope plano = y 70 → fila 50, x 0..64), runas verdes que laten
    apagadas en la cara, y adelante la losa de granito (y 122 → fila 102, x 10..74)."""
    P = PIR_PAD
    W, H = 74 + 2 * P, 130
    img = Image.new("RGBA", (W, H), T)
    px = img.load()
    d = ImageDraw.Draw(img)
    for y in range(50, H):
        fila = (y - 50) // 11                                   # escalonada: cada hilada asoma 2 px
        x0, x1 = P - min(P, 2 * fila), P + 64 + min(P, 2 * fila)
        for x in range(x0, x1):
            if x - x0 < 4:                                      # faldón izquierdo: luna
                c = BASALTO[2] if (x - x0) + BAYER[y % 4][x % 4] * 0.4 < 3 else BASALTO[1]
            elif x1 - x < 4:                                    # faldón derecho: sombra
                c = BASALTO[0]
            else:                                               # cara: casi negra, tramada
                c = BASALTO[1] if BAYER[y % 4][x % 4] < 3 else BASALTO[0]
            px[x, y] = c
        if (y - 50) % 11 == 0 and y > 50:                       # canto de cada hilada (luna)
            d.line([(x0, y), (x1 - 1, y)], fill=BASALTO[2])
        if (y - 50) % 11 == 1 and y > 51:                       # juntas verticales
            for jx in range(x0 + 8 + (fila % 2) * 9, x1 - 4, 18):
                d.line([(jx, y), (jx, min(H - 1, y + 9))], fill=BASALTO[2] if jx < x0 + 30 else BASALTO[0])
    d.line([(P, 50), (P + 63, 50)], fill=BASALTO[3])            # canto del tope (se pisa)
    d.line([(P, 51), (P + 63, 51)], fill=BASALTO[2])
    # runas en la cara (verde del lab, apagadas): columna de glifos
    cx = P + 32
    glifos = [((-3, 0), (3, 0), (0, -4)), ((-3, -2), (3, 2)), ((0, -3), (0, 3), (-3, 0)),
              ((-3, 3), (0, -3), (3, 3)), ((-3, -3), (3, -3), (0, 3))]
    for n, g in enumerate(glifos):
        gy = 62 + n * 8
        pts = [(cx + gx, gy + gy2) for gx, gy2 in g]
        d.line(pts, fill=RUNA, width=1)
        d.point(pts[::2], fill=(196, 250, 150, 255))
    for gy in (60, 98):                                         # marco del panel
        d.line([(cx - 7, gy), (cx + 7, gy)], fill=RUNA_S)
    # losa de granito adelante (superficie y 122), con la cinta de cuarentena
    _block(img, P + 10, 102, P + 74, H, GRAN)
    d.rectangle([P + 28, 110, P + 56, 120], fill=GRAN[0])       # placa
    d.line([(P + 31, 113), (P + 53, 113)], fill=GRAN[2])
    d.line([(P + 31, 116), (P + 47, 116)], fill=GRAN[2])
    for x in range(P + 10, P + 74):
        img.putpixel((x, 124), TAPE_Y if (x // 3) % 2 == 0 else TAPE_K)
    _outline(img)
    return img


def estatua_busto():
    """64x80, esquina en el mundo (110, 70) a la izquierda: pedestal alto (superficie y=96 →
    fila 80-54=26, x 0..64) con el busto de un prócer arriba… con barbijo."""
    W, H = 64, 80
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    _block(img, 0, 26, 64, H, GRAN)                             # pedestal: escalón del medio
    _block(img, 4, 34, 60, 37, GRAN)                            # moldura
    d.rectangle([18, 46, 46, 58], fill=GRAN[0])                 # placa
    for yy in (49, 52, 55):
        d.line([(21, yy), (43 - (yy % 4) * 3, yy)], fill=GRAN[2])
    d.line([(10, 66), (26, 62), (34, 70)], fill=(90, 170, 120, 255), width=2)   # graffiti
    # busto (hombros + cabeza) apoyado en el pedestal, detrás de donde se para Lio
    d.rectangle([20, 18, 44, 25], fill=BRON[1])                 # hombros
    d.line([(20, 18), (44, 18)], fill=BRON[2])
    d.rectangle([27, 4, 37, 17], fill=BRON[2])                  # cabeza
    d.rectangle([35, 4, 37, 17], fill=BRON[1])
    d.rectangle([27, 2, 37, 5], fill=BRON[1])                   # pelo
    d.point((29, 8), fill=BRON[0])
    d.point((34, 8), fill=BRON[0])
    d.rectangle([27, 11, 37, 15], fill=(220, 226, 228, 255))    # barbijo
    d.line([(27, 13), (37, 13)], fill=(170, 180, 186, 255))
    d.line([(26, 10), (27, 11)], fill=(220, 226, 228, 255))     # elásticos
    d.line([(38, 10), (37, 11)], fill=(220, 226, 228, 255))
    _outline(img)
    return img


def estatuas():
    for name, fn in (("estatua_columna", estatua_columna), ("estatua_busto", estatua_busto)):
        im = fn()
        im.save(f"{OUT}/{name}_izq.png")
        im.transpose(Image.FLIP_LEFT_RIGHT).save(f"{OUT}/{name}_der.png")


if __name__ == "__main__":
    valla()
    tablon()
    poste()
    obelisco()
    estatuas()
    print(f"valla, andamio_tablon, andamio_poste, obelisco_cerca, estatua_columna/busto_izq/der  ->  {OUT}/")
