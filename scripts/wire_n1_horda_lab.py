#!/usr/bin/env python3
"""
wire_n1_horda_lab.py — Nivel 1 (27/09/2026):

  1. La horda pasa a ser el PERSONAL DEL LABORATORIO (médico, enfermera,
     investigador — scripts/gen_zombies_lab.py). Así en el Nivel 1 se ve
     salir a la calle a la gente del lab, y en el Nivel 2 se la vuelve a
     encontrar adentro. Renombra los objetos (y todas sus referencias en
     eventos e instancias) y les cambia los frames:
         HordaZombieF -> HordaZombieEnf   (enfermera)
         HordaZombieM -> HordaZombieMed   (médico)
         HordaZombieT -> HordaZombieInv   (investigador)
     Mismas posiciones, misma lógica de horda (no está en el grupo Zombies:
     no se infecta ni se stompea, igual que antes).

  2. Saca al ZombieT del Nivel 1: ese sprite queda reservado como look del
     jefe Paciente Zero (Level3). Borra objeto, instancia, su pertenencia
     al grupo Zombies, sus eventos de patrulla y la scene var ZombieTDir.

  3. FIX "los 4 zombies que no hacen nada" (bug viejo, captura
     4_zobies_rotos.png): el evento que termina la horda tiene la condición
     PosX(HordaZombieM) > Player.X()+380. En GDevelop una condición sobre un
     objeto FILTRA sus instancias, así que el Hide(HordaZombieM) de ese
     evento solo ocultaba la instancia que había cruzado el umbral: las
     otras 4 quedaban visibles y quietas para siempre (HordaActive=3 ya no
     las mueve), y no se podían matar porque la horda no está en el grupo
     Zombies. Se agrega un evento sin filtro: HordaActive=3 -> Hide de todo.

  4. Comportamiento nuevo de la horda (pedido del usuario, 27/09):
     - FUERA la regla "si quedás atrás de la horda: -2 vidas + volvés al
       checkpoint" (descartada).
     - NUEVO: si la horda te choca de costado, -1 vida (mismo empujón ±70
       e invulnerabilidad de 1 s que los zombies comunes). Montado encima
       (sobre HordaPiso, invisible, a la altura de las cabezas) NO daña:
       el daño exige PosY(Player) > Horda.Y() - 12. Solo con la horda
       activa (HordaActive 1 o 2): en reposo está oculta pero colisiona.
     Grupo nuevo "Horda" = HordaZombieEnf/Med/Inv.

  5. La horda suma 3 zombies de la calle NUEVOS (solo aparecen acá,
     scripts/gen_zombies_horda.py): hincha, repartidor y policía. Objetos
     HordaZombieHin/Rep/Pol (clones de HordaZombieMed con otros frames).
     Toda acción de la horda sobre HordaZombieMed (mover, Show/Hide, loop
     -850, reset por HordaShift, animación) se duplica para los nuevos: se
     comportan igual. Los 15 lugares se reparten en orden de X, alternando
     Med, Hin, Enf, Rep, Inv, Pol.

Edita game/game.json directo (backup .bak-<ts>). Idempotente: si ya no hay
HordaZombieF/M/T ni ZombieT, no hace nada.
Correr desde la raíz del repo, con GDevelop CERRADO, y DESPUÉS de
scripts/gen_zombies_lab.py. Luego volver a correr
`python3 scripts/wire_levels23.py --force` (Level2/3 copian eventos de L1).
"""
import copy
import datetime
import json
import os
import re
import shutil

GAME = "game/game.json"

RENAMES = {"HordaZombieF": "HordaZombieEnf",
           "HordaZombieM": "HordaZombieMed",
           "HordaZombieT": "HordaZombieInv"}
# objeto nuevo -> (carpeta en game/assets, segundos entre frames)
FRAMES = {"HordaZombieEnf": ("Zombie_Enf", 0.09),
          "HordaZombieMed": ("Zombie_Med", 0.11),
          "HordaZombieInv": ("Zombie_Inv", 0.14)}
REMOVE = "ZombieT"


def ensure_resource(d, name, file):
    res = d["resources"]["resources"]
    if not any(r["name"] == name for r in res):
        res.append({"file": file, "kind": "image", "metadata": "", "name": name,
                    "smoothed": False, "userAdded": True})


def set_frames(d, obj, folder, tbf):
    a = obj["animations"][0]
    direction = a["directions"][0]
    proto = direction["sprites"][0]
    sprites = []
    for i in range(1, 9):
        img = f"{folder.replace('_', '')}_Walk_{i}.png"
        path = f"assets/{folder}/{folder}_Walk_{i}.png"
        assert os.path.exists(f"game/{path}"), f"falta {path} (¿gen_zombies_lab/horda.py?)"
        ensure_resource(d, img, path)
        sp = copy.deepcopy(proto)
        sp["image"] = img
        sprites.append(sp)
    direction["sprites"] = sprites
    direction["timeBetweenFrames"] = tbf


def rename_in(value, old, new):
    """Renombra un objeto en un parámetro: nombre exacto o dentro de una
    expresión (p. ej. 'HordaZombieF.X()')."""
    if value == old:
        return new
    return re.sub(rf"\b{re.escape(old)}\b", new, value)


def walk_events(events, fn):
    for e in events:
        fn(e)
        walk_events(e.get("events", []), fn)


def refs_object(e, name):
    for ins in e.get("conditions", []) + e.get("actions", []):
        for p in ins.get("parameters", []):
            if re.search(rf"\b{re.escape(name)}\b", p):
                return True
    return False


NEW_HORDE = {"HordaZombieHin": ("Zombie_Hin", 0.09),
             "HordaZombieRep": ("Zombie_Rep", 0.08),
             "HordaZombiePol": ("Zombie_Pol", 0.12)}
HORDE_CYCLE = ["HordaZombieMed", "HordaZombieHin", "HordaZombieEnf",
               "HordaZombieRep", "HordaZombieInv", "HordaZombiePol"]
HIDE_ALL = ["HordaZombieEnf", "HordaZombieMed", "HordaZombieInv", "HumoHorda"]


def has_hide_fix(l1):
    for e in l1["events"]:
        c = e.get("conditions", [])
        if len(c) == 1 and c[0]["type"]["value"] == "VarScene" and \
                c[0]["parameters"] == ["HordaActive", "=", "3"] and \
                {a["parameters"][0] for a in e.get("actions", [])
                 if a["type"]["value"] == "Hide"} >= set(HIDE_ALL):
            return True
    return False


def cond(t, params):
    return {"type": {"value": t}, "parameters": params}


def is_left_behind_rule(e):
    """HordaActive=1 & PosX(Player) < HordaPiso.X()-25 ... -> Lives -2"""
    j = json.dumps(e)
    return '"HordaActive", "=", "1"' in j and '"Lives", "-", "2"' in j


def has_new_horde_rules(l1):
    has_hit = any(any(c["type"]["value"] == "CollisionNP" and c["parameters"][:2] ==
                      ["Player", "Horda"] for c in e.get("conditions", []))
                  for e in l1["events"])
    return has_hit and not any(is_left_behind_rule(e) for e in l1["events"])


def main():
    d = json.load(open(GAME))
    l1 = next(l for l in d["layouts"] if l["name"] == "Level1")
    names = {o["name"] for o in l1["objects"]}
    if not (set(RENAMES) & names) and REMOVE not in names and has_hide_fix(l1) \
            and has_new_horde_rules(l1) and set(NEW_HORDE) <= names:
        print("Nada que hacer (idempotente): horda del lab, sin ZombieT y con el fix de Hide.")
        return

    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    # ---------- 1. horda -> personal del lab ----------
    for old, new in RENAMES.items():
        if old not in names:
            continue
        obj = next(o for o in l1["objects"] if o["name"] == old)
        obj["name"] = new
        set_frames(d, obj, *FRAMES[new])
        n_inst = 0
        for i in l1["instances"]:
            if i["name"] == old:
                i["name"] = new
                n_inst += 1

        def fix(e, old=old, new=new):
            for ins in e.get("conditions", []) + e.get("actions", []):
                ins["parameters"] = [rename_in(p, old, new) for p in ins.get("parameters", [])]
        walk_events(l1["events"], fix)
        for ch in l1["objectsFolderStructure"]["children"]:
            if ch.get("objectName") == old:
                ch["objectName"] = new
        for g in l1["objectsGroups"]:
            for m in g["objects"]:
                if m["name"] == old:
                    m["name"] = new
        print(f"{old} -> {new} ({n_inst} instancias)")

    # ---------- 2. fuera ZombieT (reservado para el jefe) ----------
    if REMOVE in names:
        before = len(l1["events"])
        l1["events"] = [e for e in l1["events"] if not refs_object(e, REMOVE)]
        # (los eventos de ZombieT son todos top-level; por las dudas, sub-eventos)
        walk_events(l1["events"], lambda e: e.__setitem__(
            "events", [s for s in e.get("events", []) if not refs_object(s, REMOVE)]))
        n_inst = sum(1 for i in l1["instances"] if i["name"] == REMOVE)
        l1["instances"] = [i for i in l1["instances"] if i["name"] != REMOVE]
        l1["objects"] = [o for o in l1["objects"] if o["name"] != REMOVE]
        l1["objectsFolderStructure"]["children"] = [
            c for c in l1["objectsFolderStructure"]["children"] if c.get("objectName") != REMOVE]
        for g in l1["objectsGroups"]:
            g["objects"] = [m for m in g["objects"] if m["name"] != REMOVE]
        l1["variables"] = [v for v in l1["variables"] if v["name"] != "ZombieTDir"]
        print(f"ZombieT fuera: {n_inst} instancia(s), {before - len(l1['events'])} evento(s)")

    # ---------- 3. fix: ocultar TODA la horda al terminar ----------
    if not has_hide_fix(l1):
        idx = next(i for i, e in enumerate(l1["events"])
                   if any(a["type"]["value"] == "ModVarScene" and a["parameters"][:3] ==
                          ["HordaActive", "=", "3"] for a in e.get("actions", [])))
        l1["events"].insert(idx + 1, {
            "type": "BuiltinCommonInstructions::Standard",
            "conditions": [{"type": {"value": "VarScene"},
                            "parameters": ["HordaActive", "=", "3"]}],
            "actions": [{"type": {"value": "Hide"}, "parameters": [n]} for n in HIDE_ALL],
            "events": []})
        print("fix: evento 'HordaActive=3 -> Hide de toda la horda' agregado")

    # ---------- 4. comportamiento nuevo: choque = -1 vida ----------
    if not has_new_horde_rules(l1):
        if not any(g["name"] == "Horda" for g in l1["objectsGroups"]):
            l1["objectsGroups"].append({"name": "Horda",
                                        "objects": [{"name": n} for n in HIDE_ALL[:3]]})
        before = len(l1["events"])
        l1["events"] = [e for e in l1["events"] if not is_left_behind_rule(e)]
        print(f"fuera la regla 'quedaste atrás': {before - len(l1['events'])} evento(s)")
        idx = next(i for i, e in enumerate(l1["events"])
                   if any(a["type"]["value"] == "ModVarScene" and a["parameters"][:3] ==
                          ["HordaActive", "=", "3"] for a in e.get("actions", [])))
        for op, dx in ((">=", "70"), ("<", "-70")):
            idx += 1
            l1["events"].insert(idx, {
                "type": "BuiltinCommonInstructions::Standard",
                "conditions": [
                    cond("CollisionNP", ["Player", "Horda", "", "", ""]),
                    cond("VarScene", ["HordaActive", ">=", "1"]),
                    cond("VarScene", ["HordaActive", "<=", "2"]),
                    cond("PosY", ["Player", ">", "Horda.Y() - 12"]),
                    cond("ObjectTimer", ["Player", '"Invuln"', "1"]),
                    cond("PosX", ["Player", op, "Horda.X()"])],
                "actions": [
                    cond("ModVarScene", ["Lives", "-", "1"]),
                    cond("ResetObjectTimer", ["Player", '"Invuln"']),
                    cond("SetAnimationName", ["Player", '"Hit"']),
                    cond("PlaySound", ["", "sfx_hurt.wav", "no", "GlobalVariable(SfxVolume)", "1"]),
                    cond("SetX", ["Player", "+", dx]),
                    cond("SetY", ["Player", "+", "-30"])],
                "events": []})
        print("nuevo: choque lateral con la horda -> -1 vida")

    # ---------- 5. 3 zombies nuevos de la calle en la horda ----------
    names = {o["name"] for o in l1["objects"]}
    if not set(NEW_HORDE) <= names:
        proto = next(o for o in l1["objects"] if o["name"] == "HordaZombieMed")
        pos = next(i for i, o in enumerate(l1["objects"]) if o is proto)
        for k, (new, (folder, tbf)) in enumerate(NEW_HORDE.items(), 1):
            o = copy.deepcopy(proto)
            o["name"] = new
            set_frames(d, o, folder, tbf)
            l1["objects"].insert(pos + k, o)
            l1["objectsFolderStructure"]["children"].append({"objectName": new})
        horda = next(g for g in l1["objectsGroups"] if g["name"] == "Horda")
        horda["objects"] += [{"name": n} for n in NEW_HORDE]

        def dup(e):
            for key in ("actions",):
                out = []
                for a in e.get(key, []):
                    out.append(a)
                    if a.get("parameters") and a["parameters"][0] == "HordaZombieMed":
                        for new in NEW_HORDE:
                            c = copy.deepcopy(a)
                            c["parameters"][0] = new
                            out.append(c)
                e[key] = out
        walk_events(l1["events"], dup)
        # repartir los 15 lugares alternando los 6 tipos, en orden de X
        slots = sorted((i for i in l1["instances"] if i["name"] in HORDE_CYCLE),
                       key=lambda i: i["x"])
        for n, inst in enumerate(slots):
            inst["name"] = HORDE_CYCLE[n % len(HORDE_CYCLE)]
        from collections import Counter
        print("horda:", dict(Counter(i["name"] for i in slots)))

    left = re.findall(r"\b(ZombieT|HordaZombie[FMT])\b", json.dumps(l1))
    assert not left, f"quedaron referencias: {set(left)}"

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("OK. Level1:", len(l1["objects"]), "objetos,", len(l1["instances"]), "instancias,",
          len(l1["events"]), "eventos")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré este script desde la raíz del repo"
    main()
