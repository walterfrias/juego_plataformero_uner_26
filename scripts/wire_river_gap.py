#!/usr/bin/env python3
"""
wire_river_gap.py  —  rompe el suelo entre el 4to y el 5to caño y mete hierros
expuestos (rebar) saliendo del agua. El hueco es más ancho que el salto máximo
del Player => solo se cruza subido a la horda (mecánica a cablear después).

Parte el suelo y el muro de verdad (colisión incluida). NO agrega lógica de
muerte/respawn del Player ni el "te lleva la horda" (eso es la mecánica).

Edita game/game.json (backup .bak-<ts>, idempotente):
  - parte en 2 las instancias de Ground, Embankment y RiverFoam, dejando el
    hueco x[1730..1970] (240px; salto máx del Player ~90px).
  - objetos nuevos (visual): RebarSpikes, BarbedWire (púas casi al ras del
    cordón), WallBreakL/R, GapWater, GapDebris (montículos en los bordes).
  - River queda entero (se ve más agua en el hueco).
  - HORDA: el evento que la reciclaba ahora la BORRA cuando cruza el hueco
    (HordaPiso.X() > 2060). La horda camina sobre el hueco con su propio piso
    (HordaPiso, oculto) y desaparece del otro lado.

Requiere: scripts/gen_costanera.py corrido (rebar_spikes.png, wall_break_*.png).
Revertir:  REVERT=1 python3 scripts/wire_river_gap.py   (vuelve a unir el suelo)
Uso:  python3 scripts/wire_river_gap.py    (desde la raíz del repo)
"""
import json
import os
import shutil
import datetime

GAME = "game/game.json"
GAP_L, GAP_R = 1730, 1970
LVL_X0, LVL_X1 = -200, 2600
NEW = ["RebarSpikes", "WallBreakL", "WallBreakR", "GapWater", "GapDebris", "BarbedWire"]
SPLIT = ["Ground", "Embankment", "RiverFoam"]
HORDA_OBJS = ["HordaZombieF", "HordaZombieM", "HordaPiso", "HumoHorda"]
DESPAWN_X = 2060   # la horda cruzó el hueco -> desaparece


def spr(name, img):
    return {"adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False,
            "variables": [], "effects": [], "behaviors": [],
            "animations": [{"name": "Idle", "useMultipleDirections": False,
                            "directions": [{"looping": True, "timeBetweenFrames": 1.0,
                                            "sprites": [{
                                                "hasCustomCollisionMask": False, "image": img,
                                                "points": [],
                                                "originPoint": {"name": "origine", "x": 0, "y": 0},
                                                "centerPoint": {"automatic": True, "name": "centre",
                                                                "x": 0, "y": 0},
                                                "customCollisionMask": []}]}]}]}


def tiled(name, img, w, h):
    return {"assetStoreId": "", "name": name, "texture": img,
            "type": "TiledSpriteObject::TiledSprite", "width": w, "height": h,
            "variables": [], "effects": [], "behaviors": []}


def inst(name, x, y, z, w=0, h=0, custom=False):
    return {"angle": 0, "customSize": custom, "height": h, "layer": "", "name": name,
            "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}


def find_horda_recycle_event(events):
    """el evento que hoy recicla la horda (SetX HordaPiso - 700) o el que la borra."""
    for e in events:
        for a in e.get("actions", []):
            p = a.get("parameters", [])
            t = a.get("type", {}).get("value")
            if (t == "SetX" and p[:1] == ["HordaPiso"] and "700" in "".join(map(str, p))) \
               or (t == "Delete" and p[:1] == ["HordaPiso"]):
                return e
    return None


def main(revert=False):
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-000Z")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    print("backup", f"{GAME}.bak-{ts}")

    d = json.load(open(GAME))
    lay = d["layouts"][0]
    res = d["resources"]["resources"]

    # plantilla de cada objeto que se parte (tomada de la 1ra instancia viva)
    tmpl = {}
    for name in SPLIT:
        ins = [i for i in lay["instances"] if i["name"] == name]
        if ins:
            tmpl[name] = dict(ins[0])

    # limpiar: sacar todas las instancias de los partidos y de los nuevos objetos
    lay["instances"] = [i for i in lay["instances"]
                        if i["name"] not in SPLIT and i["name"] not in NEW]
    lay["objects"] = [o for o in lay["objects"] if o["name"] not in NEW]
    fs = lay.get("objectsFolderStructure", {})
    if "children" in fs:
        fs["children"] = [c for c in fs["children"] if c.get("objectName") not in NEW]

    ev = find_horda_recycle_event(lay["events"])

    if revert:
        res[:] = [r for r in res if r["name"] not in
                  ("rebar_spikes.png", "gap_debris.png", "barbed_wire.png",
                   "wall_break_l.png", "wall_break_r.png")]
        for name, t in tmpl.items():
            t["x"] = LVL_X0
            t["width"] = LVL_X1 - LVL_X0
            lay["instances"].append(t)
        if ev is not None:   # volver al reciclado original
            ev["conditions"] = [{"type": {"value": "PosX"},
                                 "parameters": ["HordaPiso", ">", "1500"]}]
            ev["actions"] = [{"type": {"value": "SetX"}, "parameters": [o, "-", "700"]}
                             for o in ("HordaPiso", "HordaZombieF", "HordaZombieM")]
        json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
        open(GAME, "a").write("\n")
        print("revert OK: suelo reunido, horda recicla de nuevo")
        return

    # re-crear cada partido en 2 tramos
    for name, t in tmpl.items():
        for x0, x1 in ((LVL_X0, GAP_L), (GAP_R, LVL_X1)):
            seg = dict(t)
            seg["x"] = x0
            seg["width"] = x1 - x0
            seg["customSize"] = True
            lay["instances"].append(seg)
        print(f"{name}: partido en {LVL_X0}..{GAP_L} y {GAP_R}..{LVL_X1}")

    # resources
    have = {r["name"] for r in res}
    for fn in ("rebar_spikes.png", "gap_debris.png", "barbed_wire.png",
               "wall_break_l.png", "wall_break_r.png"):
        if fn not in have:
            res.append({"file": f"assets/City/{fn}", "kind": "image", "metadata": "",
                        "name": fn, "smoothed": False, "userAdded": True})

    # objetos + instancias nuevas
    gw = GAP_R - GAP_L
    lay["objects"] += [
        tiled("GapWater", "river.png", gw, 90),           # el agua sube en el hueco
        tiled("RebarSpikes", "rebar_spikes.png", gw, 46),
        tiled("BarbedWire", "barbed_wire.png", gw, 14),
        spr("GapDebris", "gap_debris.png"),
        spr("WallBreakL", "wall_break_l.png"),
        spr("WallBreakR", "wall_break_r.png"),
    ]
    if "children" in fs:
        fs["children"] += [{"objectName": n} for n in NEW]
    lay["instances"] += [
        inst("GapWater", GAP_L, 138, -2, gw, 90, True),   # y138..228, tapa el hueco
        inst("RebarSpikes", GAP_L, 128, -1, gw, 46, True),  # hierros hasta ~y128
        inst("BarbedWire", GAP_L, 100, 0, gw, 14, True),     # púas casi al ras (cordón y=110)
        inst("WallBreakL", GAP_L - 12, 118, 0),
        inst("WallBreakR", GAP_R - 4, 118, 0),
        inst("GapDebris", GAP_L - 6, 96, 1),              # montículo borde izq
        inst("GapDebris", GAP_R - 42, 98, 1),             # montículo borde der
    ]

    # --- horda: en vez de reciclar, cruza el hueco y DESAPARECE ---
    if ev is not None:
        ev["conditions"] = [{"type": {"value": "PosX"},
                             "parameters": ["HordaPiso", ">", str(DESPAWN_X)]}]
        ev["actions"] = [{"type": {"value": "Delete"}, "parameters": [o, ""]}
                         for o in HORDA_OBJS]
        print(f"horda: desaparece al pasar x={DESPAWN_X}")

    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")
    json.load(open(GAME))
    print("instancias:", len(lay["instances"]), "| objetos:", len(lay["objects"]),
          "| resources:", len(res))
    print(f"HUECO x[{GAP_L}..{GAP_R}]  ({GAP_R - GAP_L}px)")


if __name__ == "__main__":
    assert os.path.exists(GAME), "corré desde la raíz del repo"
    assert os.path.exists("game/assets/City/rebar_spikes.png"), "corré gen_costanera.py primero"
    main(revert=os.environ.get("REVERT") == "1")
