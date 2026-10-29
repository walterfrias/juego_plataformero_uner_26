#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_l3_escombros.py  —  escombros y basura en la calle del Nivel 3 (28/10). Pedido
del usuario: "agrega algunos escombros, quizás tachos de basura rotos en la calle,
que se vea algo de caos". DECORADO, sin colisión: lo cablea wire_l3_escombros.py.

Mismo estilo que los props de la calle (gen_l3_caos.py: cono, neumático, escombro):
formas simples, sin contorno, colores apagados para la noche. Los tachos con la
paleta del tacho de L1 (gen_street_props.py), para que se lean como el mismo modelo.

Crea (game/assets/City/):
  tacho_volcado.png   22x10   tacho tirado, abollado, la tapa al lado y la basura
                              desparramada por la boca
  tacho_roto.png      16x18   tacho parado pero hundido y rajado, la basura rebalsa
                              y una bolsa apoyada
  bolsas_basura.png   24x12   tres bolsas negras, una rota con basura afuera
  escombros_pila.png  28x12   ladrillos, cascotes de hormigón y un hierro que asoma
  basura_suelta.png   20x4    papeles, latas y una botella rota
Uso:  python3 scripts/gen_l3_escombros.py
"""
import os

from PIL import Image, ImageDraw

OUT = "game/assets/City"
T = (0, 0, 0, 0)
# tacho (los de tacho.png)
CAN_BODY, CAN_RIDGE = (54, 62, 58, 255), (78, 88, 82, 255)
CAN_LID, CAN_DARK = (70, 80, 76, 255), (30, 36, 34, 255)
HUECO = (16, 18, 20, 255)
# basura
PAPEL, PAPEL_S = (150, 146, 128, 255), (112, 108, 96, 255)
CARTON = (110, 88, 62, 255)
LATA = (128, 60, 56, 255)
VIDRIO = (96, 132, 110, 255)
VIDRIO_H = (170, 200, 180, 255)
BOLSA, BOLSA_H, BOLSA_S = (34, 34, 40, 255), (66, 66, 76, 255), (22, 22, 26, 255)
ATADO = (90, 84, 70, 255)
# escombros (los de escombro.png) y ladrillo apagado
HORM, HORM_H, HORM_S = (84, 80, 82, 255), (110, 104, 100, 255), (56, 52, 54, 255)
LADR, LADR_S = (118, 70, 56, 255), (86, 52, 44, 255)
HIERRO = (70, 58, 50, 255)


def basura(d, pts):
    """puntitos de basura: (x, y, color)."""
    for x, y, c in pts:
        d.point([(x, y)], fill=c)


def tacho_volcado():
    img = Image.new("RGBA", (22, 10), T)
    d = ImageDraw.Draw(img)
    # cuerpo acostado (la base a la izquierda, la boca a la derecha), apenas cónico
    for x in range(1, 15):
        t = (x - 1) / 14
        hw = 3 + round(t)
        d.line([(x, 6 - hw), (x, 6 + hw - 1)], fill=CAN_BODY)
    for y in (3, 6, 9):                                            # nervaduras, ahora horizontales
        d.line([(2, min(y, 9) - (1 if y == 9 else 0)), (13, min(y, 9) - (1 if y == 9 else 0))], fill=CAN_RIDGE)
    d.line([(2, 9), (14, 9)], fill=CAN_DARK)                       # sombra de abajo
    d.polygon([(6, 2), (9, 4), (12, 2)], fill=CAN_DARK)            # abolladura
    d.line([(15, 1), (15, 9)], fill=CAN_RIDGE)                     # aro de la boca
    d.line([(14, 3), (14, 8)], fill=HUECO)                         # adentro, oscuro
    basura(d, [(16, 8, PAPEL), (17, 9, PAPEL_S), (18, 8, CARTON), (17, 7, LATA),
               (19, 9, PAPEL), (16, 9, CARTON)])
    d.line([(18, 9), (21, 9)], fill=CAN_LID)                       # la tapa tirada
    d.point([(20, 8)], fill=CAN_RIDGE)
    return img


def tacho_roto():
    W, H = 16, 18
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    cx, top, bot = 8, 6, H - 1
    for y in range(top, bot):
        t = (y - top) / (bot - top)
        hw = 4 + t
        hund = 1 if 9 <= y <= 12 else 0                            # hundido en el medio
        d.line([(cx - hw + hund, y), (cx + hw, y)], fill=CAN_BODY)
    for dx in (-3, 0, 3):
        d.line([(cx + dx, top + 1), (cx + dx, bot - 1)], fill=CAN_RIDGE)
    d.line([(cx + 4, top + 1), (cx + 5, bot - 1)], fill=CAN_DARK)
    d.line([(cx - 2, 10), (cx, 13)], fill=HUECO)                   # rajadura
    d.line([(cx - 1, 10), (cx + 1, 12)], fill=HUECO)
    d.line([(cx - 5, top), (cx + 5, top)], fill=CAN_RIDGE)         # aro, torcido
    d.point([(cx + 5, top - 1)], fill=CAN_RIDGE)
    # la basura rebalsa (sin tapa)
    d.polygon([(cx - 4, top), (cx - 2, top - 3), (cx + 1, top - 2), (cx + 3, top - 4), (cx + 4, top)],
              fill=CARTON)
    basura(d, [(cx - 2, top - 2, PAPEL), (cx + 2, top - 3, PAPEL), (cx, top - 1, LATA),
               (cx + 3, top - 1, PAPEL_S), (cx - 3, top - 1, PAPEL_S)])
    # una bolsa apoyada abajo a la izquierda
    d.ellipse([0, H - 6, 6, H - 1], fill=BOLSA)
    d.point([(2, H - 5), (1, H - 4)], fill=BOLSA_H)
    d.point([(3, H - 7)], fill=ATADO)
    return img


def bolsas_basura():
    img = Image.new("RGBA", (24, 12), T)
    d = ImageDraw.Draw(img)
    for x0, y0, w, h in ((0, 3, 10, 9), (12, 4, 9, 8), (6, 0, 9, 9)):   # la de arriba, última
        d.ellipse([x0, y0, x0 + w, y0 + h], fill=BOLSA, outline=BOLSA_S)   # el borde las separa
        d.arc([x0 + 1, y0 + 1, x0 + w - 1, y0 + h - 1], 190, 270, fill=BOLSA_H)
        d.point([(x0 + w // 2, y0 - 1)], fill=ATADO)               # el nudo
    d.line([(19, 6), (20, 9)], fill=HUECO)                         # la rota, con basura afuera
    basura(d, [(21, 10, PAPEL), (22, 11, CARTON), (20, 11, LATA), (23, 10, PAPEL_S)])
    return img


def escombros_pila():
    img = Image.new("RGBA", (28, 12), T)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 11), (5, 5), (10, 3), (15, 1), (20, 4), (24, 7), (27, 11)], fill=HORM)
    d.polygon([(10, 3), (15, 1), (17, 5), (12, 7)], fill=HORM_H)
    d.polygon([(19, 6), (24, 7), (25, 10), (20, 10)], fill=HORM_S)
    for x0, y0 in ((3, 8), (7, 6), (16, 7), (21, 9)):              # ladrillos sueltos
        d.rectangle([x0, y0, x0 + 3, y0 + 1], fill=LADR)
        d.line([(x0, y0 + 1), (x0 + 3, y0 + 1)], fill=LADR_S)
    d.line([(13, 2), (11, -1)], fill=HIERRO)                       # hierro que asoma
    d.line([(14, 2), (17, 0)], fill=HIERRO)
    d.point([(6, 10), (13, 9), (24, 11)], fill=HORM_S)
    return img


def basura_suelta():
    img = Image.new("RGBA", (20, 4), T)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 2, 2, 3], fill=PAPEL)                          # papeles
    d.point([(1, 2)], fill=PAPEL_S)
    d.rectangle([6, 3, 8, 3], fill=PAPEL_S)
    d.rectangle([4, 2, 5, 3], fill=LATA)                           # lata aplastada
    d.line([(11, 3), (14, 2)], fill=VIDRIO)                        # botella rota
    d.point([(12, 2)], fill=VIDRIO_H)
    d.point([(15, 3), (16, 3)], fill=VIDRIO)
    d.rectangle([17, 2, 19, 3], fill=CARTON)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    for nombre, fn in (("tacho_volcado", tacho_volcado), ("tacho_roto", tacho_roto),
                       ("bolsas_basura", bolsas_basura), ("escombros_pila", escombros_pila),
                       ("basura_suelta", basura_suelta)):
        im = fn()
        im.save(f"{OUT}/{nombre}.png")
        print(f"{nombre}.png", im.size)


if __name__ == "__main__":
    main()
