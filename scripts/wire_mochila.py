#!/usr/bin/env python3
"""
wire_mochila.py  —  mete el pickup `Mochila` (mochila de repartidor) en
el Nivel 1.

Mecánica (confirmada 2026-09-12): al agarrarla, el jugador puede
planear (caída lenta) el resto del nivel manteniendo Space mientras
cae. No es un ítem temporal ni un botón nuevo: reusa la tecla de salto
y la condición "IsFalling" del behavior Platformer Character.

  - MaxFallingSpeed normal del Player: 600 px/s (game.json).
  - MaxFallingSpeed en planeo: 80 px/s.
  - Cada frame se resetea a 600 y, si CanGlide=1 + cae + Space
    apretado, se pisa a 80 — así no hace falta un evento de "soltar".

Visual (agregado 2026-09-12): al agarrarla, un sprite `MochilaWorn`
(estático, sin animación) aparece pegado a la espalda del jugador y lo
sigue el resto del nivel — el Player no tiene FlipX en ningún lado del
juego, así que no hace falta lógica de espejo.

Requiere: scripts/gen_mochila.py corrido.

Edita game/game.json (backup .bak-<ts>, idempotente, marca los eventos
propios con "_mochila": true):
  - resources mochila_1..6.png, mochila_worn.png
  - objeto `Mochila` (Sprite, anim "Idle" loop, 6 frames) — el pickup
  - objeto `MochilaWorn` (Sprite, 1 frame estático) — la puesta
  - var de escena `CanGlide` = 0
  - 1 instancia de `Mochila` en x=950,y=96 (mismo estante que el 3er
    antídoto, sobre el pozo de agua — spot ya validado como alcanzable)
  - 1 instancia de `MochilaWorn` en x=0,y=0, zOrder=0 (debajo del
    Player, que tiene zOrder=1), oculta hasta el pickup
  - eventos: oculta MochilaWorn al empezar la escena; pickup (colisión
    -> Delete Mochila + CanGlide=1 + Show MochilaWorn); reset de
    MaxFallingSpeed a 600 cada frame; override a 80 mientras
    CanGlide=1 + IsFalling + Space apretado; mientras CanGlide=1,
    MochilaWorn sigue la posición del Player (offset +1,+13, ver
    WORN_W/WORN_H)

Ojo con la escala (encontrado 2026-09-14): la instancia `Player` tiene
customSize=true, 18x25 — se renderiza mas chica que el canvas nativo
32x34 de los PNG (probablemente ajustado a mano en el editor para el
Mask Dude viejo). Cualquier offset u tamaño de MochilaWorn tiene que
calcularse en ese espacio ESCALADO (x18/32, y x25/34), no contra el
canvas nativo del sprite, o la mochila queda mal ubicada/tamaño
(paso por esto: con MochilaWorn a tamaño nativo 14x16 sin escalar,
quedaba mas abajo de los pies y se metia en el piso). WORN_W/WORN_H
son 14x16 escalados a ese mismo factor; el offset +1,+13 deja el borde
inferior de la mochila justo a la altura de los pies.

Revertir:  REVERT=1 python3 scripts/wire_mochila.py
Uso:  python3 scripts/wire_mochila.py   (desde la raíz del repo, con
      GDevelop CERRADO — si está abierto, al guardar pisa este script)
"""
import json
import os
import shutil
import uuid
import datetime

GAME = "game/game.json"
N = 6

SPOT = (950, 96)
NORMAL_FALL_SPEED = "600"
GLIDE_FALL_SPEED = "80"

# Player se renderiza escalado (customSize 18x25 sobre un canvas nativo
# 32x34) -> mochila_worn.png (14x16 nativo) tiene que escalarse igual
# para no quedar gigante/hundida en el piso.
PLAYER_NATIVE_W, PLAYER_NATIVE_H = 32, 34
PLAYER_SCALED_W, PLAYER_SCALED_H = 18, 25
WORN_W = round(14 * PLAYER_SCALED_W / PLAYER_NATIVE_W)
WORN_H = round(16 * PLAYER_SCALED_H / PLAYER_NATIVE_H)

MYVARS = ("CanGlide",)
MYOBJS = ("Mochila", "MochilaWorn")


def cond(value, params):
    return {"type": {"value": value}, "parameters": params}


def act(value, params):
    return cond(value, params)


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard",
            "conditions": conds, "actions": acts, "_mochila": True}


def sprite_frame(image):
    return {"hasCustomCollisionMask": False, "image": image, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # ---- limpieza (idempotente / revert) ----
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in MYOBJS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in MYOBJS]
    lay["variables"] = [v for v in lay["variables"] if v["name"] not in MYVARS]
    lay["events"] = [e for e in lay["events"] if not e.get("_mochila")]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"]
                          if c.get("objectName") not in MYOBJS]

    if revert:
        res[:] = [r for r in res if not r["name"].startswith("mochila_")]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        json.load(open(GAME))
        print("revert OK")
        return

    # ---- resources ----
    have = {r["name"] for r in res}
    for i in range(1, N + 1):
        nm = f"mochila_{i}.png"
        if nm not in have:
            res.append({"file": f"assets/UI/mochila_{i}.png", "kind": "image",
                        "metadata": "", "name": nm, "smoothed": False,
                        "userAdded": True})
    if "mochila_worn.png" not in have:
        res.append({"file": "assets/UI/mochila_worn.png", "kind": "image",
                    "metadata": "", "name": "mochila_worn.png", "smoothed": False,
                    "userAdded": True})

    # ---- objeto Mochila ----
    lay["objects"].append({
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "",
        "name": "Mochila", "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{"name": "Idle", "useMultipleDirections": False,
                        "directions": [{"looping": True, "timeBetweenFrames": 0.12,
                                        "sprites": [sprite_frame(f"mochila_{i}.png")
                                                    for i in range(1, N + 1)]}]}]})

    # ---- objeto MochilaWorn (puesta en la espalda, sin animacion) ----
    lay["objects"].append({
        "adaptCollisionMaskAutomatically": True, "assetStoreId": "",
        "name": "MochilaWorn", "type": "Sprite", "updateIfNotVisible": False,
        "variables": [], "effects": [], "behaviors": [],
        "animations": [{"name": "Idle", "useMultipleDirections": False,
                        "directions": [{"looping": True, "timeBetweenFrames": 1,
                                        "sprites": [sprite_frame("mochila_worn.png")]}]}]})

    if "children" in fs:
        fs["children"] += [{"objectName": "Mochila"}, {"objectName": "MochilaWorn"}]

    # ---- vars ----
    lay["variables"] += [{"name": "CanGlide", "type": "number", "value": 0}]

    # ---- instancias ----
    x, y = SPOT
    lay["instances"].append({
        "angle": 0, "customSize": False, "height": 0, "layer": "",
        "name": "Mochila", "persistentUuid": str(uuid.uuid4()),
        "width": 0, "x": x, "y": y, "zOrder": 5,
        "numberProperties": [], "stringProperties": [], "initialVariables": []})
    lay["instances"].append({
        "angle": 0, "customSize": True, "height": WORN_H, "layer": "",
        "name": "MochilaWorn", "persistentUuid": str(uuid.uuid4()),
        "width": WORN_W, "x": 0, "y": 0, "zOrder": 0,
        "numberProperties": [], "stringProperties": [], "initialVariables": []})

    # ---- eventos ----
    lay["events"] += [
        # oculta la mochila puesta hasta que se la agarre
        std([cond("BuiltinCommonInstructions::Once", [])],
            [act("Hide", ["MochilaWorn"])]),
        # recoger la mochila -> desbloquea planeo + muestra la puesta
        std([cond("CollisionNP", ["Player", "Mochila", "", "", ""])],
            [act("Delete", ["Mochila", ""]),
             act("ModVarScene", ["CanGlide", "=", "1"]),
             act("Show", ["MochilaWorn", ""])]),
        # reset cada frame a la velocidad de caida normal
        std([],
            [act("PlatformBehavior::MaxFallingSpeed",
                 ["Player", "PlatformerObject", "=", NORMAL_FALL_SPEED, "no"])]),
        # mientras cae + Space apretado + tiene la mochila -> planea
        std([cond("VarScene", ["CanGlide", "=", "1"]),
             cond("PlatformBehavior::IsFalling", ["Player", "PlatformerObject"]),
             cond("KeyFromTextPressed", ["", "\"Space\""])],
            [act("PlatformBehavior::MaxFallingSpeed",
                 ["Player", "PlatformerObject", "=", GLIDE_FALL_SPEED, "no"])]),
        # la mochila puesta sigue al jugador (Player no usa FlipX en
        # ningun lado del juego, no hace falta espejar)
        std([cond("VarScene", ["CanGlide", "=", "1"])],
            [act("SetX", ["MochilaWorn", "=", "Player.X()+1"]),
             act("SetY", ["MochilaWorn", "=", "Player.Y()+13"])]),
    ]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("instancias Mochila:", sum(1 for i in lay["instances"] if i["name"] == "Mochila"))
    print("eventos _mochila:", sum(1 for e in lay["events"] if e.get("_mochila")))
    print("vars:", [v["name"] for v in lay["variables"] if v["name"] in MYVARS])


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/UI/mochila_1.png"), \
        "corré gen_mochila.py primero"
    main(revert=os.environ.get("REVERT") == "1")
