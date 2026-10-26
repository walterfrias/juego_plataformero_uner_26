#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportAttributeAccessIssue=false
"""
gen_l3_pilas.py — las pirámides de la arena pasan a ser PILAS DE PATRULLEROS
(25/10, pedido del usuario: "las plataformas negras de los costados no se ven
bien; que sean patrulleros apilados emanando humo", y después "que se vean más
rotos y caóticos, están muy prolijos, una sensación más dramática"): una
barricada policial que se vino abajo en la 9 de Julio.

Mismas superficies que la pirámide (gen_l3_calle.estatua_columna, 102x130 con
faldones de PIR_PAD = 14): la pelea no cambia.
  - cima  = fila 50, x 14..78   (mundo y 70): el chasis del patrullero de arriba,
            dado vuelta (las ruedas al cielo; le falta una)
  - losa  = fila 102, x 24..88  (mundo y 122): el chasis del de abajo, dado vuelta
            y aplastado sobre escombros
  - en el medio, uno derecho pero INCLINADO (se deslizó), con brasas en la
    ventanilla rota (de ahí sale el humo) y la sirena que todavía titila, con una
    luz rota (2 cuadros)
Cada auto se dibuja derecho en su propia imagen (carrocería abollada, vidrios
rotos, hollín, óxido, puerta arrancada, paragolpes colgando) y después se da
vuelta o se inclina. Alrededor: valla policial doblada, conos, cubiertas, la
puerta arrancada apoyada, cinta de peligro cortada. Estilo del patrullero de la
calle (gen_l3_caos.patrullero): blanco y azul apagados, contorno de 1 px.

Crea (game/assets/City/): pila_patrulleros_izq_1..2.png y _der_1..2.png
(102x130; la derecha es la izquierda espejada, como las estatuas).
Uso:  python3 scripts/gen_l3_pilas.py [--preview DIR]
"""
import os
import random
import sys

from PIL import Image, ImageDraw

OUT = "game/assets/City"
W, H = 102, 130
CIMA, LOSA = 50, 102              # filas de las superficies (no mover: son las de la pelea)
CW, CH = 68, 30                   # lienzo de un auto (derecho): ruedas abajo, chasis en CHASIS_Y
CHASIS_Y = 23

T = (0, 0, 0, 0)
OUTL = (24, 24, 34, 255)
BLANCO, BLANCO_S, BLANCO_L = (170, 176, 186, 255), (120, 126, 138, 255), (196, 202, 210, 255)
AZUL, AZUL_S = (46, 72, 130, 255), (32, 50, 96, 255)
CHASIS, CHASIS_L = (42, 42, 50, 255), (70, 70, 82, 255)
OXIDO, OXIDO_L = (104, 66, 46, 255), (140, 90, 58, 255)
HOLLIN = [(30, 28, 32, 255), (50, 46, 50, 255)]
VIDRIO, VIDRIO_L = (40, 48, 64, 255), (120, 134, 156, 255)
INTERIOR = (20, 18, 24, 255)
GOMA, LLANTA = (30, 30, 34, 255), (90, 92, 100, 255)
ESCOMBRO = [(52, 54, 64, 255), (74, 76, 88, 255), (96, 98, 110, 255)]
CONO, CONO_B = (200, 96, 40, 255), (210, 210, 200, 255)
CINTA_Y, CINTA_K = (222, 190, 60, 255), (24, 24, 30, 255)
BRASA = [(255, 210, 110, 255), (240, 130, 50, 255), (170, 60, 30, 255)]
# sirena: (rojo, azul) por cuadro; la derecha está rota (se apaga y prende distinto)
SIRENA = [((230, 54, 54, 255), (40, 52, 80, 255)), ((110, 40, 40, 255), (80, 130, 240, 255))]
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def rueda(d, cx, cy):
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=GOMA)
    d.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=LLANTA)


def mancha(img, cx, cy, r, colores, rnd, densidad=0.8):
    """mancha irregular tramada (hollín, óxido) dentro de lo ya pintado."""
    px = img.load()
    for y in range(max(0, cy - r), min(img.size[1], cy + r + 1)):
        for x in range(max(0, cx - r), min(img.size[0], cx + r + 1)):
            q = 1 - ((x - cx) ** 2 + (y - cy) ** 2) / (r * r + 0.01) + rnd.uniform(-0.3, 0.3)
            if q > 0 and px[x, y][3] and q * densidad * 16 > BAYER[y % 4][x % 4]:
                px[x, y] = colores[0] if q > 0.5 else colores[-1]


def auto(seed, k=0, brasas=False, falta_rueda=None, puerta=True, sirena=False):
    """patrullero derecho y destruido en un lienzo de CWxCH (chasis en CHASIS_Y)."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (CW, CH), T)
    d = ImageDraw.Draw(img)
    b = CHASIS_Y
    abolla = rnd.randint(2, 4)                                      # techo hundido
    capot = rnd.randint(1, 3)                                       # capot levantado
    d.polygon([(2, b - 6), (10, b - 7 - capot), (17, b - 14 + 1), (26, b - 14 + abolla),
               (34, b - 15), (42, b - 14), (50, b - 7), (CW - 4, b - 6 + 1), (CW - 3, b), (1, b)],
              fill=BLANCO)
    d.line([(17, b - 13), (26, b - 14 + abolla), (34, b - 15), (42, b - 14)], fill=BLANCO_L)
    d.rectangle([1, b - 5, CW - 4, b - 3], fill=AZUL)
    d.rectangle([1, b - 2, CW - 4, b], fill=BLANCO_S)
    d.line([(1, b), (CW - 4, b)], fill=CHASIS)
    # ventanillas: una rota del todo (se ve el interior), la otra con astillas
    d.polygon([(18, b - 12), (28, b - 12 + abolla // 2), (28, b - 7), (14, b - 7)], fill=INTERIOR)
    d.polygon([(31, b - 13), (41, b - 13), (47, b - 7), (31, b - 7)], fill=VIDRIO)
    for _ in range(4):
        x, y = rnd.randint(32, 44), rnd.randint(b - 12, b - 8)
        d.line([(x, y), (x + rnd.choice((-2, 2)), y + 2)], fill=VIDRIO_L)
    if brasas:                                                      # brasas en la ventanilla rota
        for _ in range(9):
            x, y = rnd.randint(17, 27), rnd.randint(b - 10, b - 7)
            d.point((x, y), fill=BRASA[(rnd.randint(0, 2) + k) % 3])
        d.line([(16, b - 7), (27, b - 7)], fill=BRASA[1 + k % 2])
    if puerta:                                                      # puerta arrancada: el hueco
        d.rectangle([30, b - 6, 36, b - 1], fill=INTERIOR)
    else:
        d.polygon([(30, b - 9), (36, b - 13), (37, b - 2), (31, b)], fill=BLANCO_S)
    # barra de luces: la izquierda prende, la derecha está rota y colgando
    rojo, azul = SIRENA[k] if sirena else (CHASIS, CHASIS_L)     # solo titila la del auto del medio
    d.rectangle([23, b - 18 + abolla // 2, 27, b - 15 + abolla // 2], fill=rojo)
    d.polygon([(28, b - 16), (32, b - 18), (33, b - 15), (29, b - 14)], fill=azul)
    # paragolpes de atrás colgando
    d.line([(CW - 4, b - 1), (CW - 1, b + 3)], fill=BLANCO_S)
    d.line([(CW - 3, b - 1), (CW - 1, b + 2)], fill=CHASIS_L)
    # hollín y óxido (incendio y abandono)
    for _ in range(2):                                              # poco: el blanco y azul es lo que se lee
        mancha(img, rnd.randint(6, CW - 8), rnd.randint(b - 12, b - 1), rnd.randint(2, 4), HOLLIN, rnd, 0.6)
    mancha(img, rnd.randint(8, CW - 10), b - 2, 3, [OXIDO, OXIDO_L], rnd, 0.6)
    # bordes abollados: se comen algunos píxeles del contorno
    px = img.load()
    for x in range(CW):
        for y in range(CH):
            if px[x, y][3] and rnd.random() < 0.05 and (y < b - 10 or x < 3 or x > CW - 6):
                px[x, y] = T
    for i, cx in enumerate((14, CW - 16)):
        if i != falta_rueda:
            rueda(d, cx, b + 2)
        else:
            d.line([(cx - 3, b + 1), (cx + 3, b + 1)], fill=CHASIS_L)            # el eje sin rueda
    return img


def dado_vuelta(img):
    """el auto panza arriba: el chasis (fila CHASIS_Y) queda en la fila CH-1-CHASIS_Y."""
    return img.transpose(Image.FLIP_TOP_BOTTOM)


def pegar(pila, pieza, x, y_chasis_pila, y_chasis_pieza):
    pila.alpha_composite(pieza, (x, y_chasis_pila - y_chasis_pieza))


def escombros(d, x0, x1, y0, y1, rnd):
    for _ in range((x1 - x0) * (y1 - y0) // 5):
        x, y = rnd.randint(x0, x1), rnd.randint(y0, y1)
        r = rnd.randint(1, 4)
        d.rectangle([x, y, x + r, y + r - 1], fill=rnd.choice(ESCOMBRO))


def cubiertas(d, x0, y_piso, n, rnd):
    for i in range(n):
        y = y_piso - 5 - i * 5
        dx = rnd.randint(-2, 2)
        d.ellipse([x0 + dx, y, x0 + 13 + dx, y + 5], fill=GOMA)
        d.line([(x0 + 3 + dx, y + 2), (x0 + 10 + dx, y + 2)], fill=LLANTA)


def valla(img, x, y, ang):
    """valla policial (franjas blancas y azules) doblada, apoyada en diagonal."""
    v = Image.new("RGBA", (30, 8), T)
    dv = ImageDraw.Draw(v)
    dv.rectangle([0, 1, 29, 5], fill=BLANCO_S)
    for xx in range(0, 30, 6):
        dv.rectangle([xx, 1, xx + 2, 5], fill=AZUL)
    dv.line([(2, 6), (2, 7)], fill=CHASIS)
    dv.line([(26, 6), (26, 7)], fill=CHASIS)
    dv.line([(14, 0), (16, 6)], fill=CHASIS)                         # el doblez
    v = v.rotate(ang, expand=True, resample=Image.NEAREST)
    img.alpha_composite(v, (x, y))


def puerta_suelta(img, x, y, ang):
    p = Image.new("RGBA", (9, 13), T)
    dp = ImageDraw.Draw(p)
    dp.rectangle([0, 0, 8, 12], fill=BLANCO)
    dp.rectangle([0, 7, 8, 9], fill=AZUL)
    dp.rectangle([1, 1, 7, 5], fill=VIDRIO)
    dp.line([(2, 2), (5, 4)], fill=VIDRIO_L)
    p = p.rotate(ang, expand=True, resample=Image.NEAREST)
    img.alpha_composite(p, (x, y))


def contorno(img):
    src = img.copy().load()
    px = img.load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3] == 0 and any(0 <= x + a < W and 0 <= y + b < H and src[x + a, y + b][3]
                                         for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = OUTL


def pila(k):
    rnd = random.Random(1945)
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    vuelta = CH - 1 - CHASIS_Y                                      # fila del chasis en un auto dado vuelta

    escombros(d, 16, 96, LOSA + 16, H - 1, rnd)                     # lo que sostiene al de abajo
    cubiertas(d, 1, H, 4, rnd)                                      # faldón de afuera
    valla(img, 74, LOSA + 10, -18)                                  # valla doblada contra la pila
    # abajo: dado vuelta y aplastado, chasis = losa (x 24..88)
    pegar(img, dado_vuelta(auto(11, k, falta_rueda=0)), 21, LOSA, vuelta)
    # en el medio: derecho pero inclinado, apoyado en las ruedas del de abajo
    medio = auto(27, k, brasas=True, puerta=False, sirena=True).rotate(9, expand=True, resample=Image.NEAREST)
    img.alpha_composite(medio, (5, LOSA - 6 - medio.size[1] + 5))
    # arriba: dado vuelta, chasis = cima (x 14..78); le falta una rueda
    pegar(img, dado_vuelta(auto(53, k, falta_rueda=1)), 12, CIMA, vuelta)
    puerta_suelta(img, 2, CIMA + 6, -24)                            # puerta que cuelga hacia el vacío
    puerta_suelta(img, 88, LOSA + 4, 14)                            # la arrancada, apoyada abajo
    # conos tirados y la cinta de peligro cortada
    for cx, cy in ((18, H - 9), (94, H - 7)):
        d.polygon([(cx, cy), (cx + 6, cy + 2), (cx + 1, cy + 5)], fill=CONO)
        d.line([(cx + 2, cy + 2), (cx + 4, cy + 3)], fill=CONO_B)
    for i, x in enumerate(range(24, 52)):                           # cinta caída, cortada al medio
        if 36 <= x <= 39:
            continue
        y = LOSA + 13 + (x - 24) // 7
        img.putpixel((x, y), CINTA_Y if (i // 3) % 2 == 0 else CINTA_K)
    # astillas de vidrio en el piso que brillan
    for _ in range(7):
        img.putpixel((rnd.randint(20, 92), rnd.randint(H - 6, H - 2)), VIDRIO_L)

    # las superficies, intactas: el chasis plano donde se para Lio
    d.line([(14, CIMA), (78, CIMA)], fill=CHASIS_L)
    d.line([(24, LOSA), (88, LOSA)], fill=CHASIS_L)
    contorno(img)
    return img


def main():
    out = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else OUT
    os.makedirs(out, exist_ok=True)
    for k in (0, 1):
        im = pila(k)
        im.save(f"{out}/pila_patrulleros_izq_{k + 1}.png")
        im.transpose(Image.FLIP_LEFT_RIGHT).save(f"{out}/pila_patrulleros_der_{k + 1}.png")
    if "--preview" in sys.argv:
        a = Image.open(f"{out}/pila_patrulleros_izq_1.png")
        b = Image.open(f"{out}/pila_patrulleros_izq_2.png")
        c = Image.new("RGBA", (W * 2 + 8, H), (28, 26, 40, 255))
        c.alpha_composite(a, (0, 0))
        c.alpha_composite(b, (W + 8, 0))
        c.resize((c.size[0] * 3, H * 3), Image.NEAREST).save(f"{out}/pila_x3.png")
    print(f"pila_patrulleros_izq/der_1..2.png ({W}x{H}) -> {out}/")


if __name__ == "__main__":
    main()
