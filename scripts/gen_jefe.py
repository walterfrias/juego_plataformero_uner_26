#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_jefe.py  —  Paciente Zero: EL CIENTÍFICO que empezó todo (18/10). Es el que
trabajaba en el laboratorio de L2 y escribió el diario; al final está al pie del
Obelisco, con la camiseta de Argentina como Lio, del otro lado.

Es UN ZOMBIE MÁS, en el mismo estilo que los otros, solo que más grande: se dibuja
a 32x34 con las mismas piezas que el médico y el investigador
(gen_zombies_lab.py / gen_zombies_wave2.py: _new, _legs, _outline, la paleta) y se
agranda x1.5 píxel a píxel a 48x51 (hasta el 18/10 era x2 = 64x68: "que sea
más chico"; wire_jefe.py ajusta máscaras, tamaño y lógica a la imagen). La
versión anterior se dibujó directo a 64x68 con mucho más detalle que el resto y
"tendría que ser uno idéntico a los otros pero escalado" (usuario 18/10).

  - mata de pelo NEGRO revuelto ("más pelo, de color negro"), anteojos, ojos rojos
  - guardapolvo abierto con la camiseta de Argentina (bastones celestes y blancos)
  - una motosierra en la mano de adelante (25/10; antes, una jeringa con el
    líquido verde del lab)
Mira a la DERECHA (los eventos lo espejan con FlipX); los pies en la última fila.

Animaciones (mismos nombres y cuadros: wire_jefe.py no cambia de lógica):
  jefe_walk_1..6      camina con la motosierra al frente (la cadena gira)
  jefe_carga_1..3     se agacha y levanta la motosierra sobre la cabeza
  jefe_expuesto_1..4  de rodillas, aturdido, estrellitas sobre la cabeza (= pisalo)
Uso:  python3 scripts/gen_jefe.py   (crea game/assets/Jefe/)
"""
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from gen_zombies_lab import COAT, COAT_H, COAT_S, SHOE, _legs   # noqa: E402
from gen_zombies_wave2 import EYE, MOUTH, SKIN, SKIN_S, TAU, _new, _outline  # noqa: E402

OUT = "game/assets/Jefe"
ESCALA = 1.5                                    # 32x34 → 48x51 (antes x2; "más chico", usuario 18/10)
HAIR = (34, 32, 40, 255)                        # pelo negro, mucho (antes blanco y corto)
HAIR_H = (66, 64, 78, 255)                      # brillo: si no, el negro se pierde en la noche
GLASS = (60, 70, 80, 255)
CELESTE, BLANCO = (116, 172, 223, 255), (232, 236, 240, 255)
PANTS = (52, 56, 70, 255)
# motosierra (25/10, pedido del usuario: reemplaza a la jeringa)
MOTOR, MOTOR_S, MANGO = (230, 124, 40, 255), (164, 80, 28, 255), (40, 40, 46, 255)
ESPADA, CADENA = (176, 182, 192, 255), (70, 70, 78, 255)
STAR = (255, 230, 120, 255)


def camiseta(d, x0, x1, y0, y1):
    """bastones celestes y blancos de 1 px en la abertura del guardapolvo."""
    for x in range(x0, x1 + 1):
        d.line([(x, y0), (x, y1)], fill=CELESTE if (x - x0) % 2 == 0 else BLANCO)


def cuerpo(d, cx, sh_y, hip_y, largo=4):
    """guardapolvo abierto (como el del médico) con la camiseta de Argentina."""
    d.polygon([(cx - 5, sh_y), (cx + 5, sh_y), (cx + 6, hip_y + largo), (cx - 6, hip_y + largo)], fill=COAT)
    d.polygon([(cx + 2, sh_y), (cx + 5, sh_y), (cx + 6, hip_y + largo), (cx + 3, hip_y + largo)], fill=COAT_S)
    camiseta(d, cx - 1, cx + 2, sh_y + 1, hip_y + largo - 1)
    d.line([(cx - 5, sh_y + 1), (cx - 5, hip_y + largo - 1)], fill=COAT_H)


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


def motosierra(d, x, y, arriba=False, i=0):
    """el motor naranja en la mano (x, y) y la espada hacia adelante (o hacia arriba);
    los dientes de la cadena se corren con el cuadro i (está prendida)."""
    if arriba:                                                         # levantada, en diagonal hacia adelante
        d.rectangle([x - 1, y - 1, x + 2, y + 2], fill=MOTOR)              # motor
        d.line([(x - 1, y + 2), (x + 2, y + 2)], fill=MOTOR_S)
        d.point([(x - 2, y)], fill=MANGO)                                  # manija
        pts = [(x + 2 + k, y - 1 - k) for k in range(6)]                   # espada
        for k, (px_, py_) in enumerate(pts):
            d.point([(px_, py_), (px_ + 1, py_)], fill=ESPADA)
            if (k + i) % 2 == 0:
                d.point([(px_ + 1, py_ + 1)], fill=CADENA)
    else:
        d.rectangle([x - 1, y - 2, x + 2, y + 1], fill=MOTOR)              # motor
        d.line([(x - 1, y + 1), (x + 2, y + 1)], fill=MOTOR_S)
        d.line([(x - 1, y - 3), (x + 1, y - 3)], fill=MANGO)               # manija de arriba
        d.line([(x + 3, y - 1), (x + 8, y - 1)], fill=ESPADA, width=2)     # espada al frente
        for xx in range(x + 3, x + 9):
            if (xx + i) % 2 == 0:
                d.point([(xx, y - 2), (xx, y + 1)], fill=CADENA)
        d.point([(x + 9, y - 1)], fill=ESPADA)


def walk(i):
    ph = i / 6 * TAU
    img, d = _new()
    cx = 14
    bob = abs(math.sin(ph))
    hip_y = 21 - round(bob)
    _legs(d, cx, hip_y, ph, 3, 3, PANTS, SHOE)
    sh_y = hip_y - 11
    d.line([(cx - 3, sh_y + 1), (cx - 4, sh_y + 9)], fill=COAT_S, width=2)     # brazo de atrás
    cuerpo(d, cx, sh_y, hip_y)
    fx, fy = cx + 8, sh_y + 4 + round(math.sin(ph + 1))                         # brazo con la motosierra
    d.line([(cx + 3, sh_y + 1), (fx, fy)], fill=COAT, width=2)
    d.point([(fx + 1, fy)], fill=SKIN)
    motosierra(d, fx + 2, fy, i=i)
    hx, hy = cx + 1, 3 + round(bob)
    d.rectangle([cx, hy + 6, cx + 2, hy + 8], fill=SKIN_S)
    cabeza(d, hx, hy)
    _outline(img)
    return img


def carga(i):
    img, d = _new()
    cx = 14
    hip_y = 22 + (1 if i > 0 else 0)                                            # se agacha
    _legs(d, cx, hip_y, 0.6, 3, 0, PANTS, SHOE)
    sh_y = hip_y - 10
    cuerpo(d, cx, sh_y, hip_y)
    ax, ay = cx + 7, sh_y - 1 - i                                              # brazo arriba, al costado de la cabeza
    d.line([(cx + 3, sh_y + 1), (ax, ay)], fill=COAT, width=2)
    motosierra(d, ax, ay - 1, arriba=True, i=i)
    d.line([(cx - 3, sh_y + 1), (cx - 6, sh_y + 6)], fill=COAT_S, width=2)
    hx, hy = cx + 1, sh_y - 7
    d.rectangle([cx, hy + 6, cx + 2, hy + 8], fill=SKIN_S)
    cabeza(d, hx, hy)
    d.point([(hx, hy + 3), (hx + 3, hy + 3)], fill=(255, 170, 150, 255))       # ojos que brillan
    _outline(img)
    return img


def expuesto(i):
    img, d = _new()
    cx = 14
    hip_y = 27                                                                  # de rodillas: 6 px más abajo
    d.line([(cx - 1, hip_y), (cx + 3, 32)], fill=PANTS, width=2)              # muslos al frente
    d.line([(cx + 2, hip_y), (cx + 6, 32)], fill=PANTS, width=2)
    d.rectangle([cx + 2, 32, cx + 7, 33], fill=PANTS)                          # rodillas en el piso
    d.rectangle([cx - 5, 32, cx - 2, 33], fill=SHOE)                           # pies atrás
    sh_y = hip_y - 9
    cuerpo(d, cx, sh_y, hip_y, largo=2)
    d.line([(cx + 3, sh_y + 1), (cx + 7, sh_y + 8)], fill=COAT, width=2)      # brazos caídos
    d.line([(cx - 3, sh_y + 1), (cx - 5, sh_y + 8)], fill=COAT_S, width=2)
    motosierra(d, cx + 9, 32)                                                  # la motosierra en el piso (apagada)
    hx, hy = cx + 1 + (i % 2), sh_y - 7
    d.rectangle([cx, hy + 6, cx + 2, hy + 8], fill=SKIN_S)
    cabeza(d, hx, hy, ojos="cruz")
    for k in range(3):                                                         # estrellitas
        a = i * 1.2 + k * 2.09
        d.point([(hx + round(math.cos(a) * 5), hy - 2 + round(math.sin(a)))], fill=STAR)
    _outline(img)
    return img


def main():
    out = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else OUT
    os.makedirs(out, exist_ok=True)
    for kind, fn, n in (("walk", walk, 6), ("carga", carga, 3), ("expuesto", expuesto, 4)):
        for k in range(n):
            im = fn(k)
            im.resize((round(im.width * ESCALA), round(im.height * ESCALA)),
                      Image.Resampling.NEAREST).save(f"{out}/jefe_{kind}_{k + 1}.png")
    print(f"jefe_walk_1..6, jefe_carga_1..3, jefe_expuesto_1..4 (32x34 x{ESCALA})  ->  {out}/")


if __name__ == "__main__":
    main()
