#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""
wire_horda_chase.py  —  cierra el "hueco de la horda" del Nivel 1: el tramo
de persecución sobre la estampida que el GDD pide pero que estaba a medias
(la horda era una plataforma lenta que loopeaba, sin tensión ni penalización
por quedarse atrás).

Qué deja (ver GDD §6d / HIGH_CONCEPT §4-5):

  1. La horda se STAGEA detrás del jugador y ARRANCA cuando el Player pisa
     la última plataforma antes del hueco grande del río (x>1600). Antes:
     x>1300, y arrancaba lejísimo.
  2. La estampida SURGE a 130 px/s (antes 25) — más rápido que el Player
     (maxSpeed 95): tenés que subirte arriba, no podés ganarle corriendo.
  3. `HordaPiso` (jumpthru invisible, ahora 380px de ancho) es el único
     piso sobre el hueco del río (1730..1970). El Player salta arriba y
     la masa lo cruza.
  4. QUEDARSE ATRÁS cuesta 1 vida: si el frente de la horda te pasa y
     seguís en el piso (Player.X() < HordaPiso.X()-25, Player.Y()<210) →
     -1 vida + respawn en checkpoint + la horda se resetea al inicio y
     vuelve a venir. (Mecánica que faltaba.)
  5. Caer al río (Player.Y()>260, evento ya existente) ahora también
     resetea la horda, así siempre tenés otra pasada sin softlock.
  6. Al cruzar (Player.X()>2010) la horda deja de arrastrarte y se va
     corriendo hacia adelante (fase 2), después se oculta. Sale de cuadro
     limpio en vez de quedar congelada en la mitad del río.

Loop infinito con guarda: sólo recicla la horda (-850px) si el Player está
DETRÁS de ella (nunca te teletransporta mientras la venís montando).

Bookkeeping con scene var `HordaShift` (px acumulados) para poder resetear
las 3 tandas de zombies sin colapsarlas a un punto (SetX "=" las juntaría
todas).

Los eventos base se ubican por CONTENIDO, no por índice (GDevelop resavea
y reordena). Edita game/game.json (backup .bak-<ts>, idempotente).
Revertir:  REVERT=1 python3 scripts/wire_horda_chase.py
Uso:       python3 scripts/wire_horda_chase.py   (desde la raíz del repo)
Después en GDevelop: cerrar sin guardar + reabrir game/game.json.
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"

# --- parámetros de diseño (tuneables tras playtest) ---
PISO_X, PISO_Y, PISO_W = 1150, 79, 380
PISO_ORIGIN = (1482, 79, 211)   # x,y,w previos (para revert)

# posiciones x de las tandas: ORIGEN (prototipo) -> STAGED (este script).
# Se asignan por orden de x (no dependen de la posición en la lista de
# instancias). La y de cada instancia no se toca.
ORIGIN_X = {
    "HordaZombieF": [1482, 1527, 1572, 1617, 1662],
    "HordaZombieM": [1467, 1512, 1557, 1602, 1647],
    "HordaZombieT": [1497, 1542, 1587, 1632, 1677],
    "HumoHorda":    [1529, 1663],
}
_SHIFT = -302
STAGED_X = {k: [x + _SHIFT for x in v] for k, v in ORIGIN_X.items()}
TRIGGER_X = 1580          # Player.X() que dispara la estampida (última plat. antes del hueco)
SURGE_SPEED = 130         # px/s de la horda con HordaActive=1
PHASE2_SPEED = 210        # px/s cuando ya cruzaste y la horda se va
RECYCLE_AT = 2000         # HordaPiso.X() al que se recicla el loop
RECYCLE_BACK = 850        # px que retrocede (2000-850 = 1150 = origen)
CROSSED_X = 2010          # Player.X() = cruzaste, la horda te suelta
BEHIND_MARGIN = 25        # px: Player.X() < HordaPiso.X()-margen = quedaste atrás
BEHIND_Y = 210            # arriba de esto ya es "caída al río" (evento aparte)
PHASE2_HIDE_AHEAD = 380   # HordaZombieM.X() > Player.X()+esto -> ocultar

HORDA_ALL = ["HordaZombieF", "HordaZombieM", "HordaZombieT", "HordaPiso"]
HORDA_VIS = ["HordaZombieF", "HordaZombieM", "HordaZombieT", "HumoHorda"]

DESIGN_COMMENT = (
    "=== Horda de persecucion (Nivel 1). Estados en scene var HordaActive: "
    "0=en reposo detras del Player / 1=estampida (arrastra, 130px/s) / "
    "2=ya cruzaste, se va corriendo / 3=oculta. HordaPiso = jumpthru "
    "invisible, unico piso sobre el hueco del rio. HordaShift = px "
    "acumulados (para resetear las tandas sin colapsarlas). "
    "Quedarse atras o caer al rio = -1 vida + respawn + horda vuelve. "
    "Tuneables en scripts/wire_horda_chase.py. ==="
)


def C(t, params, inverted=False):
    ty = {"value": t}
    if inverted:
        ty["inverted"] = True
    return {"type": ty, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard",
            "conditions": conds, "actions": acts}


def A(t, params):
    return {"type": {"value": t}, "parameters": params}


# ---------- localizadores de eventos base ----------
def find_move(events):
    for e in events:
        for a in e.get("actions", []):
            if a["type"]["value"] == "SetX" and a["parameters"][:1] == ["HordaPiso"] \
               and "TimeDelta" in str(a["parameters"][-1]):
                return e
    return None


def find_recycle(events):
    for e in events:
        cs = e.get("conditions", [])
        if any(c["type"]["value"] == "PosX" and c["parameters"][:2] == ["HordaPiso", ">"]
               for c in cs):
            return e
    return None


def find_trigger(events):
    for e in events:
        cs = e.get("conditions", [])
        has_px = any(c["type"]["value"] == "PosX" and c["parameters"][0] == "Player" for c in cs)
        has_active0 = any(c["type"]["value"] == "VarScene"
                          and c["parameters"] == ["HordaActive", "=", "0"] for c in cs)
        if has_px and has_active0:
            return e
    return None


def find_fall(events):
    for e in events:
        cs = e.get("conditions", [])
        if len(cs) >= 2 and cs[0]["type"]["value"] == "PosY" \
           and cs[0]["parameters"][0] == "Player" and cs[0]["parameters"][1] == ">" \
           and any(c["type"]["value"] == "VarScene" and c["parameters"][0] == "Over" for c in cs):
            return e
    return None


def find_hide_start(events):
    for e in events:
        cs = e.get("conditions", [])
        if len(cs) == 1 and cs[0]["type"]["value"] == "BuiltinCommonInstructions::Once" \
           and any(a["type"]["value"] == "Hide" and a["parameters"][:1] == ["HordaPiso"]
                   for a in e.get("actions", [])):
            return e
    return None


def find_design_comment(events):
    for e in events:
        if e.get("type") == "BuiltinCommonInstructions::Comment" \
           and "Horda de persecucion" in e.get("comment", ""):
            return e
    return None


def is_ours(e):
    """eventos agregados por este script (para limpiar en re-run / revert).
    Por marca `_hchase` y, si GDevelop la borró al resavear, por contenido."""
    if not isinstance(e, dict):
        return False
    if e.get("_hchase") is True:
        return True
    conds = e.get("conditions", [])
    acts = e.get("actions", [])
    # cruzo / fase2_hide: setean HordaActive a 2 o 3
    if any(a["type"]["value"] == "ModVarScene"
           and a["parameters"][:2] == ["HordaActive", "="]
           and a["parameters"][2] in ("2", "3") for a in acts):
        return True
    # fase2_move: condición HordaActive=2
    if any(c["type"]["value"] == "VarScene" and c["parameters"] == ["HordaActive", "=", "2"]
           for c in conds):
        return True
    # quedar_atras: condición PosX Player < "HordaPiso.X() - <margen>"
    if any(c["type"]["value"] == "PosX" and c["parameters"][:2] == ["Player", "<"]
           and "HordaPiso.X() -" in str(c["parameters"][2]) for c in conds):
        return True
    return False


def reposition(insts, mapping, piso):
    """asigna x por orden (idempotente). `piso` = (x,y,w) para HordaPiso."""
    for name, xs in mapping.items():
        sel = sorted((i for i in insts if i["name"] == name), key=lambda i: i["x"])
        for i, x in zip(sel, sorted(xs)):
            i["x"] = x
    for i in insts:
        if i["name"] == "HordaPiso":
            i["x"], i["y"], i["width"] = piso
            i["customSize"] = True


def reset_actions():
    """volver la horda al origen sin colapsar las tandas + apagarla."""
    return [A("SetX", [o, "-", "Variable(HordaShift)"]) for o in HORDA_ALL] + [
        A("ModVarScene", ["HordaShift", "=", "0"]),
        A("ModVarScene", ["HordaActive", "=", "0"]),
    ]


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    events = lay["events"]
    insts = lay["instances"]
    variables = lay["variables"]

    # limpiar lo que agregamos antes (idempotente) ANTES de localizar los base
    events[:] = [e for e in events if not is_ours(e)]

    move = find_move(events)
    recycle = find_recycle(events)
    trigger = find_trigger(events)
    fall = find_fall(events)
    hide_start = find_hide_start(events)
    assert move and recycle and trigger and fall and hide_start, \
        f"falta un evento base: move={bool(move)} recycle={bool(recycle)} " \
        f"trigger={bool(trigger)} fall={bool(fall)} hide_start={bool(hide_start)}"

    # ---------- REVERT ----------
    if revert:
        reposition(insts, ORIGIN_X, PISO_ORIGIN)
        variables[:] = [v for v in variables if v["name"] != "HordaShift"]
        # move -> 25 px/s, sin HordaShift
        for a in move["actions"]:
            if a["type"]["value"] == "SetX" and a["parameters"][1] == "+" \
               and "TimeDelta" in str(a["parameters"][2]):
                a["parameters"][2] = "25 * TimeDelta()"
        move["actions"] = [a for a in move["actions"]
                           if not (a["type"]["value"] == "ModVarScene"
                                   and a["parameters"][0] == "HordaShift")]
        # recycle -> comportamiento viejo (>2060, -560, sin guardas)
        recycle["conditions"] = [C("PosX", ["HordaPiso", ">", "2060"])]
        recycle["actions"] = [A("SetX", [o, "-", "560"]) for o in HORDA_ALL]
        # trigger -> x>1300
        for c in trigger["conditions"]:
            if c["type"]["value"] == "PosX" and c["parameters"][0] == "Player":
                c["parameters"][2] = "1300"
        # fall -> sin reset de horda
        fall["actions"] = [a for a in fall["actions"]
                           if not (a["type"]["value"] in ("SetX", "ModVarScene")
                                   and a["parameters"][0] in ("HordaShift", "HordaActive")
                                   or (a["type"]["value"] == "SetX" and a["parameters"][0] in HORDA_ALL))]
        dc = find_design_comment(events)
        if dc:
            dc["comment"] = ("=== Horda de persecucion (prototipo): masa de zombies M/F. "
                             "HordaPiso (Jumpthru, invisible) es la superficie sobre la que "
                             "el Player puede saltar. HumoHorda = particulas de polvo. ===")
        _save(d)
        print("revert OK: horda vuelve al prototipo lento (25px/s, loop -560, sin quedarse-atras)")
        return

    # ---------- APPLY ----------
    # 1) scene var
    if not any(v["name"] == "HordaShift" for v in variables):
        variables.append({"name": "HordaShift", "type": "number", "value": 0})

    # 2) re-stagear instancias (idempotente: asigna por orden de x)
    reposition(insts, STAGED_X, (PISO_X, PISO_Y, PISO_W))

    # 3) move: 130 px/s + acumular HordaShift
    for a in move["actions"]:
        if a["type"]["value"] == "SetX" and a["parameters"][1] == "+" \
           and "TimeDelta" in str(a["parameters"][2]):
            a["parameters"][2] = f"{SURGE_SPEED} * TimeDelta()"
    if not any(a["type"]["value"] == "ModVarScene" and a["parameters"][0] == "HordaShift"
               for a in move["actions"]):
        move["actions"].append(A("ModVarScene", ["HordaShift", "+", f"{SURGE_SPEED} * TimeDelta()"]))

    # 4) recycle: loop con guarda (sólo si el Player está detrás) + HordaShift
    recycle["conditions"] = [
        C("VarScene", ["HordaActive", "=", "1"]),
        C("PosX", ["HordaPiso", ">", str(RECYCLE_AT)]),
        C("PosX", ["Player", "<", "HordaPiso.X()"]),
    ]
    recycle["actions"] = [A("SetX", [o, "-", str(RECYCLE_BACK)]) for o in HORDA_ALL] + [
        A("ModVarScene", ["HordaShift", "-", str(RECYCLE_BACK)]),
    ]

    # 5) trigger: x>1600
    for c in trigger["conditions"]:
        if c["type"]["value"] == "PosX" and c["parameters"][0] == "Player":
            c["parameters"][2] = str(TRIGGER_X)

    # 6) fall al río: además resetea la horda
    fall["actions"] = [a for a in fall["actions"]
                       if not (a["type"]["value"] == "SetX" and a["parameters"][0] in HORDA_ALL)
                       and not (a["type"]["value"] == "ModVarScene"
                                and a["parameters"][0] in ("HordaShift", "HordaActive"))]
    fall["actions"] += reset_actions()

    # 7) comentario de diseño
    dc = find_design_comment(events)
    if dc:
        dc["comment"] = DESIGN_COMMENT
    else:
        c = {"type": "BuiltinCommonInstructions::Comment", "comment": DESIGN_COMMENT}
        events.insert(events.index(move), c)

    # 8) eventos nuevos (marcados _hchase)
    quedar_atras = std(
        [C("VarScene", ["HordaActive", "=", "1"]),
         C("PosX", ["Player", "<", f"HordaPiso.X() - {BEHIND_MARGIN}"]),
         C("PosY", ["Player", "<", str(BEHIND_Y)])],
        [A("ModVarScene", ["Lives", "-", "1"]),
         A("SetX", ["Player", "=", "Variable(CheckX)"]),
         A("SetY", ["Player", "=", "Variable(CheckY)"]),
         A("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
           ["Player", "PlatformerObject", "=", "0"]),
         A("ModVarScene", ["BounceVel", "=", "0"])] + reset_actions())
    quedar_atras["_hchase"] = True

    cruzo = std(
        [C("VarScene", ["HordaActive", "=", "1"]),
         C("PosX", ["Player", ">", str(CROSSED_X)])],
        [A("ModVarScene", ["HordaActive", "=", "2"])])
    cruzo["_hchase"] = True

    fase2_move = std(
        [C("VarScene", ["HordaActive", "=", "2"])],
        [A("SetX", [o, "+", f"{PHASE2_SPEED} * TimeDelta()"]) for o in HORDA_VIS])
    fase2_move["_hchase"] = True

    fase2_hide = std(
        [C("VarScene", ["HordaActive", "=", "2"]),
         C("PosX", ["HordaZombieM", ">", f"Player.X() + {PHASE2_HIDE_AHEAD}"])],
        [A("Hide", [o]) for o in HORDA_VIS] + [
            # el piso invisible vuelve al origen (fuera de cuadro, lejos de la Meta)
            A("SetX", ["HordaPiso", "-", "Variable(HordaShift)"]),
            A("ModVarScene", ["HordaShift", "=", "0"]),
            A("ModVarScene", ["HordaActive", "=", "3"])])
    fase2_hide["_hchase"] = True

    # insertarlos justo después del recycle
    at = events.index(recycle) + 1
    for e in (quedar_atras, cruzo, fase2_move, fase2_hide):
        events.insert(at, e)
        at += 1

    _save(d)
    print(f"horda chase: trigger x>{TRIGGER_X}, surge {SURGE_SPEED}px/s, "
          f"piso ({PISO_X},{PISO_Y}) {PISO_W}px, recycle @{RECYCLE_AT}-{RECYCLE_BACK}")
    print("  estados HordaActive: 0 reposo / 1 estampida / 2 se va / 3 oculta")
    print("  cerrá GDevelop sin guardar y reabrí game/game.json")


def _save(d):
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))  # valida


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main(revert=os.environ.get("REVERT") == "1")
