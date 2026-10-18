#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_jefe.py  —  Paciente Zero: EL CIENTÍFICO que empezó todo (18/10). El usuario
descartó el ser de fantasía (la masa viral): "que sea un científico con
guardapolvo pero con camiseta de Argentina". Es el que trabajaba en el
laboratorio de L2 y escribió el diario (las notas); al final está al pie del
Obelisco, con la camiseta de Argentina como Lio, del otro lado.

Mismo estilo que los zombies del juego (gen_zombies_lab.py: piel verdosa, ojos
rojos, contorno oscuro de 1 px) pero dibujado al DOBLE: 64x68, el tamaño con el
que se juega el jefe (no cambia la colisión: no se puede saltar, Lio salta 37).
Mira a la DERECHA (los eventos lo espejan con FlipX); los pies en la última fila.

  - pelo blanco revuelto (científico loco), anteojos redondos con un vidrio rajado
  - guardapolvo largo ABIERTO, sucio y roto en el borde, con la credencial
  - debajo, la camiseta de Argentina: bastones celestes y blancos
  - en la mano de adelante, una jeringa con el líquido verde del virus

Animaciones (mismos nombres y cuadros que antes: wire_jefe.py no cambia):
  jefe_walk_1..6      avanza tambaleándose, la jeringa al frente
  jefe_carga_1..3     se agacha y levanta la jeringa sobre la cabeza; ojos encendidos
  jefe_expuesto_1..4  de rodillas, aturdido: anteojos torcidos, la jeringa en el
                      piso y estrellitas girando sobre la cabeza (= pisalo)
Uso:  python3 scripts/gen_jefe.py   (crea game/assets/Jefe/)
"""
from PIL import Image, ImageDraw
import math
import os

OUT = "game/assets/Jefe"
os.makedirs(OUT, exist_ok=True)
W, H = 64, 68
T = (0, 0, 0, 0)
OUTLINE = (24, 24, 34, 255)                       # = zombies del juego
SKIN, SKIN_S, SKIN_H = (150, 190, 150, 255), (108, 150, 116, 255), (186, 214, 180, 255)
EYE, EYE_HI = (214, 74, 74, 255), (255, 170, 150, 255)
MOUTH = (60, 20, 26, 255)
HAIR, HAIR_S = (214, 214, 206, 255), (160, 162, 158, 255)         # pelo blanco
COAT, COAT_S, COAT_H = (190, 198, 202, 255), (140, 150, 158, 255), (220, 226, 228, 255)  # = médico
STAIN = (120, 130, 110, 255)
CELESTE, CELESTE_S = (116, 172, 223, 255), (84, 136, 186, 255)     # camiseta de Argentina
BLANCO, BLANCO_S = (232, 236, 240, 255), (186, 192, 200, 255)
PANTS, PANTS_S = (52, 56, 70, 255), (36, 38, 50, 255)
SHOE = (40, 36, 34, 255)
GLASS, GLASS_H = (60, 70, 80, 255), (200, 230, 236, 255)
BADGE = (214, 200, 110, 255)
SYR, SYR_H = (190, 210, 214, 255), (240, 250, 250, 255)
VIRUS_G, VIRUS_GH = (90, 200, 100, 255), (160, 240, 150, 255)    # = líquido del lab
STAR = (255, 230, 120, 255)


def outline(img):
    src = img.copy()
    sp, px = src.load(), img.load()
    for y in range(H):
        for x in range(W):
            if sp[x, y][3] == 0 and any(0 <= x + a < W and 0 <= y + b < H and sp[x + a, y + b][3]
                                        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = OUTLINE
    return img


def legs(d, cx, hip_y, ph, stride, foot_y=67):
    """dos piernas con zancada (ph = fase de la caminata)."""
    for sign, phase in ((-1, 0.0), (1, math.pi)):
        sw = math.sin(ph + phase)
        fx = cx + sign * 4 + round(sw * stride)
        fy = foot_y - round(max(0.0, sw) * 4)
        d.line([(cx + sign * 4, hip_y), (fx, fy - 2)], fill=PANTS if sign > 0 else PANTS_S, width=6)
        d.rectangle([fx - 4, fy - 3, fx + 4, fy], fill=SHOE)


def torso(d, cx, sh_y, hip_y, lean=0):
    """camiseta de Argentina (bastones) asomando por el guardapolvo abierto."""
    # camiseta: rectángulo de bastones celestes y blancos
    for x in range(cx - 7 + lean, cx + 8 + lean):
        col = CELESTE if ((x - cx) // 3) % 2 == 0 else BLANCO
        sh = CELESTE_S if col == CELESTE else BLANCO_S
        for y in range(sh_y + 1, hip_y + 1):
            d.point((x, y), fill=sh if x > cx + 4 + lean else col)
    d.line([(cx - 3 + lean, sh_y + 1), (cx + lean, sh_y + 4), (cx + 3 + lean, sh_y + 1)], fill=OUTLINE)  # cuello en V
    # guardapolvo: dos paños abiertos que llegan a la rodilla
    d.polygon([(cx - 10 + lean, sh_y), (cx - 5 + lean, sh_y), (cx - 4 + lean, hip_y + 12),
               (cx - 13 + lean, hip_y + 12)], fill=COAT)
    d.polygon([(cx + 6 + lean, sh_y), (cx + 11 + lean, sh_y), (cx + 14 + lean, hip_y + 12),
               (cx + 5 + lean, hip_y + 12)], fill=COAT_S)
    d.line([(cx - 10 + lean, sh_y + 1), (cx - 13 + lean, hip_y + 11)], fill=COAT_H)
    # borde roto y manchas
    for x, dy in ((-12, 0), (-9, 2), (-6, 0), (8, 1), (11, 3), (13, 0)):
        d.point((cx + x + lean, hip_y + 12 + dy), fill=COAT_S if x < 0 else COAT)
    d.point((cx - 8 + lean, sh_y + 9), fill=STAIN)
    d.point((cx - 7 + lean, sh_y + 10), fill=STAIN)
    d.point((cx + 9 + lean, hip_y + 4), fill=STAIN)
    # credencial colgando del bolsillo
    d.rectangle([cx - 9 + lean, sh_y + 6, cx - 6 + lean, sh_y + 10], fill=BADGE)
    d.point((cx - 8 + lean, sh_y + 7), fill=OUTLINE)


def head(d, hx, hy, eyes="rojo", glasses_tilt=0):
    """cabeza: pelo blanco revuelto, anteojos redondos (uno rajado), ojos rojos."""
    d.rectangle([hx - 3, hy + 13, hx + 3, hy + 17], fill=SKIN_S)                 # cuello
    d.ellipse([hx - 8, hy, hx + 8, hy + 16], fill=SKIN)
    d.ellipse([hx + 3, hy + 3, hx + 8, hy + 14], fill=SKIN_S)                     # mejilla en sombra
    # pelo: mechones parados hacia todos lados
    for (x0, y0, x1, y1) in ((-9, 4, -12, -1), (-6, 1, -7, -4), (-2, 0, -1, -5), (2, 0, 4, -4),
                             (6, 1, 9, -2), (8, 4, 12, 1), (-9, 8, -13, 7)):
        d.line([(hx + x0, hy + y0), (hx + x1, hy + y1)], fill=HAIR, width=3)
    d.ellipse([hx - 9, hy - 2, hx + 9, hy + 6], fill=HAIR)
    d.line([(hx - 8, hy + 5), (hx + 7, hy + 4)], fill=HAIR_S)
    # anteojos
    gy = hy + 6 + glasses_tilt
    for gx in (hx - 4, hx + 4):
        d.ellipse([gx - 3, gy - 3, gx + 3, gy + 3], outline=GLASS)
        if eyes == "cruz":
            d.line([(gx - 1, gy - 1), (gx + 1, gy + 1)], fill=MOUTH)
            d.line([(gx - 1, gy + 1), (gx + 1, gy - 1)], fill=MOUTH)
        else:
            d.rectangle([gx - 1, gy - 1, gx + 1, gy], fill=EYE)
            if eyes == "brillo":
                d.point((gx, gy - 1), fill=EYE_HI)
    d.line([(hx - 1, gy - 1 - glasses_tilt), (hx + 1, gy - 1)], fill=GLASS)       # puente
    d.line([(hx + 2, gy - 2), (hx + 6, gy + 2)], fill=GLASS_H)                    # el vidrio rajado
    d.point((hx - 6, gy - 2), fill=GLASS_H)
    # boca abierta
    d.rectangle([hx - 2, hy + 11, hx + 3, hy + 13], fill=MOUTH)
    d.point((hx - 1, hy + 11), fill=SKIN_H)
    d.point((hx + 2, hy + 11), fill=SKIN_H)


def jeringa(d, x, y, ang):
    """jeringa con líquido verde, desde la mano (x, y) hacia el ángulo ang (rad)."""
    c, s = math.cos(ang), math.sin(ang)
    p = lambda t, n=0: (round(x + c * t - s * n), round(y + s * t + c * n))
    d.line([p(0), p(12)], fill=SYR, width=4)                                    # cuerpo
    d.line([p(2, -1), p(10, -1)], fill=VIRUS_G, width=2)                        # líquido
    d.point(p(4, -1), fill=VIRUS_GH)
    d.line([p(12), p(17)], fill=SYR_H)                                          # aguja
    d.line([p(-3, -2), p(-3, 2)], fill=SYR, width=2)                            # émbolo


def arm(d, x0, y0, x1, y1, front=True):
    d.line([(x0, y0), (x1, y1)], fill=COAT if front else COAT_S, width=5)       # manga
    d.ellipse([x1 - 2, y1 - 2, x1 + 2, y1 + 2], fill=SKIN if front else SKIN_S)  # mano


def frame_walk(k):
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    ph = k / 6 * 2 * math.pi
    bob = round(abs(math.sin(ph)) * 2)
    cx, hip_y = 28, 44 - bob
    sh_y = hip_y - 22
    legs(d, cx, hip_y, ph, 6)
    arm(d, cx - 6, sh_y + 3, cx - 10, sh_y + 18 + round(math.sin(ph) * 2), front=False)  # brazo de atrás colgando
    torso(d, cx, sh_y, hip_y)
    head(d, cx + 2, sh_y - 17 + round(math.sin(ph) * 0.6))
    hx, hy = cx + 15, sh_y + 10 + round(math.sin(ph + 1) * 2)                   # brazo de adelante, jeringa al frente
    arm(d, cx + 6, sh_y + 3, hx, hy)
    jeringa(d, hx + 1, hy, -0.15)
    return outline(img)


def frame_carga(k):
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    crouch = 2 + k * 2                                                          # se agacha cuadro a cuadro
    cx, hip_y = 26, 46 + crouch // 2
    sh_y = hip_y - 21 + crouch // 2
    legs(d, cx, hip_y, 0.6, 7)
    torso(d, cx, sh_y, hip_y, lean=2)
    head(d, cx + 5, sh_y - 15, eyes="brillo")
    # la jeringa sube por encima de la cabeza
    hx, hy = cx + 10 + k, sh_y - 8 - k * 3
    arm(d, cx + 7, sh_y + 3, hx, hy)
    jeringa(d, hx, hy, -1.1 - k * 0.15)
    arm(d, cx - 5, sh_y + 4, cx - 12, sh_y + 10, front=False)
    return outline(img)


def frame_expuesto(k):
    """de rodillas: todo el cuerpo ~10 px más abajo y el guardapolvo corto, para que
    se lean las rodillas en el piso (con el cuerpo a la altura de parado no se leía)."""
    img = Image.new("RGBA", (W, H), T)
    d = ImageDraw.Draw(img)
    cx = 28
    sh_y, hip_y = 38, 52
    # rodillas en el piso (adelante) y los pies atrás
    d.line([(cx - 2, hip_y), (cx + 5, 64)], fill=PANTS_S, width=6)
    d.line([(cx + 3, hip_y), (cx + 10, 64)], fill=PANTS, width=6)
    d.rectangle([cx + 2, 63, cx + 13, 67], fill=PANTS)                          # rodillas apoyadas
    d.line([(cx - 2, 64), (cx - 12, 66)], fill=PANTS_S, width=4)                # pantorrillas hacia atrás
    d.rectangle([cx - 16, 63, cx - 10, 67], fill=SHOE)
    torso(d, cx, sh_y, hip_y - 8, lean=-1)                                      # guardapolvo hasta las rodillas
    head(d, cx + 1 + (1 if k % 2 else 0), sh_y - 16, eyes="cruz", glasses_tilt=2)
    arm(d, cx + 6, sh_y + 4, cx + 14, 62)                                       # brazos caídos hasta el piso
    arm(d, cx - 6, sh_y + 4, cx - 9, 60, front=False)
    jeringa(d, cx + 19, 64, 0.05)                                               # la jeringa en el piso
    # estrellitas girando sobre la cabeza: "pisalo ahora"
    for i in range(3):
        a = k * 1.2 + i * 2.09
        sx, sy = cx + 1 + round(math.cos(a) * 11), sh_y - 20 + round(math.sin(a) * 3)
        for ddx, ddy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            d.point((sx + ddx, sy + ddy), fill=STAR)
    return outline(img)


def main():
    for kind, fn, n in (("walk", frame_walk, 6), ("carga", frame_carga, 3), ("expuesto", frame_expuesto, 4)):
        for k in range(n):
            fn(k).save(f"{OUT}/jefe_{kind}_{k + 1}.png")
    print(f"jefe_walk_1..6, jefe_carga_1..3, jefe_expuesto_1..4 (el científico)  ->  {OUT}/")


if __name__ == "__main__":
    main()
