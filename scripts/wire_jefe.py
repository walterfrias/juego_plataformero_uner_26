#!/usr/bin/env python3
"""
wire_jefe.py  —  Paciente Zero definitivo (18/10): reemplaza el sprite del
jefe (el zombie T agrandado al doble) por el de gen_jefe.py y le da una
animación a cada estado de la pelea. La pelea (tiempos, velocidades, vida,
escupitajos) NO cambia.

Requiere: gen_jefe.py (game/assets/Jefe/).

Edita game/game.json (backup .bak-<ts>, idempotente), en Level3:
  - objeto PacienteZero: animaciones
        Walk      6 cuadros, en loop      (estado 0 y la embestida, estado 2)
        Carga     3 cuadros, sin loop     (estado 1: se hincha antes de embestir)
        Expuesto  4 cuadros, en loop      (estado 3: núcleo verde arriba = pisalo)
    con máscara de colisión ajustada al cuerpo (la caja entera de 64x68 hacía
    que Lio "pisara" el aire sobre las espículas; aplastado, el cuerpo de
    Expuesto empieza más abajo). Se mantiene el efecto InfectedOutline.
  - eventos del jefe: donde el estado pasaba a 1 se congelaba la animación
    (PauseAnimation) → ahora "Carga"; donde pasaba a 3 (expuesto) → "Expuesto";
    donde vuelve a 0 o arranca la embestida (2) → "Walk". Se reconocen por la
    acción ModVarScene BossState = N del mismo evento.
Re-correr después de `wire_l3_recorrido.py` si se regenera L3.
Uso:  python3 scripts/wire_jefe.py   (raíz del repo, GDevelop CERRADO)
"""
import datetime
import json
import os
import shutil

from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
BOSS = "PacienteZero"
# nombre: (prefijo, cuadros, s entre cuadros, loop, máscara (x0, y0, x1, y1))
ANIMS = {
    "Walk": ("jefe_walk", 6, 0.13, True, (6, 14, 58, 68)),
    "Carga": ("jefe_carga", 3, 0.27, False, (4, 8, 60, 68)),
    "Expuesto": ("jefe_expuesto", 4, 0.18, True, (4, 22, 58, 68)),
}
STATE_ANIM = {0: "Walk", 1: "Carga", 2: "Walk", 3: "Expuesto"}


def ins(value, params):
    return {"type": {"value": value}, "parameters": params}


def animation(name, prefix, n, tbf, loop, mask):
    x0, y0, x1, y1 = mask
    poly = [[{"x": x0, "y": y0}, {"x": x1, "y": y0}, {"x": x1, "y": y1}, {"x": x0, "y": y1}]]
    return {"name": name, "useMultipleDirections": False, "directions": [{
        "looping": loop, "timeBetweenFrames": tbf, "sprites": [{
            "hasCustomCollisionMask": True, "image": f"{prefix}_{k}.png", "points": [],
            "originPoint": {"name": "origine", "x": 0, "y": 0},
            "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
            "customCollisionMask": poly} for k in range(1, n + 1)]}]}


def walk(events):
    for e in events:
        yield e
        yield from walk(e.get("events", []))


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    res = d["resources"]["resources"]
    have = {r["name"] for r in res}
    for prefix, n, *_ in ANIMS.values():
        for k in range(1, n + 1):
            nm = f"{prefix}_{k}.png"
            if nm not in have:
                res.append({"file": f"assets/Jefe/{nm}", "kind": "image", "metadata": "",
                            "name": nm, "smoothed": False, "userAdded": True})
    sc = next(x for x in d["layouts"] if x["name"] == "Level3")

    # ---- objeto ----
    boss = next(o for o in sc["objects"] if o["name"] == BOSS)
    boss["animations"] = [animation(name, *spec) for name, spec in ANIMS.items()]
    for i in sc["instances"]:
        if i["name"] == BOSS:
            i.update(customSize=True, width=64, height=68)          # 1:1 con el sprite nuevo

    # ---- eventos: una animación por estado ----
    changed = 0
    for e in walk(sc["events"]):
        acts = e.get("actions", [])
        states = [int(a["parameters"][2]) for a in acts if a["type"]["value"] == "ModVarScene"
                  and a["parameters"][0] == "BossState" and a["parameters"][1] == "="
                  and a["parameters"][2].isdigit()]
        if not states:
            continue
        anim = STATE_ANIM[states[-1]]
        touches = [a for a in acts if a["parameters"][:1] == [BOSS] and a["type"]["value"] in
                   ("PauseAnimation", "PlayAnimation", "SetAnimationName")]
        if not touches:
            continue
        # fuera las de animación del jefe; adentro: nombre + que corra
        e["actions"] = [a for a in acts if a not in touches]
        e["actions"] += [ins("SetAnimationName", [BOSS, f'"{anim}"']), ins("PlayAnimation", [BOSS])]
        changed += 1
    assert changed >= 4, f"esperaba al menos 4 eventos de cambio de estado del jefe, hay {changed}"

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print(f"Level3: jefe con {', '.join(ANIMS)} | eventos de estado con animación: {changed}")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/Jefe/jefe_walk_1.png"), "corré gen_jefe.py primero"
    main()
