#!/usr/bin/env python3
"""
wire_options_menu.py — Menú de opciones (consigna punto 6 / GDD.md §5):
volumen de música, volumen de SFX, reiniciar nivel, salir al menú
principal.

Dos piezas:
  1. Layout nuevo "MainMenu" (pasa a ser firstLayout): título, ENTER
     para jugar, O para abrir un panel de opciones (volumen).
  2. Pausa dentro de "Level1": ESC abre/cierra un overlay con volumen,
     [R] reinicia el nivel, [M] vuelve al menú principal.

El volumen es scaffolding para cuando haya música/SFX reales (todavía
no hay ningún audio en el proyecto): las variables GLOBALES
MusicVolume/SfxVolume (0-100, persisten entre escenas) quedan listas
para que cualquier PlaySound/PlayMusic futuro las multiplique. Por eso
son variables de PROYECTO (GlobalVariable), no de escena — si fueran
de escena se perderían al cambiar de MainMenu a Level1.

Nombres de tecla verificados contra el código fuente de GDevelop
(GDJS/Runtime/gameplay-tests/gameplay-test-runner.ts, tabla de alias):
"Left"/"Right"/"Up"/"Down" (no "ArrowLeft"), "Return" (no "Enter").
Igual que el resto del repo, con KeyFromTextPressed (documentado) en
vez de KeyPressed (dropdown, evitado desde 2026-08-30). Para
ajustes +/- de volumen se usa KeyFromTextJustPressed (flanco, no cada
frame) para que mantener la tecla apretada no dispare el ajuste 60
veces por segundo.

Edita game/game.json (backup .bak-<ts>, idempotente). REVERT=1 deshace
(saca MainMenu, deja firstLayout=Level1, saca el overlay de pausa).
Uso:  python3 scripts/wire_options_menu.py    (desde la raíz del repo)
Después en GDevelop: cerrar sin guardar + abrir game/game.json.
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"
GLOBAL_VARS = {"MusicVolume": 100, "SfxVolume": 100}
MM_OBJS = ["MMTitle", "MMHint", "OptTitle", "OptMusic", "OptSfx", "OptHint"]
PAUSE_OBJS = ["PauseTitle", "PauseMusic", "PauseSfx", "PauseHint"]
PB = "PlatformBehavior::PlatformerObjectBehavior"


def cond(t, params):
    return {"type": {"value": t}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts}


def text_obj(name, txt, size=18, bold=True):
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


def inst(name, x, y, layer, z=1, w=0, h=0, custom=False):
    return {"angle": 0, "customSize": custom, "height": h, "layer": layer, "name": name,
            "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def base_layer():
    return {"ambientLightColorB": 32, "ambientLightColorG": 32, "ambientLightColorR": 32,
            "camera2DPlaneMaxDrawingDistance": 5000, "camera3DFarPlaneDistance": 10000,
            "camera3DFieldOfView": 45, "camera3DNearPlaneDistance": 0.1,
            "cameraType": "perspective", "followBaseLayerCamera": False,
            "isLightingLayer": False, "isLocked": False, "name": "",
            "renderingType": "", "visibility": True,
            "cameras": [{"defaultSize": True, "defaultViewport": True, "height": 0,
                         "viewportBottom": 1, "viewportLeft": 0, "viewportRight": 1,
                         "viewportTop": 0, "width": 0}],
            "effects": []}


def volume_text_updates(music_obj, sfx_obj):
    """acciones que sincronizan el texto de volumen con las variables globales (cada frame)."""
    return [
        {"type": {"value": "TextObject::String"}, "parameters":
            [music_obj, "=", '"Musica: " + ToString(GlobalVariable(MusicVolume)) + "%"']},
        {"type": {"value": "TextObject::String"}, "parameters":
            [sfx_obj, "=", '"SFX: " + ToString(GlobalVariable(SfxVolume)) + "%"']},
    ]


def volume_adjust_events(gate_conds):
    """4 eventos +/-10 con clamp 0..100, gateados por gate_conds (ej. estar en el panel de opciones)."""
    evs = []
    for key, var, delta, guard in (
        ("Left", "MusicVolume", -10, (">", "0")),
        ("Right", "MusicVolume", 10, ("<", "100")),
        ("Up", "SfxVolume", 10, ("<", "100")),
        ("Down", "SfxVolume", -10, (">", "0")),
    ):
        evs.append(std(
            gate_conds + [cond("KeyFromTextJustPressed", ["", f'"{key}"']),
                          cond("VarGlobal", [var, guard[0], guard[1]])],
            [cond("ModVarGlobal", [var, "+", str(delta)])]))
    return evs


def main_menu_layout():
    lay = {
        "b": 40, "disableInputWhenNotFocused": True, "mangledName": "MainMenu",
        "name": "MainMenu", "r": 16, "standardSortMethod": True,
        "stopSoundsOnStartup": True, "title": "", "v": 20,
        "uiSettings": {"grid": False, "gridType": "rectangular", "gridWidth": 32,
                       "gridHeight": 32, "gridDepth": 32, "gridOffsetX": 0, "gridOffsetY": 0,
                       "gridOffsetZ": 0, "gridColor": 10401023, "gridAlpha": 0.8, "snap": False,
                       "zoomFactor": 1, "windowMask": False, "selectedLayer": "",
                       "gameEditorMode": "instances-editor"},
        "objectsGroups": [], "behaviorsSharedData": [],
        "variables": [{"name": "MMShowOptions", "type": "number", "value": 0}],
        "layers": [base_layer()],
        "objects": [
            text_obj("MMTitle", "PACIENTE ZERO", size=26),
            text_obj("MMHint", "J: Jugar (o ENTER/ESPACIO)     O: Opciones", size=13, bold=False),
            text_obj("OptTitle", "OPCIONES", size=20),
            text_obj("OptMusic", "Musica: 100%", size=16, bold=False),
            text_obj("OptSfx", "SFX: 100%", size=16, bold=False),
            text_obj("OptHint", "<- -> Musica   ^ v SFX   ESC: Volver", size=13, bold=False),
        ],
        "objectsFolderStructure": {"folderName": "__ROOT",
                                    "children": [{"objectName": n} for n in MM_OBJS]},
        "instances": [
            inst("MMTitle", 130, 90, "", 1),
            inst("MMHint", 110, 130, "", 1),
            inst("OptTitle", 190, 60, "", 1),
            inst("OptMusic", 150, 100, "", 1),
            inst("OptSfx", 150, 122, "", 1),
            inst("OptHint", 60, 170, "", 1),
        ],
        "events": [
            std([cond("BuiltinCommonInstructions::Once", [])],
                [cond("Hide", [n]) for n in ("OptTitle", "OptMusic", "OptSfx", "OptHint")]),
            std([], volume_text_updates("OptMusic", "OptSfx")),
            *[std([cond("KeyFromTextJustPressed", ["", key]),
                   cond("VarScene", ["MMShowOptions", "=", "0"])],
                  [cond("Scene", ["", "Level1", "no"])])
              for key in ('"Return"', '"Space"', '"j"')],
            std([cond("KeyFromTextJustPressed", ["", '"o"']),
                 cond("VarScene", ["MMShowOptions", "=", "0"])],
                [cond("ModVarScene", ["MMShowOptions", "=", "1"]),
                 cond("Hide", ["MMTitle"]), cond("Hide", ["MMHint"]),
                 cond("Show", ["OptTitle", ""]), cond("Show", ["OptMusic", ""]),
                 cond("Show", ["OptSfx", ""]), cond("Show", ["OptHint", ""])]),
            std([cond("KeyFromTextJustPressed", ["", '"Escape"']),
                 cond("VarScene", ["MMShowOptions", "=", "1"])],
                [cond("ModVarScene", ["MMShowOptions", "=", "0"]),
                 cond("Show", ["MMTitle", ""]), cond("Show", ["MMHint", ""]),
                 cond("Hide", ["OptTitle"]), cond("Hide", ["OptMusic"]),
                 cond("Hide", ["OptSfx"]), cond("Hide", ["OptHint"])]),
        ] + volume_adjust_events([cond("VarScene", ["MMShowOptions", "=", "1"])]),
    }
    return lay


def add_pause_to_level1(lay):
    # limpiar (idempotente / revert)
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in PAUSE_OBJS]
    lay["instances"] = [i for i in lay["instances"] if i["name"] not in PAUSE_OBJS]
    lay["variables"] = [v for v in lay["variables"] if v["name"] != "Paused"]

    def is_pause_ev(e):
        blob = json.dumps(e.get("actions", [])) + json.dumps(e.get("conditions", []))
        return any(f'"{o}"' in blob for o in PAUSE_OBJS) or '"Paused"' in blob
    lay["events"] = [e for e in lay["events"] if not is_pause_ev(e)]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in PAUSE_OBJS]


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    level1 = [l for l in d["layouts"] if l["name"] == "Level1"][0]

    add_pause_to_level1(level1)
    d["layouts"] = [l for l in d["layouts"] if l["name"] != "MainMenu"]

    if revert:
        d["variables"] = [v for v in d["variables"] if v["name"] not in GLOBAL_VARS]
        d["firstLayout"] = "Level1"
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        print("revert OK: sin MainMenu, sin pausa en Level1, firstLayout=Level1")
        return

    # --- variables globales (persisten entre escenas) ---
    have = {v["name"] for v in d["variables"]}
    for n, v in GLOBAL_VARS.items():
        if n not in have:
            d["variables"].append({"name": n, "type": "number", "value": v})

    # --- MainMenu ---
    d["layouts"].append(main_menu_layout())
    d["firstLayout"] = "MainMenu"

    # --- pausa en Level1 ---
    fs = level1.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in PAUSE_OBJS]
    level1["variables"].append({"name": "Paused", "type": "number", "value": 0})
    level1["objects"] += [
        text_obj("PauseTitle", "PAUSA", size=22),
        text_obj("PauseMusic", "Musica: 100%", size=15, bold=False),
        text_obj("PauseSfx", "SFX: 100%", size=15, bold=False),
        text_obj("PauseHint", "<- -> Musica  ^ v SFX\nR: Reiniciar   M: Menu   ESC: Reanudar",
                  size=12, bold=False),
    ]
    level1["instances"] += [
        inst("PauseTitle", 190, 50, "UI", 30),
        inst("PauseMusic", 140, 90, "UI", 30),
        inst("PauseSfx", 140, 110, "UI", 30),
        inst("PauseHint", 80, 140, "UI", 30, 320, 40, True),
    ]

    pause_gate = [cond("VarScene", ["Paused", "=", "1"])]
    level1["events"] += [
        std([cond("BuiltinCommonInstructions::Once", [])],
            [cond("Hide", [n]) for n in PAUSE_OBJS]),
        std([], volume_text_updates("PauseMusic", "PauseSfx")),
        # abrir pausa: no si ya está pausado, ni durante game over / victoria
        std([cond("KeyFromTextJustPressed", ["", '"Escape"']),
             cond("VarScene", ["Paused", "=", "0"]),
             cond("VarScene", ["Over", "=", "0"]),
             cond("VarScene", ["Won", "=", "0"])],
            [cond("ModVarScene", ["Paused", "=", "1"]),
             cond("ChangeTimeScale", ["", "0"])] +
            [cond("Show", [n, ""]) for n in PAUSE_OBJS]),
        # cerrar pausa
        std([cond("KeyFromTextJustPressed", ["", '"Escape"']), *pause_gate],
            [cond("ModVarScene", ["Paused", "=", "0"]),
             cond("ChangeTimeScale", ["", "1"])] +
            [cond("Hide", [n]) for n in PAUSE_OBJS]),
        # reiniciar nivel desde la pausa
        std([cond("KeyFromTextJustPressed", ["", '"r"']), *pause_gate],
            [cond("ChangeTimeScale", ["", "1"]), cond("Scene", ["", "Level1", "no"])]),
        # volver al menu principal desde la pausa
        std([cond("KeyFromTextJustPressed", ["", '"m"']), *pause_gate],
            [cond("ChangeTimeScale", ["", "1"]), cond("Scene", ["", "MainMenu", "no"])]),
    ] + volume_adjust_events(pause_gate)

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("layouts:", [l["name"] for l in d["layouts"]], "| firstLayout:", d["firstLayout"])
    print("Level1 eventos:", len(level1["events"]), "| objetos:", len(level1["objects"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
