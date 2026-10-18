#!/usr/bin/env python3
# pyright: reportOptionalSubscript=false, reportIndexIssue=false
"""
gen_l3_ciudad_capas.py  —  dos filas de edificios entre la silueta lejana de L1 y
las fachadas de la vereda (Nivel 3, 18/10). Pedido del usuario: "una fila o dos
más de edificios en dos capas hacia atrás, con más detalle; en el centro hay
muchos edificios, tiene que dar la sensación de estar entre edificios".

Cada fila es una tira de 1024 px que se repite en X sin que se note la unión
(los edificios se reparten para que el último termine justo en el borde). La
fila de abajo de la imagen apoya en el piso (y = 150 del mundo); lo que pasa
de y = −25 queda fuera de la cámara.

  ciudad_media.png    1024x200  la fila de atrás de las fachadas: edificios
                                clásicos con cornisas y CÚPULAS, medianeras con
                                publicidades despintadas, una torre vidriada;
                                ventanas prendidas sueltas y alguna en llamas
  ciudad_capas.json             los edificios de cada tira (tipo, x, ancho, techo):
                                ahí se apoyan los incendios (wire_l3_luces.py)
  ciudad_trasera.png  1024x210  torres altas con grilla de ventanas, tanques de
                                agua y antenas con luz roja; más azulada y oscura
                                (la distancia le quita contraste)

Las dos van más oscuras que las fachadas para no competir con el plano de juego
(zombies, virus). Dejan algún hueco entre torres para que se vea la luna.
Pillow, tramado Bayer, semillas fijas.
Uso:  python3 scripts/gen_l3_ciudad_capas.py   (crea en game/assets/City/)
"""
from PIL import Image, ImageDraw
import json
import random
import os

OUT = "game/assets/City"
os.makedirs(OUT, exist_ok=True)
T = (0, 0, 0, 0)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
FIRE = [(150, 60, 30, 255), (220, 110, 40, 255), (255, 190, 90, 255)]
RED_LIGHT = (230, 60, 60, 255)
OUTL = (14, 14, 22, 255)

# paletas por profundidad: pared (sombra, base, luz, canto), vidrio, ventana prendida
DEPTH = {
    "media": {"wall": [(36, 36, 48), (50, 50, 64), (64, 64, 80), (84, 84, 102)],
              "glass": (16, 20, 34), "lit": (186, 146, 86), "lit_dk": (130, 96, 56),
              "tv": (90, 124, 170), "p_lit": 0.14},
    "trasera": {"wall": [(26, 30, 44), (34, 38, 54), (44, 50, 68), (58, 64, 84)],
                "glass": (14, 18, 30), "lit": (140, 116, 80), "lit_dk": (100, 82, 58),
                "tv": (70, 96, 140), "p_lit": 0.09},
}


def rgba(c):
    return tuple(c) + (255,)


class Strip:
    def __init__(self, w, h, depth, seed):
        self.img = Image.new("RGBA", (w, h), T)
        self.d = ImageDraw.Draw(self.img)
        self.px = self.img.load()
        self.p = DEPTH[depth]
        self.rnd = random.Random(seed)
        self.W, self.H = w, h

    def wall(self, x0, y0, x1, tone_shift=0):
        """paño de pared hasta el piso, luz de luna en el canto izquierdo."""
        wl = self.p["wall"]
        for y in range(y0, self.H):
            for x in range(x0, x1):
                t = (y - y0) / max(1, self.H - y0)
                i = 1 if t * 16 > BAYER[y % 4][x % 4] + 4 else 2
                i = max(0, min(3, i + tone_shift))
                self.px[x % self.W, y] = rgba(wl[i])
        self.d.line([(x0, y0), (x0, self.H)], fill=rgba(wl[3]))
        self.d.line([(x1 - 1, y0), (x1 - 1, self.H)], fill=rgba(wl[0]))
        self.d.line([(x0, y0), (x1 - 1, y0)], fill=OUTL)

    def win(self, x, y, w, h):
        p, r = self.p, self.rnd.random()
        if r < p["p_lit"] * 0.08:                                # en llamas (pocas)
            self.d.rectangle([x, y, x + w - 1, y + h - 1], fill=FIRE[1])
            self.d.rectangle([x, y + h // 2, x + w - 1, y + h - 1], fill=FIRE[2])
            self.d.line([(x, y - 1), (x + w - 1, y - 1)], fill=FIRE[0])    # hollín
            self.d.line([(x, y - 2), (x + w - 2, y - 2)], fill=rgba((30, 26, 30)))
            return
        if r < p["p_lit"]:
            c = rgba(p["lit"]) if self.rnd.random() < 0.8 else rgba(p["tv"])
        else:
            c = rgba(p["glass"])
        self.d.rectangle([x, y, x + w - 1, y + h - 1], fill=c)
        if c == rgba(p["lit"]) and h >= 4:
            self.d.line([(x, y + h - 2), (x + w - 1, y + h - 2)], fill=rgba(p["lit_dk"]))

    # --- tipos de edificio ---
    def clasico(self, x0, w, top):
        """8-12 pisos: cornisas, ventanas altas con balconcito, cúpula en algunos."""
        wl = self.p["wall"]
        self.wall(x0, top, x0 + w)
        self.d.rectangle([x0 - 1, top, x0 + w, top + 2], fill=rgba(wl[3]))          # cornisa de remate
        y = top + 8
        floor = 0
        while y < self.H - 8:
            for x in range(x0 + 4, x0 + w - 5, 9):
                self.win(x, y, 5, 8)
                if floor % 2 == 0:
                    self.d.line([(x - 1, y + 8), (x + 5, y + 8)], fill=rgba(wl[0]))   # balconcito
            if floor % 3 == 2:
                self.d.line([(x0, y + 11), (x0 + w - 1, y + 11)], fill=rgba(wl[3]))    # cornisa intermedia
            y += 13
            floor += 1
        if self.rnd.random() < 0.6 and w >= 30:                                       # cúpula porteña
            cx, r = x0 + w // 2, min(9, w // 4)
            self.d.rectangle([cx - r - 2, top - 5, cx + r + 2, top], fill=rgba(wl[2]))  # tambor
            self.d.pieslice([cx - r, top - 5 - r, cx + r, top - 5 + r], 180, 360, fill=rgba((54, 70, 76)))
            self.d.arc([cx - r, top - 5 - r, cx + r, top - 5 + r], 180, 270, fill=rgba((84, 104, 110)))
            self.d.line([(cx, top - 5 - r), (cx, top - 12 - r)], fill=rgba(wl[3]))   # aguja

    def medianera(self, x0, w, top):
        """muro ciego con una publicidad vieja despintada (porteñísimo)."""
        wl = self.p["wall"]
        self.wall(x0, top, x0 + w, tone_shift=-1)
        ax0, ay0 = x0 + 4, top + 10
        ax1, ay1 = x0 + w - 5, top + min(46, (self.H - top) // 3)
        cols = [(120, 56, 50), (60, 90, 120), (150, 130, 60)]
        c = self.rnd.choice(cols)
        for y in range(ay0, ay1):
            for x in range(ax0, ax1):
                if BAYER[y % 4][x % 4] < 9:                                       # despintada
                    self.px[x, y] = rgba(tuple(int(v * 0.55) for v in c))
        self.d.rectangle([ax0 + 4, ay0 + 5, ax0 + (ax1 - ax0) // 2, ay0 + 9], fill=rgba(tuple(int(v * 0.35) for v in c)))
        self.d.line([(x0 + 2, top + 2), (x0 + 2, self.H)], fill=rgba(wl[0]))      # caño de bajada

    def vidriada(self, x0, w, top):
        """torre de oficinas: grilla de vidrio azul oscuro, pocos pisos prendidos."""
        g = (24, 32, 52) if self.p is DEPTH["media"] else (20, 26, 42)
        for y in range(top, self.H):
            for x in range(x0, x0 + w):
                self.px[x, y] = rgba(g)
        for y in range(top + 3, self.H, 5):
            self.d.line([(x0, y), (x0 + w - 1, y)], fill=rgba(tuple(v + 10 for v in g)))
            if self.rnd.random() < 0.12:                                          # piso de oficinas prendido
                self.d.line([(x0 + 1, y + 2), (x0 + w - 2, y + 2)], fill=rgba(self.p["lit_dk"]))
        for x in range(x0 + 3, x0 + w, 6):
            self.d.line([(x, top), (x, self.H)], fill=rgba(tuple(v + 6 for v in g)))
        for k in range(3):                                                        # reflejo diagonal
            self.d.line([(x0 + 2 + k * 3, top + 4), (x0 + 10 + k * 3, top + 20)], fill=rgba(tuple(v + 22 for v in g)))
        self.d.line([(x0, top), (x0 + w - 1, top)], fill=OUTL)

    def torre(self, x0, w, top):
        """torre de departamentos: grilla de ventanas chicas, techo con tanque y antena."""
        wl = self.p["wall"]
        self.wall(x0, top, x0 + w)
        for y in range(top + 5, self.H - 4, 7):
            for x in range(x0 + 3, x0 + w - 3, 5):
                self.win(x, y, 3, 4)
        # techo: tanque de agua sobre patas, antena con luz roja
        if self.rnd.random() < 0.7:
            tx = x0 + self.rnd.randint(3, max(3, w - 14))
            self.d.rectangle([tx, top - 9, tx + 9, top - 4], fill=rgba(wl[1]))
            self.d.line([(tx, top - 9), (tx + 9, top - 9)], fill=rgba(wl[3]))
            for lx in (tx + 1, tx + 8):
                self.d.line([(lx, top - 4), (lx, top - 1)], fill=rgba(wl[0]))
        if self.rnd.random() < 0.6:
            ax = x0 + w - 5
            self.d.line([(ax, top), (ax, top - 16)], fill=rgba(wl[3]))
            self.d.line([(ax - 3, top - 10), (ax + 3, top - 10)], fill=rgba(wl[3]))
            self.px[ax, top - 17] = RED_LIGHT


def build(depth, w, h, seed, kinds, top_range, gaps):
    s = Strip(w, h, depth, seed)
    x = 0
    plan = []
    while x < w:
        if gaps and s.rnd.random() < gaps:                                         # hueco (se ve la luna)
            gw = s.rnd.randint(10, 22)
            x += gw
            continue
        bw = s.rnd.randint(26, 58)
        if w - (x + bw) < 26:                                                     # que el último cierre justo
            bw = w - x
        plan.append((s.rnd.choice(kinds), x, bw, s.rnd.randint(*top_range)))
        x += bw
    for kind, x0, bw, top in plan:
        getattr(s, kind)(x0, bw, top)
    return s.img, plan


def main():
    # trasera: torres altas (la cámara ve desde y = −25 → fila 25 en una imagen de 210 que
    # termina en el piso: fila 0 = y −60)
    tras, plan_t = build("trasera", 1024, 210, 77, ["torre", "torre", "vidriada", "clasico"], (20, 80), 0.10)
    tras.save(f"{OUT}/ciudad_trasera.png")
    # media: más baja y con más detalle (fila 0 = y −50)
    med, plan_m = build("media", 1024, 200, 91, ["clasico", "clasico", "medianera", "torre", "vidriada"], (40, 100), 0.05)
    med.save(f"{OUT}/ciudad_media.png")
    # los edificios de cada tira (para apoyar los incendios de wire_l3_luces.py sobre un
    # techo de verdad): tipo, x en la tira, ancho y fila del techo
    with open(f"{OUT}/ciudad_capas.json", "w") as f:
        json.dump({"trasera": {"alto": 210, "edificios": plan_t},
                   "media": {"alto": 200, "edificios": plan_m}}, f, indent=1)
    print("ciudad_trasera (1024x210), ciudad_media (1024x200), ciudad_capas.json  ->", OUT)


if __name__ == "__main__":
    main()
