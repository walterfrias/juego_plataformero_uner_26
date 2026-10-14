#!/usr/bin/env python3
"""
wire_n1_platforms.py  —  mete los elementos de plataformeo del Nivel 1
(cadena de mobiliario + colchón con rebote + secciones de edificio).

Requiere: scripts/gen_n1_platforms.py + scripts/gen_arch_platforms.py corridos.

Edita game/game.json (backup .bak-<ts>, idempotente):
  - resources de game/assets/N1/
  - objetos:
      BancoPlaza        Sprite + Platform Jumpthru (máscara: sólo el asiento)
      Toldo             Sprite (puesto de feria entero) + Platform Jumpthru
                        (máscara custom = SÓLO el techo; el resto es dibujo)
      Balcon            Sprite (sección de edificio) + Platform Jumpthru
                        (máscara = sólo la losa del balcón)
      EscaleraIncendio  ídem (máscara = sólo la reja del descanso)
      FarolRepisa       Sprite + Platform Jumpthru
      Colchon           Sprite + Platform (sólido) + evento de rebote
  - instancias: cadena ascendente banco -> techo del puesto -> ménsula del
    farol -> balcón / escalera de incendios; el colchón bajo la ruta alta
  - eventos: rebote del colchón (al caer encima, BounceVel=-480 — reusa el
    arco que ya aplica el evento del stomp)

Revertir:  REVERT=1 python3 scripts/wire_n1_platforms.py
Uso:  python3 scripts/wire_n1_platforms.py   (desde la raíz del repo)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
# El sprite del Toldo (46x34) dibuja el puesto entero, pero SÓLO el techo
# lleva colisión: máscara custom = rectángulo de los ~5px de arriba. El
# resto (columnas, mesada, hule) es decoración y el player lo atraviesa.
TOLDO_ROOF_MASK = [{"x": 1, "y": 0}, {"x": 45, "y": 0}, {"x": 45, "y": 5}, {"x": 1, "y": 5}]
# El banco: sólo el asiento lleva colisión (jumpthru) — el player lo cruza
# caminando y sólo se sube saltando.
BANCO_SEAT_MASK = [{"x": 3, "y": 1}, {"x": 25, "y": 1}, {"x": 25, "y": 5}, {"x": 3, "y": 5}]
# Ruta alta = secciones de edificio completas (azotea -> calle), reemplazan
# la Cornisa que flotaba. Sólo la losa del balcón / la reja del descanso
# llevan colisión; el resto del edificio es dibujo (el player camina por
# delante). Sprites 46x80; la franja landable va cerca de arriba (la máscara
# es relativa al sprite, así que no cambia al agrandarlo hacia abajo).
BALCON_MASK = [{"x": 2, "y": 12}, {"x": 40, "y": 12}, {"x": 40, "y": 18}, {"x": 2, "y": 18}]
ESC_MASK = [{"x": 2, "y": 12}, {"x": 37, "y": 12}, {"x": 37, "y": 17}, {"x": 2, "y": 17}]

# objeto: (archivo_png, [frames]|None, platform_type, mask)
#   platform_type: "solid"|"jumpthru"|None ; mask: polígono [{x,y}] o None
OBJECTS = {
    "BancoPlaza":       ("BancoPlaza.png", None, "jumpthru", BANCO_SEAT_MASK),
    "Toldo":            ("Toldo.png", None, "jumpthru", TOLDO_ROOF_MASK),
    "Balcon":           ("Balcon.png", None, "jumpthru", BALCON_MASK),
    "EscaleraIncendio": ("EscaleraIncendio.png", None, "jumpthru", ESC_MASK),
    "FarolRepisa":      ("FarolRepisa.png", None, "jumpthru", None),
    "Colchon":          ("Colchon.png", None, "solid", None),
}
ALL_NAMES = list(OBJECTS)
# objetos de versiones anteriores de este script, a limpiar si quedaron
LEGACY_NAMES = ["PuestoMesada", "Cornisa", "BaldosaFloja", "BaldosaSplash"]
LEGACY_RES = ["PuestoMesada.png", "Cornisa.png", "BaldosaFloja.png",
              "BaldosaSplash_1.png", "BaldosaSplash_2.png", "BaldosaSplash_3.png"]
CLEAN_NAMES = ALL_NAMES + LEGACY_NAMES

# instancia: (objeto, x, y, z)
# cadena ascendente que usa el Farol existente en x=268 como escalón:
#   piso -> banco -> techo del puesto -> ménsula del farol -> balcón/escalera
# banco y puesto van a z=0 (el player, z=1, pasa POR DELANTE).
INSTANCES = [
    ("BancoPlaza",       172, 95, 0),
    ("Toldo",            206, 76, 0),   # 46x34, apoyado en el piso; techo en y=76
    ("FarolRepisa",      258, 66, 3),
    ("Balcon",           258, 30, 0),   # 46x80, pie al piso (30+80=110); losa landable ~y43
    ("EscaleraIncendio", 286, 30, 0),   # nudge izq para no colgar sobre el hueco de x335
    ("Colchon",          300, 100, 3),
]

RES = {  # name -> file rel a game/
    "BancoPlaza.png": "assets/N1/BancoPlaza.png",
    "Toldo.png": "assets/N1/Toldo.png",
    "Balcon.png": "assets/N1/Balcon.png",
    "EscaleraIncendio.png": "assets/N1/EscaleraIncendio.png",
    "FarolRepisa.png": "assets/N1/FarolRepisa.png",
    "Colchon.png": "assets/N1/Colchon.png",
}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}


def C(t, p):
    return {"type": {"value": t}, "parameters": p}


def anim(frames, tbf=0.1, loop=True):
    return {"name": "Splash", "useMultipleDirections": False, "directions": [{
        "looping": loop, "timeBetweenFrames": tbf, "sprites": [{
            "hasCustomCollisionMask": False, "image": f, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []} for f in frames]}]}


def one_frame_anim(img, mask=None):
    return {"name": "Idle", "useMultipleDirections": False, "directions": [{
        "looping": False, "timeBetweenFrames": 1.0, "sprites": [{
            "hasCustomCollisionMask": mask is not None, "image": img, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": [mask] if mask is not None else []}]}]}


def platform_behavior(kind):
    if kind == "solid":
        return [{"name": "Platform", "type": "PlatformBehavior::PlatformBehavior"}]
    if kind == "jumpthru":
        return [{"name": "Platform", "type": "PlatformBehavior::PlatformBehavior",
                 "platformType": "Jumpthru"}]
    return []


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # --- limpiar (idempotente / revert) ---
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in CLEAN_NAMES]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in CLEAN_NAMES]
    lay["variables"] = [v for v in lay["variables"] if v["name"] != "BaldosaGag"]

    def _is_n1_event(e):
        if e.get("_n1plat"):
            return True
        blob = json.dumps(e)
        return any(f'"{n}"' in blob for n in CLEAN_NAMES) or '"BaldosaGag"' in blob
    lay["events"] = [e for e in lay["events"] if not _is_n1_event(e)]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in CLEAN_NAMES]
    res[:] = [r for r in res if r["name"] in RES or r["name"] not in LEGACY_RES]

    if revert:
        res[:] = [r for r in res if r["name"] not in RES]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    # --- resources ---
    have = {r["name"] for r in res}
    for nm, f in RES.items():
        if nm not in have:
            res.append({"file": f, "kind": "image", "metadata": "", "name": nm,
                        "smoothed": False, "userAdded": True})

    # --- objetos ---
    for name, (png, frames, ptype, mask) in OBJECTS.items():
        animations = [anim(frames)] if frames else [one_frame_anim(png, mask)]
        lay["objects"].append({
            "adaptCollisionMaskAutomatically": mask is None, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False,
            "variables": [], "effects": [], "behaviors": platform_behavior(ptype),
            "animations": animations})
        if "children" in fs:
            fs["children"].append({"objectName": name})

    # --- instancias ---
    for obj, x, y, z in INSTANCES:
        lay["instances"].append({
            "angle": 0, "customSize": False, "height": 0, "layer": "", "name": obj,
            "persistentUuid": str(uuid.uuid4()), "width": 0, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []})

    # --- eventos ---
    def tag(e):
        e["_n1plat"] = True
        return e

    lay["events"] += [
        # rebote del colchón: al tocarlo desde arriba, pop grande (arco: evento del stomp)
        tag(std(
            [C("CollisionNP", ["Player", "Colchon", "", "", ""]),
             C("PosY", ["Player", "<", "Colchon.Y()"])],
            [C("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
               ["Player", "PlatformerObject", "=", "0"]),
             C("ModVarScene", ["BounceVel", "=", "-480"])])),
    ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("objetos N1:", [o["name"] for o in lay["objects"] if o["name"] in ALL_NAMES])
    print("instancias:", len(lay["instances"]), "| eventos:", len(lay["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/N1/BancoPlaza.png"), "corré gen_n1_platforms.py primero"
    main(revert=os.environ.get("REVERT") == "1")
