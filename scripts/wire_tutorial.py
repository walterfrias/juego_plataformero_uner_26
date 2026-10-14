#!/usr/bin/env python3
"""
wire_tutorial.py — agrega la escena "Tutorial" (consigna punto 3: "al
menos 3 niveles + un tutorial de práctica"; GDD.md §4). Va antes de
Level1: enseña mover / saltar / stomp SIN ninguna forma de perder — no
hay variable Lives, ni corazones, ni Game Over en esta escena.

Reusa por deep-copy los objetos ya existentes de Level1 (mismos
sprites/comportamientos, sin arte nuevo): Player, Ground, Poste,
CityFar, CityNear, ZombieF -> TutZombie, Meta -> TutExit. Mismo GROUND
Y (110) que Level1 -> se reusan tal cual los offsets ya validados de
Player/Zombie/Meta respecto al piso.

Layout (una sola franja de piso CONTINUA, sin huecos, para que sea
literalmente imposible caerse):
  x -50..900  piso (Ground), una sola instancia, sin escalones ni pits.
  x 380       Poste (Platform, 14x24) como obstáculo a saltar — bloquea
              el paso pero NO hay penalidad por chocarlo: reintentar el
              salto las veces que haga falta no cuesta nada.
  x 560       TutZombie (copia de ZombieF) — SOLO se cablea el evento
              de stomp-kill (igual que Level1). El evento de daño
              lateral se omite a propósito: tocarlo de costado no hace
              nada.
  x 860       TutExit (copia de Meta) — colisión con Player -> Scene
              "Level1" (con las comillas escapadas, si no el cambio de
              escena falla en silencio, ver reseach.md).

Cablea el MainMenu: la acción de "empezar juego" (Return/Space) pasa de
apuntar a "Level1" a apuntar a "Tutorial". No toca la pausa de Level1
(reiniciar sigue yendo a Level1, volver al menú sigue yendo a MainMenu).

Cámara: mismo FixCamera que ya usa Level1 (no el CenterCameraOnObject +
ClampCamera especulativo de wire_camera_follow.py, que nunca se
confirmó en el editor).

Edita game/game.json directo (backup .bak-<ts>, idempotente: si ya
existe una escena "Tutorial" no hace nada).
Correr desde la raíz del repo:  python3 scripts/wire_tutorial.py
Después, en GDevelop: Cerrar proyecto (sin guardar) + Abrir game/game.json.
"""
import json
import copy
import datetime
import shutil
import os

GAME = "game/game.json"

GROUND_Y = 110
GROUND_X, GROUND_W = -50, 950

POSTE_X, POSTE_Y, POSTE_W, POSTE_H = 380, GROUND_Y - 24, 14, 24

ZOMBIE_X = 560
ZOMBIE_LEFT, ZOMBIE_RIGHT = 520, 650
ZOMBIE_SPEED = 22

EXIT_X = 860

PLAYER_X, PLAYER_Y = 40, GROUND_Y - 25 - 1  # mismo offset que Level1

JUMP_HINT_X = 300     # a partir de acá se muestra el hint de salto
STOMP_HINT_X = 480    # a partir de acá se muestra el hint de stomp

CAM_LEFT, CAM_TOP, CAM_RIGHT, CAM_BOTTOM = -60, -65, 950, 205


def cond(t, params):
    return {"type": {"value": t}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}


def text_obj(name, txt, size=13, bold=False):
    return {"assetStoreId": "", "name": name, "type": "TextObject::Text",
            "variables": [], "effects": [], "behaviors": [],
            "content": {
                "bold": bold, "italic": False, "smoothed": True, "underlined": False,
                "text": txt, "font": "", "characterSize": size,
                "color": "240;240;240", "textAlignment": "left",
                "verticalTextAlignment": "center",
                "isOutlineEnabled": True, "outlineThickness": 2, "outlineColor": "12;14;22",
                "isShadowEnabled": False, "shadowColor": "0;0;0", "shadowOpacity": 127,
                "shadowDistance": 4, "shadowAngle": 90, "shadowBlurRadius": 2,
            }}


def inst(name, x, y, layer="", z=1, w=0, h=0, custom=False):
    return {"angle": 0, "customSize": custom, "height": h, "layer": layer, "name": name,
            "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def base_layer(name="", follow=True):
    return {"ambientLightColorB": 32, "ambientLightColorG": 32, "ambientLightColorR": 32,
            "camera2DPlaneMaxDrawingDistance": 5000, "camera3DFarPlaneDistance": 10000,
            "camera3DFieldOfView": 45, "camera3DNearPlaneDistance": 0.1,
            "cameraType": "perspective", "followBaseLayerCamera": follow,
            "isLightingLayer": False, "isLocked": False, "name": name,
            "renderingType": "", "visibility": True,
            "cameras": [{"defaultSize": True, "defaultViewport": True, "height": 0,
                         "viewportBottom": 1, "viewportLeft": 0, "viewportRight": 1,
                         "viewportTop": 0, "width": 0}],
            "effects": []}


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))

    if any(l["name"] == "Tutorial" for l in d["layouts"]):
        print("Tutorial ya existe (idempotente) — no hago nada. "
              "Borrala a mano del game.json si querés regenerarla.")
        return

    level1 = next(l for l in d["layouts"] if l["name"] == "Level1")
    mainmenu = next(l for l in d["layouts"] if l["name"] == "MainMenu")

    def obj(name):
        return copy.deepcopy(next(o for o in level1["objects"] if o["name"] == name))

    player = obj("Player")
    ground = obj("Ground")
    poste = obj("Poste")
    cityfar = obj("CityFar")
    citynear = obj("CityNear")
    tutzombie = obj("ZombieF")
    tutzombie["name"] = "TutZombie"
    tutexit = obj("Meta")
    tutexit["name"] = "TutExit"

    hint_move = text_obj("HintMove", "Flechas / A-D: moverte")
    hint_jump = text_obj("HintJump", "Espacio: saltar")
    hint_stomp = text_obj("HintStomp", "Saltale encima para eliminarlo")

    objects = [player, ground, poste, cityfar, citynear, tutzombie, tutexit,
               hint_move, hint_jump, hint_stomp]

    instances = [
        inst("Player", PLAYER_X, PLAYER_Y, "", 1, 18, 25, True),
        inst("Ground", GROUND_X, GROUND_Y, "", 1, GROUND_W, 14, True),
        inst("Poste", POSTE_X, POSTE_Y, "", 1, POSTE_W, POSTE_H, True),
        inst("CityFar", -492, 28, "BG_far", 0, 4000, 70, True),
        inst("CityNear", -488, 47, "BG_near", 0, 4000, 96, True),
        inst("TutZombie", ZOMBIE_X, 76, "", 2),
        inst("TutExit", EXIT_X, 63, "", 1),
        inst("HintMove", 60, 20, "UI", 30),
        inst("HintJump", 60, 20, "UI", 30),
        inst("HintStomp", 60, 20, "UI", 30),
    ]

    events = [
        std([cond("BuiltinCommonInstructions::Once", [])],
            [cond("PlayMusicOnChannel",
                  ["", "music_menu.wav", "1", "yes", "GlobalVariable(MusicVolume)", "1"])]),

        std([], [cond("FixCamera", ["", "Player", str(CAM_LEFT), str(CAM_TOP),
                                     str(CAM_RIGHT), str(CAM_BOTTOM), "yes", "", ""])]),

        # patrulla de TutZombie (mismo patron que wire_zombie_female.py)
        std([], [cond("SetAnimationName", ["TutZombie", '"Walk"'])]),
        std([], [cond("SetX", ["TutZombie", "+",
                               f"Variable(TutZombieDir) * {ZOMBIE_SPEED} * TimeDelta()"])]),
        std([cond("PosX", ["TutZombie", ">", str(ZOMBIE_RIGHT)]),
             cond("VarScene", ["TutZombieDir", "=", "1"])],
            [cond("ModVarScene", ["TutZombieDir", "=", "-1"]),
             cond("FlipX", ["TutZombie", "yes"])]),
        std([cond("PosX", ["TutZombie", "<", str(ZOMBIE_LEFT)]),
             cond("VarScene", ["TutZombieDir", "=", "-1"])],
            [cond("ModVarScene", ["TutZombieDir", "=", "1"]),
             cond("FlipX", ["TutZombie", "no"])]),

        # stomp mata al zombie de practica (SIN dano lateral a proposito)
        std([cond("CollisionNP", ["Player", "TutZombie", "", "", ""]),
             cond("PosY", ["Player", "<", "TutZombie.Y()"])],
            [cond("Delete", ["TutZombie", ""]),
             cond("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
                  ["Player", "PlatformerObject", "=", "0"]),
             cond("ModVarScene", ["BounceVel", "=", "-330"]),
             cond("PlaySound", ["", "sfx_stomp.wav", "no", "GlobalVariable(SfxVolume)", "1"])]),

        # consumidor del rebote (identico al de Level1)
        std([cond("VarScene", ["BounceVel", "<", "0"])],
            [cond("SetY", ["Player", "+", "Variable(BounceVel) * TimeDelta()"]),
             cond("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
                  ["Player", "PlatformerObject", "=", "0"]),
             cond("ModVarScene", ["BounceVel", "+", "1100 * TimeDelta()"])]),

        # hints contextuales segun avance del jugador
        std([cond("BuiltinCommonInstructions::Once", [])],
            [cond("Show", ["HintMove", ""]), cond("Hide", ["HintJump"]),
             cond("Hide", ["HintStomp"])]),
        std([cond("PosX", ["Player", ">=", str(JUMP_HINT_X)])],
            [cond("Hide", ["HintMove"]), cond("Show", ["HintJump", ""])]),
        std([cond("PosX", ["Player", ">=", str(STOMP_HINT_X)])],
            [cond("Hide", ["HintJump"]), cond("Show", ["HintStomp", ""])]),

        # salida -> Level1
        std([cond("CollisionNP", ["Player", "TutExit", "", "", ""])],
            [cond("Scene", ["", "\"Level1\"", "no"])]),
    ]

    tutorial = {
        "b": level1["b"], "disableInputWhenNotFocused": level1["disableInputWhenNotFocused"],
        "mangledName": "Tutorial", "name": "Tutorial", "r": level1["r"],
        "standardSortMethod": level1["standardSortMethod"], "stopSoundsOnStartup": True,
        "title": "", "v": level1["v"],
        "uiSettings": {"grid": False, "gridType": "rectangular", "gridWidth": 32,
                       "gridHeight": 32, "gridDepth": 32, "gridOffsetX": 0, "gridOffsetY": 0,
                       "gridOffsetZ": 0, "gridColor": 10401023, "gridAlpha": 0.8, "snap": False,
                       "zoomFactor": 1, "windowMask": False, "selectedLayer": "",
                       "gameEditorMode": "instances-editor"},
        "objectsGroups": [], "behaviorsSharedData": [],
        "variables": [
            {"name": "TutZombieDir", "type": "number", "value": 1},
            {"name": "BounceVel", "type": "number", "value": 0},
        ],
        "layers": [base_layer("BG_far", True), base_layer("BG_near", True),
                   base_layer("", True), base_layer("UI", False)],
        "objects": objects,
        "objectsFolderStructure": {"folderName": "__ROOT",
                                    "children": [{"objectName": o["name"]} for o in objects]},
        "instances": instances,
        "events": events,
    }

    d["layouts"].append(tutorial)

    # --- cablear MainMenu: "empezar juego" -> Tutorial (no Level1) ---
    patched = 0
    for e in mainmenu["events"]:
        for a in e.get("actions", []):
            if a.get("type", {}).get("value") == "Scene" and \
                    a.get("parameters", [None, None])[1] == '"Level1"':
                a["parameters"][1] = '"Tutorial"'
                patched += 1
    print(f"MainMenu: {patched} accion(es) de cambio de escena repuntadas a Tutorial")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("OK. layouts:", [l["name"] for l in d["layouts"]])
    print("Tutorial objetos:", [o["name"] for o in objects])
    print("Tutorial eventos:", len(events), "| instancias:", len(instances))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
