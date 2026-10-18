#!/usr/bin/env python3
"""
fix_n1_horda_piso_end3.py  —  dos arreglos de Nivel 1 (playtest 16/10).

1. HordaPiso (jumpthru invisible que viaja con la horda para cruzar el río
   montado) quedaba ACTIVA cuando la horda no corría: HordaActive=0 (antes
   de que arranque en x>1580, o tras morir) y HordaActive=3 (la horda ya
   pasó y se ocultó). Resultado: una plataforma invisible en el aire pasando
   a la anciana (ZombieV, x≈1200). Ahora el behavior "Platform" solo está
   activo con HordaActive 1 o 2 (horda visible).
2. ZombieEnd3 (tramo final, x=2480) usaba el sprite de ZombieT, que es
   exclusivo del jefe Paciente Zero. Se saca la instancia (el objeto y sus
   eventos quedan, sin instancias no hacen nada).

Edita game/game.json (backup .bak-<ts>, idempotente: eventos marcados con
"_horda_piso_fix": true).
Uso:  python3 scripts/fix_n1_horda_piso_end3.py   (raíz del repo, GDevelop CERRADO)
"""
import datetime
import json
import os
import shutil

GAME = "game/game.json"
MARK = "_horda_piso_fix"


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds,
            "actions": acts, MARK: True}


def platform(on):
    return [ins("ActivateBehavior", ["HordaPiso", "Platform", "yes" if on else "no"])]


def main():
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    lay = next(x for x in d["layouts"] if x["name"] == "Level1")

    # 1) HordaPiso solo es plataforma mientras la horda corre
    lay["events"] = [e for e in lay["events"] if not e.get(MARK)]
    var = lambda op, v: ins("VarScene", ["HordaActive", op, v])  # noqa: E731
    lay["events"] += [
        {"type": "BuiltinCommonInstructions::Comment", "color": {
            "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
         "comment": "HordaPiso es plataforma solo con la horda visible (HordaActive 1-2); "
                    "si no, flotaba invisible en el aire (fix_n1_horda_piso_end3.py).",
         "comment2": "", MARK: True},
        std([var("=", "0")], platform(False)),
        std([var(">=", "1"), var("<=", "2")], platform(True)),
        std([var("=", "3")], platform(False)),
    ]

    # 2) sin el sprite del jefe en L1
    n = len(lay["instances"])
    lay["instances"] = [i for i in lay["instances"] if i["name"] != "ZombieEnd3"]
    print("instancias ZombieEnd3 sacadas:", n - len(lay["instances"]))

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main()
