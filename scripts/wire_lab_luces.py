#!/usr/bin/env python3
"""
wire_lab_luces.py — iluminación de terror clase B en el laboratorio (L2 y
la arena de L3), pedida el 14/10. Arte: gen_lab_luces.py.

  - Capa nueva "Atmos" entre la de juego ("") y la UI: ahí van la sombra de
    las zonas a oscuras (LabSombra, ~55 %) y los conos de luz (LampGlow),
    por encima de la sombra. Las carcasas de los tubos (LampFixture) van en
    Decor, detrás de todo lo jugable.
  - Cada LampGlow tiene Mode (0 estable, 1 intermitente, 2 roto) y Seed.
    Parpadeo con ruido pseudoaleatorio por instancia, sin timers:
      h1 = ruido lento (2.5 Hz) -> ¿está "fallando" ahora?
      h2 = ruido rápido (16 Hz) -> prendido/apagado durante la falla
    intermitente: casi siempre prendido, ráfagas de parpadeo (~20 % del
    tiempo); roto: casi siempre apagado, destellos sueltos (~14 %).
  - La oscuridad es parcial a propósito: no tiene que esconder huecos,
    vidrios ni zombies (los bordes por cercanía siguen ayudando).
  - Sonido: zumbido en loop (canal de sonido 2) cuyo volumen sigue a la
    cercanía de Lio a un tubo PRENDIDO (si el tubo falla, el zumbido se corta
    con él); mudo en pausa, popup de nota, victoria y Game Over. Chispazo
    (pitch al azar) cada vez que un tubo cambia de estado cerca de Lio, con
    un mínimo de 0.12 s entre chispazos del mismo tubo (timer "Spark").

Idempotente (borra sus instancias y reemplaza su grupo). GDevelop CERRADO.
Requiere: python3 scripts/gen_lab_luces.py && python3 scripts/gen_sfx.py
Uso:  python3 scripts/wire_lab_luces.py   (desde la raíz del repo)
"""
import copy
import datetime
import json
import shutil

from gdevelop_cerrado import asegurar_gdevelop_cerrado

from wire_score_hud import act, comment, ev, put_object

GAME = "game/game.json"
GROUP = "Luces del laboratorio (wire_lab_luces.py)"
IMGS = ("lamp_fixture.png", "lamp_glow.png", "lab_sombra.png")
SOUNDS = ("sfx_zumbido.wav", "sfx_chispazo.wav")          # gen_sfx.py -> lab_sfx()
HUM_CHANNEL = "2"           # canal de SONIDO (los de música son otro espacio; la música usa el 1)
HUM_REACH, SPARK_REACH = 220, 240     # px horizontales desde el centro del cono (240 = media pantalla: solo suena lo que se ve)
CX = 65                     # centro del cono (lamp_glow mide 130 de ancho)
MINE = ("LampFixture", "LampGlow", "LabSombra")
GLOW_DX, GLOW_DY = -45, 3          # cono centrado bajo la carcasa (40 de ancho, cono 130)
STEADY, FLICKER, BROKEN = 0, 1, 2

LEVELS = {
    # techo = borde de arriba de la cámara (FixCamera), piso = tope del Ground
    "Level2": {
        "ceiling": -64, "screen_top": -65,
        "lamps": [(100, STEADY), (360, STEADY), (620, STEADY), (880, FLICKER),
                  (1140, STEADY), (1400, STEADY), (1660, FLICKER),
                  (1960, BROKEN),                       # pasillo del piso encerado, a oscuras
                  (2240, STEADY), (2500, FLICKER), (2780, STEADY),
                  (3250, FLICKER), (3560, BROKEN)],     # tramo final antes de la meta
        # (x0, x1, opacidad)
        "dark": [(1740, 2200, 140), (2940, 3800, 140)],
    },
    "Level3": {
        # desde el 18/10 el lab de L3 es solo el tramo de salida del recorrido
        # (wire_l3_recorrido.py: x −2140..−1770); la arena es la calle
        "ceiling": -24, "screen_top": -25,
        "lamps": [(-2040, FLICKER), (-1880, STEADY)],
        "dark": [(-2180, -1780, 90)],
    },
}


def sprite(name, image):
    return {"adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False, "variables": [], "effects": [],
            "behaviors": [],
            "animations": [{"name": "Idle", "useMultipleDirections": False,
                            "directions": [{"looping": False, "timeBetweenFrames": 1, "sprites": [{
                                "hasCustomCollisionMask": False, "image": image, "points": [],
                                "originPoint": {"name": "origine", "x": 0, "y": 0},
                                "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                                "customCollisionMask": []}]}]}]}


def inst(name, x, y, z, layer, w=None, h=None, ivars=()):
    return {"angle": 0, "customSize": w is not None, "width": w or 0, "height": h or 0,
            "layer": layer, "name": name, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": list(ivars)}


def add_layer(lay):
    if any(l["name"] == "Atmos" for l in lay["layers"]):
        return
    new = copy.deepcopy(next(l for l in lay["layers"] if l["name"] == "Decor"))   # sigue a la cámara
    new["name"] = "Atmos"
    base = next(k for k, l in enumerate(lay["layers"]) if l["name"] == "")
    lay["layers"].insert(base + 1, new)                                          # arriba del juego


def flicker_events():
    t = "TimeFromStart()"
    h1 = f"mod(floor({t} * 2.5) * 7919 + LampGlow.Variable(Seed) * 104729, 101)"
    h2 = f"mod(floor({t} * 16) * 6007 + LampGlow.Variable(Seed) * 7727, 101)"

    def cmp(expr, op, val):
        return act("BuiltinCommonInstructions::CompareNumbers", [expr, op, str(val)])

    def mode(m):
        return act("NumberObjectVariable", ["LampGlow", "Mode", "=", str(m)])

    def op(v):
        return [act("Opacity", ["LampGlow", "=", str(v)])]

    return {"type": "BuiltinCommonInstructions::ForEach", "object": "LampGlow",
            "objectsToPick": "LampGlow", "conditions": [], "actions": [], "events": [
                ev([mode(STEADY)], op(255)),
                ev([mode(FLICKER), cmp(h1, ">=", 20)], op(255)),
                ev([mode(FLICKER), cmp(h1, "<", 20), cmp(h2, "<", 45)], op(0)),
                ev([mode(FLICKER), cmp(h1, "<", 20), cmp(h2, ">=", 45)], op(255)),
                ev([mode(BROKEN), cmp(h1, ">=", 14)], op(0)),
                ev([mode(BROKEN), cmp(h1, "<", 14), cmp(h2, ">=", 55)], op(255)),
                ev([mode(BROKEN), cmp(h1, "<", 14), cmp(h2, "<", 55)], op(0)),
                *spark_events(),
            ]}


def sound_events(lay):
    """zumbido por cercanía a un tubo prendido + chispazo al cambiar de estado."""
    if not any(v["name"] == "LampNear" for v in lay["variables"]):
        lay["variables"].append({"name": "LampNear", "type": "number", "value": 0})
    pcx = "(Player.X() + Player.Width() / 2)"
    dist = f"abs(LampGlow.X() + {CX} - {pcx})"
    mute = ("(1 - min(1, Variable(Paused) + Variable(Over) + Variable(Won) "
            "+ Variable(NotaOpen)))")
    near_each = {"type": "BuiltinCommonInstructions::ForEach", "object": "LampGlow",
                 "objectsToPick": "LampGlow", "conditions": [], "actions": [], "events": [
                     ev([], [act("ModVarScene", ["LampNear", "=",
                                                 f"max(Variable(LampNear), clamp(1 - {dist} / {HUM_REACH}, 0, 1)"
                                                 " * LampGlow.Opacity() / 255)"])])]}
    return [
        ev([act("BuiltinCommonInstructions::Once", [])],
           [act("PlaySoundOnChannel", ["", "sfx_zumbido.wav", HUM_CHANNEL, "yes", "0", "1"]),
            act("ResetObjectTimer", ["LampGlow", '"Spark"'])]),
        ev([], [act("ModVarScene", ["LampNear", "=", "0"])]),
        near_each,
        ev([], [act("SetSoundChannelVolume", ["", HUM_CHANNEL, "=",
                                              f"GlobalVariable(SfxVolume) * (0.05 + 0.3 * Variable(LampNear)) * {mute}"])]),
    ]


def spark_events():
    """dentro del ForEach del parpadeo, después de fijar la opacidad."""
    pcx = "(Player.X() + Player.Width() / 2)"
    dist = f"abs(LampGlow.X() + {CX} - {pcx})"
    on = act("BuiltinCommonInstructions::CompareNumbers", ["LampGlow.Opacity()", ">", "0"])
    off = act("BuiltinCommonInstructions::CompareNumbers", ["LampGlow.Opacity()", "=", "0"])
    near = act("BuiltinCommonInstructions::CompareNumbers", [dist, "<", str(SPARK_REACH)])
    ready = act("ObjectTimer", ["LampGlow", '"Spark"', "0.12"])
    spark = [act("PlaySound", ["", "sfx_chispazo.wav", "no",
                               f"GlobalVariable(SfxVolume) * 0.6 * (1 - {dist} / {SPARK_REACH})",
                               "RandomFloatInRange(0.8, 1.3)"]),
             act("ResetObjectTimer", ["LampGlow", '"Spark"'])]
    prev = lambda v: act("NumberObjectVariable", ["LampGlow", "Prev", "=", str(v)])   # noqa: E731
    setp = lambda v: act("ModVarObjet", ["LampGlow", "Prev", "=", str(v)])            # noqa: E731
    return [
        ev([on, prev(0)], [setp(1)], [ev([near, ready], spark)]),
        ev([off, prev(1)], [setp(0)], [ev([near, ready], spark)]),
    ]


def wire(lay, cfg):
    add_layer(lay)
    put_object(lay, sprite("LampFixture", "lamp_fixture.png"))
    glow = sprite("LampGlow", "lamp_glow.png")
    glow["variables"] = [{"name": "Mode", "type": "number", "value": 0},
                         {"name": "Seed", "type": "number", "value": 0},
                         {"name": "Prev", "type": "number", "value": 1}]
    put_object(lay, glow)
    # la opacidad de instancia ("opacity" en numberProperties) el runtime la
    # ignora en los Sprite (quedaba en 255): va en la var Alpha y la aplica un evento
    sombra = sprite("LabSombra", "lab_sombra.png")
    sombra["variables"] = [{"name": "Alpha", "type": "number", "value": 140}]
    put_object(lay, sombra)
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in MINE]
    new = []
    for x0, x1, opacity in cfg["dark"]:
        new.append(inst("LabSombra", x0, cfg["screen_top"], 0, "Atmos", w=x1 - x0, h=270,
                        ivars=[{"name": "Alpha", "type": "number", "value": opacity}]))
    for k, (x, mode) in enumerate(cfg["lamps"], 1):
        new.append(inst("LampFixture", x, cfg["ceiling"], 50, "Decor"))
        new.append(inst("LampGlow", x + GLOW_DX, cfg["ceiling"] + GLOW_DY, 1, "Atmos",
                        ivars=[{"name": "Mode", "type": "number", "value": mode},
                               {"name": "Seed", "type": "number", "value": k}]))
    lay["instances"] += new
    lay["events"] = [e for e in lay["events"] if e.get("name") != GROUP]
    lay["events"].append({
        "type": "BuiltinCommonInstructions::Group", "name": GROUP, "source": "",
        "creationTime": 0, "folded": True, "color": {"b": 200, "g": 230, "r": 190},
        "events": [comment("Tubos del lab: Mode 0 estable, 1 intermitente, 2 roto. "
                           "Generado por wire_lab_luces.py."),
                   {"type": "BuiltinCommonInstructions::ForEach", "object": "LabSombra",
                    "objectsToPick": "LabSombra", "conditions": [], "actions": [],
                    "events": [ev([], [act("Opacity", ["LabSombra", "=", "LabSombra.Variable(Alpha)"])])]},
                   flicker_events(),
                   *sound_events(lay)]})
    return len(cfg["lamps"]), len(cfg["dark"])


def main():
    asegurar_gdevelop_cerrado()
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    res = g["resources"]["resources"]
    for img in IMGS:
        if not any(r["name"] == img for r in res):
            res.append({"file": f"assets/Lab/{img}", "kind": "image", "metadata": "", "name": img,
                        "smoothed": False, "userAdded": True})
    for snd in SOUNDS:
        if not any(r["name"] == snd for r in res):
            res.append({"file": f"assets/audio/{snd}", "kind": "audio", "metadata": "", "name": snd,
                        "preloadAsMusic": False, "preloadAsSound": True, "preloadInCache": True,
                        "userAdded": True})
    lays = {l["name"]: l for l in g["layouts"]}
    for name, cfg in LEVELS.items():
        n, z = wire(lays[name], cfg)
        print(f"{name}: {n} tubos, {z} zona(s) a oscuras")
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
