#!/usr/bin/env python3
"""
wire_tier1.py  —  Tier 1: convierte el paseo en un bucle jugable.
  - capa "UI" (no sigue la cámara) con 3 corazones (contador de vidas).
  - objeto Meta (entrada al laboratorio) en x=1650 -> tocarla = victoria.
  - game over cuando Lives <= 0 (o si el Player cae: Y > 300).
  - carteles VICTORIA / GAME OVER + [R] para reiniciar (congela la escena).

NO toca los eventos de stomp / daño que ya existen (solo los hace visibles
vía el HUD y el game over). La Meta está ANTES del hueco a propósito: el
tramo post-hueco no es alcanzable hasta cablear el "te lleva la horda".

Edita game/game.json (backup .bak-<ts>, idempotente). REVERT=1 para deshacer.
Requiere: scripts/gen_hud.py corrido.  Uso:  python3 scripts/wire_tier1.py
Después en GDevelop: cerrar sin guardar + abrir game/game.json.
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"
NEW_OBJS = ["Heart1", "Heart2", "Heart3", "Meta", "GameOverText", "VictoryText"]
META_X = 1650
NEW_VARS = {"Won": 0, "Over": 0, "BounceVel": 0}


def layer_ui():
    return {
        "ambientLightColorB": 32, "ambientLightColorG": 32, "ambientLightColorR": 32,
        "camera2DPlaneMaxDrawingDistance": 5000, "camera3DFarPlaneDistance": 10000,
        "camera3DFieldOfView": 45, "camera3DNearPlaneDistance": 0.1,
        "cameraType": "perspective", "followBaseLayerCamera": False,
        "isLightingLayer": False, "isLocked": False, "name": "UI",
        "renderingType": "", "visibility": True,
        "cameras": [{"defaultSize": True, "defaultViewport": True, "height": 0,
                     "viewportBottom": 1, "viewportLeft": 0, "viewportRight": 1,
                     "viewportTop": 0, "width": 0}],
        "effects": [],
    }


def spr(name, img):
    return {"adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False,
            "variables": [], "effects": [], "behaviors": [],
            "animations": [{"name": "Idle", "useMultipleDirections": False,
                            "directions": [{"looping": True, "timeBetweenFrames": 1.0,
                                            "sprites": [{
                                                "hasCustomCollisionMask": False, "image": img,
                                                "points": [],
                                                "originPoint": {"name": "origine", "x": 0, "y": 0},
                                                "centerPoint": {"automatic": True, "name": "centre",
                                                                "x": 0, "y": 0},
                                                "customCollisionMask": []}]}]}]}


def text_obj(name, txt):
    return {"assetStoreId": "", "name": name, "type": "TextObject::Text",
            "variables": [], "effects": [], "behaviors": [],
            "content": {
                "bold": True, "italic": False, "smoothed": True, "underlined": False,
                "text": txt, "font": "", "characterSize": 18,
                "color": "240;240;240", "textAlignment": "center",
                "verticalTextAlignment": "center",
                "isOutlineEnabled": True, "outlineThickness": 2, "outlineColor": "12;14;22",
                "isShadowEnabled": False, "shadowColor": "0;0;0", "shadowOpacity": 127,
                "shadowDistance": 4, "shadowAngle": 90, "shadowBlurRadius": 2,
            }}


def inst(name, x, y, layer, z=1, w=0, h=0, custom=False, ivars=None):
    return {"angle": 0, "customSize": custom, "height": h, "layer": layer, "name": name,
            "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [],
            "initialVariables": ivars or []}


def cond(t, params):
    return {"type": {"value": t}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard",
            "conditions": conds, "actions": acts}


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # limpiar lo previo (idempotente / revert)
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in NEW_OBJS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in NEW_OBJS]
    lay["layers"] = [ly for ly in lay["layers"] if ly["name"] != "UI"]
    lay["variables"] = [v for v in lay["variables"] if v["name"] not in NEW_VARS]

    def is_t1(e):
        if e.get("_t1"):
            return True
        acts = e.get("actions", [])
        # el evento del stomp (Delete Zombies) NO es un evento t1: se parchea aparte
        if any(a.get("type", {}).get("value") == "Delete"
               and a.get("parameters", [""])[0] == "Zombies" for a in acts):
            return False
        blob = json.dumps(acts) + json.dumps(e.get("conditions", []))
        return (any(f'"{o}"' in blob for o in NEW_OBJS)
                or '"Won"' in blob or '"Over"' in blob or '"BounceVel"' in blob)
    lay["events"] = [e for e in lay["events"] if not is_t1(e)]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in NEW_OBJS]

    # --- rebote del stomp ---
    # SetCurrentFallSpeed NO sirve (el behavior clampea a >=0).
    # SetCanJump+SimulateJumpKey NO es confiable (falla si el jugador tenía
    # la tecla de salto apretada: _jumpKeyHeldSinceJumpStart bloquea el salto).
    # Solución: arco manual controlado por la scene var BounceVel (ver eventos
    # más abajo). El stomp solo: mata el zombie, frena la caída, dispara el arco.
    PB = "PlatformBehavior::PlatformerObjectBehavior"
    BOUNCE_ACT_TYPES = {f"{PB}::SetCurrentFallSpeed", f"{PB}::SetCanJump",
                        f"{PB}::SimulateJumpKey"}
    for e in lay["events"]:
        acts = e.get("actions", [])
        is_stomp = (any(a.get("type", {}).get("value") == "Delete"
                        and a.get("parameters", [""])[0] == "Zombies" for a in acts)
                    and any(a.get("type", {}).get("value") in BOUNCE_ACT_TYPES
                            or a.get("type", {}).get("value") == "ModVarScene"
                            and a.get("parameters", [""])[0] == "BounceVel"
                            for a in acts))
        if not is_stomp:
            continue
        kept = [a for a in acts
                if a.get("type", {}).get("value") not in BOUNCE_ACT_TYPES
                and not (a.get("type", {}).get("value") == "ModVarScene"
                         and a.get("parameters", [""])[0] == "BounceVel")]
        if revert:
            kept.append({"type": {"value": f"{PB}::SetCurrentFallSpeed"},
                         "parameters": ["Player", "PlatformerObject", "=", "-150"]})
        else:
            kept.append({"type": {"value": f"{PB}::SetCurrentFallSpeed"},
                         "parameters": ["Player", "PlatformerObject", "=", "0"]})
            kept.append({"type": {"value": "ModVarScene"},
                         "parameters": ["BounceVel", "=", "-330"]})
        e["actions"] = kept

    if revert:
        res[:] = [r for r in res if r["name"] not in ("heart.png", "sign_lab.png")]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        print("revert OK (rebote stomp -> -150)")
        return

    # --- capa UI ---
    lay["layers"].append(layer_ui())

    # --- scene vars ---
    for n, v in NEW_VARS.items():
        lay["variables"].append({"name": n, "type": "number", "value": v})

    # --- resources ---
    have = {r["name"] for r in res}
    for fn in ("heart.png", "sign_lab.png"):
        if fn not in have:
            res.append({"file": f"assets/UI/{fn}", "kind": "image", "metadata": "",
                        "name": fn, "smoothed": False, "userAdded": True})

    # --- objetos ---
    lay["objects"] += [
        spr("Heart1", "heart.png"), spr("Heart2", "heart.png"), spr("Heart3", "heart.png"),
        spr("Meta", "sign_lab.png"),
        text_obj("GameOverText", "GAME OVER\n[R] para reiniciar"),
        text_obj("VictoryText", "LLEGASTE AL LABORATORIO\n[R] para reiniciar"),
    ]
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in NEW_OBJS]

    # --- instancias ---
    lay["instances"] += [
        inst("Heart1", 8, 8, "UI", 10), inst("Heart2", 22, 8, "UI", 10),
        inst("Heart3", 36, 8, "UI", 10),
        inst("Meta", META_X, 64, "", 1),
        inst("GameOverText", 40, 108, "UI", 20, 400, 54, True),
        inst("VictoryText", 40, 108, "UI", 20, 400, 54, True),
    ]

    # --- eventos (marcados con _t1 para poder revertir) ---
    def t1(conds, acts):
        e = std(conds, acts)
        e["_t1"] = True
        return e

    PB = "PlatformBehavior::PlatformerObjectBehavior"
    evs = [
        t1([cond("BuiltinCommonInstructions::Once", [])],
           [cond("Hide", ["GameOverText"]), cond("Hide", ["VictoryText"]),
            cond("ResetObjectTimer", ["Player", '"Invuln"'])]),
        # arco de rebote del stomp: mientras BounceVel<0, empuja al Player
        # hacia arriba y frena la caída; BounceVel decae hasta 0 y para.
        t1([cond("VarScene", ["BounceVel", "<", "0"])],
           [cond("SetY", ["Player", "+", "Variable(BounceVel) * TimeDelta()"]),
            cond(f"{PB}::SetCurrentFallSpeed", ["Player", "PlatformerObject", "=", "0"]),
            cond("ModVarScene", ["BounceVel", "+", "1100 * TimeDelta()"])]),
    ]
    # corazones
    for k in (1, 2, 3):
        evs.append(t1([cond("VarScene", ["Lives", ">=", str(k)])], [cond("Show", [f"Heart{k}", ""])]))
        evs.append(t1([cond("VarScene", ["Lives", "<", str(k)])], [cond("Hide", [f"Heart{k}"])]))
    # caída al vacío -> muerte
    evs.append(t1([cond("PosY", ["Player", ">", "300"]), cond("VarScene", ["Over", "=", "0"])],
                  [cond("ModVarScene", ["Lives", "=", "0"])]))
    # game over
    evs.append(t1([cond("VarScene", ["Lives", "<=", "0"]), cond("VarScene", ["Over", "=", "0"])],
                  [cond("ModVarScene", ["Over", "=", "1"]),
                   cond("SetAnimationName", ["Player", '"Death"']),
                   cond("Show", ["GameOverText", ""]),
                   cond("ChangeTimeScale", ["", "0"])]))
    # victoria
    evs.append(t1([cond("CollisionNP", ["Player", "Meta", "", "", ""]),
                   cond("VarScene", ["Won", "=", "0"])],
                  [cond("ModVarScene", ["Won", "=", "1"]),
                   cond("Show", ["VictoryText", ""]),
                   cond("ChangeTimeScale", ["", "0"])]))
    # reiniciar ([R] o Espacio). KeyFromTextPressed = la variante documentada,
    # clave como expresion ("r"). ChangeTimeScale 1 antes de cambiar de escena.
    for gate in ("Over", "Won"):
        for key in ('"r"', '"Space"'):
            evs.append(t1(
                [cond("KeyFromTextPressed", ["", key]), cond("VarScene", [gate, "=", "1"])],
                [cond("ChangeTimeScale", ["", "1"]), cond("Scene", ["", "Level1", "no"])]))

    lay["events"] += evs

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("objetos:", len(lay["objects"]), "| instancias:", len(lay["instances"]),
          "| eventos:", len(lay["events"]), "| capas:", [x["name"] for x in lay["layers"]])


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/UI/heart.png"), "corré gen_hud.py primero"
    main(revert=os.environ.get("REVERT") == "1")
