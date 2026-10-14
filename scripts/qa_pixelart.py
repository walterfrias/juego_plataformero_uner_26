#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
qa_pixelart.py  —  utilidades para revisar arte pixel: onion skin, chequeo
de tileado, y mock a escala de juego. Genera PNGs de inspeccion en la
carpeta que le indiques (no toca los assets).

Tech: Python 3 + Pillow.

Comandos:

  onion  SHEET.png  FW  FH  OUT.png
      Superpone todos los frames del spritesheet, cada uno con un tinte
      (rojo = frame 1, verde = 2, azul = 3, ...). Lo que queda gris es lo
      que NO se mueve; los colores sueltos marcan el "drift" entre frames.

  tile   TEXTURA.png  OUT.png
      Pega la textura dos veces lado a lado y marca la union con una
      linea roja. Si el skyline cruza la linea sin corte, tilea bien.

  scale  SPRITE.png  OUT.png  [ESCALA]
      Escala con vecino-mas-cercano (default 12x) sobre fondo damero,
      para ver el sprite grande sin interpolacion.
"""
import sys
from PIL import Image, ImageDraw

NEAREST = getattr(getattr(Image, "Resampling", Image), "NEAREST")

TINTS = [(255, 60, 60), (60, 200, 60), (70, 90, 255),
         (235, 180, 40), (200, 60, 200), (60, 200, 200)]


def _frames(sheet, fw, fh):
    im = Image.open(sheet).convert("RGBA")
    w, h = im.size
    return [im.crop((i * fw, 0, i * fw + fw, fh)) for i in range(w // fw)], fw, fh


def _checker(w, h, c=10):
    b = Image.new("RGBA", (w, h), (235, 235, 235, 255))
    for y in range(h):
        for x in range(w):
            if (x // c + y // c) % 2:
                b.putpixel((x, y), (200, 200, 200, 255))
    return b


def cmd_onion(sheet, fw, fh, out):
    frames, fw, fh = _frames(sheet, int(fw), int(fh))
    base = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    for f, tint in zip(frames, TINTS):
        layer = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        fp, lp = f.load(), layer.load()
        for y in range(fh):
            for x in range(fw):
                if fp[x, y][3] > 40:
                    lp[x, y] = (*tint, 90)
        base = Image.alpha_composite(base, layer)
    base.resize((fw * 16, fh * 16), NEAREST).save(out)
    print(f"onion -> {out}   (frames: {len(frames)})")


def cmd_tile(tex, out):
    im = Image.open(tex).convert("RGBA")
    w, h = im.size
    strip = Image.new("RGBA", (w * 2, h), (16, 20, 40, 255))
    strip.alpha_composite(im, (0, 0))
    strip.alpha_composite(im, (w, 0))
    ImageDraw.Draw(strip).line([(w, 0), (w, h)], fill=(255, 0, 0, 130))
    strip.resize((w * 2 * 3, h * 3), NEAREST).save(out)
    print(f"tile -> {out}")


def cmd_scale(sprite, out, scale=12):
    scale = int(scale)
    im = Image.open(sprite).convert("RGBA")
    w, h = im.size
    bg = _checker(w, h)
    bg.alpha_composite(im)
    bg.resize((w * scale, h * scale), NEAREST).save(out)
    print(f"scale x{scale} -> {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd, rest = sys.argv[1], sys.argv[2:]
    {"onion": cmd_onion, "tile": cmd_tile, "scale": cmd_scale}[cmd](*rest)
