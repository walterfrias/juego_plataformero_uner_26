#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_jefe.py  —  Paciente Zero: EL CIENTÍFICO que empezó todo (18/10). Es el que
trabajaba en el laboratorio de L2 y escribió el diario; al final está al pie del
Obelisco, con la camiseta de Argentina como Lio, del otro lado.

Es UN ZOMBIE MÁS, en el mismo estilo que los otros, solo que más grande: se dibuja
a 32x34 con las mismas piezas que el médico y el investigador
(gen_zombies_lab.py / gen_zombies_wave2.py: _legs, _outline, la paleta) y se
agranda x1.5 píxel a píxel (hasta el 18/10 era x2: "que sea más chico";
wire_jefe.py ajusta máscaras, tamaño y lógica a la imagen). La versión anterior se
dibujó directo a 64x68 con mucho más detalle que el resto y "tendría que ser uno
idéntico a los otros pero escalado" (usuario 18/10).

  - mata de pelo NEGRO revuelto ("más pelo, de color negro"), anteojos, ojos rojos
  - guardapolvo abierto con la camiseta de Argentina (bastones celestes y blancos)
  - una motosierra (25/10; antes, una jeringa con el líquido verde del lab). El
    28/10, "que sea más grande": espada de 12 px con la cadena arriba y abajo
    (antes 6), motor con manija. No entraba en 32 px de ancho: el lienzo tiene
    PAD px vacíos de cada lado (simétrico, así el cuerpo no salta al espejarse)
    → 48x34, x1.5 = 72x51. Las máscaras de wire_jefe.py y los topes de
    wire_jefe_jeringa.py se corren con PAD.
Mira a la DERECHA (los eventos lo espejan con FlipX); los pies en la última fila.

Animaciones (28/10: más cuadros, como los zombies, que tienen 8):
  jefe_walk_1..8      camina con la motosierra al frente (la cadena gira)
  jefe_carga_1..6     se agacha, levanta la motosierra y la acelera (humo)
  jefe_embiste_1..4   corre inclinado con la motosierra al frente, chispas
  jefe_expuesto_1..8  de rodillas con la motosierra trabada, estrellitas (= pisalo)
  jefe_<anim>_sheet   las tiras de referencia (todos los cuadros en fila; las usa el GDD)
Uso:  python3 scripts/gen_jefe.py [--preview DIR]   (crea game/assets/Jefe/)
"""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from gen_zombies_lab import COAT, COAT_H, COAT_S, SHOE, _legs   # noqa: E402
from gen_zombies_wave2 import EYE, H, MOUTH, SKIN, SKIN_S, TAU, W, _outline  # noqa: E402

OUT = "game/assets/Jefe"
ESCALA = 1.5                                    # 48x34 → 72x51 (antes x2; "más chico", usuario 18/10)
PAD = 8                                         # px vacíos de cada lado para la motosierra (28/10)
CX = 14 + PAD                                   # el centro del cuerpo, como antes en 32 px
HAIR = (34, 32, 40, 255)                        # pelo negro, mucho (antes blanco y corto)
HAIR_H = (66, 64, 78, 255)                      # brillo: si no, el negro se pierde en la noche
GLASS = (60, 70, 80, 255)
CELESTE, BLANCO = (116, 172, 223, 255), (232, 236, 240, 255)
PANTS = (52, 56, 70, 255)
# motosierra (25/10, pedido del usuario: reemplaza a la jeringa)
MOTOR, MOTOR_S, MANGO = (230, 124, 40, 255), (164, 80, 28, 255), (40, 40, 46, 255)
ESPADA, ESPADA_H, CADENA = (176, 182, 192, 255), (214, 220, 228, 255), (70, 70, 78, 255)
HUMO = (120, 120, 128, 200)
CHISPA = (255, 214, 90, 255)
STAR = (255, 230, 120, 255)


def _new():
    img = Image.new("RGBA", (W + 2 * PAD, H), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def camiseta(d, x0, x1, y0, y1, lean=0):
    """bastones celestes y blancos de 1 px en la abertura del guardapolvo."""
    for x in range(x0, x1 + 1):
        d.line([(x + lean, y0), (x, y1)], fill=CELESTE if (x - x0) % 2 == 0 else BLANCO)


def cuerpo(d, cx, sh_y, hip_y, largo=4, lean=0, vuelo=0):
    """guardapolvo abierto (como el del médico) con la camiseta de Argentina.
    lean: hombros corridos hacia adelante; vuelo: el faldón flamea hacia atrás."""
    b = hip_y + largo
    d.polygon([(cx - 5 + lean, sh_y), (cx + 5 + lean, sh_y), (cx + 6, b), (cx - 6 - vuelo, b - vuelo // 2)],
              fill=COAT)
    d.polygon([(cx + 2 + lean, sh_y), (cx + 5 + lean, sh_y), (cx + 6, b), (cx + 3, b)], fill=COAT_S)
    camiseta(d, cx - 1, cx + 2, sh_y + 1, b - 1, lean)
    d.line([(cx - 5 + lean, sh_y + 1), (cx - 5 - vuelo, b - 1 - vuelo // 2)], fill=COAT_H)


def cabeza(d, hx, hy, ojos="rojo"):
    """mata de pelo negro revuelto (cae por los costados), anteojos, ojos rojos."""
    d.ellipse([hx - 3, hy, hx + 4, hy + 7], fill=SKIN)
    d.polygon([(hx - 5, hy + 5), (hx - 6, hy + 1), (hx - 4, hy - 3), (hx - 1, hy - 4), (hx + 1, hy - 3),
               (hx + 3, hy - 4), (hx + 6, hy - 2), (hx + 6, hy + 2), (hx + 4, hy + 1), (hx + 1, hy + 2),
               (hx - 2, hy + 1), (hx - 3, hy + 6)], fill=HAIR)                 # mata revuelta
    d.line([(hx - 3, hy - 2), (hx + 1, hy - 2)], fill=HAIR_H)                 # brillo arriba
    d.point([(hx + 4, hy - 1), (hx - 5, hy + 2)], fill=HAIR_H)
    d.rectangle([hx - 1, hy + 3, hx + 1, hy + 4], outline=GLASS)               # anteojos
    d.rectangle([hx + 2, hy + 3, hx + 4, hy + 4], outline=GLASS)
    if ojos == "cruz":
        d.point([(hx, hy + 3), (hx + 3, hy + 4)], fill=MOUTH)
    else:
        d.point([(hx, hy + 4), (hx + 3, hy + 4)], fill=EYE)
    d.line([(hx, hy + 6), (hx + 3, hy + 6)], fill=MOUTH)


def motosierra(d, x, y, ang=0.0, i=0, largo=12):
    """motor naranja con manija en la mano (x, y) y la espada de `largo` px hacia
    adelante, girada `ang` rad (negativo = hacia arriba). Los dientes de la cadena,
    arriba y abajo de la espada, se corren con el cuadro i (está prendida).
    Devuelve la punta, para las chispas."""
    c, s = math.cos(ang), math.sin(ang)
    sx, sy = x + 3 * c, y + 3 * s
    ex, ey = sx + largo * c, sy + largo * s
    d.line([(round(sx), round(sy)), (round(ex), round(ey))], fill=ESPADA, width=3)
    d.line([(round(sx), round(sy)), (round(ex - c), round(ey - s))], fill=ESPADA_H)
    for k in range(largo + 1):                                         # cadena arriba y abajo
        if (k + i) % 2 == 0:
            px_, py_ = sx + k * c, sy + k * s
            d.point([(round(px_ + 2 * s), round(py_ - 2 * c)), (round(px_ - 2 * s), round(py_ + 2 * c))],
                    fill=CADENA)
    d.point([(round(ex + c), round(ey + s))], fill=CADENA if i % 2 else ESPADA)   # punta redondeada
    d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=MOTOR)              # motor
    d.line([(x - 2, y + 2), (x + 2, y + 2)], fill=MOTOR_S)
    d.line([(x - 2, y - 4), (x + 1, y - 4)], fill=MANGO)               # manija de arriba
    d.point([(x - 2, y - 3), (x + 1, y - 3)], fill=MANGO)
    d.point([(x - 3, y), (x - 3, y + 1)], fill=MANGO)                  # empuñadura de atrás
    return ex, ey


def humo(d, x, y, n):
    """bocanadas del escape que suben y se corren hacia atrás."""
    for k in range(n):
        d.point([(x - 3 - k, y - 4 - 2 * k), (x - 2 - k, y - 5 - 2 * k)], fill=HUMO)


def chispas(d, x, y, i):
    for k in range(3):
        a = 2.4 + k * 0.7 + (i % 2) * 0.35
        r = 2 + (i + k) % 3
        d.point([(round(x + math.cos(a) * r), round(y + math.sin(a) * r))], fill=CHISPA)


def walk(i):
    ph = i / 8 * TAU
    img, d = _new()
    cx = CX
    bob = abs(math.sin(ph))
    hip_y = 21 - round(bob)
    _legs(d, cx, hip_y, ph, 3, 3, PANTS, SHOE)
    sh_y = hip_y - 11
    d.line([(cx - 3, sh_y + 1), (cx - 4, sh_y + 9)], fill=COAT_S, width=2)     # brazo de atrás
    cuerpo(d, cx, sh_y, hip_y)
    fx, fy = cx + 6, sh_y + 7 + round(math.sin(ph + 1))                         # brazo con la motosierra
    d.line([(cx + 3, sh_y + 1), (fx, fy)], fill=COAT, width=2)
    motosierra(d, fx + 1, fy, ang=0.08 * math.sin(ph), i=i)
    d.point([(fx, fy)], fill=SKIN)
    hx, hy = cx + 1, 3 + round(bob)
    d.rectangle([cx, hy + 6, cx + 2, hy + 8], fill=SKIN_S)
    cabeza(d, hx, hy)
    _outline(img)
    return img


CARGA = [  # (agachado px, ángulo de la motosierra en grados, humo)
    (0, 0, 0), (1, -15, 0), (2, -32, 1), (2, -48, 2), (2, -50, 3), (2, -50, 3)]


def carga(i):
    baja, grados, n_humo = CARGA[i]
    img, d = _new()
    cx = CX
    tiembla = (i % 2) if i >= 4 else 0                                         # la acelera: vibra
    hip_y = 21 + baja
    _legs(d, cx, hip_y, 0.6, 3, 0, PANTS, SHOE)
    sh_y = hip_y - 10 - (1 if baja == 0 else 0)
    cuerpo(d, cx, sh_y, hip_y)
    d.line([(cx - 3, sh_y + 1), (cx - 6, sh_y + 6)], fill=COAT_S, width=2)
    t = min(1.0, -grados / 50)                                                 # la mano sube con el ángulo
    ax, ay = cx + 6, round(sh_y + 7 - t * 8) - tiembla
    d.line([(cx + 3, sh_y + 1), (ax, ay)], fill=COAT, width=2)
    motosierra(d, ax + 1, ay, ang=math.radians(grados), i=i)
    d.point([(ax, ay)], fill=SKIN)
    humo(d, ax + 1, ay, n_humo)
    hx, hy = cx + 1, sh_y - 7
    d.rectangle([cx, hy + 6, cx + 2, hy + 8], fill=SKIN_S)
    cabeza(d, hx, hy)
    if i >= 2:
        d.point([(hx, hy + 3), (hx + 3, hy + 3)], fill=(255, 170, 150, 255))   # ojos que brillan
    _outline(img)
    return img


def embiste(i):
    ph = i / 4 * TAU
    img, d = _new()
    cx = CX
    hip_y = 22 - round(abs(math.sin(ph)))
    _legs(d, cx, hip_y, ph, 5, 2, PANTS, SHOE)                                 # zancada larga
    sh_y = hip_y - 10
    d.line([(cx - 2, sh_y + 1), (cx - 6, sh_y + 6)], fill=COAT_S, width=2)     # brazo de atrás, suelto
    cuerpo(d, cx, sh_y, hip_y, lean=2, vuelo=2 + i % 2)                       # inclinado, faldón al viento
    fx, fy = cx + 8, sh_y + 6
    d.line([(cx + 5, sh_y + 1), (fx, fy)], fill=COAT, width=2)
    tx, ty = motosierra(d, fx + 1, fy, ang=0.1, i=i)
    d.point([(fx, fy)], fill=SKIN)
    chispas(d, tx, ty, i)
    hx, hy = cx + 3, sh_y - 7
    d.rectangle([cx + 2, hy + 6, cx + 4, hy + 8], fill=SKIN_S)
    cabeza(d, hx, hy)
    d.point([(hx - 6, hy + i % 2), (hx - 7, hy + 2 + i % 2)], fill=HAIR)       # el pelo hacia atrás
    _outline(img)
    return img


def expuesto(i):
    ph = i / 8 * TAU
    img, d = _new()
    cx = CX
    hip_y = 27                                                                  # de rodillas: 6 px más abajo
    d.line([(cx - 1, hip_y), (cx + 3, 32)], fill=PANTS, width=2)              # muslos al frente
    d.line([(cx + 2, hip_y), (cx + 6, 32)], fill=PANTS, width=2)
    d.rectangle([cx + 2, 32, cx + 7, 33], fill=PANTS)                          # rodillas en el piso
    d.rectangle([cx - 5, 32, cx - 2, 33], fill=SHOE)                           # pies atrás
    sh_y = hip_y - 9
    cuerpo(d, cx, sh_y, hip_y, largo=2)
    sacude = i % 2                                                             # la motosierra trabada vibra
    mx, my = cx + 7, sh_y + 7 + sacude
    d.line([(cx + 3, sh_y + 1), (mx - 1, my)], fill=COAT, width=2)            # los dos brazos agarrándola
    d.line([(cx - 3, sh_y + 2), (mx - 2, my + 1)], fill=COAT_S, width=2)
    tx, ty = motosierra(d, mx, my, ang=0.12, i=0)                              # trabada: la cadena no gira
    d.point([(mx - 1, my)], fill=SKIN)
    if i % 4 < 2:
        chispas(d, tx, ty, i)
    hx, hy = cx + 1 + round(math.sin(ph)), sh_y - 7
    d.rectangle([cx, hy + 6, cx + 2, hy + 8], fill=SKIN_S)
    cabeza(d, hx, hy, ojos="cruz")
    for k in range(3):                                                         # estrellitas
        a = ph + k * 2.09
        d.point([(hx + round(math.cos(a) * 5), hy - 2 + round(math.sin(a)))], fill=STAR)
    _outline(img)
    return img


ANIMS = (("walk", walk, 8), ("carga", carga, 6), ("embiste", embiste, 4), ("expuesto", expuesto, 8))


def main():
    out = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else OUT
    os.makedirs(out, exist_ok=True)
    for kind, fn, n in ANIMS:
        cuadros = []
        for k in range(n):
            im = fn(k)
            im = im.resize((round(im.width * ESCALA), round(im.height * ESCALA)), Image.Resampling.NEAREST)
            im.save(f"{out}/jefe_{kind}_{k + 1}.png")
            cuadros.append(im)
        # tira de referencia (como las de caminata de los zombies; la usa el GDD)
        tira = Image.new("RGBA", (cuadros[0].width * n, cuadros[0].height), (0, 0, 0, 0))
        for k, im in enumerate(cuadros):
            tira.alpha_composite(im, (k * im.width, 0))
        tira.save(f"{out}/jefe_{kind}_sheet.png")
    print(", ".join(f"jefe_{k}_1..{n}" for k, _, n in ANIMS),
          f"({W + 2 * PAD}x{H} x{ESCALA})  ->  {out}/")


if __name__ == "__main__":
    main()
