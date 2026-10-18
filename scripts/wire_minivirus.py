#!/usr/bin/env python3
"""
wire_minivirus.py — el zombie infectado (estado "power", Infected=1) escupe
minivirus (pedido del 15/10). También el jefe Paciente Zero, desde que le
sacaste la primera vida.

  - Objeto MiniVirus (L1, L2, L3): copia del Virus1 de L1 (mismos frames y
    tamaño, 16 px). Uno solo con muchas instancias. Vuela como los virus
    voladores (55 px/s, cambia de rumbo cada 1.5-2.5 s), pero cada rumbo
    nuevo sale de la dirección hacia Lio ±35°: deambula y se le acerca.
    Vida: 5 s en L1 (bajada el 15/10), 8 s en L2/L3; los últimos 0.8 s se
    desvanece. Se congela con time scale 0
    (pausa, nota, mochila, fin): se mueve con TimeDelta y timers.
  - Brillo por cercanía, como los bordes de plataforma (mismos NEAR/FAR y
    color: ámbar en L1, verde tóxico en L2/L3): efecto Glow cuyo
    outerStrength va de 0 (Lio a más de 150 px) a 3 (a menos de 40).
    Lo mismo para los virus voladores (grupo Virus de L1/L2), que no
    cambian su vuelo (siguen patrullando su caja).
  - Zombies (L1, L2): mientras está infectado, si Lio está cerca (|dx|<200,
    |dy|<130) y pasaron 0.8 s desde el contagio y 2.5 s desde el último
    escupitajo -> aviso de 0.45 s (el contorno rojo parpadea + chispazo
    grave) -> escupe 1, apuntado a Lio. Con los 6 s del contagio salen 2
    como mucho. Si lo curás (stomp o 6 s)
    durante el aviso, no escupe.
  - Jefe (L3): con BossHP <= 2, en el estado 0 (camina hacia Lio): a los
    0.5 s se prende el contorno (aviso), a los 1.0 s escupe 1 (BossHP 2) o
    2 (BossHP 1) y apaga el contorno. No escupe en el estado 1 (prepara la
    embestida) para no cargar a través de sus propios virus.
  - Golpe: como el virus volador (Invuln 1 s, −1 vida, anim Hit, sfx_hurt),
    knockback de 40 px (lo aleja del minivirus). El minivirus se borra
    al tocar a Lio. No se pisan y no contagian zombies (no están en el
    grupo Virus).

Idempotente (reemplaza su objeto, sus vars y su grupo). GDevelop CERRADO.
Re-correr después de wire_levels23.py --force.
Uso:  python3 scripts/wire_minivirus.py   (desde la raíz del repo)
"""
import copy
import datetime
import json
import shutil

from wire_score_hud import act, comment, ev, put_object
from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
GROUP = "Minivirus (wire_minivirus.py)"
SPEED, SPREAD, FADE = 55, 0.35, 0.8           # px/s (= virus voladores), rad (~20°), s
# vida en s: en L1 se bajó de 8 a 5 el 15/10 (el final se hacía muy difícil)
LIFE = {"Level1": 5, "Level2": 8, "Level3": 8}
WANDER = 35                                    # ° alrededor de la dirección a Lio al cambiar de rumbo
NEAR, FAR, GLOW_MAX = 40, 150, 3               # como wire_bordes_plataforma.py (allá MAX es opacidad)
GLOW_COLOR = {"Level1": "255;206;110", "Level2": "132;214;92", "Level3": "132;214;92"}
REACH_X, REACH_Y = 200, 130
WARN, COOLDOWN, AFTER_INFECT = 0.45, 2.5, 0.8
BOSS_WARN_AT, BOSS_SPIT_AT = 0.5, 1.0        # s dentro del estado 0 (dura 1.8)

PCX = "(Player.X() + Player.Width() / 2)"
PCY = "(Player.Y() + Player.Height() / 2)"


def cmp(expr, op, val):
    return act("BuiltinCommonInstructions::CompareNumbers", [expr, op, str(val)])


def objvar(obj, var, op, val):
    return act("NumberObjectVariable", [obj, var, op, str(val)])


def setobjvar(obj, var, val):
    return act("ModVarObjet", [obj, var, "=", str(val)])


def scenevar(var, op, val):
    return act("VarScene", [var, op, str(val)])


def setscenevar(var, val):
    return act("ModVarScene", [var, "=", str(val)])


def foreach(obj, conds, acts, subs):
    # el motor lee "object"; el esquema del MCP usa "objectsToPick": van las dos
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": conds, "actions": acts, "events": subs}


def glow_effect(color):
    return {"name": "ProxGlow", "effectType": "Glow",
            "doubleParameters": {"innerStrength": 0, "outerStrength": 0, "distance": 10},
            "stringParameters": {"color": color}, "booleanParameters": {}}


def glow_action(obj):
    """outerStrength por cercanía del centro de Lio al centro de cada instancia."""
    cx, cy = f"({obj}.X() + {obj}.Width() / 2)", f"({obj}.Y() + {obj}.Height() / 2)"
    dist = f"sqrt(pow({PCX} - {cx}, 2) + pow({PCY} - {cy}, 2))"
    return act("SetEffectDoubleParameter", [obj, '"ProxGlow"', '"outerStrength"',
                                            f"clamp({GLOW_MAX} * ({FAR} - {dist}) / {FAR - NEAR}, 0, {GLOW_MAX})"])


def mini_object(src, color):
    o = copy.deepcopy(src)
    o["name"] = "MiniVirus"
    o["behaviors"] = []
    o["effects"] = [glow_effect(color)]
    o["variables"] = [{"name": "Ang", "type": "number", "value": 0},
                      {"name": "Next", "type": "number", "value": 1}]
    return o


def spit(sx, sy, n):
    """sub-eventos: uno por minivirus (Create elige solo al recién creado
    dentro de su propio sub-evento)."""
    aim = f"atan2({PCY} - ({sy}), {PCX} - ({sx}))"
    offs = [0.0] if n == 1 else [SPREAD * (2 * k / (n - 1) - 1) for k in range(n)]
    subs = []
    for off in offs:
        ang = f"({aim} + {off:.3f})"
        subs.append(ev([], [
            act("Create", ["", "MiniVirus", f"{sx} - 8", f"{sy} - 8", ""]),
            act("ChangePlan", ["MiniVirus", "=", "900"]),
            act("ModVarObjet", ["MiniVirus", "Ang", "=", ang]),
            act("ModVarObjet", ["MiniVirus", "Next", "=", "1"]),     # primer tramo recto hacia Lio
            act("ResetObjectTimer", ["MiniVirus", '"Life"']),
            act("ResetObjectTimer", ["MiniVirus", '"Retarget"']),
        ]))
    return subs


def common_events(life_s):
    """movimiento, vida y golpe a Lio (igual en los 3 niveles)."""
    hurt = [act("ModVarScene", ["Lives", "-", "1"]),
            act("ResetObjectTimer", ["Player", '"Invuln"']),
            act("SetAnimationName", ["Player", '"Hit"']),
            act("PlaySound", ["", "sfx_hurt.wav", "no", "GlobalVariable(SfxVolume)", "1"]),
            act("SetY", ["Player", "+", "-20"]),
            act("Delete", ["MiniVirus", ""])]     # acá: el knockback saca a Lio de la colisión
    hit = [act("CollisionNP", ["Player", "MiniVirus", "", "", ""]),
           act("ObjectTimer", ["Player", '"Invuln"', "1"]),
           scenevar("Over", "=", 0), scenevar("Won", "=", 0)]
    mcx, mcy = "(MiniVirus.X() + MiniVirus.Width() / 2)", "(MiniVirus.Y() + MiniVirus.Height() / 2)"
    aim = f"atan2({PCY} - {mcy}, {PCX} - {mcx})"
    life = 'MiniVirus.ObjectTimerElapsedTime("Life")'
    return [
        ev([], [act("SetX", ["MiniVirus", "+", f"cos(MiniVirus.Variable(Ang)) * {SPEED} * TimeDelta()"]),
                act("SetY", ["MiniVirus", "+", f"sin(MiniVirus.Variable(Ang)) * {SPEED} * TimeDelta()"]),
                glow_action("MiniVirus"),
                act("Opacity", ["MiniVirus", "=", f"255 * clamp(({life_s} - {life}) / {FADE}, 0, 1)"])]),
        ev([act("ObjectTimer", ["MiniVirus", '"Retarget"', "MiniVirus.Variable(Next)"])],
           [act("ResetObjectTimer", ["MiniVirus", '"Retarget"']),
            act("ModVarObjet", ["MiniVirus", "Ang", "=",
                                f"{aim} + (Random({2 * WANDER}) - {WANDER}) * 3.14159265 / 180"]),
            act("ModVarObjet", ["MiniVirus", "Next", "=", "1.5 + Random(100) / 100"])]),
        ev([act("ObjectTimer", ["MiniVirus", '"Life"', str(life_s)])], [act("Delete", ["MiniVirus", ""])]),
        ev(hit + [act("PosX", ["Player", ">=", "MiniVirus.X()"])], hurt + [act("SetX", ["Player", "+", "40"])]),
        ev(hit + [act("PosX", ["Player", "<", "MiniVirus.X()"])], hurt + [act("SetX", ["Player", "+", "-40"])]),
        ev([act("CollisionNP", ["Player", "MiniVirus", "", "", ""])], [act("Delete", ["MiniVirus", ""])]),
    ]


def warn_sound(pitch):
    return act("PlaySound", ["", "sfx_chispazo.wav", "no", "GlobalVariable(SfxVolume) * 0.5", str(pitch)])


def zombie_events():
    zcx = "(Zombies.X() + Zombies.Width() / 2)"
    mouth_y = "(Zombies.Y() + 10)"
    blink = "mod(floor(TimeFromStart() * 14), 2)"
    outline = lambda on: act("EnableEffect", ["Zombies", '"InfectedOutline"', on])   # noqa: E731
    # un ObjectTimer que no existe se crea al consultarlo y da false: sin esto,
    # la primera infección de cada zombie escupía recién a los ~3.3 s
    return [ev([act("BuiltinCommonInstructions::Once", [])],
               [act("ResetObjectTimer", ["Zombies", '"SpitCD"'])]),
            foreach("Zombies", [], [], [
        # arranca el aviso
        ev([objvar("Zombies", "Infected", "=", 1), objvar("Zombies", "Spit", "=", 0),
            act("ObjectTimer", ["Zombies", '"InfectedTime"', str(AFTER_INFECT)]),
            act("ObjectTimer", ["Zombies", '"SpitCD"', str(COOLDOWN)]),
            scenevar("Over", "=", 0), scenevar("Won", "=", 0),
            cmp(f"abs({PCX} - {zcx})", "<", REACH_X),
            cmp(f"abs({PCY} - {mouth_y})", "<", REACH_Y)],
           [setobjvar("Zombies", "Spit", 1), act("ResetObjectTimer", ["Zombies", '"SpitCD"']),
            warn_sound(0.55)]),
        # durante el aviso: el contorno parpadea; al terminar, escupe
        ev([objvar("Zombies", "Infected", "=", 1), objvar("Zombies", "Spit", "=", 1)], [], [
            ev([cmp(blink, "=", 0)], [outline("yes")]),
            ev([cmp(blink, "=", 1)], [outline("no")]),
            ev([act("ObjectTimer", ["Zombies", '"SpitCD"', str(WARN)])],
               [setobjvar("Zombies", "Spit", 0), act("ResetObjectTimer", ["Zombies", '"SpitCD"']),
                outline("yes")],
               spit(zcx, mouth_y, 1)),
        ]),
        # lo curaron durante el aviso: se cancela (el contorno ya lo apagó la cura)
        ev([objvar("Zombies", "Infected", "=", 0), objvar("Zombies", "Spit", "=", 1)],
           [setobjvar("Zombies", "Spit", 0), outline("no")]),
    ])]


def boss_events():
    bx, by = "(PacienteZero.X() + 32)", "(PacienteZero.Y() + 16)"
    in0 = [scenevar("BossState", "=", 0), scenevar("Won", "=", 0), scenevar("Over", "=", 0)]
    t = lambda s: act("ObjectTimer", ["PacienteZero", '"BossT"', str(s)])   # noqa: E731
    outline = lambda on: act("EnableEffect", ["PacienteZero", '"InfectedOutline"', on])   # noqa: E731
    return [
        ev(in0 + [scenevar("BossHP", "<=", 2), scenevar("BossHP", ">=", 1),
                  scenevar("BossSpit", "=", 0), t(BOSS_WARN_AT)],
           [setscenevar("BossSpit", 1), outline("yes"), warn_sound(0.45)]),
        ev(in0 + [scenevar("BossSpit", "=", 1), t(BOSS_SPIT_AT)],
           [setscenevar("BossSpit", 2), outline("no")], [
               ev([scenevar("BossHP", "=", 2)], [], spit(bx, by, 1)),
               ev([scenevar("BossHP", "<=", 1)], [], spit(bx, by, 2)),
           ]),
        # fuera del estado 0 se rearma para la próxima vuelta
        ev([scenevar("BossState", "!=", 0)], [setscenevar("BossSpit", 0)]),
    ]


def ensure_var(vars_, name):
    if not any(v["name"] == name for v in vars_):
        vars_.append({"name": name, "type": "number", "value": 0})


def wire(lay, src, boss):
    put_object(lay, mini_object(src, GLOW_COLOR[lay["name"]]))
    lay["instances"] = [i for i in lay["instances"] if i["name"] != "MiniVirus"]
    evs = common_events(LIFE[lay["name"]])
    if boss:
        ensure_var(lay["variables"], "BossSpit")
        evs += boss_events()
    # zombies infectados: en L1/L2 siempre; en L3 desde que tiene recorrido con
    # zombies (wire_l3_recorrido.py, 18/10)
    if any(g["name"] == "Zombies" for g in lay.get("objectsGroups", [])):
        zg = next(g for g in lay["objectsGroups"] if g["name"] == "Zombies")
        names = {o["name"] for o in zg["objects"]}
        for o in lay["objects"]:
            if o["name"] in names:
                ensure_var(o["variables"], "Spit")
        # los virus voladores también brillan por cercanía
        vg = next(g for g in lay["objectsGroups"] if g["name"] == "Virus")
        vnames = {o["name"] for o in vg["objects"]}
        for o in lay["objects"]:
            if o["name"] in vnames:
                o["effects"] = [e for e in o["effects"] if e["name"] != "ProxGlow"]
                o["effects"].append(glow_effect(GLOW_COLOR[lay["name"]]))
        evs = zombie_events() + [ev([], [glow_action("Virus")])] + evs
    lay["events"] = [e for e in lay["events"] if e.get("name") != GROUP]
    lay["events"].append({
        "type": "BuiltinCommonInstructions::Group", "name": GROUP, "source": "",
        "creationTime": 0, "folded": True, "color": {"b": 120, "g": 60, "r": 200},
        "events": [comment("Minivirus que escupe el zombie infectado"
                           + (" / el jefe desde BossHP 2" if boss else "")
                           + ". Generado por wire_minivirus.py."), *evs]})


def main():
    asegurar_gdevelop_cerrado()
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    lays = {l["name"]: l for l in g["layouts"]}
    src = next(o for o in lays["Level1"]["objects"] if o["name"] == "Virus1")
    for name, boss in (("Level1", False), ("Level2", False), ("Level3", True)):
        wire(lays[name], src, boss)
        print(f"{name}: minivirus {'del jefe' if boss else 'de zombies infectados'}")
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
