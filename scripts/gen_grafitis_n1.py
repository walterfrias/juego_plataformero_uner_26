#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportAttributeAccessIssue=false
"""
gen_grafitis_n1.py  —  pintadas en el muro de la costanera del Nivel 1 (19/10,
pedido del usuario):
  grafiti_malvinas.png     al comienzo: "LAS MALVINAS SON ARGENTINAS"
  grafiti_universidad.png  antes de la meta: "#YO APOYO LA LEY DE
                           FINANCIAMIENTO UNIVERSITARIO"

Copia la letra de la bandera que mostraron los jugadores tras la semifinal con
Inglaterra (Mundial 2026; foto de referencia en lasmalvinassonargentinas.jpeg,
"fiel a la bandera, sin dibujos"): pincel grueso, letras altas y
angostas, trazo tembloroso; I con remates, S angulosa, G con ganchito. Cuatro
renglones: LAS / MALVINAS / SON (más chico) / ARGENTINAS (el más grande).

Pintada con látex blanco directo sobre el hormigón del muro (el usuario probó
primero letras negras sobre un parche a la cal y prefirió esto): bordes de
pincel seco semitransparentes y algunos chorreados.

Cómo se pinta: cada letra es un juego de trazos en una caja de 0..1. Se dibujan
a K veces el tamaño con un pincel grueso que tiembla y se reducen contando la
cobertura de cada pixel: lleno = blanco, a medias = semitransparente (pincel seco).

Uso:  python3 scripts/gen_grafitis_n1.py                         → game/assets/City/grafiti_*.png
      python3 scripts/gen_grafitis_n1.py --preview <nombre> <png>  (vista sobre el muro)
"""
from PIL import Image, ImageDraw
import random
import sys

OUT = "game/assets/City"
T = (0, 0, 0, 0)
K = 8                                   # sobremuestreo del pincel

# (pintura, donde el pincel cargó menos)
BLANCO = ((226, 228, 230), (196, 198, 202))       # látex blanco
ROJO_GULP = ((184, 82, 80), (160, 70, 68))        # el rojo de la tapa de Gulp!, menos saturado

ENSANCHE = 1.25                         # la caja de cada letra, más ancha que en la foto: a 10 px se cierran
# trazos por letra en una caja 0..1 (x a lo ancho, y hacia abajo). Ancho relativo al alto.
LETRAS = {
    "L": (0.50, [[(0.15, 0), (0.12, 1), (0.95, 0.97)]]),
    "A": (0.62, [[(0.0, 1), (0.48, 0), (1.0, 1)], [(0.22, 0.62), (0.80, 0.60)]]),
    "S": (0.55, [[(0.92, 0.10), (0.50, 0.0), (0.10, 0.12), (0.10, 0.40), (0.88, 0.58),
                  (0.92, 0.88), (0.48, 1.0), (0.05, 0.88)]]),
    "M": (0.75, [[(0.04, 1), (0.10, 0), (0.50, 0.62), (0.90, 0), (0.96, 1)]]),
    "V": (0.62, [[(0.0, 0), (0.50, 1), (1.0, 0)]]),
    "I": (0.42, [[(0.50, 0), (0.50, 1)], [(0.05, 0.02), (0.95, 0)], [(0.05, 1), (0.95, 0.98)]]),
    "N": (0.60, [[(0.08, 1), (0.10, 0), (0.90, 1), (0.92, 0)]]),
    "O": (0.55, [[(0.50, 0), (0.12, 0.18), (0.05, 0.55), (0.20, 0.92), (0.55, 1),
                  (0.90, 0.80), (0.95, 0.40), (0.80, 0.08), (0.45, 0)]]),
    "R": (0.58, [[(0.10, 1), (0.10, 0), (0.75, 0.04), (0.92, 0.24), (0.78, 0.46), (0.10, 0.50)],
                 [(0.42, 0.50), (0.98, 1)]]),
    "G": (0.60, [[(0.92, 0.12), (0.50, 0), (0.10, 0.22), (0.06, 0.70), (0.42, 1),
                  (0.88, 0.88), (0.92, 0.56), (0.55, 0.56)]]),
    "E": (0.52, [[(0.92, 0.02), (0.12, 0), (0.10, 1), (0.92, 0.98)], [(0.12, 0.50), (0.72, 0.48)]]),
    "T": (0.62, [[(0.0, 0.06), (1.0, 0)], [(0.50, 0.02), (0.48, 1)]]),
    "Y": (0.62, [[(0.0, 0), (0.50, 0.50)], [(1.0, 0), (0.50, 0.50), (0.48, 1)]]),
    "P": (0.55, [[(0.10, 1), (0.10, 0), (0.75, 0.04), (0.92, 0.25), (0.75, 0.48), (0.10, 0.52)]]),
    "F": (0.50, [[(0.92, 0.02), (0.12, 0), (0.10, 1)], [(0.12, 0.50), (0.72, 0.48)]]),
    "C": (0.55, [[(0.92, 0.12), (0.50, 0), (0.10, 0.22), (0.06, 0.72), (0.45, 1), (0.92, 0.88)]]),
    "U": (0.58, [[(0.10, 0), (0.08, 0.75), (0.40, 1), (0.80, 0.92), (0.90, 0)]]),
    "D": (0.58, [[(0.10, 1), (0.10, 0), (0.60, 0.05), (0.92, 0.40), (0.85, 0.80), (0.50, 1), (0.10, 1)]]),
    "#": (0.95, [[(0.34, 0.0), (0.24, 1.0)], [(0.80, 0.0), (0.70, 1.0)],
                 [(0.0, 0.30), (1.0, 0.28)], [(0.0, 0.72), (1.0, 0.70)]]),
    " ": (0.50, []),
    # minúsculas cursivas (tapa de Gulp!): misma caja, cuerpo de 0.45 a 1, astas desde 0
    "y": (0.55, [[(0.10, 0.45), (0.35, 0.80), (0.62, 0.45)], [(0.62, 0.45), (0.35, 1.05), (0.05, 1.10)]]),
    "s": (0.48, [[(0.85, 0.50), (0.45, 0.45), (0.15, 0.58), (0.50, 0.72), (0.85, 0.85), (0.50, 1.0), (0.10, 0.95)]]),
    "u": (0.55, [[(0.10, 0.45), (0.10, 0.90), (0.45, 1.0), (0.85, 0.85), (0.85, 0.45)], [(0.85, 0.45), (0.92, 1.0)]]),
    "e": (0.52, [[(0.15, 0.72), (0.85, 0.70), (0.75, 0.50), (0.45, 0.45), (0.12, 0.60), (0.15, 0.90),
                  (0.50, 1.0), (0.88, 0.92)]]),
    "d": (0.58, [[(0.85, 0.0), (0.85, 1.0)], [(0.85, 0.55), (0.45, 0.45), (0.12, 0.65), (0.15, 0.92),
                                               (0.50, 1.0), (0.85, 0.85)]]),
    "o": (0.52, [[(0.50, 0.45), (0.12, 0.58), (0.10, 0.85), (0.45, 1.0), (0.85, 0.90), (0.90, 0.60), (0.50, 0.45)]]),
    "n": (0.55, [[(0.10, 1.0), (0.10, 0.45)], [(0.10, 0.60), (0.45, 0.45), (0.85, 0.55), (0.88, 1.0)]]),
    "i": (0.30, [[(0.50, 0.50), (0.50, 1.0)], [(0.50, 0.18), (0.52, 0.22)]]),
    "t": (0.48, [[(0.45, 0.10), (0.45, 0.92), (0.80, 1.0)], [(0.05, 0.42), (0.90, 0.40)]]),
    "c": (0.50, [[(0.88, 0.52), (0.50, 0.45), (0.12, 0.62), (0.15, 0.92), (0.50, 1.0), (0.88, 0.90)]]),
    "a": (0.55, [[(0.85, 0.55), (0.50, 0.45), (0.12, 0.65), (0.18, 0.95), (0.50, 1.0), (0.85, 0.80)],
                 [(0.85, 0.45), (0.92, 1.0)]]),
}

# por pintada: renglones (texto, alto de letra en px, separación entre letras en px,
# sangría desde la izquierda), esquina sup. izq. en Level1, semilla, grosor del pincel
# en px finales, color y cuántos chorreados (el fibrón no chorrea). Muro a la vista:
# y 124..178 (entre el cordón y el río).
PINTADAS = {
    "grafiti_malvinas": dict(
        renglones=[("LAS", 8, 2, 26), ("MALVINAS", 10, 2, 5), ("SON", 8, 3, 26), ("ARGENTINAS", 11, 1, 0)],
        x=12, y=125, semilla=1982, trazo=2.1, color=BLANCO, chorreados=9),
    "grafiti_universidad": dict(           # tramo 1970..2600, entre el caño (2120) y la meta (2569)
        renglones=[("#YO APOYO LA LEY DE", 9, 2, 0), ("FINANCIAMIENTO", 11, 1, 8), ("UNIVERSITARIO", 11, 1, 13)],
        x=2370, y=128, semilla=2024, trazo=1.9, color=BLANCO, chorreados=9),
    "grafiti_patricio": dict(              # centro del nivel: tramo 1155..1334 (sin caño)
        renglones=[("PATRICIO", 10, 2, 0), ("REY", 10, 3, 22), ("y sus Redonditos", 9, 1, 14), ("de Ricota", 9, 1, 50)],
        x=1166, y=125, semilla=1985, trazo=1.6, color=ROJO_GULP, chorreados=0),
    # esténcil del esclavo que rompe las cadenas (tapa de Oktubre; esclavo.webp en la raíz),
    # pasando el agua desde la roja: tramo 1400..1503. imagen = (archivo, recorte, alto, umbral)
    "grafiti_esclavo": dict(
        imagen=("esclavo.webp", (0, 250, 953, 953), 52, 120),
        x=1404, y=125, semilla=1983, color=BLANCO, chorreados=4),
}
# x donde arranca cada TiledSprite del muro (para la vista previa)
TRAMOS = [-200, 397, 951, 1155, 1400, 1575, 1970]
INTERLINEA = 3
MARGEN = 3                              # aire alrededor del texto (chorreados)


def letra(d, ch, x0, y0, alto, pincel, rnd):
    """dibuja una letra a K veces su tamaño; devuelve su ancho en px finales."""
    rel, trazos = LETRAS[ch]
    ancho = rel * alto * ENSANCHE
    inclina = rnd.uniform(-0.06, 0.06)              # cada letra un poco torcida
    for trazo in trazos:
        pts = []
        for x, y in trazo:
            jx, jy = rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03)
            px = x0 + (x + jx + inclina * (0.5 - y)) * ancho
            py = y0 + (y + jy) * alto
            pts.append((px * K, py * K))
        grosor = pincel * K * rnd.uniform(0.85, 1.15)
        d.line(pts, fill=255, width=int(grosor), joint="curve")
        for p in (pts[0], pts[-1]):                 # puntas redondeadas del pincel
            r = grosor / 2
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)
    return ancho


def texto(W, H, renglones, trazo, rnd):
    """máscara de cobertura (0..255) del texto a tamaño final."""
    big = Image.new("L", (W * K, H * K), 0)
    d = ImageDraw.Draw(big)
    y = MARGEN
    for s, alto, sep, sangria in renglones:
        x = MARGEN + sangria
        for ch in s:
            dy = rnd.uniform(-0.6, 0.6)
            x += letra(d, ch, x, y + dy, alto, trazo, rnd) + sep
        y += alto + INTERLINEA
    return big.resize((W, H), Image.BOX)


def medidas(renglones):
    ancho = max(MARGEN + sangria + sum(LETRAS[c][0] * alto * ENSANCHE + sep for c in s)
                for s, alto, sep, sangria in renglones)
    alto = sum(r[1] for r in renglones) + INTERLINEA * (len(renglones) - 1)
    return int(ancho) + MARGEN + 1, alto + 2 * MARGEN


def estencil(imagen):
    """máscara de cobertura (0..255) de un dibujo blanco sobre negro, reducido al alto del muro."""
    archivo, recorte, alto, umbral = imagen
    im = Image.open(archivo).convert("L").crop(recorte)
    im = im.resize((round(im.width * alto / im.height), alto), Image.LANCZOS)
    # sube el contraste alrededor del umbral: lo que pasa holgado queda lleno, lo de cerca, pincel seco
    return im.point(lambda v: 255 if v > umbral + 25 else 100 if v > umbral else 0)


def grafiti(nombre):
    p = PINTADAS[nombre]
    rnd = random.Random(p["semilla"])
    if "imagen" in p:
        m = estencil(p["imagen"])
        W, H = m.size
        m = m.load()
    else:
        W, H = medidas(p["renglones"])
        m = texto(W, H, p["renglones"], p["trazo"], rnd).load()
    img = Image.new("RGBA", (W, H), T)
    px = img.load()
    pintura, cargo_menos = (c + (255,) for c in p["color"])
    seca = p["color"][0] + (130,)                                    # pincel seco: deja ver el hormigón
    for y in range(H):
        for x in range(W):
            c = m[x, y]
            if c > 120:
                px[x, y] = pintura if rnd.random() > 0.12 else cargo_menos
            elif c > 95:
                px[x, y] = seca
    # chorreados: la pintura corre hacia abajo desde la base de algunos trazos
    bases = [(x, y) for y in range(H - 1) for x in range(W)
             if px[x, y][3] == 255 and px[x, y + 1][3] == 0]
    for x, y in rnd.sample(bases, min(p["chorreados"], len(bases))):
        largo = rnd.choice((1, 2, 2, 3, 4))
        for k in range(1, largo + 1):
            if y + k < H:
                px[x, y + k] = pintura if k < largo else seca
    return img


def preview(nombre, path):
    """la pintada sobre su tramo de muro, con la sombra de la noche, x4 y a escala de juego."""
    from PIL import ImageEnhance
    p = PINTADAS[nombre]
    g = grafiti(nombre)
    x0, x1, y0, y1 = p["x"] - 60, p["x"] + g.width + 60, 60, 200
    tramo = max(t for t in TRAMOS if t <= p["x"])
    c = Image.new("RGBA", (x1 - x0, y1 - y0), (16, 20, 40, 255))

    def tira(archivo, y, brillo=None):
        im = Image.open(f"{OUT}/{archivo}")
        if brillo:
            im = ImageEnhance.Brightness(im).enhance(brillo)
        for x in range(tramo, x1, im.width):
            if x + im.width > x0:
                c.alpha_composite(im, (x - x0, y - y0))
    tira("embankment.png", 120, 0.62)
    c.alpha_composite(ImageEnhance.Brightness(g).enhance(0.62), (p["x"] - x0, p["y"] - y0))
    tira("river.png", 178, 0.62)
    tira("sidewalk_luna.png", 110)
    for xc in (150, 2120):                           # caños de desagüe
        if x0 - 50 < xc < x1:
            c.alpha_composite(Image.open(f"{OUT}/drain_pipe_luna.png"), (xc - x0, 122 - y0))
    c.alpha_composite(Image.open("game/assets/Player/Player_Idle_1.png"), (p["x"] - 30 - x0, 84 - y0))
    big = c.resize((c.width * 4, c.height * 4), Image.NEAREST)
    out = Image.new("RGBA", (big.width, big.height + c.height + 8), (16, 20, 40, 255))
    out.alpha_composite(big, (0, 0))
    out.alpha_composite(c, (0, big.height + 8))
    out.save(path)


def main():
    if len(sys.argv) > 3 and sys.argv[1] == "--preview":
        preview(sys.argv[2], sys.argv[3])
        return
    for nombre in PINTADAS:
        img = grafiti(nombre)
        img.save(f"{OUT}/{nombre}.png")
        print(f"{OUT}/{nombre}.png", img.size)


if __name__ == "__main__":
    main()
