#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false, reportMissingImports=false
"""
gen_luz_luna.py  —  luz fría de la luna horneada sobre los props del Nivel 1
(15/10, parte C de la noche: versión "horneada", sin capa de iluminación).

La luna está arriba a la derecha. Sobre una copia de cada sprite:
  - cantos que miran hacia ARRIBA: el 1er píxel se mezcla 60 % con la luz
    de luna y el 2do 25 % (la parte más visible);
  - cantos que miran a la DERECHA: 30 % (solo sprites sueltos);
  - cantos que miran a la IZQUIERDA: se oscurecen 18 % (lado en sombra).
Las texturas que se repiten (TiledSprite: vereda, cable) solo llevan el
canto de arriba: un canto lateral se repetiría en cada baldosa.

Siempre parte del archivo ORIGINAL (nunca de un *_luna.png): se puede
re-correr sin que la luz se acumule. wire_noche_n1.py hace que los objetos
de Level1 usen las copias; los demás niveles siguen con el original.

Crea, junto a cada original:  <nombre>_luna.png
Uso:  python3 scripts/gen_luz_luna.py   (desde la raíz del repo)
"""
from PIL import Image

MOON = (200, 216, 255)
SHADE = 0.82

# archivo (relativo a game/), es_tileado
SOURCES = {
    "assets/City/sidewalk.png": True,
    "assets/City/cable_tile.png": True,
    "assets/City/poste.png": False,
    "assets/City/tacho.png": False,
    "assets/City/drain_pipe.png": False,
    "assets/City/wall_break_l.png": False,
    "assets/City/wall_break_r.png": False,
    "assets/City/gap_debris.png": False,
    "assets/UI/sign_lab.png": False,
    "assets/N1/puente_a.png": False,
    "assets/N1/puente_b.png": False,
    "assets/N1/puente_c.png": False,
    "assets/N1/puente_d.png": False,
    "assets/N1/puente_e.png": False,
    "assets/N1/Balcon.png": False,
    "assets/N1/EscaleraIncendio.png": False,
    "assets/N1/Toldo.png": False,
    "assets/N1/BancoPlaza.png": False,
    "assets/N1/Colchon.png": False,
    "assets/N1/FarolRepisa.png": False,
}


def out_name(src):
    return src[:-4] + "_luna.png"


def mix(c, target, a):
    return tuple(round(c[i] * (1 - a) + target[i] * a) for i in range(3)) + (c[3],)


def moonlit(im, tiled):
    w, h = im.size
    px = im.load()
    out = im.copy()
    o = out.load()

    def solid(x, y):
        if tiled and not 0 <= x < w:
            x %= w
        return 0 <= x < w and 0 <= y < h and px[x, y][3] > 128

    for y in range(h):
        for x in range(w):
            if not solid(x, y):
                continue
            c = px[x, y]
            if not solid(x, y - 1):
                o[x, y] = mix(c, MOON, 0.6)
                if solid(x, y + 1):
                    o[x, y + 1] = mix(px[x, y + 1], MOON, 0.25)
                continue
            if tiled:
                continue
            cur = o[x, y]                    # puede traer ya el 25 % del canto de arriba
            if not solid(x + 1, y):
                o[x, y] = mix(cur, MOON, 0.3)
            elif not solid(x - 1, y):
                o[x, y] = tuple(round(v * SHADE) for v in cur[:3]) + (cur[3],)
    return out


def main():
    for src, tiled in SOURCES.items():
        im = Image.open("game/" + src).convert("RGBA")
        moonlit(im, tiled).save("game/" + out_name(src))
    print(f"{len(SOURCES)} sprites con luz de luna -> *_luna.png")


if __name__ == "__main__":
    main()
