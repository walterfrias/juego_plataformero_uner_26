#!/usr/bin/env python3
"""
gen_mapas_gdd.py — mapas de los niveles para el walkthrough del GDD final
(Thompson, pág. 107: "mapas de niveles (2D y/o mapa de bloques),
localización de los PNJ, encuentros").

Lee game/game.json (no lo modifica) y arma, por nivel:
  - el arte real de la capa de juego y del decorado (más la pared del lab en
    L2 y las fachadas en L3), sin cielo, luces ni interfaz;
  - encima, el "mapa de bloques": plataformas macizas (celeste), atravesables
    (amarillo, raya arriba) y escaleras (verde);
  - una franja de etiquetas arriba con flechas a cada cosa: inicio,
    checkpoints, antídotos, notas, mochila, zombies, virus, mecánicas,
    peligros, jefe y meta.
El nivel se corta en tiras parejas de hasta TIRA px, apiladas, para que entre
en una página ("cortes" fuerza un corte en una x del juego).

Salida: gdd_final/mapas/<Nivel>.png, cada tira en <Nivel>_<n>.png (para el
PDF) y <Nivel>_completo.png (una sola tira a escala 1, de referencia).
Uso:  python3 scripts/gen_mapas_gdd.py [Level1 Level2 Level3]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

GAME = "game/game.json"
OUT = "gdd_final/mapas"
ESC = 2          # escala del dibujo (pixel art)
TIRA = 640       # ancho máximo de cada tira, en px del juego
FONT = "/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono-Bold.ttf"
FONDO = (24, 27, 40)

# capas que se dibujan (de atrás para adelante), recorte horizontal y
# borde de abajo (y1: lo que hay más abajo es río / subsuelo sin juego)
NIVELES = {
    "Level1": {"capas": ["Decor", ""], "x": (0, 2600), "y1": 215},
    "Level2": {"capas": ["BG_far", "Decor", ""], "x": (0, 3800), "y1": 236},
    "Level3": {"capas": ["BG_near", "Decor", ""], "x": (-2140, 480), "y1": 270,
               "cortes": [0]},   # la arena (0..480) va en su propia tira
}

# objetos que no aportan al mapa: brillos, luces, ayudas de la interfaz
NO_DIBUJAR = {"PlatEdge", "ContencionGlow", "LuzFuegoCalle", "LuzSirena", "Chispa",
              "PisaloText", "MochilaWorn", "HumoHorda", "Destello", "LampGlow",
              "LabVentanaLuz"}
NO_DIBUJAR_NIVEL = {"Level3": {"Estante"}}   # invisibles: van solo como bloque
SIN_ETIQUETA_NIVEL = {"Level3": {"ContencionRota"}}   # en L3 los tubos rotos son decorado

COL = {
    "inicio": (240, 240, 240), "check": (200, 200, 220), "antidoto": (120, 220, 90),
    "nota": (240, 214, 150), "mochila": (255, 150, 60), "zombie": (235, 80, 80),
    "virus": (230, 110, 210), "mecanica": (110, 180, 255), "peligro": (255, 190, 40),
    "jefe": (255, 60, 60), "meta": (240, 240, 240),
}
BLOQUE = {"solida": (90, 210, 255), "jumpthru": (255, 220, 90), "escalera": (110, 230, 120)}

# etiqueta para las mecánicas y los peligros (una por grupo de instancias cercanas)
MECANICAS = {
    "Colchon": "COLCHÓN", "Poste": "POSTE", "Cable": "CABLES", "Piston": "PISTONES",
    "AirFlow": "DUCTO", "WetFloor": "PISO ENCERADO", "Gabinete": "GABINETE",
    "ToldoRebote": "TOLDO", "Vapor": "VAPOR", "Marquesina": "MARQUESINA",
    "PuenteA": "PUENTE", "Toldo": "TOLDO", "EscaleraIncendio": "ESCALERA",
}
PELIGROS = {
    "GapWater": "AGUA", "RebarSpikes": "HIERROS", "BarbedWire": "ALAMBRE",
    "GlassSpikes": "VIDRIOS", "PozoFondo": "POZO", "Charco": "CHARCO",
    "ContencionRota": "TUBO ROTO",
}


def cargar():
    g = json.load(open(GAME, encoding="utf-8"))
    res = {r["name"]: r["file"] for r in g["resources"]["resources"]}
    return g, res


_cache = {}


def imagen(res, nombre):
    if nombre not in _cache:
        p = os.path.join("game", res[nombre])
        _cache[nombre] = Image.open(p).convert("RGBA") if os.path.exists(p) else None
    return _cache[nombre]


def tamano_y_dibujo(obj, ins, res):
    """(w, h, imagen ya del tamaño de la instancia, dx, dy) o None."""
    t = obj["type"]
    if t == "Sprite":
        sp = obj["animations"][0]["directions"][0]["sprites"][0]
        im = imagen(res, sp["image"])
        if im is None:
            return None
        o = sp["originPoint"]
        w, h = (ins["width"], ins["height"]) if ins.get("customSize") else im.size
        if (int(w), int(h)) != im.size:
            im = im.resize((max(1, int(w)), max(1, int(h))), Image.NEAREST)
        if ins.get("angle"):
            im = im.rotate(-ins["angle"], expand=True, resample=Image.NEAREST)
        return w, h, im, -o["x"], -o["y"]
    if t == "TiledSpriteObject::TiledSprite":
        tex = imagen(res, obj["texture"])
        if tex is None:
            return None
        w, h = (ins["width"], ins["height"]) if ins.get("customSize") else (obj["width"], obj["height"])
        w, h = max(1, int(w)), max(1, int(h))
        im = Image.new("RGBA", (w, h))
        for yy in range(0, h, tex.size[1]):
            for xx in range(0, w, tex.size[0]):
                im.paste(tex, (xx, yy))
        return w, h, im, 0, 0
    return None


def tipo_plataforma(obj):
    for b in obj.get("behaviors", []):
        if b["type"] == "PlatformBehavior::PlatformBehavior":
            pt = b.get("platformType") or "NormalPlatform"
            return {"Jumpthru": "jumpthru", "Ladder": "escalera"}.get(pt, "solida")
    return None


def checkpoints(lay):
    xs = []

    def walk(evs):
        for e in evs:
            yield e
            yield from walk(e.get("events", []))
    for e in walk(lay["events"]):
        for a in e.get("actions", []):
            if a["type"]["value"] == "ModVarScene" and a["parameters"][0] == "CheckX":
                try:
                    xs.append(float(a["parameters"][2]))
                except ValueError:
                    pass
    return sorted(set(xs))


def agrupar(items, dist=80):
    """junta instancias del mismo tipo que están cerca (una etiqueta por grupo)."""
    grupos = []
    for x, y, w, h in sorted(items):
        if grupos and x - grupos[-1][1] < dist:
            g = grupos[-1]
            g[1] = max(g[1], x + w)
            g[2] = min(g[2], y)
        else:
            grupos.append([x, x + w, y])
    return [((a + b) / 2, y) for a, b, y in grupos]


def generar(nivel, g, res):
    cfg = NIVELES[nivel]
    lay = next(l for l in g["layouts"] if l["name"] == nivel)
    objs = {o["name"]: o for o in lay["objects"]}
    orden_capas = [l["name"] for l in lay["layers"]]
    x0, x1 = cfg["x"]
    skip = NO_DIBUJAR | NO_DIBUJAR_NIVEL.get(nivel, set())

    # --- arte y bloques (a escala 1) ---
    dibujos, bloques, cosas = [], [], []
    for ins in lay["instances"]:
        obj = objs.get(ins["name"])
        if obj is None:
            continue
        td = tamano_y_dibujo(obj, ins, res)
        if td is None:
            continue
        w, h, im, dx, dy = td
        x, y = ins["x"] + dx, ins["y"] + dy
        if ins["layer"] == "":
            cosas.append((ins, x, y, w, h))
            pt = tipo_plataforma(obj)
            if pt:
                bloques.append((pt, x, y, w, h))
        if ins["layer"] in cfg["capas"] and ins["name"] not in skip:
            dibujos.append((orden_capas.index(ins["layer"]), ins.get("zOrder", 0), x, y, im))

    # alto útil: del tope de lo jugable al fondo del suelo
    ys = [y for _, x, y, w, h in bloques if x + w > x0 and x < x1]
    ys += [c[2] for c in cosas if c[0]["name"].startswith(("Zombie", "Antidoto", "NotaPick", "Virus"))]
    y0 = max(-40, int(min(ys)) - 24)
    y1 = cfg["y1"]
    W, H = x1 - x0, y1 - y0

    mapa = Image.new("RGBA", (W, H), FONDO + (255,))
    for _, _, x, y, im in sorted(dibujos, key=lambda d: (d[0], d[1])):
        mapa.paste(im, (int(x - x0), int(y - y0)), im)
    grande = mapa.resize((W * ESC, H * ESC), Image.NEAREST)
    d = ImageDraw.Draw(grande, "RGBA")
    X = lambda x: (x - x0) * ESC
    Y = lambda y: (y - y0) * ESC

    for pt, x, y, w, h in bloques:
        c = BLOQUE[pt]
        if pt == "solida":
            d.rectangle([X(x), Y(y), X(x + w) - 1, Y(y + h) - 1], outline=c + (230,), width=2)
            d.rectangle([X(x), Y(y), X(x + w) - 1, Y(y) + 3], fill=c + (255,))
        elif pt == "jumpthru":
            d.rectangle([X(x), Y(y), X(x + w) - 1, Y(y) + 3], fill=c + (255,))
        else:
            for xx in range(int(X(x)), int(X(x + w)), 6):
                d.line([xx, Y(y), xx, Y(y + h)], fill=c + (150,), width=1)

    # --- marcadores: (x del juego, y del juego, texto, color) ---
    marcas = []
    player = next((c for c in cosas if c[0]["name"] == "Player"), None)
    if player:
        marcas.append((player[1] + player[3] / 2, player[2], "INICIO", COL["inicio"]))
    for n, cx in enumerate([c for c in checkpoints(lay) if x0 < c < x1], start=1):
        for yy in range(0, H * ESC, 10):
            d.line([X(cx), yy, X(cx), yy + 5], fill=COL["check"] + (170,), width=2)
        marcas.append((cx, y0 + 8, f"C{n}", COL["check"]))
    anti = sorted((c for c in cosas if c[0]["name"] == "Antidoto"), key=lambda c: c[1])
    for n, (_, x, y, w, h) in enumerate(anti, start=1):
        marcas.append((x + w / 2, y, f"A{n}", COL["antidoto"]))
    for ins, x, y, w, h in cosas:
        nm = ins["name"]
        if nm == "NotaPick":
            nid = next((v["value"] for v in ins.get("initialVariables", []) if v["name"] == "Id"), "?")
            marcas.append((x + w / 2, y, f"N{nid}", COL["nota"]))
        elif nm == "Mochila":
            marcas.append((x + w / 2, y, "MOCHILA", COL["mochila"]))
        elif nm == "Meta":
            marcas.append((x + w / 2, y, "META", COL["meta"]))
        elif nm == "PacienteZero":
            marcas.append((x + w / 2, y, "JEFE", COL["jefe"]))
        elif nm.startswith("Zombie") and not nm.startswith("ZombiesFondo"):
            marcas.append((x + w / 2, y, "Z", COL["zombie"]))
        elif nm.startswith("Virus") and nm[5:].isdigit():
            marcas.append((x + w / 2, y, "V", COL["virus"]))
    horda = [(x, y, w, h) for ins, x, y, w, h in cosas if ins["name"].startswith("HordaZombie")]
    for cx, cy in agrupar(horda, 200):
        marcas.append((cx, cy, "HORDA", COL["zombie"]))
    for tabla, color in ((MECANICAS, COL["mecanica"]), (PELIGROS, COL["peligro"])):
        for nm, txt in tabla.items():
            if nm in SIN_ETIQUETA_NIVEL.get(nivel, set()):
                continue
            items = [(x, y, w, h) for ins, x, y, w, h in cosas if ins["name"] == nm]
            for cx, cy in agrupar(items):
                marcas.append((cx, cy, txt, color))
    marcas = [m for m in marcas if x0 <= m[0] <= x1]

    # --- tiras con su franja de etiquetas ---
    font = ImageFont.truetype(FONT, 15)
    tiras = []
    bordes = [0] + [c - x0 for c in cfg.get("cortes", [])] + [W]
    tramos = []
    for a, b in zip(bordes, bordes[1:]):
        n = -(-(b - a) // TIRA)
        paso = -(-(b - a) // n)
        tramos += [(t, min(b, t + paso)) for t in range(a, b, paso)]
    for t0, t1 in tramos:
        enla = sorted((m for m in marcas if t0 <= m[0] - x0 < t1), key=lambda m: m[0])
        filas = []   # x final ocupado por fila
        pos = []
        for gx, gy, txt, c in enla:
            tw = d.textlength(txt, font=font) + 10
            lx = max(2, min((gx - x0 - t0) * ESC - tw / 2, (t1 - t0) * ESC - tw - 2))
            fila = next((i for i, fin in enumerate(filas) if lx > fin + 4), None)
            if fila is None:
                filas.append(0)
                fila = len(filas) - 1
            filas[fila] = lx + tw
            pos.append((fila, lx, tw, gx, gy, txt, c))
        lane = 8 + 22 * max(1, len(filas))
        tira = Image.new("RGBA", ((t1 - t0) * ESC, lane + H * ESC), (14, 16, 24, 255))
        tira.paste(grande.crop((t0 * ESC, 0, t1 * ESC, H * ESC)), (0, lane))
        td = ImageDraw.Draw(tira, "RGBA")
        for fila, lx, tw, gx, gy, txt, c in pos:
            ty = 4 + 22 * fila
            ax = (gx - x0 - t0) * ESC
            td.line([ax, ty + 18, ax, lane + Y(gy) - 2], fill=c + (200,), width=2)
            td.polygon([(ax - 4, lane + Y(gy) - 8), (ax + 4, lane + Y(gy) - 8), (ax, lane + Y(gy) - 1)],
                       fill=c + (255,))
            td.rounded_rectangle([lx, ty, lx + tw, ty + 18], 4, fill=(14, 16, 24, 235), outline=c + (255,), width=2)
            td.text((lx + 5, ty + 1), txt, font=font, fill=c + (255,))
        # regla de x del juego (cada 100 px) para ubicarse con el texto
        for gx in range((x0 + t0) // 100 * 100, x0 + t1, 100):
            if gx >= x0 + t0:
                px = (gx - x0 - t0) * ESC
                td.line([px, tira.size[1] - 8, px, tira.size[1]], fill=(255, 255, 255, 120), width=1)
                td.text((px + 2, tira.size[1] - 20), str(gx), font=ImageFont.truetype(FONT, 11),
                        fill=(255, 255, 255, 140))
        tiras.append(tira)

    os.makedirs(OUT, exist_ok=True)
    ancho = max(t.size[0] for t in tiras)
    final = Image.new("RGBA", (ancho, sum(t.size[1] for t in tiras) + 12 * (len(tiras) - 1)), (255, 255, 255, 0))
    yy = 0
    for t in tiras:
        final.paste(t, (0, yy))
        yy += t.size[1] + 12
    final.save(f"{OUT}/{nivel}.png")
    for k, t in enumerate(tiras, start=1):   # una por una, para el PDF (no se parten entre páginas)
        t.save(f"{OUT}/{nivel}_{k}.png")
    mapa.save(f"{OUT}/{nivel}_completo.png")
    print(f"{nivel}: {len(tiras)} tiras, {len(marcas)} marcas, x {x0}..{x1}, y {y0}..{y1}")


def main():
    g, res = cargar()
    for nivel in (sys.argv[1:] or list(NIVELES)):
        generar(nivel, g, res)


if __name__ == "__main__":
    main()
