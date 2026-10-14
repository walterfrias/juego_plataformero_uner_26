#!/usr/bin/env python3
"""
wire_mochila_niveles.py — la mochila de repartidor acompaña a Lio desde que
la agarra en Level1 hasta el final (GDD §6: planeo + inventario en L2/L3).

  - Global `TieneMochila`: 1 al agarrarla en Level1, 0 al apretar "Jugar"
    en el MainMenu (como Puntaje y Nota1..7). El Tutorial no lo toca: su
    mochila es de práctica.
  - Level1: si ya la tenía (murió / reintentó después de agarrarla), arranca
    con la mochila puesta y sin el pickup, igual que las notas.
  - Level2 / Level3: objeto `MochilaWorn` (el mismo de Level1) en la
    espalda, planeo con Espacio / J mientras cae (MaxFallingSpeed 80) y
    sigue el giro del Player (wire_mochila_back.py). Todo depende de
    CanGlide, que se pone en 1 al empezar si TieneMochila = 1.

La pausa con MOCHILA (I) en L2/L3 la arma wire_notas.py.

Idempotente: grupo de eventos propio por escena; la acción agregada al
pickup de Level1 y al "Jugar" se quita antes de volver a ponerla.
Si se corre wire_levels23.py --force, volver a correr este script.

Requiere: wire_mochila.py y wire_mochila_back.py ya corridos en Level1.
Edita game/game.json (backup .bak-<ts>). GDevelop CERRADO.
Uso:  python3 scripts/wire_mochila_niveles.py   (desde la raíz del repo)
"""
import copy
import datetime
import json
import shutil
import uuid

import wire_mochila_back
from wire_score_hud import (act, comment, ev, find_event, has_cond, put_instances,
                            put_object, set_var)

GAME = "game/game.json"
GROUP = "Mochila puesta en todo el juego (wire_mochila_niveles.py)"
LEVELS = ["Level2", "Level3"]
GLIDE_SPEED = "80"
GOT = act("VarGlobal", ["TieneMochila", "=", "1"])


def strip_global(e):
    e["actions"] = [a for a in e["actions"] if a["parameters"][:1] != ["TieneMochila"]]


def replace_group(lay, events):
    lay["events"] = [e for e in lay["events"] if e.get("name") != GROUP]
    lay["events"].append({"type": "BuiltinCommonInstructions::Group", "name": GROUP,
                          "source": "", "creationTime": 0, "folded": True,
                          "color": {"b": 0, "g": 90, "r": 255}, "events": events})


def wire_level1(lay):
    pick = find_event(lay, lambda e: has_cond(e, "CollisionNP", "Player", "Mochila"), "pickup mochila")
    strip_global(pick)
    pick["actions"].append(act("ModVarGlobal", ["TieneMochila", "=", "1"]))
    replace_group(lay, [
        comment("Si ya tenía la mochila (murió / reintentó), arranca con ella puesta. "
                "Generado por wire_mochila_niveles.py."),
        # va al final: pisa el Once que la oculta al empezar
        ev([act("BuiltinCommonInstructions::Once", []), GOT],
           [act("Delete", ["Mochila", ""]),
            act("ModVarScene", ["CanGlide", "=", "1"]),
            act("Show", ["MochilaWorn", ""])]),
    ])


def wire_level(lay, worn_obj, worn_inst):
    set_var(lay, "CanGlide")
    put_object(lay, copy.deepcopy(worn_obj))
    w = copy.deepcopy(worn_inst)
    w["persistentUuid"] = str(uuid.uuid4())
    put_instances(lay, [w])
    glide = [ev([act("VarScene", ["CanGlide", "=", "1"]),
                 act("PlatformBehavior::IsFalling", ["Player", "PlatformerObject"]),
                 act("KeyFromTextPressed", ["", k])],
                [act("PlatformBehavior::MaxFallingSpeed",
                     ["Player", "PlatformerObject", "=", GLIDE_SPEED, "no"])])
             for k in ('"Space"', '"j"')]
    # va al final: después del reset de MaxFallingSpeed a 600 de cada frame
    replace_group(lay, [
        comment("Mochila puesta desde Level1 (global TieneMochila): planeo + espalda. "
                "Generado por wire_mochila_niveles.py."),
        ev([act("BuiltinCommonInstructions::Once", [])], [act("Hide", ["MochilaWorn"])]),
        ev([act("BuiltinCommonInstructions::Once", []), GOT],
           [act("ModVarScene", ["CanGlide", "=", "1"]), act("Show", ["MochilaWorn", ""])]),
        *glide,
        ev([act("VarScene", ["CanGlide", "=", "1"])],
           [act("SetX", ["MochilaWorn", "=", wire_mochila_back.X]),
            act("SetY", ["MochilaWorn", "=", wire_mochila_back.Y])]),
    ])
    wire_mochila_back.wire(lay)       # giro con el Player, tamaño y z


def wire_menu(lay):
    jugar = find_event(lay, lambda e: any(a["type"]["value"] == "Scene" and a["parameters"][1] == '"Tutorial"'
                                          for a in e.get("actions", [])), "Jugar")
    strip_global(jugar)
    jugar["actions"].insert(0, act("ModVarGlobal", ["TieneMochila", "=", "0"]))


def main():
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    gv = g.setdefault("variables", [])
    if not any(v["name"] == "TieneMochila" for v in gv):
        gv.append({"name": "TieneMochila", "type": "number", "value": 0})
    lays = {l["name"]: l for l in g["layouts"]}
    l1 = lays["Level1"]
    worn_obj = next(o for o in l1["objects"] if o["name"] == "MochilaWorn")
    worn_inst = next(i for i in l1["instances"] if i["name"] == "MochilaWorn")
    wire_level1(l1)
    print("Level1: pickup -> TieneMochila = 1; arranca con ella si ya la tenía")
    for name in LEVELS:
        wire_level(lays[name], worn_obj, worn_inst)
        print(f"{name}: mochila puesta + planeo si TieneMochila = 1")
    wire_menu(lays["MainMenu"])
    print("MainMenu: TieneMochila = 0 en Jugar")
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
