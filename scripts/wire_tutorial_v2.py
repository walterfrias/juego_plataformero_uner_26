#!/usr/bin/env python3
"""
wire_tutorial_v2.py — pulido del Tutorial (2026-09-30): textos + coleccionables.

Problemas que arregla:
  - IntroText y HintClimb decían "Hello" en tamaño 30 (se crearon por MCP
    con el contenido por defecto y nunca se les cargó el texto).
  - Los hints se pisaban por orden de eventos y no enseñaban ni el
    antídoto ni la mochila, que sí aparecen en el Nivel 1.

Qué hace:
  - Reescribe los carteles (mismo estilo que HintMove: 13 px, outline) y
    agrega HintAnti, HintGlide, HintExit + el contador TutAntiText.
  - Copia de Level1 los objetos Antidoto, Mochila y MochilaWorn (mismos
    sprites, sin arte nuevo) y pone 2 antídotos + 1 mochila:
      Antídoto A  x=165 y=62  -> hay que saltar para agarrarlo.
      Mochila     x=270 y=90  -> habilita el planeo.
      Antídoto B  x=445 y=16  -> desde arriba del poste (saltar/planear).
  - Hints por zona de PosX(Player). Cada evento de zona oculta el grupo
    TutHints y muestra uno solo, en orden creciente: gana la última zona
    alcanzada en el mismo frame (no hay toggles, así que no aplica el
    problema de los eventos hermanos que se deshacen).
  - Stomp con IsFalling (igual que Level1).
  - Planeo con Espacio O J (Level1 solo tenía Espacio): también agrega el
    evento con "j" en Level1 para que lo que enseña el tutorial sea cierto.

Idempotente: si ya existe el objeto TutAntiText no hace nada.
GDevelop tiene que estar CERRADO. Correr desde la raíz del repo:
    python3 scripts/wire_tutorial_v2.py
"""
import copy
import datetime
import json
import os
import shutil

GAME = "game/game.json"

TEXTS = {
    "IntroText": "Buenos Aires cayó ante el virus.\nLio es inmune: tiene que llegar al origen.",
    "HintMove": "Flechas o A/D: moverte",
    "HintJump": "Espacio o J: saltar\nAgarrá el antídoto de arriba",
    "HintAnti": "Antídotos: juntá los 4 de cada nivel\ny ganás una vida extra",
    "HintGlide": "Mochila: cayendo, mantené Espacio o J\npara planear",
    "HintClimb": "W/S o flechas: trepar el poste\nArriba hay otro antídoto",
    "HintStomp": "Caele encima a los zombies para eliminarlos\nDe costado te lastiman (acá no, es práctica)",
    "HintExit": "ESC o P: pausa\nEntrá al cartel para ir al Nivel 1",
}
HINTS = [n for n in TEXTS if n != "IntroText"]

# zonas: (PosX mínima del Player, hints visibles)
ZONES = [
    (0, ["IntroText", "HintMove"]),
    (110, ["HintJump"]),
    (200, ["HintAnti"]),
    (235, ["HintGlide"]),
    (320, ["HintClimb"]),
    (480, ["HintStomp"]),
    (700, ["HintExit"]),
]

ANTI_TOTAL = 2


def ins(t, params):
    return {"type": {"value": t}, "parameters": params}


def std(conds, acts):
    return {"type": "BuiltinCommonInstructions::Standard", "conditions": conds,
            "actions": acts, "events": []}


def inst(name, x, y, layer="", z=1):
    return {"angle": 0, "customSize": False, "height": 0, "layer": layer, "name": name,
            "width": 0, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def main():
    d = json.load(open(GAME))
    tut = next(l for l in d["layouts"] if l["name"] == "Tutorial")
    l1 = next(l for l in d["layouts"] if l["name"] == "Level1")

    if any(o["name"] == "TutAntiText" for o in tut["objects"]):
        print("Tutorial v2 ya aplicado (idempotente) — no hago nada.")
        return

    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    template = copy.deepcopy(next(o for o in tut["objects"] if o["name"] == "HintMove"))

    def text_obj(name, txt, align="left"):
        o = copy.deepcopy(template)
        o["name"] = name
        o["content"]["text"] = txt
        o["content"]["characterSize"] = 13
        o["content"]["textAlignment"] = align
        return o

    # --- objetos: fuera los textos viejos, entran los nuevos ---
    old_text = {o["name"] for o in tut["objects"] if o["type"] == "TextObject::Text"}
    tut["objects"] = [o for o in tut["objects"] if o["name"] not in old_text]
    tut["instances"] = [i for i in tut["instances"] if i["name"] not in old_text]

    new_objs = [text_obj(n, t) for n, t in TEXTS.items()]
    new_objs.append(text_obj("TutAntiText", ""))
    for name in ("Antidoto", "Mochila", "MochilaWorn"):
        new_objs.append(copy.deepcopy(next(o for o in l1["objects"] if o["name"] == name)))
    tut["objects"] += new_objs

    tut["instances"] += [inst("IntroText", 12, 24, "UI", 30)]
    tut["instances"] += [inst(n, 12, 24 if n != "HintMove" else 58, "UI", 30) for n in HINTS]
    tut["instances"] += [
        inst("TutAntiText", 372, 16, "UI", 30),
        inst("Antidoto", 165, 62, "", 3),
        inst("Antidoto", 445, 16, "", 3),
        inst("Mochila", 270, 90, "", 3),
        inst("MochilaWorn", 0, 0, "", 2),
    ]

    tut["objectsFolderStructure"] = {"folderName": "__ROOT",
                                     "children": [{"objectName": o["name"]} for o in tut["objects"]]}
    tut["objectsGroups"] = [g for g in tut["objectsGroups"] if g["name"] != "TutHints"]
    tut["objectsGroups"].append({"name": "TutHints",
                                 "objects": [{"name": n} for n in TEXTS]})

    for v in ("Antidotes", "CanGlide"):
        if not any(x["name"] == v for x in tut["variables"]):
            tut["variables"].append({"name": v, "type": "number", "value": 0})

    # --- eventos: se sacan los de hints viejos y el stomp, se rearman ---
    def is_old(e):
        s = json.dumps(e)
        return any(f'"{n}"' in s for n in old_text) or ("TutZombie" in s and "Delete" in s) \
            or "TutExit" in s

    events = [e for e in tut["events"] if not is_old(e)]

    # stomp con IsFalling (como Level1)
    events.append(std(
        [ins("CollisionNP", ["Player", "TutZombie", "", "", ""]),
         ins("PlatformBehavior::IsFalling", ["Player", "PlatformerObject"]),
         ins("PosY", ["Player", "<", "TutZombie.Y()"])],
        [ins("Delete", ["TutZombie", ""]),
         ins("PlatformBehavior::PlatformerObjectBehavior::SetCurrentFallSpeed",
             ["Player", "PlatformerObject", "=", "0"]),
         ins("ModVarScene", ["BounceVel", "=", "-330"]),
         ins("PlaySound", ["", "sfx_stomp.wav", "no", "GlobalVariable(SfxVolume)", "1"])]))

    # antídotos
    events.append(std(
        [ins("CollisionNP", ["Player", "Antidoto", "", "", ""])],
        [ins("Delete", ["Antidoto", ""]),
         ins("ModVarScene", ["Antidotes", "+", "1"]),
         ins("PlaySound", ["", "sfx_pickup.wav", "no", "GlobalVariable(SfxVolume)", "1"])]))
    events.append(std([], [ins("TextObject::String", [
        "TutAntiText", "=",
        f'"Antídotos: " + ToString(Variable(Antidotes)) + "/{ANTI_TOTAL}"'])]))

    # mochila + planeo (Espacio o J)
    events.append(std([ins("BuiltinCommonInstructions::Once", [])],
                      [ins("Hide", ["MochilaWorn"])]))
    events.append(std(
        [ins("CollisionNP", ["Player", "Mochila", "", "", ""])],
        [ins("Delete", ["Mochila", ""]),
         ins("ModVarScene", ["CanGlide", "=", "1"]),
         ins("Show", ["MochilaWorn", ""]),
         ins("PlaySound", ["", "sfx_pickup.wav", "no", "GlobalVariable(SfxVolume)", "1"])]))
    for key in ('"Space"', '"j"'):
        events.append(std(
            [ins("VarScene", ["CanGlide", "=", "1"]),
             ins("PlatformBehavior::IsFalling", ["Player", "PlatformerObject"]),
             ins("KeyFromTextPressed", ["", key])],
            [ins("PlatformBehavior::MaxFallingSpeed",
                 ["Player", "PlatformerObject", "=", "80", "no"])]))
    events.append(std(
        [ins("VarScene", ["CanGlide", "=", "1"])],
        [ins("SetX", ["MochilaWorn", "=", "Player.X()+1"]),
         ins("SetY", ["MochilaWorn", "=", "Player.Y()+13"])]))

    # hints por zona: oculta el grupo, muestra el de la zona (gana la última)
    for x, names in ZONES:
        events.append(std(
            [ins("PosX", ["Player", ">=", str(x)])],
            [ins("Hide", ["TutHints"])] + [ins("Show", [n, ""]) for n in names]))

    # salida -> Level1
    events.append(std([ins("CollisionNP", ["Player", "TutExit", "", "", ""])],
                      [ins("Scene", ["", "\"Level1\"", "no"])]))

    tut["events"] = events

    # --- Level1: planeo también con J ---
    glide = next(e for e in l1["events"] if e.get("_mochila") and
                 any(c["type"]["value"] == "KeyFromTextPressed" for c in e["conditions"]))
    has_j = any(e.get("_mochila") and '"\\"j\\""' in json.dumps(e) for e in l1["events"])
    if not has_j:
        glide_j = copy.deepcopy(glide)
        for c in glide_j["conditions"]:
            if c["type"]["value"] == "KeyFromTextPressed":
                c["parameters"][1] = '"j"'
        l1["events"].insert(l1["events"].index(glide) + 1, glide_j)
        print("Level1: planeo con J agregado")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("OK. Tutorial objetos:", len(tut["objects"]), "| instancias:", len(tut["instances"]),
          "| eventos:", len(tut["events"]))


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
