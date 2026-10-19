#!/usr/bin/env python3
"""
wire_l3_arena_zombies.py  —  en la arena del jefe no paran de entrar zombies
(18/10). Pedido del usuario: "que en la pantalla del jefe no paren de entrar
zombies, me sirven de plataforma".

Mientras dura la pelea (BossActivo = 1, BossDown = 0, Won = 0) entra un zombie
cada ENTRA_CADA s, alternando el lado (por la izquierda sale de atrás de la
barricada, por la derecha desde afuera de la pantalla), cruza la arena caminando
sin darse vuelta y se borra al salir por el otro lado. Como mucho MAX_EN_ARENA a
la vez. Son del grupo Zombies, así que valen las reglas de siempre: pisarlo
rebota a Lio (trampolín para subir a las estatuas o saltar por arriba de la
embestida) y suma puntos con la cadena de pisotones; chocarlo de costado = −1
vida. Tipos (rotan): TODOS los NPC del juego (L1, L2 y la calle), cada uno con
su velocidad; el policía que entra no dispara (ver TIPOS). Además cae del cielo un
coronavirus de los que se desvanecen (MiniVirus) cada VIRUS_CADA s.

Variables: de escena ArenaT (cuenta tiempo con TimeDelta: se congela en pausa
y con las notas), ArenaLado (0 izq / 1 der), ArenaTipo (rota), ArenaZ (cuántos
hay). De objeto Arena = 1 en los que entran (los del recorrido no la tienen:
así no se borran ni se cuentan).

Edita game/game.json (backup .bak-<ts>, idempotente; eventos marcados con
"_l3_arena_z": true), en Level3. Re-correr después de wire_l3_recorrido.py.
Uso:  python3 scripts/wire_l3_arena_zombies.py   (raíz del repo, GDevelop CERRADO)
"""
import datetime
import json
import os
import shutil

from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
MARK = "_l3_arena_z"
ENTRA_CADA = 1.8                     # s entre zombie y zombie (3.0 → 1.8: "más zombies que entren", 18/10)
PRIMERO = 1.0                        # el primero entra 1 s después de despertar al jefe
MAX_EN_ARENA = 7                     # (4 → 7, 18/10)
PISO = 150
# (objeto, velocidad px/s): cruzan los 480 px de la arena en ~12-16 s
# TODOS los NPC del juego (18/10: "que aparezcan todos los npc del juego en este último
# enfrentamiento"), en un orden que mezcla los niveles. El policía que entra NO dispara: su
# disparo (wire_l3_mecanicas.py) necesita el timer "Fuego", que solo se arranca (Once) en
# los policías puestos al cargar la escena. La anciana sigue lenta, el corredor rápido.
TIPOS = [("ZombieM", 34), ("ZombieMed", 30), ("ZombieHin", 38), ("ZombieF", 32), ("ZombieEnf", 34),
         ("ZombieRep", 40), ("ZombieV", 16), ("ZombieInv", 28), ("ZombiePol", 34), ("ZombieD", 32),
         ("ZombieJ", 52), ("ZombieN", 32), ("ZombieO", 30)]
ALTO = 34
ENTRA_IZQ, ENTRA_DER = -34, 482      # x de entrada (la izquierda, detrás de la barricada en −16..0)
SALE_IZQ, SALE_DER = -40, 500        # se borran al pasar estos x
# coronavirus que se desvanecen (18/10: "y algunos coronavirus de los que se desvanecen"):
# el MiniVirus de wire_minivirus.py (persigue a Lio, se desvanece a los 8 s, golpe = −1 vida).
# Cae uno del cielo de la arena cada VIRUS_CADA s apuntado a Lio, si hay menos de MAX_VIRUS
# (cuentan también los que escupe el jefe).
VIRUS_CADA = 4.0
VIRUS_PRIMERO = 2.5
MAX_VIRUS = 3
VARS = ("ArenaT", "ArenaLado", "ArenaTipo", "ArenaZ", "ArenaVT", "ArenaV")


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def std(conds, acts, subs=(), mark=True):
    e = {"type": "BuiltinCommonInstructions::Standard", "conditions": conds, "actions": acts,
         "events": list(subs)}
    if mark:
        e[MARK] = True
    return e


def foreach(obj, conds, acts):
    # el motor lee "object"; el esquema del MCP usa "objectsToPick": las dos
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj, "objectsToPick": obj,
            "conditions": conds, "actions": acts, "events": [], MARK: True}


def var(name, op, val):
    return ins("VarScene", [name, op, str(val)])


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    sc = next(x for x in d["layouts"] if x["name"] == "Level3")
    names = {o["name"] for o in sc["objects"]}
    assert all(t in names for t, _ in TIPOS), "faltan zombies en Level3 (correr wire_l3_recorrido.py)"
    assert "MiniVirus" in names, "falta MiniVirus en Level3 (correr wire_minivirus.py)"

    # ---- limpieza (idempotente) ----
    sc["events"] = [e for e in sc["events"] if not e.get(MARK)]
    sc["variables"] = [v for v in sc["variables"] if v["name"] not in VARS]
    sc["variables"] += [{"name": "ArenaT", "type": "number", "value": ENTRA_CADA - PRIMERO},
                         {"name": "ArenaVT", "type": "number", "value": VIRUS_CADA - VIRUS_PRIMERO}] + [
        {"name": n, "type": "number", "value": 0} for n in VARS if n not in ("ArenaT", "ArenaVT")]

    # ---- entrada: un sub-evento por (tipo, lado) ----
    entradas = []
    for k, (obj, vel) in enumerate(TIPOS):
        for lado, (x, dire, flip) in enumerate(((ENTRA_IZQ, 1, "no"), (ENTRA_DER, -1, "yes"))):
            entradas.append(std([var("ArenaTipo", "=", k), var("ArenaLado", "=", lado)], [
                ins("Create", ["", obj, str(x), str(PISO - ALTO), ""]),
                ins("ModVarObjet", [obj, "Arena", "=", "1"]),
                ins("ModVarObjet", [obj, "Dir", "=", str(dire)]),
                ins("ModVarObjet", [obj, "Speed", "=", str(vel)]),
                ins("ModVarObjet", [obj, "MinX", "=", "-100000"]),      # sin darse vuelta: cruzan
                ins("ModVarObjet", [obj, "MaxX", "=", "100000"]),
                ins("ModVarObjet", [obj, "Infected", "=", "0"]),
                ins("FlipX", [obj, flip]),
                ins("SetAnimationName", [obj, '"Walk"']),
            ], mark=False))
    pelea = [var("BossActivo", "=", 1), var("BossDown", "=", 0), var("Won", "=", 0)]
    sc["events"] += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": f"Zombies que entran a la arena (wire_l3_arena_zombies.py): uno cada {ENTRA_CADA} s "
                    f"alternando el lado, como mucho {MAX_EN_ARENA}; cruzan y se borran al salir. "
                    "Sirven de trampolín (pisotón).",
         "comment2": "", MARK: True},
        # cuántos hay (solo los que entraron: var de objeto Arena = 1)
        std([], [ins("ModVarScene", ["ArenaZ", "=", "0"])]),
        foreach("Zombies", [ins("NumberObjectVariable", ["Zombies", "Arena", "=", "1"])],
                [ins("ModVarScene", ["ArenaZ", "+", "1"])]),
        # reloj (TimeDelta: se congela en pausa) y entrada
        std(pelea, [ins("ModVarScene", ["ArenaT", "+", "TimeDelta()"])]),
        std(pelea + [var("ArenaT", ">=", ENTRA_CADA), var("ArenaZ", "<", MAX_EN_ARENA)],
            [ins("ModVarScene", ["ArenaT", "=", "0"])],
            subs=entradas + [std([], [
                ins("ModVarScene", ["ArenaLado", "=", "1 - Variable(ArenaLado)"]),
                ins("ModVarScene", ["ArenaTipo", "=", f"mod(Variable(ArenaTipo) + 1, {len(TIPOS)})"]),
            ], mark=False)]),
        # coronavirus que caen del cielo de la arena (Create elige solo al recién creado)
        std([], [ins("ModVarScene", ["ArenaV", "=", "0"])]),
        foreach("MiniVirus", [], [ins("ModVarScene", ["ArenaV", "+", "1"])]),
        std(pelea, [ins("ModVarScene", ["ArenaVT", "+", "TimeDelta()"])]),
        std(pelea + [var("ArenaVT", ">=", VIRUS_CADA), var("ArenaV", "<", MAX_VIRUS)], [
            ins("ModVarScene", ["ArenaVT", "=", "0"]),
            ins("Create", ["", "MiniVirus", "40 + Random(392)", "-12", ""]),
            ins("ChangePlan", ["MiniVirus", "=", "900"]),
            ins("ModVarObjet", ["MiniVirus", "Ang", "=",
                                "atan2(Player.Y() + Player.Height() / 2 - MiniVirus.Y() - 8, "
                                "Player.X() + Player.Width() / 2 - MiniVirus.X() - 8)"]),
            ins("ModVarObjet", ["MiniVirus", "Next", "=", "1"]),
            ins("ResetObjectTimer", ["MiniVirus", '"Life"']),
            ins("ResetObjectTimer", ["MiniVirus", '"Retarget"']),
        ]),
        # salen por el otro lado
        std([ins("NumberObjectVariable", ["Zombies", "Arena", "=", "1"]),
             ins("PosX", ["Zombies", "<", str(SALE_IZQ)])], [ins("Delete", ["Zombies", ""])]),
        std([ins("NumberObjectVariable", ["Zombies", "Arena", "=", "1"]),
             ins("PosX", ["Zombies", ">", str(SALE_DER)])], [ins("Delete", ["Zombies", ""])]),
        # ganada la pelea: los que quedan se van (un poof cada uno), y los virus también
        std([var("BossDown", "=", 1)], [ins("Delete", ["MiniVirus", ""])]),
        std([var("BossDown", "=", 1), ins("NumberObjectVariable", ["Zombies", "Arena", "=", "1"])], [
            ins("Create", ["", "ZombiePoofFX", "Zombies.X()", "Zombies.Y()", ""]),
            ins("Delete", ["Zombies", ""])]),
    ]
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print(f"Level3: zombies en la arena cada {ENTRA_CADA} s (máx {MAX_EN_ARENA}), tipos {[t for t, _ in TIPOS]}; "
          f"minivirus cada {VIRUS_CADA} s (máx {MAX_VIRUS})")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main()
