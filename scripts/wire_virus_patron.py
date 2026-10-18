#!/usr/bin/env python3
"""
wire_virus_patron.py  —  los virus voladores originales (grupo `Virus`, L1 y
L2) dejan el vuelo al azar y siguen un PATRÓN FIJO y legible.

Por qué (playtest 16/10, "frustrante"): con el rumbo random cada 1.5-2.5 s
no había nada que aprender; la única jugada segura era esperar, a veces
4-5 s (medido con una simulación de cruzar caminando). Con patrón periódico
el jugador mira una o dos vueltas y pasa en el momento justo: espera máxima
~1 s, y la dificultad pasa a ser de timing, no de suerte. Los minivirus
(los que escupe el zombie) siguen erráticos y persiguen: contraste de roles.

Trayectoria (coordenadas de la esquina sup-izq del sprite, t = VirusT):
    X = CX + AX * sin(t*WX + PX)
    Y = CY + AY * sin(t*WY + PY)
  - ascensor: AX=0              - péndulo: WY=2*WX, PY=pi/2 (baja en el medio)
  - ocho:     WY=2*WX           - círculo: WX=WY, PY=PX+pi/2
VirusT (scene var) acumula TimeDelta(), así se congela con time scale 0
(pausa, popup de nota) igual que antes.

Edita game/game.json (backup .bak-<ts>, idempotente, eventos marcados con
"_virus_patron": true):
  - saca los eventos del vuelo random (L1: los de Virus<N>Angle/NextChange;
    L2: los ForEach de Angle/Next/Init de wire_levels23.py y su comentario)
  - variables de objeto CX/CY/AX/AY/WX/WY/PX/PY en cada Virus<N>
  - scene var VirusT + 2 eventos (avanzar el tiempo, posicionar el grupo)
  No toca el daño, el contagio de zombies ni el brillo por cercanía.
Re-correr después de `wire_levels23.py --force` (regenera el vuelo random
en L2).
Uso:  python3 scripts/wire_virus_patron.py   (raíz del repo, GDevelop CERRADO)
"""
import datetime
import json
import math
import os
import re
import shutil

GAME = "game/game.json"
H = math.pi / 2
KEYS = ("CX", "CY", "AX", "AY", "WX", "WY", "PX", "PY")

# piso en y=110, Lio parado ocupa y 85..110 y salta ~37 px.
PATRONES = {
    "Level1": {
        # arranque: sube y baja en el lugar, se pasa cuando está arriba
        "Virus3": (150, 47, 0, 37, 0, 2.4, 0, 0),
        # péndulo: barre de lado a lado y baja al pasar por el medio
        "Virus4": (620, 44, 60, 34, 1.6, 3.2, 0, H),
        # ascensor en el medio del puente (x 874-962). Era un ocho en x=850
        # que barría las patrullas de ZombieM (680-880) y ZombieN (730-850):
        # contagiaba a varios y se juntaban zombies escupiendo (playtest 16/10).
        # Acá queda entre ZombieM (hasta ~914) y ZombieO (desde ~958).
        "Virus2": (926, 47, 0, 37, 0, 2.4, 0, 1.0),
        # tramo final: dos círculos girando en sentidos opuestos
        "Virus5": (2250, 52, 32, 32, 2.4, 2.4, 0, H),
        "Virus1": (2460, 52, 32, 32, -2.4, 2.4, 0, H + 1.6),
    },
    "Level2": {
        # ocho por encima de los estantes (amenaza al que va por arriba)
        "Virus1": (710, 30, 90, 26, 1.2, 2.4, 0, 0),
        # péndulo sobre el estante largo
        "Virus2": (1550, 34, 90, 30, 1.4, 2.8, 0, H),
        # círculo en el pasillo abierto
        "Virus3": (1980, 52, 32, 32, 2.2, 2.2, 0, H),
    },
}

OLD_L1 = re.compile(r"Virus\d(Angle|NextChange)")


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds,
            "actions": acts, "_virus_patron": True}


def comment(text):
    return {"type": "BuiltinCommonInstructions::Comment", "color": {
        "b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0},
        "comment": text, "comment2": "", "_virus_patron": True}


def is_old(lay_name, e):
    s = json.dumps(e, ensure_ascii=False)
    if e.get("_virus_patron"):
        return True
    if lay_name == "Level1":
        return e.get("type") == "BuiltinCommonInstructions::Standard" and bool(OLD_L1.search(s))
    if e.get("type") == "BuiltinCommonInstructions::Comment":
        return "Vuelo genérico de virus" in s
    return (e.get("type") == "BuiltinCommonInstructions::ForEach"
            and e.get("object") == "Virus" and '"Angle"' in s)


def new_events():
    v = lambda k: f"Virus.Variable({k})"
    t = "Variable(VirusT)"
    return [
        comment("Vuelo de virus con patrón fijo (wire_virus_patron.py): "
                "X = CX + AX*sin(t*WX+PX), Y = CY + AY*sin(t*WY+PY), t = VirusT."),
        std([], [ins("ModVarScene", ["VirusT", "+", "TimeDelta()"])]),
        std([], [
            ins("SetX", ["Virus", "=", f"{v('CX')} + {v('AX')} * sin({t} * {v('WX')} + {v('PX')})"]),
            ins("SetY", ["Virus", "=", f"{v('CY')} + {v('AY')} * sin({t} * {v('WY')} + {v('PY')})"]),
        ]),
    ]


def main():
    # con microsegundos: dos corridas en el mismo segundo pisaban el backup
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))

    for lay in d["layouts"]:
        pats = PATRONES.get(lay["name"])
        if not pats:
            continue
        evs = lay["events"]
        idx = [i for i, e in enumerate(evs) if is_old(lay["name"], e)]
        assert idx, f"{lay['name']}: no encontré los eventos de vuelo"
        at = idx[0]
        lay["events"] = [e for i, e in enumerate(evs) if i not in set(idx)]
        lay["events"][at:at] = new_events()

        if not any(x["name"] == "VirusT" for x in lay["variables"]):
            lay["variables"].append({"name": "VirusT", "type": "number", "value": 0})

        for o in lay["objects"]:
            if o["name"] not in pats:
                continue
            vals = dict(zip(KEYS, pats[o["name"]]))
            o["variables"] = [x for x in o.get("variables", []) if x["name"] not in KEYS]
            o["variables"] += [{"name": k, "type": "number", "value": round(vals[k], 4)}
                               for k in KEYS]
            # en el editor, la instancia queda donde arranca el patrón (t=0)
            for i in lay["instances"]:
                if i["name"] == o["name"]:
                    i["x"] = round(vals["CX"] + vals["AX"] * math.sin(vals["PX"]))
                    i["y"] = round(vals["CY"] + vals["AY"] * math.sin(vals["PY"]))
        print(lay["name"], "eventos viejos sacados:", len(idx), "| virus:", ", ".join(pats))

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    main()
