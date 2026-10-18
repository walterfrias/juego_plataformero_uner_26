#!/usr/bin/env python3
"""
wire_noche_n1.py — iluminación de la noche del Nivel 1 (pedida el 15/10:
se veía claro y con poco contraste entre el fondo y lo jugable). Idea:
oscurecer todo y devolver la luz solo donde importa. Arte: gen_noche_n1.py
y gen_luz_luna.py; sonido: gen_sfx.py -> fuego_sfx().

A. Fondo con profundidad
  - NocheCielo: degradé de cielo (BG_farthest, fijo en pantalla).
  - Efecto Adjustment "Noche" sobre CityFarthest / CityFar / CityNear /
    Obelisco: cuanto más lejos, más oscuro y desaturado.
  - NocheNiebla (3 tiras) sobre la base de cada skyline, con el parallax de
    su capa y una deriva lenta. Opacidad en la var Alpha (el runtime ignora
    la de instancia en los Sprite; acá es TiledSprite, pero queda igual que
    LabSombra).
  - NocheNubes delante de la Luna, a la deriva.
B. Fuego
  - Tachos con fuego (NocheFuego animado + NocheFuegoGlow en la capa Atmos,
    que titila). Los 2 tachos que había más los de EXTRA_TACHOS.
  - Incendios lejanos (NocheIncendio + NocheHumo) detrás del skyline, con
    parallax como el Obelisco.
  - Crepitar en loop (canal de sonido 3) según la cercanía a un fuego; mudo
    en pausa, nota, victoria y Game Over.
  - NocheFarolCono: cono de luz de sodio de cada farol (uno falla).
C. Luna horneada
  - Los props de Level1 pasan a usar las copias *_luna.png (gen_luz_luna.py).
  - Tinte frío (ChangeColor) sobre Lio y los zombies que se vuelve cálido
    cerca de un fuego (var de escena NocheCalor para Lio).

NocheCalor también marca el grupo como "solo Level1" para wire_levels23.py
(L1_ONLY_VARS): así un --force no copia el tinte al laboratorio.

Idempotente (borra sus objetos/instancias y reemplaza su grupo). GDevelop
CERRADO. Crea la capa Atmos si no existe (como wire_lab_luces.py).
Requiere: gen_noche_n1.py, gen_luz_luna.py, gen_sfx.py
Uso:  python3 scripts/wire_noche_n1.py   (desde la raíz del repo)
"""
import copy
import datetime
import json
import shutil

from gen_luz_luna import SOURCES as LUNA_SOURCES, out_name
from wire_lab_luces import add_layer, inst, sprite
from wire_score_hud import act, comment, ev, put_object

GAME = "game/game.json"
SCENE = "Level1"
GROUP = "Noche: niebla, fuego y luna (wire_noche_n1.py)"
CAM = 'CameraCenterX("")'
CAM0 = 140                    # centro de cámara al arrancar (igual que wire_parallax.py)
W = 480
T = "TimeFromStart()"
FIRE_CHANNEL = "3"            # canal de SONIDO (el 2 es el zumbido del lab)
NOCHE = "assets/N1/Noche"

MINE = ("NocheCielo", "NocheNubes", "NocheNiebla", "NocheIncendio", "NocheHumo",
        "NocheFuego", "NocheFuegoGlow", "NocheFarolCono")

# --- A. Adjustment por objeto (lejos = más oscuro y gris)
ADJUST = {"CityFarthest": dict(brightness=0.62, saturation=0.55, contrast=0.8),
          "CityFar": dict(brightness=0.7, saturation=0.65, contrast=0.85),
          "CityNear": dict(brightness=0.78, saturation=0.8, contrast=1.0),
          "Obelisco": dict(brightness=0.68, saturation=0.6, contrast=0.9),
          # la cara del muro y el río dan al jugador, de espaldas a la luna: en sombra
          "Embankment": dict(brightness=0.62, saturation=0.8, contrast=1.0),
          "DrainPipe": dict(brightness=0.7, saturation=0.8, contrast=1.0),
          "River": dict(brightness=0.75, saturation=0.9, contrast=1.0),
          "GapWater": dict(brightness=0.75, saturation=0.9, contrast=1.0)}
# niebla: (capa, y, z, f de parallax, deriva px/s, opacidad)
NIEBLAS = [("BG_farthest", 30, 3, 0.12, 2.0, 170),
           ("BG_far", 58, 2, 0.30, 3.5, 130),
           ("BG_near", 78, 1, 0.55, 5.0, 70)]
NUBES = ("BG_farthest", -82, 4, 0.02, 3.0)          # capa, y, z, f, deriva

# --- B. Fuego
EXTRA_TACHOS = [(655, 92), (1415, 92), (2165, 92), (2410, 92)]
FIRE_REACH = 160             # px: hasta dónde se oye el fuego
WARM_REACH = 70              # px: hasta dónde entibia el tinte
# incendios lejanos: x en pantalla al arrancar (con f=0.2 cruzan ~470 px en el nivel)
INCENDIOS = [130, 420, 700]
INC_F, INC_Y = 0.2, -14
# conos: los faroles fallan si están en FLICKER (x de la instancia de Farol)
FLICKER_FAROLES = {526}

# --- C. Tinte
COLD = (185, 198, 240)
WARM = (255, 222, 182)


def res_image(res, name, file):
    if not any(r["name"] == name for r in res):
        res.append({"file": file, "kind": "image", "metadata": "", "name": name,
                    "smoothed": False, "userAdded": True})


def anim_sprite(name, images, dt):
    o = sprite(name, images[0])
    d = o["animations"][0]["directions"][0]
    d.update(looping=True, timeBetweenFrames=dt)
    d["sprites"] = [dict(copy.deepcopy(d["sprites"][0]), image=i) for i in images]
    return o


def tiled(name, texture, w, h):
    return {"assetStoreId": "", "height": h, "name": name, "texture": texture,
            "type": "TiledSpriteObject::TiledSprite", "width": w, "variables": [],
            "effects": [], "behaviors": []}


def adjustment(brightness, saturation, contrast):
    return {"name": "Noche", "effectType": "Adjustment",
            "doubleParameters": {"gamma": 1, "saturation": saturation, "contrast": contrast,
                                 "brightness": brightness, "red": 1, "green": 1, "blue": 1,
                                 "alpha": 1},
            "stringParameters": {}, "booleanParameters": {}}


def var(name, value):
    return {"name": name, "type": "number", "value": value}


def moonlight(g, lay):
    """los props de Level1 pasan a las copias *_luna.png."""
    res = g["resources"]["resources"]
    by_file = {r["file"]: r["name"] for r in res}
    swap = {}
    for src in LUNA_SOURCES:
        name = by_file[src]
        new = name[:-4] + "_luna.png"
        res_image(res, new, out_name(src))
        swap[name] = new
    n = 0
    for o in lay["objects"]:
        if o["type"] == "TiledSpriteObject::TiledSprite" and o["texture"] in swap:
            o["texture"] = swap[o["texture"]]
            n += 1
        for a in o.get("animations", []):
            for d in a["directions"]:
                for s in d["sprites"]:
                    if s["image"] in swap:
                        s["image"] = swap[s["image"]]
                        n += 1
    return n


def tint(color_expr_r, color_expr_g, color_expr_b):
    return (f'ToString(round({color_expr_r})) + ";" + ToString(round({color_expr_g})) '
            f'+ ";" + ToString(round({color_expr_b}))')


def tint_for(w):
    return tint(*(f"{c} + ({h} - {c}) * {w}" for c, h in zip(COLD, WARM)))


def warmth_expr(x_expr, fires, reach=WARM_REACH):
    """cercanía (0..1) según la X: el fuego más cercano manda (no se mueven)."""
    terms = [f"clamp(1 - abs({x_expr} - {fx}) / {reach}, 0, 1)" for fx in fires]
    out = terms[0]
    for t in terms[1:]:
        out = f"max({out}, {t})"
    return out


def events(fires):
    def cmp(expr, op, val):
        return act("BuiltinCommonInstructions::CompareNumbers", [expr, op, str(val)])

    def xoff(obj, f, drift):
        return act("TiledSpriteObject::XOffset",
                   [obj, "=", f"round(-{1 - f:.2f} * {CAM} + {T} * {drift})"])

    ev_out = [comment("Noche del Nivel 1: niebla y nubes a la deriva, fuegos que titilan, "
                      "conos de farol, tinte frío de luna que se entibia cerca del fuego. "
                      "Generado por wire_noche_n1.py.")]

    # --- A: cielo fijo en pantalla, nubes y nieblas con parallax + deriva
    acts = [act("TiledSpriteObject::XOffset", ["NocheCielo", "=", f"round(-{CAM})"]),
            xoff("NocheNubes", NUBES[3], NUBES[4])]
    ev_out.append(ev([], acts))
    ev_out.append({"type": "BuiltinCommonInstructions::ForEach", "object": "NocheNiebla",
                   "objectsToPick": "NocheNiebla", "conditions": [], "actions": [], "events": [
                       ev([], [act("TiledSpriteObject::XOffset",
                                   ["NocheNiebla", "=",
                                    f"round(-(1 - NocheNiebla.Variable(F)) * {CAM} "
                                    f"+ {T} * NocheNiebla.Variable(Drift))"]),
                               act("TiledSpriteObject::SetOpacity", ["NocheNiebla", "=", "NocheNiebla.Variable(Alpha)"])])]})

    # --- B: incendios lejanos (parallax como el Obelisco) y humo encima
    ev_out.append({"type": "BuiltinCommonInstructions::ForEach", "object": "NocheIncendio",
                   "objectsToPick": "NocheIncendio", "conditions": [], "actions": [], "events": [
                       ev([], [act("SetX", ["NocheIncendio", "=",
                                            f"round(NocheIncendio.Variable(Base) + {1 - INC_F:.2f} * {CAM})"]),
                               act("Opacity", ["NocheIncendio", "=",
                                               f"round(255 * (0.78 + 0.12 * sin({T} * 3.1 + NocheIncendio.Variable(Seed)) "
                                               f"+ 0.1 * sin({T} * 7.3 + NocheIncendio.Variable(Seed) * 2)))"])])]})
    ev_out.append({"type": "BuiltinCommonInstructions::ForEach", "object": "NocheHumo",
                   "objectsToPick": "NocheHumo", "conditions": [], "actions": [], "events": [
                       ev([], [act("SetX", ["NocheHumo", "=",
                                            f"round(NocheHumo.Variable(Base) + {1 - INC_F:.2f} * {CAM})"])])]})

    # --- B: los tachos titilan (opacidad del halo, ruido suave por instancia)
    ev_out.append({"type": "BuiltinCommonInstructions::ForEach", "object": "NocheFuegoGlow",
                   "objectsToPick": "NocheFuegoGlow", "conditions": [], "actions": [], "events": [
                       ev([], [act("Opacity", ["NocheFuegoGlow", "=",
                                               f"round(255 * (0.8 + 0.1 * sin({T} * 11 + NocheFuegoGlow.Variable(Seed)) "
                                               f"+ 0.1 * sin({T} * 23.7 + NocheFuegoGlow.Variable(Seed) * 3)))"])])]})

    # --- B: conos de farol (Mode 1 = falla, mismo ruido que los tubos del lab)
    h1 = f"mod(floor({T} * 2.5) * 7919 + NocheFarolCono.Variable(Seed) * 104729, 101)"
    h2 = f"mod(floor({T} * 16) * 6007 + NocheFarolCono.Variable(Seed) * 7727, 101)"
    mode = lambda m: act("NumberObjectVariable", ["NocheFarolCono", "Mode", "=", str(m)])   # noqa: E731
    op = lambda v: [act("Opacity", ["NocheFarolCono", "=", str(v)])]                     # noqa: E731
    ev_out.append({"type": "BuiltinCommonInstructions::ForEach", "object": "NocheFarolCono",
                   "objectsToPick": "NocheFarolCono", "conditions": [], "actions": [], "events": [
                       ev([mode(0)], op(255)),
                       ev([mode(1), cmp(h1, ">=", 25)], op(255)),
                       ev([mode(1), cmp(h1, "<", 25), cmp(h2, "<", 50)], op(0)),
                       ev([mode(1), cmp(h1, "<", 25), cmp(h2, ">=", 50)], op(255))]})

    # --- B: crepitar por cercanía + C: tinte de Lio
    pcx = "(Player.X() + Player.Width() / 2)"
    mute = ("(1 - min(1, Variable(Paused) + Variable(Over) + Variable(Won) "
            "+ Variable(NotaOpen)))")
    loud = warmth_expr(pcx, fires, FIRE_REACH)
    ev_out += [
        ev([act("BuiltinCommonInstructions::Once", [])],
           [act("PlaySoundOnChannel", ["", "sfx_fuego.wav", FIRE_CHANNEL, "yes", "0", "1"])]),
        ev([], [act("ModVarScene", ["NocheCalor", "=", warmth_expr(pcx, fires)]),
                act("SetSoundChannelVolume", ["", FIRE_CHANNEL, "=",
                                              f"GlobalVariable(SfxVolume) * 0.45 * {loud} * {mute}"]),
                act("ChangeColor", ["Player", tint_for("Variable(NocheCalor)")])]),
    ]
    # --- C: tinte de los zombies (cada uno según su propia X)
    for grp in ("Zombies", "Horda"):
        zx = f"({grp}.X() + {grp}.Width() / 2)"
        ev_out.append({"type": "BuiltinCommonInstructions::ForEach", "object": grp,
                       "objectsToPick": grp, "conditions": [], "actions": [], "events": [
                           ev([], [act("ChangeColor", [grp, tint_for(f"({warmth_expr(zx, fires)})")])])]})
    return ev_out


def main():
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    res = g["resources"]["resources"]
    imgs = (["cielo.png", "nubes.png", "niebla.png", "incendio.png", "fuego_glow.png",
             "farol_cono.png"] + [f"humo_{k}.png" for k in range(1, 7)]
            + [f"fuego_{k}.png" for k in range(1, 7)])
    for img in imgs:
        res_image(res, "noche_" + img, f"{NOCHE}/{img}")
    if not any(r["name"] == "sfx_fuego.wav" for r in res):
        res.append({"file": "assets/audio/sfx_fuego.wav", "kind": "audio", "metadata": "",
                    "name": "sfx_fuego.wav", "preloadAsMusic": False, "preloadAsSound": True,
                    "preloadInCache": True, "userAdded": True})

    lay = next(l for l in g["layouts"] if l["name"] == SCENE)
    add_layer(lay)
    if not any(v["name"] == "NocheCalor" for v in lay["variables"]):
        lay["variables"].append(var("NocheCalor", 0))

    # --- objetos
    objs = {o["name"]: o for o in lay["objects"]}
    for name, kw in ADJUST.items():
        o = objs[name]
        o["effects"] = [e for e in o.get("effects", []) if e["name"] != "Noche"] + [adjustment(**kw)]
    put_object(lay, tiled("NocheCielo", "noche_cielo.png", 4000, 270))
    put_object(lay, tiled("NocheNubes", "noche_nubes.png", 4000, 80))
    niebla = tiled("NocheNiebla", "noche_niebla.png", 4000, 48)
    niebla["variables"] = [var("Alpha", 255), var("F", 1), var("Drift", 0)]
    put_object(lay, niebla)
    inc = sprite("NocheIncendio", "noche_incendio.png")
    inc["variables"] = [var("Base", 0), var("Seed", 0)]
    put_object(lay, inc)
    humo = anim_sprite("NocheHumo", [f"noche_humo_{k}.png" for k in range(1, 7)], 0.16)
    humo["variables"] = [var("Base", 0)]
    put_object(lay, humo)
    put_object(lay, anim_sprite("NocheFuego", [f"noche_fuego_{k}.png" for k in range(1, 7)], 0.08))
    glow = sprite("NocheFuegoGlow", "noche_fuego_glow.png")
    glow["variables"] = [var("Seed", 0)]
    put_object(lay, glow)
    cono = sprite("NocheFarolCono", "noche_farol_cono.png")
    cono["variables"] = [var("Mode", 0), var("Seed", 0)]
    put_object(lay, cono)
    n_luna = moonlight(g, lay)

    # --- instancias
    lay["instances"] = [i for i in lay["instances"]
                        if i["name"] not in MINE
                        and not (i["name"] == "Tacho"
                                 and any(v["name"] == "Noche" for v in i.get("initialVariables", [])))]
    new = [inst("NocheCielo", -492, -65, -10, "BG_farthest", w=4000, h=270)]
    lay_n, y_n, z_n, _, _ = NUBES
    new.append(inst("NocheNubes", -492, y_n, z_n, lay_n, w=4000, h=80))
    for layer, y, z, f, drift, alpha in NIEBLAS:
        new.append(inst("NocheNiebla", -492, y, z, layer, w=4000, h=48,
                        ivars=[var("Alpha", alpha), var("F", f), var("Drift", drift)]))
    for k, screen0 in enumerate(INCENDIOS, 1):
        base = round(screen0 - W / 2 + INC_F * CAM0 - 48)            # 48 = medio ancho del resplandor
        new.append(inst("NocheIncendio", base, INC_Y, 2, "BG_farthest",
                        ivars=[var("Base", base), var("Seed", k * 1.7)]))
        new.append(inst("NocheHumo", base + 38, INC_Y - 70, 1, "BG_farthest",
                        ivars=[var("Base", base + 38)]))
    for x, y in EXTRA_TACHOS:
        new.append(inst("Tacho", x, y, 1, "Decor", ivars=[var("Noche", 1)]))
    tachos = [(i["x"], i["y"]) for i in lay["instances"] if i["name"] == "Tacho"] + EXTRA_TACHOS
    fires = []
    for k, (tx, ty) in enumerate(sorted(tachos), 1):
        new.append(inst("NocheFuego", tx + 2, ty - 11, 3, "Decor"))
        new.append(inst("NocheFuegoGlow", tx - 52, ty - 46, 1, "Atmos", ivars=[var("Seed", k * 2.3)]))
        fires.append(round(tx + 8))
    for k, f in enumerate(sorted((i for i in lay["instances"] if i["name"] == "Farol"),
                                 key=lambda i: i["x"]), 1):
        mode = 1 if round(f["x"]) in FLICKER_FAROLES else 0
        new.append(inst("NocheFarolCono", f["x"] + 10 - 32, f["y"] + 9 - 4, 0, "Atmos",
                        ivars=[var("Mode", mode), var("Seed", k)]))
    lay["instances"] += new

    lay["events"] = [e for e in lay["events"] if e.get("name") != GROUP]
    lay["events"].append({
        "type": "BuiltinCommonInstructions::Group", "name": GROUP, "source": "",
        "creationTime": 0, "folded": True, "color": {"b": 140, "g": 90, "r": 60},
        "events": events(fires)})
    with open(GAME, "w", encoding="utf-8") as fh:
        json.dump(g, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"{SCENE}: {len(fires)} fuegos, {len(INCENDIOS)} incendios lejanos, "
          f"{sum(1 for i in new if i['name'] == 'NocheFarolCono')} conos de farol, "
          f"{n_luna} imágenes con luz de luna")


if __name__ == "__main__":
    main()
