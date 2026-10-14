#!/usr/bin/env python3
"""
wire_notas.py — pruebas del brote (notas del diario de Paciente Zero) en
Level1. Ver GDD §6 y gen_notas.py (arte + textos).

Mecánica:
  - pickup `NotaPick` (papel flotante) con var de objeto Id = n.° de nota;
  - al tocarlo: global NotaN = 1, se borra, el mundo se congela
    (time scale 0) y se ve la nota completa (`NotaPaper`, una animación
    por nota) sobre el velo `NotaDim`, con "GUARDADA EN LA MOCHILA" y
    "[J] SEGUIR" abajo;
  - se cierra soltando J / Espacio / Enter / ESC después de 0.5 s, o sola
    a los 6 s. Se cuenta en FRAMES (NotaFrames), no con timers: con time
    scale 0 los timers no avanzan;
  - mientras está abierta: los controles del Player quedan bloqueados
    (IgnoreDefaultControls + condición NotaOpen=0 en los eventos de
    WASD/J) para que la tecla no se "guarde" como salto al despausar, y la
    pausa no abre (condición NotaOpen=0 en ESC/P). Se cierra al SOLTAR la
    tecla, así la pausa no ve un JustPressed en el mismo frame. NotaOpen=2
    es "cerrando" un frame, mismo truco que fix_pause_toggle.py;
  - las notas ya juntadas no reaparecen al morir / reintentar (globals);
    "Jugar" en el MainMenu las pone en 0, igual que el Puntaje.

Mochila (inventario): con la pausa abierta, I muestra las pruebas: la nota
elegida grande (o "???" si falta) y una fila de 7 casilleros; ← → elige
(SettingsOpen queda en 0 para que las flechas no toquen el volumen), I /
ESC / P vuelven al panel de pausa. MochilaOpen=3 = "cerrando" un frame.
Con la mochila abierta, ESC/P no cierran la pausa y R/M no hacen nada.

Nota 7 (L3): al morir, Paciente Zero suelta la nota (cae al piso) y el
evento de victoria original espera BossDown=1 + Nota7=1 + NotaOpen=0. Si ya
la tenía (repetir L3), victoria inmediata como antes.

Idempotente: grupo de eventos propio que se reemplaza entero; las
condiciones agregadas a eventos existentes se quitan antes de volver a
ponerlas. Si se corre wire_levels23.py --force, fix_pause_toggle.py o
wire_pause_panel.py, volver a correr este script.

Requiere:  python3 scripts/gen_notas.py
Edita game/game.json (backup .bak-<ts>). GDevelop CERRADO.
Uso:  python3 scripts/wire_notas.py   (desde la raíz del repo)
"""
import copy
import datetime
import json
import shutil
import uuid

from wire_score_hud import (AMBER, WHITE, act, btext, comment, ev, inst,
                            put_instances, put_object, walk)

GAME = "game/game.json"
GROUP = "Pruebas del brote (wire_notas.py)"
INV_GROUP = "Mochila: inventario de pruebas (wire_notas.py)"
BOSS_GROUP = "Nota 7: la suelta Paciente Zero (wire_notas.py)"
BOSS_NOTE = 7
BOSS_FLOOR_Y = 150 - 18          # tope del Ground de la arena (y=150) - alto del pickup - 2
# acciones de la muerte del jefe que pasan al grupo de la nota 7 (las de la
# victoria se quedan en el evento original, que ahora espera a la nota)
BOSS_DEATH = [("Create", ["", "ZombiePoofFX", "PacienteZero.X() + 16", "PacienteZero.Y() + 20", ""]),
              ("Create", ["", "ZombiePoofFX", "PacienteZero.X() + 48", "PacienteZero.Y() + 40", ""]),
              ("Delete", ["PacienteZero", ""]),
              ("Hide", ["BossHPText"])]
N_NOTAS = 7
W, H = 480, 270
PAPER_W, PAPER_H = 204, 128
MIN_FRAMES, MAX_FRAMES = 30, 360       # 0.5 s / 6 s a 60 fps

# (id, x, y) — sobre el piso (tope del Ground en y=110), después de la mochila
SPOTS = {"Level1": [(2, 1010, 92), (1, 1232, 92), (3, 2220, 92)],
         # L2: 4 sobre el estante largo, 5 en el ducto opcional bajo el antídoto
         # escondido, 6 en el piso justo después del gabinete (arriba del gabinete
         # no: el ducto obligatorio sube a Lio por encima y aterriza sin tocarla)
         "Level2": [(4, 1125, 64), (5, 3409, -15), (6, 3168, 92)],
         # L3: la 7 la suelta el jefe al morir (wire_boss_drop)
         "Level3": []}

CLOSE_KEYS = ('"j"', '"Space"', '"Return"', '"Escape"')
MOVE_KEYS = ('"a"', '"d"', '"w"', '"s"', '"j"')
NOTA_COND = {"type": {"value": "VarScene"}, "parameters": ["NotaOpen", "=", "0"]}
MOCHILA_COND = {"type": {"value": "VarScene"}, "parameters": ["MochilaOpen", "=", "0"]}
MY_VARS = (["NotaOpen"], ["MochilaOpen"])

# inventario: nota grande arriba, fila de 7 casilleros abajo
INV_PAPER_Y = 30
SLOT_W, SLOT_PITCH, SLOT_Y = 22, 30, 170
SLOT_X0 = (W - (6 * SLOT_PITCH + SLOT_W)) // 2
INV_TITLE = "MOCHILA - PRUEBAS 0/7"
INV_HINT = "← → ELEGIR    I / ESC: VOLVER"
PAUSE_ITEMS = ["PauseTitle", "PauseMusic", "PauseSfx", "PauseHint"]
INV_UI = ["NotaPaper", "NotaSlot", "NotaCursor", "MochilaTitle", "MochilaNums", "MochilaHint"]
# el espejo de la pausa a SettingsOpen: con la mochila abierta las flechas
# eligen nota en vez de cambiar el volumen (SettingsControls)
MIRROR = "Variable(Paused) * (1 - min(1, Variable(MochilaOpen)))"


def frame(image):
    return {"hasCustomCollisionMask": False, "image": image, "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": []}


def sprite(name, anims):
    """anims: [(nombre, [imágenes], segundos por frame)]"""
    return {"adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False, "variables": [], "effects": [],
            "behaviors": [],
            "animations": [{"name": a, "useMultipleDirections": False,
                            "directions": [{"looping": True, "timeBetweenFrames": t,
                                            "sprites": [frame(i) for i in imgs]}]}
                           for a, imgs, t in anims]}


def add_resources(g):
    res = g["resources"]["resources"]
    files = [f"nota_{i}.png" for i in range(1, N_NOTAS + 1)] + \
        [f"nota_pick_{i}.png" for i in range(1, 7)] + \
        ["nota_none.png", "nota_icon.png", "nota_slot_found.png", "nota_slot_empty.png",
         "nota_cursor.png"]
    res[:] = [r for r in res if r["name"] not in files]
    res += [{"file": f"assets/UI/Notas/{f}", "kind": "image", "metadata": "", "name": f,
             "smoothed": False, "userAdded": True} for f in files]


def has(e, kind, t, *p):
    return any(x["type"]["value"] == t and all(x["parameters"][i] == v for i, v in enumerate(p))
               for x in e.get(kind, []))


def guard_existing(lay):
    """NotaOpen=0 en los controles WASD/J y en la apertura de la pausa."""
    n = 0
    for e in walk(lay["events"]):
        if "conditions" not in e:
            continue
        e["conditions"] = [c for c in e["conditions"] if c["parameters"][:1] not in MY_VARS]
        is_move = len(e["conditions"]) == 1 and any(
            has(e, "conditions", "KeyFromTextPressed", "", k) for k in MOVE_KEYS) and \
            any(a["type"]["value"].startswith("PlatformBehavior::Simulate") for a in e["actions"])
        is_pause_open = has(e, "conditions", "VarScene", "Paused", "=", "0") and \
            has(e, "actions", "ChangeTimeScale", "", "0")
        if is_move or is_pause_open:
            e["conditions"].append(copy.deepcopy(NOTA_COND))
            n += 1
    assert n == 7, f"{lay['name']}: esperaba 5 controles + 2 pausas, encontré {n}"

    # con la mochila abierta: ESC/P vuelven a la pausa (no la cierran), R/M no
    # hacen nada y el panel de pausa no se vuelve a mostrar
    m = 0
    for e in walk(lay["events"]):
        if "conditions" not in e:
            continue
        is_pause_close = has(e, "conditions", "VarScene", "Paused", "=", "1") and \
            has(e, "actions", "ChangeTimeScale", "", "1") and \
            has(e, "actions", "ModVarScene", "Paused")
        is_r_m = has(e, "conditions", "VarScene", "Paused", "=", "1") and any(
            has(e, "conditions", "KeyFromTextJustPressed", "", k) for k in ('"r"', '"m"'))
        is_panel = has(e, "conditions", "VarScene", "Paused", "=", "1") and \
            has(e, "actions", "Show", "PausePanel")
        if is_pause_close or is_r_m or is_panel:
            e["conditions"].append(copy.deepcopy(MOCHILA_COND))
            m += 1
        for a in e.get("actions", []):
            if a["type"]["value"] == "ModVarGlobal" and a["parameters"][0] == "SettingsOpen":
                a["parameters"][2] = MIRROR
                m += 1
    assert m == 6, f"{lay['name']}: esperaba 2 cierres + R/M + panel + espejo, encontré {m}"


def wire_level(lay, spots):
    for v in ("NotaOpen", "NotaShow", "NotaFrames", "MochilaOpen", "MochilaSel"):
        if not any(x["name"] == v for x in lay["variables"]):
            lay["variables"].append({"name": v, "type": "number", "value": 0})

    pick = sprite("NotaPick", [("Idle", [f"nota_pick_{i}.png" for i in range(1, 7)], 0.12)])
    pick["variables"] = [{"name": "Id", "type": "number", "value": 0}]
    put_object(lay, pick)
    put_object(lay, sprite("NotaPaper",
                           [(f"n{i}", [f"nota_{i}.png"], 1) for i in range(1, N_NOTAS + 1)]
                           + [("none", ["nota_none.png"], 1)]))
    dim = copy.deepcopy(next(o for o in lay["objects"] if o["name"] == "PauseDim"))
    dim["name"] = "NotaDim"
    put_object(lay, dim)
    put_object(lay, sprite("NotaIcon", [("Idle", ["nota_icon.png"], 1)]))
    put_object(lay, btext("NotaToast", "GUARDADA EN LA MOCHILA", AMBER))
    put_object(lay, btext("NotaHint", "[J] SEGUIR", WHITE))

    toast = "GUARDADA EN LA MOCHILA"
    tw = len(toast) * 6 + 2
    px, py = (W - PAPER_W) // 2, (H - PAPER_H) // 2 - 16
    ty = py + PAPER_H + 10
    picks = []
    for nid, x, y in spots:
        i = inst("NotaPick", x, y, 5, layer="")
        i["persistentUuid"] = str(uuid.uuid4())
        i["initialVariables"] = [{"name": "Id", "type": "number", "value": nid}]
        picks.append(i)
    dim_i = inst("NotaDim", 0, 0, 40)
    dim_i.update(customSize=True, width=W, height=H)    # igual que PauseDim
    put_instances(lay, picks + [
        dim_i, inst("NotaPaper", px, py, 41),
        inst("NotaIcon", (W - tw) // 2 - 13, ty + 1, 41),
        inst("NotaToast", (W - tw) // 2, ty, 41),
        inst("NotaHint", (W - 10 * 6 - 2) // 2, ty + 14, 41)])

    lay["events"] = [e for e in lay["events"] if e.get("name") not in (GROUP, INV_GROUP, BOSS_GROUP)]
    guard_existing(lay)
    wire_inventory(lay)
    if any(o["name"] == "PacienteZero" for o in lay["objects"]):
        wire_boss_drop(lay)

    ui = ["NotaDim", "NotaPaper", "NotaIcon", "NotaToast", "NotaHint"]
    ids = sorted(nid for nid, _, _ in spots)
    open_acts = [act("ModVarScene", ["NotaShow", "=", "NotaPick.Variable(Id)"]),
                 act("ModVarScene", ["NotaOpen", "=", "1"]),
                 act("ModVarScene", ["NotaFrames", "=", "0"]),
                 act("Delete", ["NotaPick", ""]),
                 act("PlaySound", ["", "sfx_pickup.wav", "no", "GlobalVariable(SfxVolume)", "0.8"]),
                 act("ChangeTimeScale", ["", "0"]),
                 act("PlatformBehavior::IgnoreDefaultControls", ["Player", "PlatformerObject", "yes"]),
                 act("SetAnimationName", ["NotaPaper", '"n" + ToString(Variable(NotaShow))']),
                 act("SetY", ["NotaPaper", "=", str(py)])] + \
        [act("Show", [o, ""]) for o in ui]
    close_acts = [act("ModVarScene", ["NotaOpen", "=", "2"]),
                  act("ChangeTimeScale", ["", "1"]),
                  act("PlatformBehavior::IgnoreDefaultControls", ["Player", "PlatformerObject", "no"])] + \
        [act("Hide", [o]) for o in ui]
    can_close = [act("VarScene", ["NotaOpen", "=", "1"]),
                 act("VarScene", ["NotaFrames", ">=", str(MIN_FRAMES)])]

    events = [
        comment("Pruebas del brote: pickup -> mundo congelado + nota en pantalla; "
                "se guarda en el global NotaN. Generado por wire_notas.py."),
        ev([act("VarScene", ["NotaOpen", "=", "2"])], [act("ModVarScene", ["NotaOpen", "=", "0"])]),
        ev([act("BuiltinCommonInstructions::Once", [])], [act("Hide", [o]) for o in ui]),
        # las ya juntadas no reaparecen (morir / reintentar)
        *[ev([act("VarGlobal", [f"Nota{n}", "=", "1"]),
              act("NumberObjectVariable", ["NotaPick", "Id", "=", str(n)])],
             [act("Delete", ["NotaPick", ""])]) for n in ids],
        # pickup: abre la nota y marca el global según el Id
        ev([act("CollisionNP", ["Player", "NotaPick", "", "", ""]),
            act("VarScene", ["NotaOpen", "=", "0"]),
            act("VarScene", ["Paused", "=", "0"]),
            act("VarScene", ["Over", "=", "0"]),
            act("VarScene", ["Won", "=", "0"])],
           open_acts,
           [ev([act("VarScene", ["NotaShow", "=", str(n)])],
               [act("ModVarGlobal", [f"Nota{n}", "=", "1"])]) for n in range(1, N_NOTAS + 1)]),
        ev([act("VarScene", ["NotaOpen", "=", "1"])],
           [act("ModVarScene", ["NotaFrames", "+", "1"])]),
        *[ev(can_close + [act("KeyFromTextReleased", ["", k])], close_acts) for k in CLOSE_KEYS],
        ev([act("VarScene", ["NotaOpen", "=", "1"]),
            act("VarScene", ["NotaFrames", ">=", str(MAX_FRAMES)])], close_acts),
    ]
    # antes del grupo de la mochila (y del de la nota 7), ya agregados
    k = next(i for i, e in enumerate(lay["events"]) if e.get("name") == INV_GROUP)
    lay["events"].insert(k,
                         {"type": "BuiltinCommonInstructions::Group", "name": GROUP,
                          "source": "", "creationTime": 0, "folded": True,
                          "color": {"b": 128, "g": 200, "r": 96}, "events": events})


def wire_inventory(lay):
    """pausa -> I -> MOCHILA: nota grande + fila de casilleros, ← → elige."""
    slot = sprite("NotaSlot", [("found", ["nota_slot_found.png"], 1),
                               ("empty", ["nota_slot_empty.png"], 1)])
    slot["variables"] = [{"name": "Idx", "type": "number", "value": 0}]
    put_object(lay, slot)
    put_object(lay, sprite("NotaCursor", [("Idle", ["nota_cursor.png"], 1)]))
    put_object(lay, btext("MochilaTitle", INV_TITLE, AMBER))
    nums = (" " * 4).join(str(n) for n in range(1, N_NOTAS + 1))
    put_object(lay, btext("MochilaNums", nums, WHITE))
    put_object(lay, btext("MochilaHint", INV_HINT, WHITE))
    slots = []
    for n in range(1, N_NOTAS + 1):
        i = inst("NotaSlot", SLOT_X0 + (n - 1) * SLOT_PITCH, SLOT_Y, 42)
        i["initialVariables"] = [{"name": "Idx", "type": "number", "value": n}]
        slots.append(i)
    put_instances(lay, slots + [
        inst("NotaCursor", SLOT_X0 - 2, SLOT_Y - 2, 43),
        inst("MochilaTitle", (W - len(INV_TITLE) * 6 - 2) // 2, 12, 42),
        inst("MochilaNums", SLOT_X0 + (SLOT_W - 6) // 2, SLOT_Y + 29, 42),
        inst("MochilaHint", (W - len(INV_HINT) * 6 - 2) // 2, 236, 42)])

    # la ayuda de la pausa ahora tiene 4 líneas (I: MOCHILA): misma y que
    # wire_pause_panel.py (PY + 77)
    for i in lay["instances"]:
        if i["name"] == "PauseHint":
            i["y"] = 70 + 77

    found = " + ".join(f"GlobalVariable(Nota{n})" for n in range(1, N_NOTAS + 1))
    open_acts = [act("ModVarScene", ["MochilaOpen", "=", "1"]),
                 act("ModVarScene", ["MochilaSel", "=", "max(1, Variable(NotaShow))"]),
                 act("SetY", ["NotaPaper", "=", str(INV_PAPER_Y)]),
                 act("Hide", ["PausePanel"])] + \
        [act("Hide", [o]) for o in PAUSE_ITEMS] + [act("Show", [o, ""]) for o in INV_UI]
    close_acts = [act("Hide", [o]) for o in INV_UI] + [act("Show", [o, ""]) for o in PAUSE_ITEMS]
    if any(o["name"] == "BossHPText" for o in lay["objects"]):
        # L3: el cartel del jefe va en la misma franja que el título
        open_acts.append(act("Hide", ["BossHPText"]))
        close_acts.append(act("Show", ["BossHPText", ""]))
    is_open = act("VarScene", ["MochilaOpen", "=", "1"])

    def key(k):
        return act("KeyFromTextJustPressed", ["", k])

    events = [
        comment("Mochila: desde la pausa, I abre el inventario de pruebas (Nota1..7). "
                "← → elige, I / ESC / P vuelven a la pausa. Generado por wire_notas.py."),
        ev([act("BuiltinCommonInstructions::Once", [])], [act("Hide", [o]) for o in INV_UI[1:]]),
        # toggle con I: estado intermedio 3 ("cerrando"), ver fix_pause_toggle.py
        ev([key('"i"')], [], [
            ev([is_open], [act("ModVarScene", ["MochilaOpen", "=", "3"])] + close_acts),
            ev([act("VarScene", ["MochilaOpen", "=", "0"]),
                act("VarScene", ["Paused", "=", "1"])], open_acts),
            ev([act("VarScene", ["MochilaOpen", "=", "3"])],
               [act("ModVarScene", ["MochilaOpen", "=", "0"])]),
        ]),
        # ESC / P: la pausa no los ve (MochilaOpen=1), acá vuelven al panel
        *[ev([is_open, key(k)], [act("ModVarScene", ["MochilaOpen", "=", "0"])] + close_acts)
          for k in ('"Escape"', '"p"')],
        ev([is_open, key('"Left"'), act("VarScene", ["MochilaSel", ">", "1"])],
           [act("ModVarScene", ["MochilaSel", "-", "1"]),
            act("PlaySound", ["", "sfx_select.wav", "no", "GlobalVariable(SfxVolume)", "1"])]),
        ev([is_open, key('"Right"'), act("VarScene", ["MochilaSel", "<", str(N_NOTAS)])],
           [act("ModVarScene", ["MochilaSel", "+", "1"]),
            act("PlaySound", ["", "sfx_select.wav", "no", "GlobalVariable(SfxVolume)", "1"])]),
        ev([is_open],
           [act("SetX", ["NotaCursor", "=", f"{SLOT_X0 - 2} + (Variable(MochilaSel) - 1) * {SLOT_PITCH}"]),
            act("BitmapText::BitmapTextObject::SetText",
                ["MochilaTitle", "=", f'"MOCHILA - PRUEBAS " + ToString({found}) + "/{N_NOTAS}"'])],
           [ev([act("VarScene", ["MochilaSel", "=", str(n)])], [], [
               ev([act("VarGlobal", [f"Nota{n}", "=", "1"])],
                  [act("SetAnimationName", ["NotaPaper", f'"n{n}"'])]),
               ev([act("VarGlobal", [f"Nota{n}", "=", "0"])],
                  [act("SetAnimationName", ["NotaPaper", '"none"'])])])
            for n in range(1, N_NOTAS + 1)] +
           [ev([act("NumberObjectVariable", ["NotaSlot", "Idx", "=", str(n)])], [], [
               ev([act("VarGlobal", [f"Nota{n}", "=", "1"])],
                  [act("SetAnimationName", ["NotaSlot", '"found"'])]),
               ev([act("VarGlobal", [f"Nota{n}", "=", "0"])],
                  [act("SetAnimationName", ["NotaSlot", '"empty"'])])])
            for n in range(1, N_NOTAS + 1)]),
    ]
    lay["events"].append({"type": "BuiltinCommonInstructions::Group", "name": INV_GROUP,
                          "source": "", "creationTime": 0, "folded": True,
                          "color": {"b": 0, "g": 90, "r": 255}, "events": events})


def wire_boss_drop(lay):
    """L3: al morir, el jefe suelta la nota 7 y la victoria espera a que se
    lea. Si ya la tenía (repetir L3), victoria inmediata como antes."""
    for v in ("BossDown",):
        if not any(x["name"] == v for x in lay["variables"]):
            lay["variables"].append({"name": v, "type": "number", "value": 0})
    hits = [e for e in walk(lay["events"]) if e.get("_nota7_victoria") or any(
        a["type"]["value"] == "Delete" and a["parameters"][:1] == ["PacienteZero"]
        for a in e.get("actions", []))]
    assert len(hits) == 1, f"Level3: esperaba 1 evento de muerte del jefe, hay {len(hits)}"
    win = hits[0]
    win["_nota7_victoria"] = True
    moved = [list(p) for _, p in BOSS_DEATH]
    win["actions"] = [a for a in win["actions"] if a["parameters"] not in moved]
    win["conditions"] = [c for c in win["conditions"]
                         if c["parameters"][:1] not in (["BossDown"], [f"Nota{BOSS_NOTE}"], ["NotaOpen"])]
    win["conditions"] += [act("VarScene", ["BossDown", "=", "1"]),
                          act("VarGlobal", [f"Nota{BOSS_NOTE}", "=", "1"]),
                          act("VarScene", ["NotaOpen", "=", "0"])]

    death = [act(t, list(p)) for t, p in BOSS_DEATH[:2]]
    after = [act(t, list(p)) for t, p in BOSS_DEATH[2:]] + [act("ModVarScene", ["BossDown", "=", "1"])]
    dying = [act("VarScene", ["BossHP", "<=", "0"]), act("VarScene", ["BossDown", "=", "0"])]
    drop = [act("Create", ["", "NotaPick", "PacienteZero.X() + 25", "PacienteZero.Y() + 20", ""]),
            act("ModVarObjet", ["NotaPick", "Id", "=", str(BOSS_NOTE)])]
    lay["events"].append({"type": "BuiltinCommonInstructions::Group", "name": BOSS_GROUP,
                          "source": "", "creationTime": 0, "folded": True,
                          "color": {"b": 60, "g": 60, "r": 200}, "events": [
        comment(f"Al morir el jefe suelta la nota {BOSS_NOTE} (cae al piso); la victoria "
                "(evento original) espera a que se agarre y se cierre. Generado por wire_notas.py."),
        # se crea antes del Delete: necesita la posición del jefe
        ev(dying + [act("VarGlobal", [f"Nota{BOSS_NOTE}", "=", "0"])], death + drop + after),
        ev(dying + [act("VarGlobal", [f"Nota{BOSS_NOTE}", "=", "1"])], death + after),
        ev([act("VarScene", ["BossDown", "=", "1"]), act("PosY", ["NotaPick", "<", str(BOSS_FLOOR_Y)])],
           [act("SetY", ["NotaPick", "+", f"min({BOSS_FLOOR_Y} - NotaPick.Y(), 120 * TimeDelta())"])]),
        # el cerrar la MOCHILA vuelve a mostrar el cartel del jefe: acá se pisa
        ev([act("VarScene", ["BossDown", "=", "1"])], [act("Hide", ["BossHPText"])]),
    ]})


def wire_menu(lay):
    jugar = [e for e in walk(lay["events"]) if any(
        a["type"]["value"] == "Scene" and a["parameters"][1] == '"Tutorial"'
        for a in e.get("actions", []))]
    assert len(jugar) == 1, "MainMenu: esperaba 1 evento Jugar"
    e = jugar[0]
    e["actions"] = [a for a in e["actions"]
                    if not (a["type"]["value"] == "ModVarGlobal" and a["parameters"][0].startswith("Nota"))]
    e["actions"][0:0] = [act("ModVarGlobal", [f"Nota{n}", "=", "0"]) for n in range(1, N_NOTAS + 1)]


def main():
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    add_resources(g)
    gv = g.setdefault("variables", [])
    for n in range(1, N_NOTAS + 1):
        if not any(x["name"] == f"Nota{n}" for x in gv):
            gv.append({"name": f"Nota{n}", "type": "number", "value": 0})
    lays = {l["name"]: l for l in g["layouts"]}
    for name, spots in SPOTS.items():
        wire_level(lays[name], spots)
        print(f"{name}: {len(spots)} notas {[s[0] for s in spots]}")
    wire_menu(lays["MainMenu"])
    print("MainMenu: Nota1..7 = 0 en Jugar")
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
