#!/usr/bin/env python3
"""
wire_levels23.py — agrega las escenas "Level2" (El laboratorio) y "Level3"
(Confrontación con el Paciente Zero) y cablea el flujo completo:

  MainMenu -> Tutorial -> Level1 -> Level2 -> Level3 -> MainMenu

Primer corte JUGABLE (no terminado) para la entrega de avance del
29/09/2026. Todo es tuneable desde las constantes de más abajo.

Cómo se arma cada nivel nuevo:
  - Objetos: deep-copy de los de Level1 (Player, zombies, virus, HUD,
    textos de pausa/victoria/game over, antídoto, meta, FX). Arte nuevo
    solo para el interior del laboratorio (scripts/gen_lab.py): LabFar,
    LabNear, piso (Ground con otra textura), Estante (jumpthru) y
    GlassSpikes (vidrios/jeringas en el fondo de los huecos).
  - Eventos "genéricos" de Level1 (controles, animaciones del Player,
    stomp/daño contra el grupo Zombies, infección zombie<->virus, HUD de
    vidas, caída al vacío, Game Over, pausa, antídotos, sonido de salto)
    se copian FILTRADOS: se descarta todo evento que nombre un objeto que
    el nivel nuevo no tiene, y todo lo específico de Level1 (patrullas
    individuales con ZombieXDir, virus individuales Virus1Angle...,
    checkpoints con las X de Level1, horda, río).
  - Patrulla de zombies y vuelo de virus: versión GENÉRICA nueva con
    variables de objeto por instancia (Dir/MinX/MaxX/Speed en zombies,
    Angle/Next/MinX/MaxX/MinY/MaxY en virus) + ForEach. Así se pueden
    poner N instancias del mismo zombie sin crear un objeto por cada una.
  - Level3: jefe "PacienteZero" (copia de ZombieT al doble de tamaño),
    patrón del GDD §3: avanza -> se prepara (contorno rojo) -> embiste ->
    queda expuesto. Solo recibe daño con stomp mientras está expuesto;
    3 stomps = victoria.

Transiciones (en los 3 niveles): al ganar, [Espacio] o click -> siguiente
escena, [R] -> repetir. Espacio necesita haberse SOLTADO después de ganar
(var NextReady), si no, el mismo salto con el que tocaste la meta te
saltearía la pantalla de victoria.

Edita game/game.json directo (backup .bak-<ts>). Si Level2/Level3 ya
existen, no hace nada salvo que se pase --force (las regenera desde cero:
se pierden los cambios manuales hechos en esas escenas).
Correr desde la raíz del repo, con GDevelop CERRADO:
    python3 scripts/gen_lab.py && python3 scripts/gen_zombies_lab.py \
        && python3 scripts/wire_levels23.py
"""
import copy
import datetime
import json
import os
import re
import shutil
import sys

GAME = "game/game.json"
GROUND_Y = 110          # mismo piso que Level1 (offsets de sprites ya validados)
ZOMBIE_Y = GROUND_Y - 34
PLAYER_Y = GROUND_Y - 26

# ---------------------------------------------------------------- Level2
# Recorrido (27/09, alargado de 2200 a ~3800 px con 3 mecánicas nuevas):
#   0-1700     pasillos con huecos de vidrios, estantes, zombies y virus
#   1728-2150  PISO ENCERADO (resbala) que termina en un hueco
#   2178-2960  CAMILLAS: 2 huecos anchos (140 y 200 px, imposibles de
#              saltar) con una camilla que va y viene sobre cada uno
#   2960-3900  DUCTO: un gabinete de 92 px de alto corta el paso; la
#              corriente de aire del ducto te sube por encima. Un 2do ducto
#              opcional lleva a un antídoto en altura. Después, meta.
L2_WIDTH = 3800
# segmentos de piso (x0, x1); entre uno y otro hay un hueco con vidrios
# OJO: el salto real del Player (medido en runtime 27/09) alcanza ~40 px en
# horizontal y ~37 px de alto. Huecos de 28 px (con 40 la ventana para
# saltar era de ~8 px, injugable) y escalones de <=28 px.
L2_FLOOR = [(-200, 420), (448, 900), (928, 1350), (1378, 1700), (1728, 2150),
            (2178, 2480), (2620, 2760), (2960, 3900)]
# estantes jumpthru (x, y, ancho)
L2_SHELVES = [(250, 82, 64), (560, 82, 64), (650, 56, 64), (1060, 82, 96),
              (1170, 56, 64), (1470, 82, 64), (1560, 56, 64)]
# zombies: (objeto, x, minX, maxX, velocidad). Personal del lab
# (gen_zombies_lab.py) + los 3 de la horda (gen_zombies_horda.py: hincha,
# repartidor, policía): todos ya asomaron en la horda de Level1 y se los
# vuelve a encontrar adentro. Nada de los zombies de la calle de Level1.
# ZombieT NO va en ningún nivel común: es el look del jefe (Level3).
L2_ZOMBIES = [("ZombieEnf", 300, 240, 400, 26),
              ("ZombieMed", 520, 470, 640, 20), ("ZombieRep", 660, 600, 760, 30),
              ("ZombieInv", 780, 700, 880, 12), ("ZombiePol", 1100, 1040, 1200, 16),
              ("ZombieInv", 1020, 960, 1150, 12), ("ZombieEnf", 1250, 1180, 1330, 26),
              ("ZombieMed", 1450, 1400, 1600, 20), ("ZombieHin", 1530, 1400, 1690, 24),
              ("ZombieEnf", 1620, 1560, 1690, 24),
              # piso encerado
              ("ZombieInv", 1850, 1780, 1950, 12), ("ZombieMed", 2060, 2000, 2120, 20),
              # antes de las camillas
              ("ZombieEnf", 2300, 2200, 2460, 26),
              # antes del ducto y después del gabinete
              ("ZombiePol", 3010, 2975, 3060, 16), ("ZombieRep", 3300, 3200, 3380, 30),
              ("ZombieMed", 3500, 3440, 3640, 20), ("ZombieHin", 3620, 3500, 3690, 24)]
# zombies con sprite propio: objeto -> (carpeta en game/assets, seg. entre frames)
LAB_ZOMBIES = {"ZombieMed": ("Zombie_Med", 0.11), "ZombieEnf": ("Zombie_Enf", 0.09),
               "ZombieInv": ("Zombie_Inv", 0.14), "ZombieHin": ("Zombie_Hin", 0.09),
               "ZombieRep": ("Zombie_Rep", 0.08), "ZombiePol": ("Zombie_Pol", 0.12)}
# virus: (objeto, x, y, minX, maxX, minY, maxY)
L2_VIRUS = [("Virus1", 700, 20, 600, 820, 0, 60),
            ("Virus2", 1500, 30, 1440, 1660, 0, 70),
            ("Virus3", 1960, 20, 1880, 2080, 5, 70)]
# el 4to antídoto está arriba del ducto opcional (hay que subir a buscarlo)
L2_ANTIDOTES = [(150, 90), (675, 36), (1195, 36), (3409, -44)]
L2_CHECKPOINTS = [448, 928, 1378, 1728, 2178, 2620, 2960, 3160]
L2_META_X = 3720

# --- mecánica 1: piso encerado (x0, x1). Pisarlo = casi no frenás.
L2_WET = [(1780, 2150)]
WET_DECEL, WET_ACCEL = 60, 160            # normal del Player: 1500 / 300
# --- mecánica 2: camillas (x, minX, maxX, velocidad). Superficie a ras del
#     piso: se sube caminando cuando está pegada al borde.
L2_CAMILLAS = [(2484, 2484, 2568, 40), (2764, 2764, 2908, 60)]
CAMILLA_W, CAMILLA_H = 48, 16
# --- mecánica 3: ductos de aire (x, tope_y). La corriente va del piso hasta
#     tope_y; adentro te empuja hacia arriba a AIR_LIFT px/s.
L2_VENTS = [(3080, -45), (3400, -45)]
AIR_LIFT = 140
# gabinete que corta el paso (x, y_tope, ancho): pegado al 1er ducto
L2_CABINET = (3114, 18, 32)

# ---------------------------------------------------------------- Level3
ARENA_W = 480
ARENA_GROUND = 150
# escalera a cada lado: 122 -> 96 -> 70. Arriba de 70 el jefe (top 82) no te
# toca al embestir, y desde ahí se le cae encima cuando queda expuesto.
L3_SHELVES = [(40, 122, 64), (132, 96, 64), (30, 70, 64),     # bustos y 96 corridos 22 px (wire_jefe_jeringa.py)
              (376, 122, 64), (284, 96, 64), (386, 70, 64)]
BOSS_W, BOSS_H = 64, 68
BOSS_X = 360
BOSS_HP = 3
BOSS_WALK_T, BOSS_TELEGRAPH_T, BOSS_CHARGE_T, BOSS_EXPOSED_T = 1.8, 0.8, 1.2, 1.5
BOSS_WALK_SPEED, BOSS_CHARGE_SPEED = 35, 170   # la embestida suma +40 por golpe recibido

# ------------------------------------------------------------- helpers


def ins(t, params, inverted=False):
    d = {"type": {"value": t}, "parameters": params}
    if inverted:
        d["type"]["inverted"] = True
    return d


def std(conds, acts, events=None):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds,
            "actions": acts, "events": events or []}


def foreach(obj, conds, acts, events=None):
    # OJO: GDevelop lee el objeto de la clave "object" (ForEachEvent.cpp,
    # UnserializeFrom). "objectsToPick" es lo que pide el esquema del MCP
    # gdevelop-mcp, pero el motor la ignora: con solo esa clave el ForEach
    # compila VACÍO, en silencio. Se ponen las dos.
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj,
            "objectsToPick": obj, "conditions": conds, "actions": acts,
            "events": events or []}


def fix_tiled_offset_types(events):
    """XOffset/YOffset de TiledSprite son acciones de la extensión
    TiledSpriteObject: el tipo completo es "TiledSpriteObject::XOffset". Sin
    el prefijo GDevelop no la encuentra y la descarta EN SILENCIO (así el
    río de Level1 nunca se movió). Devuelve cuántas corrigió."""
    n = 0
    for e in events:
        for a in e.get("actions", []):
            if a["type"]["value"] in ("XOffset", "YOffset"):
                a["type"]["value"] = "TiledSpriteObject::" + a["type"]["value"]
                n += 1
        n += fix_tiled_offset_types(e.get("events", []))
    return n


def fix_foreach_keys(events):
    """Agrega "object" a los ForEach que solo traen "objectsToPick"."""
    n = 0
    for e in events:
        if e.get("type") == "BuiltinCommonInstructions::ForEach" and "object" not in e:
            e["object"] = e.get("objectsToPick", "")
            n += 1
        n += fix_foreach_keys(e.get("events", []))
    return n


def comment(txt):
    return {"type": "BuiltinCommonInstructions::Comment", "color": {"b": 109, "g": 230,
            "r": 255, "textB": 0, "textG": 0, "textR": 0}, "comment": txt, "comment2": ""}


def once():
    return ins("BuiltinCommonInstructions::Once", [])


def q(s):
    return f'"{s}"'


def num_var(name, value):
    return {"name": name, "type": "number", "value": value}


def inst(name, x, y, layer="", z=1, w=0, h=0, custom=False, ivars=None):
    return {"angle": 0, "customSize": custom, "height": h, "layer": layer, "name": name,
            "width": w, "x": x, "y": y, "zOrder": z, "numberProperties": [],
            "stringProperties": [], "initialVariables": ivars or []}


def text_obj(name, txt, size=13, color="240;240;240"):
    return {"assetStoreId": "", "name": name, "type": "TextObject::Text",
            "variables": [], "effects": [], "behaviors": [],
            "content": {"bold": False, "italic": False, "smoothed": True, "underlined": False,
                        "text": txt, "font": "", "characterSize": size, "color": color,
                        "textAlignment": "left", "verticalTextAlignment": "center",
                        "isOutlineEnabled": True, "outlineThickness": 2,
                        "outlineColor": "12;14;22", "isShadowEnabled": False,
                        "shadowColor": "0;0;0", "shadowOpacity": 127, "shadowDistance": 4,
                        "shadowAngle": 90, "shadowBlurRadius": 2}}


def add_obj_vars(o, names_values):
    have = {v["name"] for v in o.get("variables", [])}
    for n, v in names_values:
        if n not in have:
            o.setdefault("variables", []).append({"name": n, "type": "number", "value": str(v)})


def ensure_resource(d, name, file):
    res = d["resources"]["resources"]
    if not any(r["name"] == name for r in res):
        res.append({"file": file, "kind": "image", "metadata": "", "name": name,
                    "smoothed": False, "userAdded": True})


# ------------------------------------------------ filtrado de eventos de Level1

INDIVIDUAL = re.compile(r"^(Zombie(F|M|T|D|N|O|V|Marcha|End\d)|Virus\d|Horda\w*)$")
# NocheCalor: el grupo de la noche de Level1 (wire_noche_n1.py) no va al lab
L1_ONLY_VARS = re.compile(r"(Zombie\w*Dir|Virus\d(Angle|NextChange)|CanGlide|NocheCalor)")


def refs(instr, names):
    out = set()
    for p in instr.get("parameters", []):
        if p in names:
            out.add(p)
        for m in re.findall(r"([A-Za-z_]\w*)\.", p):
            if m in names:
                out.add(m)
    return out


def filter_events(events, l1_names, keep_names):
    """Copia los eventos genéricos de Level1 que sirven en un nivel nuevo."""
    out = []
    for e in events:
        e = copy.deepcopy(e)
        t = e.get("type", "")
        if t.endswith("Comment"):
            continue
        if t.endswith("Link"):
            out.append(e)   # SettingsControls (pausa/opciones)
            continue
        text = json.dumps(e)
        if L1_ONLY_VARS.search(text):
            continue
        conds = e.get("conditions", [])
        # horda de Level1: fuera los eventos que la gatillan/consultan, y las
        # acciones sueltas que la reposicionan (p. ej. en la caída al vacío)
        if "Horda" in json.dumps(conds):
            continue
        e["actions"] = [a for a in e.get("actions", []) if "Horda" not in json.dumps(a)]
        # checkpoints de Level1 (PosX(Player) > N -> CheckX = N)
        if any(a["type"]["value"] == "ModVarScene" and a["parameters"][0] == "CheckX"
               for a in e.get("actions", [])) and \
                any(c["type"]["value"] == "PosX" for c in conds):
            continue
        # cámara: se agrega una propia por nivel
        if any(a["type"]["value"] == "FixCamera" for a in e.get("actions", [])):
            continue
        bad = False
        for c in conds:
            r = refs(c, l1_names)
            if any(n not in keep_names or INDIVIDUAL.match(n) for n in r):
                bad = True
        if bad:
            continue
        acts = []
        for a in e.get("actions", []):
            r = refs(a, l1_names)
            if any(n not in keep_names or INDIVIDUAL.match(n) for n in r):
                continue
            acts.append(a)
        if not conds and not acts and not e.get("events"):
            continue
        if e.get("actions") and not acts and not e.get("events"):
            continue
        e["actions"] = acts
        if e.get("events"):
            e["events"] = filter_events(e["events"], l1_names, keep_names)
        out.append(e)
    return out


def retarget_scenes(events, mapping):
    for e in events:
        for a in e.get("actions", []):
            if a["type"]["value"] == "Scene" and a["parameters"][1] in mapping:
                a["parameters"][1] = mapping[a["parameters"][1]]
        retarget_scenes(e.get("events", []), mapping)


# ------------------------------------------------ bloques de eventos nuevos

def camera_event(left, top, right, bottom):
    return std([], [ins("FixCamera", ["", "Player", str(left), str(top), str(right),
                                      str(bottom), "yes", "", ""])])


def zombie_patrol_events():
    return [
        comment("Patrulla genérica: cada instancia trae Dir/MinX/MaxX/Speed como "
                "variables de objeto (initialVariables en la instancia)."),
        std([], [ins("SetAnimationName", ["Zombies", q("Walk")])]),
        foreach("Zombies", [], [ins("SetX", ["Zombies", "+",
                "Zombies.Variable(Dir) * Zombies.Variable(Speed) * TimeDelta()"])], [
            std([ins("PosX", ["Zombies", ">", "Zombies.Variable(MaxX)"]),
                 ins("NumberObjectVariable", ["Zombies", "Dir", "=", "1"])],
                [ins("ModVarObjet", ["Zombies", "Dir", "=", "-1"]),
                 ins("FlipX", ["Zombies", "yes"])]),
            std([ins("PosX", ["Zombies", "<", "Zombies.Variable(MinX)"]),
                 ins("NumberObjectVariable", ["Zombies", "Dir", "=", "-1"])],
                [ins("ModVarObjet", ["Zombies", "Dir", "=", "1"]),
                 ins("FlipX", ["Zombies", "no"])]),
        ]),
    ]


def virus_events():
    ang = "Virus.Variable(Angle)"
    retarget = [ins("ResetObjectTimer", ["Virus", q("Retarget")]),
                ins("ModVarObjet", ["Virus", "Angle", "=", "Random(359)*3.14159265/180"]),
                ins("ModVarObjet", ["Virus", "Next", "=", "1.5+Random(100)/100"])]
    return [
        comment("Vuelo genérico de virus: Angle/Next/MinX/MaxX/MinY/MaxY por instancia."),
        foreach("Virus", [ins("NumberObjectVariable", ["Virus", "Init", "=", "0"])],
                retarget + [ins("ModVarObjet", ["Virus", "Init", "=", "1"])]),
        foreach("Virus", [], [
            ins("SetX", ["Virus", "+", f"cos({ang})*55*TimeDelta()"]),
            ins("SetY", ["Virus", "+", f"sin({ang})*55*TimeDelta()"])], [
            std([ins("ObjectTimer", ["Virus", q("Retarget"), "Virus.Variable(Next)"])],
                copy.deepcopy(retarget)),
            std([ins("PosX", ["Virus", "<", "Virus.Variable(MinX)"])],
                [ins("ModVarObjet", ["Virus", "Angle", "=", "(-60+Random(120))*3.14159265/180"])]),
            std([ins("PosX", ["Virus", ">", "Virus.Variable(MaxX)"])],
                [ins("ModVarObjet", ["Virus", "Angle", "=", "(120+Random(120))*3.14159265/180"])]),
            std([ins("PosY", ["Virus", "<", "Virus.Variable(MinY)"])],
                [ins("ModVarObjet", ["Virus", "Angle", "=", "(30+Random(120))*3.14159265/180"])]),
            std([ins("PosY", ["Virus", ">", "Virus.Variable(MaxY)"])],
                [ins("ModVarObjet", ["Virus", "Angle", "=", "(210+Random(120))*3.14159265/180"])]),
        ]),
    ] + [
        std([ins("CollisionNP", ["Player", "Virus", "", "", ""]),
             ins("ObjectTimer", ["Player", q("Invuln"), "1"]),
             ins("PosX", ["Player", op, "Virus.X()"])],
            hurt_actions(dx))
        for op, dx in ((">=", 70), ("<", -70))
    ]


def hurt_actions(dx, lives=1):
    return [ins("ModVarScene", ["Lives", "-", str(lives)]),
            ins("ResetObjectTimer", ["Player", q("Invuln")]),
            ins("SetAnimationName", ["Player", q("Hit")]),
            ins("PlaySound", ["", "sfx_hurt.wav", "no", "GlobalVariable(SfxVolume)", "1"]),
            ins("SetX", ["Player", "+", str(dx)]),
            ins("SetY", ["Player", "+", "-30"])]


def checkpoint_events(xs):
    return [std([ins("PosX", ["Player", ">", str(x)]), ins("PosY", ["Player", "<", "100"]),
                 ins("VarScene", ["CheckX", "<", str(x)])],
                [ins("ModVarScene", ["CheckX", "=", str(x)])]) for x in xs]


def next_level_events(next_scene):
    """Victoria: [Espacio] (una vez soltado) o click -> next_scene."""
    return [
        std([ins("VarScene", ["Won", "=", "1"]),
             ins("KeyFromTextPressed", ["", q("Space")], inverted=True)],
            [ins("ModVarScene", ["NextReady", "=", "1"])]),
        std([ins("KeyFromTextPressed", ["", q("Space")]), ins("VarScene", ["Won", "=", "1"]),
             ins("VarScene", ["NextReady", "=", "1"])],
            [ins("ChangeTimeScale", ["", "1"]), ins("Scene", ["", q(next_scene), "no"])]),
    ]


def mechanics_events(player_obj):
    """Piso encerado, camillas móviles y ductos de aire (Level2)."""
    pb = player_obj["behaviors"][0]
    decel, accel = pb.get("deceleration", 1500), pb.get("acceleration", 300)
    wet = ins("CollisionNP", ["Player", "WetFloor", "", "", ""])
    wet_not = copy.deepcopy(wet)
    wet_not["type"]["inverted"] = True
    plat = lambda t, v: ins(f"PlatformBehavior::{t}", ["Player", "PlatformerObject", "=", str(v)])
    return [
        comment("Piso encerado: pisándolo casi no frenás (resbala hacia el hueco)."),
        std([wet], [plat("Deceleration", WET_DECEL), plat("Acceleration", WET_ACCEL)]),
        std([wet_not], [plat("Deceleration", decel), plat("Acceleration", accel)]),
        comment("Camillas: plataformas que van y vienen sobre los huecos anchos "
                "(Dir/MinX/MaxX/Speed por instancia). El Platformer lleva al "
                "jugador parado encima."),
        foreach("Camilla", [], [ins("SetX", ["Camilla", "+",
                "Camilla.Variable(Dir) * Camilla.Variable(Speed) * TimeDelta()"])], [
            std([ins("PosX", ["Camilla", ">", "Camilla.Variable(MaxX)"]),
                 ins("NumberObjectVariable", ["Camilla", "Dir", "=", "1"])],
                [ins("ModVarObjet", ["Camilla", "Dir", "=", "-1"])]),
            std([ins("PosX", ["Camilla", "<", "Camilla.Variable(MinX)"]),
                 ins("NumberObjectVariable", ["Camilla", "Dir", "=", "-1"])],
                [ins("ModVarObjet", ["Camilla", "Dir", "=", "1"])]),
        ]),
        comment("Ductos: la corriente de aire te empuja hacia arriba."),
        std([], [ins("TiledSpriteObject::YOffset", ["AirFlow", "+", "60 * TimeDelta()"])]),
        std([ins("CollisionNP", ["Player", "AirFlow", "", "", ""])],
            [ins("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
                 ["Player", "PlatformerObject", "=", "0"]),
             ins("SetY", ["Player", "-", f"{AIR_LIFT} * TimeDelta()"])]),
    ]


def boss_events():
    pz = "PacienteZero"
    t = q("BossT")
    face = [
        std([ins("PosX", ["Player", "<", f"{pz}.X() + {BOSS_W // 2}"])],
            [ins("ModVarScene", ["BossDir", "=", "-1"]), ins("FlipX", [pz, "yes"])]),
        std([ins("PosX", ["Player", ">=", f"{pz}.X() + {BOSS_W // 2}"])],
            [ins("ModVarScene", ["BossDir", "=", "1"]), ins("FlipX", [pz, "no"])]),
    ]
    to_state = lambda s: [ins("ModVarScene", ["BossState", "=", str(s)]),
                          ins("ResetObjectTimer", [pz, t])]
    bounce = [ins("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
                  ["Player", "PlatformerObject", "=", "0"]),
              ins("ModVarScene", ["BounceVel", "=", "-380"]),
              ins("PlaySound", ["", "sfx_stomp.wav", "no", "GlobalVariable(SfxVolume)", "1"])]
    on_top = [ins("CollisionNP", ["Player", pz, "", "", ""]),
              ins("PosY", ["Player", "<", f"{pz}.Y()"]),
              ins("PlatformBehavior::IsFalling", ["Player", "PlatformerObject"])]
    return [
        comment("Jefe: 0=avanza hacia el jugador, 1=se prepara (contorno rojo), "
                "2=embiste, 3=expuesto (única ventana de stomp). 3 stomps = victoria."),
        std([once()], [ins("ResetObjectTimer", [pz, t]),
                       ins("ResetObjectTimer", [pz, q("BossHurt")]),
                       ins("SetAnimationName", [pz, q("Walk")])]),
        # 0: avanza
        std([ins("VarScene", ["BossState", "=", "0"]), ins("VarScene", ["Won", "=", "0"])],
            [ins("SetX", [pz, "+", f"Variable(BossDir) * {BOSS_WALK_SPEED} * TimeDelta()"])],
            face + [std([ins("ObjectTimer", [pz, t, str(BOSS_WALK_T)])],
                        to_state(1) + [ins("EnableEffect", [pz, q("InfectedOutline"), "yes"]),
                                       ins("PauseAnimation", [pz])])]),
        # 1: se prepara
        std([ins("VarScene", ["BossState", "=", "1"]),
             ins("ObjectTimer", [pz, t, str(BOSS_TELEGRAPH_T)])],
            to_state(2) + [ins("EnableEffect", [pz, q("InfectedOutline"), "no"]),
                           ins("PlayAnimation", [pz])]),
        # 2: embiste
        std([ins("VarScene", ["BossState", "=", "2"])],
            [ins("SetX", [pz, "+", f"Variable(BossDir) * ({BOSS_CHARGE_SPEED} + "
                                   f"({BOSS_HP} - Variable(BossHP)) * 40) * TimeDelta()"])], [
            std([ins("ObjectTimer", [pz, t, str(BOSS_CHARGE_T)])],
                to_state(3) + [ins("PauseAnimation", [pz])]),
            std([ins("PosX", [pz, "<", "4"])],
                [ins("SetX", [pz, "=", "4"])] + to_state(3) + [ins("PauseAnimation", [pz])]),
            std([ins("PosX", [pz, ">", str(ARENA_W - BOSS_W - 4)])],
                [ins("SetX", [pz, "=", str(ARENA_W - BOSS_W - 4)])] + to_state(3) +
                [ins("PauseAnimation", [pz])]),
        ]),
        # 3: expuesto
        std([ins("VarScene", ["BossState", "=", "3"]),
             ins("ObjectTimer", [pz, t, str(BOSS_EXPOSED_T)])],
            to_state(0) + [ins("PlayAnimation", [pz])]),
        # límites de la arena caminando
        std([ins("PosX", [pz, "<", "4"])], [ins("SetX", [pz, "=", "4"])]),
        std([ins("PosX", [pz, ">", str(ARENA_W - BOSS_W - 4)])],
            [ins("SetX", [pz, "=", str(ARENA_W - BOSS_W - 4)])]),
        # stomp fuera de la ventana -> rebota sin daño
        std(on_top + [ins("VarScene", ["BossState", "!=", "3"])], bounce),
        # stomp en la ventana -> daño
        std(on_top + [ins("VarScene", ["BossState", "=", "3"]),
                      ins("ObjectTimer", [pz, q("BossHurt"), "1"])],
            [ins("ModVarScene", ["BossHP", "-", "1"]),
             ins("ResetObjectTimer", [pz, q("BossHurt")]),
             ins("Create", ["", "ZombiePoofFX", f"{pz}.X() + {BOSS_W // 2}", f"{pz}.Y()", ""]),
             ins("PlayAnimation", [pz])] + to_state(0) + bounce),
        # contacto de costado -> daño al jugador (1 vida, empujón más fuerte)
        std([ins("CollisionNP", ["Player", pz, "", "", ""]),
             ins("PosY", ["Player", ">=", f"{pz}.Y()"]),
             ins("ObjectTimer", ["Player", q("Invuln"), "1"]),
             ins("PosX", ["Player", ">=", f"{pz}.X() + {BOSS_W // 2}"])], hurt_actions(90)),
        std([ins("CollisionNP", ["Player", pz, "", "", ""]),
             ins("PosY", ["Player", ">=", f"{pz}.Y()"]),
             ins("ObjectTimer", ["Player", q("Invuln"), "1"]),
             ins("PosX", ["Player", "<", f"{pz}.X() + {BOSS_W // 2}"])], hurt_actions(-90)),
        # HUD
        std([], [ins("TextObject::String", ["BossHPText", "=",
                 '"PACIENTE ZERO  " + ToString(Variable(BossHP)) + "/' + str(BOSS_HP) + '"'])]),
        # derrota del jefe
        std([ins("VarScene", ["BossHP", "<=", "0"]), ins("VarScene", ["Won", "=", "0"])],
            [ins("Create", ["", "ZombiePoofFX", f"{pz}.X() + 16", f"{pz}.Y() + 20", ""]),
             ins("Create", ["", "ZombiePoofFX", f"{pz}.X() + 48", f"{pz}.Y() + 40", ""]),
             ins("Delete", [pz, ""]), ins("Hide", ["BossHPText"]),
             ins("ModVarScene", ["Won", "=", "1"]), ins("Show", ["VictoryText", ""]),
             ins("PlaySound", ["", "sfx_victory.wav", "no", "GlobalVariable(SfxVolume)", "1"])]),
    ]


# ------------------------------------------------------------------ main

def build_scene(name, level1, objects, groups, instances, events, bg_rgb):
    return {
        "b": bg_rgb[2], "disableInputWhenNotFocused": level1["disableInputWhenNotFocused"],
        "mangledName": name, "name": name, "r": bg_rgb[0], "v": bg_rgb[1],
        "standardSortMethod": level1["standardSortMethod"], "stopSoundsOnStartup": True,
        "title": "", "uiSettings": copy.deepcopy(level1["uiSettings"]),
        "objectsGroups": groups,
        "variables": copy.deepcopy(level1["variables"]),
        "instances": instances,
        "objects": objects,
        "objectsFolderStructure": {"folderName": "__ROOT",
                                    "children": [{"objectName": o["name"]} for o in objects]},
        "events": events,
        "layers": copy.deepcopy(level1["layers"]),
        "behaviorsSharedData": copy.deepcopy(level1["behaviorsSharedData"]),
    }


def main():
    force = "--force" in sys.argv
    d = json.load(open(GAME))
    names = [l["name"] for l in d["layouts"]]
    if ("Level2" in names or "Level3" in names) and not force:
        print("Level2/Level3 ya existen — no hago nada (usá --force para regenerarlas).")
        return

    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d["layouts"] = [l for l in d["layouts"] if l["name"] not in ("Level2", "Level3")]

    for fname in ("lab_far", "lab_near", "lab_floor", "lab_shelf", "lab_glass"):
        assert os.path.exists(f"game/assets/Lab/{fname}.png"), "corré antes scripts/gen_lab.py"
        ensure_resource(d, f"{fname}.png", f"assets/Lab/{fname}.png")

    level1 = next(l for l in d["layouts"] if l["name"] == "Level1")
    l1_objs = {o["name"]: o for o in level1["objects"]}
    l1_names = set(l1_objs) | {g["name"] for g in level1["objectsGroups"]}

    for lay in d["layouts"]:
        n_off = fix_tiled_offset_types(lay["events"])
        if n_off:
            print(f"{lay['name']}: {n_off} acción(es) X/YOffset con el tipo corregido")
        n = fix_foreach_keys(lay["events"])
        if n:
            print(f"{lay['name']}: {n} ForEach reparado(s) (faltaba la clave \"object\")")

    # ---------- Level1: la victoria ahora avanza a Level2 ----------
    l1_ev = level1["events"]
    for e in l1_ev:
        cs = json.dumps(e.get("conditions", []))
        if '"Won", "=", "1"' in cs and "Space" in cs and "NextReady" not in json.dumps(e):
            e["_drop"] = True     # Space+Won -> reemplazado por next_level_events
        if '"Won", "=", "1"' in cs and "MouseButtonReleased" in cs:
            for a in e["actions"]:
                if a["type"]["value"] == "Scene":
                    a["parameters"][1] = q("Level2")
    level1["events"] = [e for e in l1_ev if not e.get("_drop")]
    if not any("NextReady" in json.dumps(e) for e in level1["events"]):
        level1["events"] += next_level_events("Level2")
    # ESC en Game Over / Victoria -> menú principal (antes solo había R).
    # No choca con la pausa (esa exige Over=0 y Won=0). Y al llegar al menú no
    # dispara su "ESC: Salir": ese usa JustPressed y el runtime ignora las
    # repeticiones de tecla (keydown con t.repeat).
    def is_esc_menu(e):
        conds = e.get("conditions", [])
        return any(c["type"]["value"] == "KeyFromTextPressed" and "Escape" in c["parameters"][1]
                   for c in conds) and \
            any(a["type"]["value"] == "Scene" and "MainMenu" in a["parameters"][1]
                for a in e.get("actions", []))
    if not any(is_esc_menu(e) for e in level1["events"]):
        for var in ("Over", "Won"):
            ev_ = std([ins("KeyFromTextPressed", ["", q("Escape")]),
                       ins("VarScene", [var, "=", "1"])],
                      [ins("ChangeTimeScale", ["", "1"]), ins("Scene", ["", q("MainMenu"), "no"])])
            level1["events"].append(ev_)
    GAME_OVER_TXT = "GAME OVER\n[R] o click: reintentar  [ESC]: menu"
    l1_objs["GameOverText"]["content"]["text"] = GAME_OVER_TXT
    if not any(v["name"] == "NextReady" for v in level1["variables"]):
        level1["variables"].append(num_var("NextReady", 0))
    l1_objs["VictoryText"]["content"]["text"] = \
        "LLEGASTE AL LABORATORIO\n[Espacio]/click: Nivel 2\n[R]: repetir  [ESC]: menu"

    generic = filter_events  # alias corto

    def cp(n, new=None):
        o = copy.deepcopy(l1_objs[n])
        if new:
            o["name"] = new
        return o

    hud = ["Heart1", "Heart2", "Heart3", "Heart4", "GameOverText", "VictoryText",
           "PauseTitle", "PauseMusic", "PauseSfx", "PauseHint"]
    hud_inst = [dict(i) for i in level1["instances"] if i["name"] in hud]
    for i in hud_inst:
        i.pop("persistentUuid", None)

    def lab_objects():
        ground = cp("Ground")
        ground["texture"] = "lab_floor.png"
        far = cp("CityFar", "LabFar")
        far["texture"], far["width"], far["height"] = "lab_far.png", 224, 176
        near = cp("CityNear", "LabNear")
        near["texture"], near["width"], near["height"] = "lab_near.png", 224, 64
        shelf = cp("Cable", "Estante")
        shelf["texture"], shelf["width"], shelf["height"] = "lab_shelf.png", 32, 8
        glass = cp("RebarSpikes", "GlassSpikes")
        glass["texture"] = "lab_glass.png"
        return [ground, far, near, shelf, glass]

    def lab_bg_inst(width):
        return [inst("LabFar", -300, -66, "BG_far", 0, width + 600, 176, True),
                inst("LabNear", -300, GROUND_Y - 64, "BG_near", 0, width + 600, 64, True)]

    # ================================================================ Level2
    zombie_types = sorted({z[0] for z in L2_ZOMBIES})
    virus_types = [v[0] for v in L2_VIRUS]
    objs2 = [cp("Player")] + lab_objects() + [cp(n) for n in hud] + \
        [cp("Antidoto"), cp("Meta"), cp("ZombiePoofFX"), cp("InfectedGasFX")]
    def sprite_zombie(name, folder, tbf):
        """Clon de ZombieF (conserva Infected + efecto InfectedOutline) con los
        8 frames de caminata de game/assets/<folder>/."""
        o = cp("ZombieF", name)
        o.pop("effects[0]", None)       # clave basura del bug del 21/09
        a = o["animations"][0]
        a["directions"][0]["timeBetweenFrames"] = tbf
        proto = a["directions"][0]["sprites"][0]
        sprites = []
        for i in range(1, 9):
            img = f"{folder.replace('_', '')}_Walk_{i}.png"
            path = f"assets/{folder}/{folder}_Walk_{i}.png"
            assert os.path.exists(f"game/{path}"), f"falta {path} (¿gen_zombies_lab.py?)"
            ensure_resource(d, img, path)
            sp = copy.deepcopy(proto)
            sp["image"] = img
            sprites.append(sp)
        a["directions"][0]["sprites"] = sprites
        return o

    for z in zombie_types:
        o = sprite_zombie(z, *LAB_ZOMBIES[z]) if z in LAB_ZOMBIES else cp(z)
        add_obj_vars(o, [("Dir", 1), ("MinX", 0), ("MaxX", 0), ("Speed", 20)])
        objs2.append(o)
    for v in virus_types:
        o = cp(v)
        add_obj_vars(o, [("Angle", 0), ("Next", 2), ("Init", 0), ("MinX", 0),
                         ("MaxX", 0), ("MinY", 0), ("MaxY", 0)])
        objs2.append(o)
    # --- objetos de las mecánicas nuevas
    for f in ("camilla", "wet_floor", "wet_sign", "vent", "airflow", "lab_cabinet"):
        ensure_resource(d, f"{f}.png", f"assets/Lab/{f}.png")

    def deco_sprite(name, image, platform=False):
        o = cp("Meta", name)
        o["animations"][0]["directions"][0]["sprites"][0]["image"] = image
        o["behaviors"] = copy.deepcopy(l1_objs["Ground"]["behaviors"]) if platform else []
        return o

    def tiled(name, texture, w, h, platform=False):
        o = cp("CityFar", name)
        o["texture"], o["width"], o["height"] = texture, w, h
        o["behaviors"] = copy.deepcopy(l1_objs["Ground"]["behaviors"]) if platform else []
        return o

    camilla = deco_sprite("Camilla", "camilla.png", platform=True)
    add_obj_vars(camilla, [("Dir", 1), ("MinX", 0), ("MaxX", 0), ("Speed", 40)])
    objs2 += [camilla, tiled("WetFloor", "wet_floor.png", 32, 4),
              deco_sprite("WetSign", "wet_sign.png"), tiled("Vent", "vent.png", 32, 6),
              tiled("AirFlow", "airflow.png", 32, 32),
              tiled("Gabinete", "lab_cabinet.png", 32, 32, platform=True)]
    keep2 = {o["name"] for o in objs2} | {"Zombies", "Virus"}
    groups2 = [{"name": "Zombies", "objects": [{"name": z} for z in zombie_types]},
               {"name": "Virus", "objects": [{"name": v} for v in virus_types]}]

    inst2 = [inst("Player", 40, PLAYER_Y, "", 1, 18, 25, True)] + lab_bg_inst(L2_WIDTH)
    for x0, x1 in L2_FLOOR:
        inst2.append(inst("Ground", x0, GROUND_Y, "", 1, x1 - x0, 96, True))
    for (_, a), (b, _) in zip(L2_FLOOR, L2_FLOOR[1:]):
        inst2.append(inst("GlassSpikes", a, 160, "", -1, b - a, 46, True))
    for x, y, w in L2_SHELVES:
        inst2.append(inst("Estante", x, y, "", 0, w, 8, True))
    for n, x, mn, mx, sp in L2_ZOMBIES:
        inst2.append(inst(n, x, ZOMBIE_Y, "", 2, ivars=[
            num_var("Dir", 1), num_var("MinX", mn), num_var("MaxX", mx), num_var("Speed", sp)]))
    for n, x, y, mnx, mxx, mny, mxy in L2_VIRUS:
        inst2.append(inst(n, x, y, "", 6, ivars=[
            num_var("MinX", mnx), num_var("MaxX", mxx),
            num_var("MinY", mny), num_var("MaxY", mxy)]))
    for x, y in L2_ANTIDOTES:
        inst2.append(inst("Antidoto", x, y, "", 5))
    inst2.append(inst("Meta", L2_META_X, GROUND_Y - 47, "", 1))
    for x0, x1 in L2_WET:
        inst2.append(inst("WetFloor", x0, GROUND_Y - 2, "", 3, x1 - x0, 4, True))
        inst2.append(inst("WetSign", x0 + 4, GROUND_Y - 18, "", 0))
    for x, mn, mx, sp in L2_CAMILLAS:
        inst2.append(inst("Camilla", x, GROUND_Y, "", 1, CAMILLA_W, CAMILLA_H, True, ivars=[
            num_var("Dir", 1), num_var("MinX", mn), num_var("MaxX", mx), num_var("Speed", sp)]))
    for x, top in L2_VENTS:
        inst2.append(inst("AirFlow", x, top, "", 4, 32, GROUND_Y - top, True))
        inst2.append(inst("Vent", x, GROUND_Y - 4, "", 3, 32, 6, True))
    cx, cy, cw = L2_CABINET
    inst2.append(inst("Gabinete", cx, cy, "", 1, cw, GROUND_Y - cy, True))
    inst2 += copy.deepcopy(hud_inst)

    ev2 = [camera_event(-100, -65, L2_WIDTH, 205)] + \
        generic(level1["events"], l1_names, keep2) + \
        zombie_patrol_events() + virus_events() + checkpoint_events(L2_CHECKPOINTS) + \
        mechanics_events(l1_objs["Player"])
    retarget_scenes(ev2, {q("Level2"): q("Level3"), q("Level1"): q("Level2")})
    lvl2 = build_scene("Level2", level1, objs2, groups2, inst2, ev2, (14, 22, 26))
    next(o for o in objs2 if o["name"] == "VictoryText")["content"]["text"] = \
        "LLEGASTE AL CORAZON DEL LAB\n[Espacio]/click: Nivel 3\n[R]: repetir  [ESC]: menu"

    # ================================================================ Level3
    # el jefe se arma con los frames de Zombie_T: ZombieT ya no existe en
    # Level1 (wire_n1_horda_lab.py lo sacó para reservar el look al jefe)
    boss = sprite_zombie("PacienteZero", "Zombie_T", 0.13)
    boss["variables"] = []
    objs3 = [cp("Player")] + lab_objects() + [cp(n) for n in hud] + \
        [cp("ZombiePoofFX"), boss,
         text_obj("BossHPText", "PACIENTE ZERO  3/3", 12, "240;120;120")]
    next(o for o in objs3 if o["name"] == "VictoryText")["content"]["text"] = \
        "DERROTASTE AL PACIENTE ZERO\n[Espacio]/click o [ESC]: menu\n[R]: repetir"
    keep3 = {o["name"] for o in objs3}

    inst3 = [inst("Player", 60, ARENA_GROUND - 26, "", 1, 18, 25, True)] + \
        lab_bg_inst(ARENA_W) + [
        inst("Ground", -40, ARENA_GROUND, "", 1, ARENA_W + 80, 96, True),
        inst("Ground", -40, -200, "", 1, 40, ARENA_GROUND + 200, True),        # pared izq.
        inst("Ground", ARENA_W, -200, "", 1, 40, ARENA_GROUND + 200, True),    # pared der.
        inst("PacienteZero", BOSS_X, ARENA_GROUND - BOSS_H, "", 2, BOSS_W, BOSS_H, True),
        inst("BossHPText", 300, 14, "UI", 30),
    ]
    for x, y, w in L3_SHELVES:
        inst3.append(inst("Estante", x, y, "", 0, w, 8, True))
    for i in inst3:
        if i["layer"] in ("BG_far", "BG_near"):
            i["y"] += ARENA_GROUND - GROUND_Y
    inst3 += copy.deepcopy(hud_inst)

    ev3 = [std([once()], [ins("ModVarScene", ["CheckX", "=", "60"]),
                          ins("ModVarScene", ["CheckY", "=", str(ARENA_GROUND - 34)])]),
           camera_event(0, -65 + (ARENA_GROUND - GROUND_Y), ARENA_W,
                        205 + (ARENA_GROUND - GROUND_Y))] + \
        generic(level1["events"], l1_names, keep3) + boss_events()
    # en Level3 la victoria la dispara el jefe, no la Meta (no hay Meta)
    retarget_scenes(ev3, {q("Level2"): q("MainMenu"), q("Level1"): q("Level3")})
    lvl3 = build_scene("Level3", level1, objs3, [], inst3, ev3, (14, 22, 26))
    lvl3["variables"] += [num_var("BossHP", BOSS_HP), num_var("BossState", 0),
                          num_var("BossDir", -1)]

    d["layouts"] += [lvl2, lvl3]

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("OK. layouts:", [l["name"] for l in d["layouts"]])
    for l in (lvl2, lvl3):
        print(f"{l['name']}: {len(l['objects'])} objetos, {len(l['instances'])} instancias, "
              f"{len(l['events'])} eventos top-level")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
