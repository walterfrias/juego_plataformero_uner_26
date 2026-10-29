#!/usr/bin/env python3
"""
gen_cover_pintada.py — 3 covers más, del mismo estilo que los de gen_cover.py (logo del
menú arriba, viñeta oscura, mismos formatos), pero sobre una captura REAL del Nivel 1
en la pintada "#YO APOYO LA LEY DE FINANCIAMIENTO UNIVERSITARIO" (28/10, pedido del
usuario: "me gusta la iluminación y todo el contenido, que se vea esa pintada").

La captura la saca cover_pintada_captura.js (juego exportado, sin HUD, Lio saltando);
queda en promo/ para poder regenerar los covers sin el juego.

Uso:  node scripts/cover_pintada_captura.js http://localhost:8791 promo/captura_pintada_960x540.png
      python3 scripts/gen_cover_pintada.py   (desde la raíz del repo)
Sale: promo/cover_pintada_630x500.png    portada itch (recorte con la pintada al centro)
      promo/cover_pintada_960x540.png    lienzo del juego x2
      promo/cover_pintada_480x270.png    lienzo del juego 1:1 (reducción de la x2)
"""
import json

from PIL import Image, ImageDraw, ImageFilter

CAPTURA = "promo/captura_pintada_960x540.png"
LOGO = "game/assets/Menu/menu_logo.png"
S = 2                                   # la captura es el lienzo de 480x270 a x2
PINTADA_X0, PINTADA_X1 = 2370, 2537     # Grafiti_Universidad (wire_grafitis_n1.py), x del mundo
ITCH_W, ITCH_H = 630, 500


def con_logo(c):
    """el logo del menú a x2, centrado arriba (como gen_cover.py: y 12 a resolución base)."""
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((logo.width * S, logo.height * S), Image.Resampling.NEAREST)
    c.alpha_composite(logo, ((c.width - logo.width) // 2, 12 * S))
    return c


def vineta(c):
    """la misma viñeta de gen_cover.py."""
    W, H = c.size
    vig = Image.new("L", c.size, 0)
    ImageDraw.Draw(vig).ellipse((-120, -100, W + 120, H + 100), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(60))
    dark = Image.new("RGBA", c.size, (6, 8, 16, 255))
    return Image.composite(c, dark, vig)


def main():
    cap = Image.open(CAPTURA).convert("RGBA")
    assert cap.size == (480 * S, 270 * S), f"la captura tiene que ser 960x540, es {cap.size}"
    cam = json.load(open(CAPTURA + ".json"))

    g = vineta(con_logo(cap.copy())).convert("RGB")
    for out, im in (("promo/cover_pintada_960x540.png", g),
                    ("promo/cover_pintada_480x270.png", g.resize((480, 270), Image.Resampling.NEAREST))):
        im.save(out)
        print("ok", out)

    # itch: recorte de 630x500 con la pintada centrada (sin salirse de la captura); desde
    # arriba de todo, así la luna queda entera detrás del título (se pierde agua de abajo)
    centro = ((PINTADA_X0 + PINTADA_X1) / 2 - cam["left"]) * S
    x0 = round(min(max(centro - ITCH_W / 2, 0), cap.width - ITCH_W))
    y0 = 0
    itch = cap.crop((x0, y0, x0 + ITCH_W, y0 + ITCH_H))
    pin0, pin1 = (PINTADA_X0 - cam["left"]) * S - x0, (PINTADA_X1 - cam["left"]) * S - x0
    assert 0 <= pin0 and pin1 <= ITCH_W, f"la pintada no entra en el recorte ({pin0:.0f}..{pin1:.0f})"
    out = "promo/cover_pintada_630x500.png"
    vineta(con_logo(itch)).convert("RGB").save(out)
    print("ok", out)


if __name__ == "__main__":
    main()
