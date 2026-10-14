#!/usr/bin/env python3
"""
gen_street_props.py  —  genera props de calle placeholder para el piso.

Qué crea (pixel-art, escala nativa, para resolución interna 224x126):
  - assets/City/farol.png  : farol de calle encendido, con glow cálido
  - assets/City/tacho.png   : tacho de basura metálico

Cómo: dibujado procedural con Pillow (PIL). Sin dependencias fuera de
Pillow. Los sprites tienen el "pie" al ras del borde inferior del canvas,
así se colocan en la escena con  y = alturaPiso - altoSprite.

Tech: Python 3 + Pillow.
Uso:  python3 scripts/gen_street_props.py     (correr desde la raíz del repo)

Para reemplazar por arte propio: dibujá en Pixaki respetando las medidas
(farol 20x56, tacho 16x18), exportá con el mismo nombre de archivo y no
hace falta tocar game.json.
"""
from PIL import Image, ImageDraw
import os

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)

# --- paleta noche (alineada al fondo de escena 16,20,40) ---
METAL_DARK  = (38, 42, 60, 255)
METAL_MID   = (58, 64, 86, 255)
METAL_LIGHT = (92, 100, 128, 255)
LAMP_CORE   = (255, 244, 196, 255)
LAMP_PANE   = (255, 214, 120, 255)
GLOW        = (255, 220, 140)          # se le agrega alpha por anillo
CAN_BODY    = (54, 62, 58, 255)
CAN_RIDGE   = (78, 88, 82, 255)
CAN_LID     = (70, 80, 76, 255)
CAN_DARK    = (30, 36, 34, 255)


def farol():
    W, H = 20, 56
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = 7                       # eje del poste (dejamos aire a la derecha para el brazo)

    # glow radial detrás de la cabeza
    head = (cx + 3, 9)
    for r in range(11, 0, -1):
        a = int(70 * (r / 11) ** 2)          # más opaco al centro
        a = 70 - a
        bbox = [head[0] - r, head[1] - r, head[0] + r, head[1] + r]
        d.ellipse(bbox, fill=GLOW + (max(a, 0),))

    # poste
    d.rectangle([cx - 1, 12, cx + 1, H - 3], fill=METAL_MID)
    d.line([(cx - 1, 12), (cx - 1, H - 3)], fill=METAL_LIGHT)   # brillo lado izq
    d.line([(cx + 1, 12), (cx + 1, H - 3)], fill=METAL_DARK)
    # base ensanchada
    d.rectangle([cx - 3, H - 3, cx + 3, H - 1], fill=METAL_DARK)
    d.rectangle([cx - 3, H - 3, cx + 3, H - 3], fill=METAL_MID)

    # brazo curvo hacia la cabeza
    d.line([(cx, 12), (cx + 2, 10), (cx + 3, 11)], fill=METAL_MID)

    # cabeza / farola
    d.rectangle([head[0] - 2, head[1] - 3, head[0] + 2, head[1] + 3], fill=METAL_DARK)
    d.rectangle([head[0] - 1, head[1] - 2, head[0] + 1, head[1] + 2], fill=LAMP_PANE)
    d.point([head, (head[0], head[1] - 1)], fill=LAMP_CORE)
    d.rectangle([head[0] - 2, head[1] - 4, head[0] + 2, head[1] - 3], fill=METAL_MID)  # sombrerito

    img.save(f"{OUT}/farol.png")
    return img


def tacho():
    W, H = 16, 18
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W // 2

    # cuerpo (tronco de cono muy suave)
    top, bot = 5, H - 1
    for y in range(top, bot):
        t = (y - top) / (bot - top)
        hw = 4 + 1 * t
        d.line([(cx - hw, y), (cx + hw, y)], fill=CAN_BODY)
    # nervaduras verticales
    for dx in (-3, 0, 3):
        d.line([(cx + dx, top + 1), (cx + dx, bot - 1)], fill=CAN_RIDGE)
    # sombra lado derecho
    d.line([(cx + 4, top + 1), (cx + 5, bot - 1)], fill=CAN_DARK)
    # aro superior
    d.line([(cx - 5, top), (cx + 5, top)], fill=CAN_RIDGE)
    # tapa
    d.rectangle([cx - 5, top - 3, cx + 4, top - 1], fill=CAN_LID)
    d.rectangle([cx - 5, top - 3, cx + 4, top - 3], fill=CAN_RIDGE)
    d.point([(cx, top - 4)], fill=CAN_RIDGE)      # manija
    # basurita asomando
    d.point([(cx - 2, top - 2), (cx + 2, top - 2)], fill=(120, 110, 90, 255))

    img.save(f"{OUT}/tacho.png")
    return img


if __name__ == "__main__":
    f = farol()
    t = tacho()
    print(f"farol.png {f.size}  ->  {OUT}/farol.png")
    print(f"tacho.png  {t.size}  ->  {OUT}/tacho.png")
