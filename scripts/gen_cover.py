#!/usr/bin/env python3
"""
gen_cover.py — portada de itch.io y su versión al lienzo del juego.

Se compone a resolución base con los assets reales del juego (cielo y logo
del menú, skyline, obelisco, faroles, Lio, la horda y los virus) y se escala
x2 con nearest para mantener el pixel art nítido. La horda se pega ya a x2
(a x3 = 1.5 del tamaño real).

Uso:  python3 scripts/gen_cover.py   (desde la raíz del repo)
Sale: promo/cover_630x500.png    portada itch (base 315x250)
      promo/cover_960x540.png    lienzo del juego x2 (base 480x270)
      promo/cover_480x270.png    lienzo del juego 1:1 (reducción de la x2)
"""
import os
import random
from PIL import Image, ImageDraw, ImageFilter

A = "game/assets"
# layouts por formato (base). X = desplazamiento del bloque Lio/tacho.
LAYOUTS = {
    "itch": dict(W=315, H=250, ground=222, sky_y=20, moon=(258, 2),
                 obel=66, farols=(128, 290), X=0, horde_dx=0,
                 virus=[(30, 130), (112, 116), (284, 126), (258, 168), (168, 150)]),
    "game": dict(W=480, H=270, ground=242, sky_y=0, moon=None,   # el cielo ya trae la luna
                 obel=96, farols=(170, 452), X=100, horde_dx=40,
                 virus=[(40, 140), (150, 118), (420, 124), (370, 176),
                        (250, 150), (300, 96)]),
}

random.seed(7)


def load(p):
    return Image.open(os.path.join(A, p)).convert("RGBA")


def paste(base, im, x, y, flip=False):
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    base.alpha_composite(im, (int(x), int(y)))


def glow(base, cx, cy, r, color, alpha):
    """halo suave (luz de farol / virus)."""
    g = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r),
                              fill=color + (alpha,))
    base.alpha_composite(g.filter(ImageFilter.GaussianBlur(r / 2)))


def tile_row(base, im, y, offset=0):
    x = -offset
    while x < base.width:
        paste(base, im, x, y)
        x += im.width


def render(L):
    W, H, GROUND, X = L["W"], L["H"], L["ground"], L["X"]
    c = Image.new("RGBA", (W, H))
    # cielo del menú (sin la luna, que se pone a mano)
    c.alpha_composite(load("Menu/menu_sky.png").crop((0, L["sky_y"], W, L["sky_y"] + H)))
    if L["moon"]:
        paste(c, load("Menu/luna.png"), *L["moon"])

    # skyline: lejano, obelisco, cercano
    tile_row(c, load("City/city_far.png"), GROUND - 70 - 14, 40)
    obel = load("City/obelisco.png")
    glow(c, L["obel"] + 9, GROUND - 70, 30, (132, 214, 92), 40)
    paste(c, obel, L["obel"], GROUND - obel.height)
    tile_row(c, load("City/city_near.png"), GROUND - 96 + 6, 100)

    # bruma tóxica a ras del piso
    fog = Image.new("RGBA", c.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(fog)
    for i in range(40):
        a = int(70 * (1 - i / 40))
        d.line((0, GROUND - i, W, GROUND - i), fill=(90, 170, 80, a // 2))
    c.alpha_composite(fog)

    # faroles con luz ámbar
    farol = load("City/farol.png")
    for fx in L["farols"]:
        glow(c, fx + 10, GROUND - farol.height + 6, 22, (255, 206, 110), 70)
        paste(c, farol, fx, GROUND - farol.height)

    # vereda
    tile_row(c, load("City/sidewalk.png"), GROUND)
    ImageDraw.Draw(c).rectangle((0, GROUND + 16, W, H), fill=(12, 14, 22, 255))

    # virus flotando (rojos, con halo rojo)
    vir = [load(f"Virus/virus_{i}.png") for i in range(1, 7)]
    for i, (vx, vy) in enumerate(L["virus"]):
        glow(c, vx + 8, vy + 8, 9, (220, 70, 80), 55)
        paste(c, vir[i % 6], vx, vy)

    # obstáculo: tacho en la vereda
    tacho = load("City/tacho.png")
    paste(c, tacho, 214 + X, GROUND - tacho.height + 1)

    # Lio a tamaño real, en la cima del salto, avanzando a la derecha
    # Fall_1 es el cuadro más de perfil (piernas abiertas), ya mira a la derecha
    lio = load("Player/Player_Fall_1.png")
    lx, ly = 206 + X, GROUND - 34 - 30
    glow(c, lx + 16, ly + 20, 18, (150, 200, 255), 55)
    paste(c, lio, lx, ly)

    # logo
    logo = load("Menu/menu_logo.png")
    paste(c, logo, (W - logo.width) // 2, 12)

    # pasar a resolución final (x2) antes de la horda: así los zombies van
    # a x3 (= 1.5 del tamaño real, un poco más grandes que Lio) sin
    # escalar con factor fraccionario.
    S = 2
    c = c.resize((W * S, H * S), Image.NEAREST)
    gy = (GROUND + 1) * S

    # la horda: zombies del Nivel 1 atrás (más oscuros), la horda adelante
    back = ["Zombie_D/Zombie_D_Walk_3.png", "Zombie_N/Zombie_N_Walk_6.png",
            "Zombie_O/Zombie_O_Walk_2.png", "Zombie_F/Zombie_F_Walk_5.png",
            "Zombie_M/Zombie_M_Walk_4.png"]
    front = ["Zombie_Pol/Zombie_Pol_Walk_3.png", "Zombie_Med/Zombie_Med_Walk_1.png",
             "Zombie_Hin/Zombie_Hin_Walk_5.png", "Zombie_Rep/Zombie_Rep_Walk_2.png",
             "Zombie_Enf/Zombie_Enf_Walk_6.png", "Zombie_Inv/Zombie_Inv_Walk_4.png"]

    def big(path, shade=1.0):
        z = load(path)
        z = z.resize((z.width * 3, z.height * 3), Image.NEAREST)
        if shade < 1.0:
            r, g, b_, al = z.split()
            r, g, b_ = (ch.point(lambda v: int(v * shade)) for ch in (r, g, b_))
            z = Image.merge("RGBA", (r, g, b_, al))
        return z

    for i, path in enumerate(back):
        z = big(path, 0.72)
        paste(c, z, 24 + i * (68 + L["horde_dx"]), gy - z.height - 18)
    for i, path in enumerate(front):
        z = big(path)
        paste(c, z, -10 + i * (64 + L["horde_dx"]), gy - z.height + 2)

    # viñeta
    vig = Image.new("L", c.size, 0)
    ImageDraw.Draw(vig).ellipse((-120, -100, W * S + 120, H * S + 100), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(60))
    dark = Image.new("RGBA", c.size, (6, 8, 16, 255))
    c = Image.composite(c, dark, vig)

    return c.convert("RGB")


def main():
    os.makedirs("promo", exist_ok=True)
    out = "promo/cover_630x500.png"
    render(LAYOUTS["itch"]).save(out)
    print("ok", out)

    g = render(LAYOUTS["game"])
    for out, im in (("promo/cover_960x540.png", g),
                    ("promo/cover_480x270.png", g.resize((480, 270), Image.NEAREST))):
        im.save(out)
        print("ok", out)


if __name__ == "__main__":
    main()
