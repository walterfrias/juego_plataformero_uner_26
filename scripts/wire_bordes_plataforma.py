#!/usr/bin/env python3
"""
wire_bordes_plataforma.py — lo que se puede pisar se ilumina cuando Lio se
acerca (pedido el 14/10; ámbar en L1, verde tóxico en el lab L2/L3).

Problema: en L1 las plataformas son decorado (árboles, toldos, balcones,
faroles, cables) y se confunden con el fondo, que no se pisa. Se descartó
un pulso constante: en el juego "brillar/titilar" ya significa pickup
(antídoto, notas, mochila).

Qué hace:
  - árboles y faroles (RIM): una copia "<Nombre>Luz" del sprite con la luz
    de borde pintada (gen_luz_borde.py, variante B), misma posición y
    tamaño, z + 1, con la misma opacidad por cercanía (14/10: la barra en
    formas orgánicas se leía como una tabla flotando);
  - el resto: por cada instancia de plataforma, una instancia de `PlatEdge`
    (borde_plataforma.png, gen_borde_plataforma.py) estirada al ancho del
    canto superior de su MÁSCARA DE COLISIÓN (no de la imagen), con la
    línea clara justo sobre ese canto; misma capa que la plataforma. En la
    capa "" va con la misma z, agregada después (queda por delante de la
    plataforma y detrás de Lio); en "Decor" con z + 1, para asegurar que
    quede delante del árbol/farol (Decor está toda detrás de Lio);
  - cada frame, la opacidad depende de la distancia del centro de Lio al
    canto: 0 lejos (> FAR px), MAX cerca (< NEAR px), lineal en el medio.

Plataformas que se mueven (MOVERS, p. ej. las camillas de L2): la barra
guarda en su var Owner la var única de la plataforma (MinX) y un ForEach la
reubica cada frame (el grupo va al final, después de que se mueven).

Quedan afuera: Ground (el piso se lee solo), Poste (es escalera, se trepa)
y HordaPiso (se mueve con la horda).

Idempotente: borra las PlatEdge viejas y reemplaza su grupo de eventos.
Requiere: python3 scripts/gen_borde_plataforma.py && python3 scripts/gen_luz_borde.py
Edita game/game.json (backup .bak-<ts>). GDevelop CERRADO.
Uso:  python3 scripts/wire_bordes_plataforma.py [Escena ...]  (por defecto L1, L2, L3)
"""
import copy
import datetime
import json
import shutil
import sys
import uuid

from PIL import Image

from wire_score_hud import act, comment, ev, put_object

GAME = "game/game.json"
SCENES = sys.argv[1:] or ["Level1", "Level2", "Level3"]
GROUP = "Bordes de plataforma por cercanía (wire_bordes_plataforma.py)"
IMGS = {"Level1": "borde_plataforma.png",                 # ámbar de farol
        "Level2": "borde_plataforma_lab.png", "Level3": "borde_plataforma_lab.png"}
EDGE_H, LINE_ROW = 7, 3
NEAR, FAR, MAX = 40, 150, 230
SKIP = {"Ground", "Poste", "HordaPiso"}
# árboles y faroles: luz pintada sobre el propio sprite (gen_luz_borde.py),
# no barra: en formas orgánicas la barra se leía como una tabla flotando
RIM = ("ArbolBajo", "ArbolAlto", "Farol")
# plataformas que se mueven por eventos: su barra las sigue cada frame. La
# barra guarda en Owner el valor de esta var de objeto (único por instancia)
MOVERS = {"Camilla": "MinX"}


def edges_of(obj, inst, res_files):
    """[(x, y_canto, ancho)] del canto superior de la máscara de colisión."""
    if obj["type"] == "Sprite":
        f = obj["animations"][0]["directions"][0]["sprites"][0]
        iw, ih = Image.open("game/" + res_files[f["image"]]).size
        sx = inst["width"] / iw if inst["customSize"] else 1
        sy = inst["height"] / ih if inst["customSize"] else 1
        polys = f["customCollisionMask"] if f["hasCustomCollisionMask"] else \
            [[{"x": 0, "y": 0}, {"x": iw, "y": 0}, {"x": iw, "y": ih}, {"x": 0, "y": ih}]]
        out = []
        for poly in polys:
            xs = [p["x"] for p in poly]
            top = min(p["y"] for p in poly)
            out.append((inst["x"] + min(xs) * sx, inst["y"] + top * sy, (max(xs) - min(xs)) * sx))
        return out
    # TiledSprite (Cable): el canto es el borde de arriba de la instancia
    w = inst["width"] if inst["customSize"] else obj.get("width", 0)
    return [(inst["x"], inst["y"], w)]


def sprite_obj(name, image):
    return {"adaptCollisionMaskAutomatically": True, "assetStoreId": "", "name": name,
            "type": "Sprite", "updateIfNotVisible": False, "variables": [], "effects": [],
            "behaviors": [],
            "animations": [{"name": "Idle", "useMultipleDirections": False,
                            "directions": [{"looping": False, "timeBetweenFrames": 1, "sprites": [{
                                "hasCustomCollisionMask": False, "image": image, "points": [],
                                "originPoint": {"name": "origine", "x": 0, "y": 0},
                                "centerPoint": {"automatic": True, "name": "centre", "x": 0, "y": 0},
                                "customCollisionMask": []}]}]}]}


def proximity_event(obj, top_expr):
    """ForEach obj: opacidad según la distancia del centro de Lio al canto
    [obj.X(), obj.X() + obj.Width()] a la altura top_expr."""
    cx = "(Player.X() + Player.Width() / 2)"
    cy = "(Player.Y() + Player.Height() / 2)"
    dx = f"max(0, max({obj}.X() - {cx}, {cx} - {obj}.X() - {obj}.Width()))"
    dy = f"abs({top_expr} - {cy})"
    dist = f"sqrt(pow({dx}, 2) + pow({dy}, 2))"
    opacity = f"clamp({MAX} * ({FAR} - {dist}) / {FAR - NEAR}, 0, {MAX})"
    return {"type": "BuiltinCommonInstructions::ForEach", "object": obj,
            "objectsToPick": obj, "conditions": [], "actions": [],
            "events": [ev([], [act("Opacity", [obj, "=", opacity])])]}


def wire_rim(lay, plats, res_files):
    """copia "luz" de cada árbol/farol, misma posición y tamaño, z + 1."""
    events = []
    for name in RIM:
        if name not in plats:
            continue
        f = plats[name]["animations"][0]["directions"][0]["sprites"][0]
        src = f["image"]
        luz = src[:-4] + "_luz.png"
        luz_file = res_files[src][:-4] + "_luz.png"
        res_files[luz] = luz_file
        ih = Image.open("game/" + res_files[src]).size[1]
        top = min(p["y"] for poly in f["customCollisionMask"] for p in poly)
        obj = name + "Luz"
        put_object(lay, sprite_obj(obj, luz))
        lay["instances"] = [i for i in lay["instances"] if i["name"] != obj]
        for i in [i for i in lay["instances"] if i["name"] == name]:
            c = copy.deepcopy(i)
            c.update(name=obj, zOrder=i["zOrder"] + 1, initialVariables=[],
                     persistentUuid=str(uuid.uuid4()))
            lay["instances"].append(c)
        events.append(proximity_event(obj, f"({obj}.Y() + {obj}.Height() * {top} / {ih})"))
    return events


def follow_events(lay, moved):
    """después de que se mueven: ForEach plataforma -> su barra (Owner)."""
    events = []
    for name, (key, dx, dy) in moved.items():
        events.append({"type": "BuiltinCommonInstructions::ForEach", "object": name,
                       "objectsToPick": name, "conditions": [], "actions": [], "events": [
                           ev([act("NumberObjectVariable", ["PlatEdge", "Owner", "=", f"{name}.Variable({key})"])],
                              [act("SetX", ["PlatEdge", "=", f"{name}.X() + {dx}"]),
                               act("SetY", ["PlatEdge", "=", f"{name}.Y() + {dy}"])])]})
    return events


def wire(lay, res_files, img):
    plats = {o["name"]: o for o in lay["objects"]
             if o["name"] not in SKIP and o["name"] != "PlatEdge" and not o["name"].endswith("Luz")
             and any(b["type"] == "PlatformBehavior::PlatformBehavior" and
                     b.get("platformType", "NormalPlatform") != "Ladder" for b in o.get("behaviors", []))}
    edge = sprite_obj("PlatEdge", img)
    edge["variables"] = [{"name": "Owner", "type": "number", "value": 0}]
    put_object(lay, edge)
    lay["instances"] = [i for i in lay["instances"] if i["name"] != "PlatEdge"]
    new, moved = [], {}
    for i in list(lay["instances"]):
        if i["name"] not in plats or i["name"] in RIM:
            continue
        owner = []
        if i["name"] in MOVERS:
            key = MOVERS[i["name"]]
            val = next(v["value"] for v in i["initialVariables"] if v["name"] == key)
            owner = [{"name": "Owner", "type": "number", "value": val}]
        for x, top, w in edges_of(plats[i["name"]], i, res_files):
            if i["name"] in MOVERS:
                moved[i["name"]] = (MOVERS[i["name"]], round(x - i["x"]), round(top - i["y"]) - LINE_ROW)
            new.append({"angle": 0, "customSize": True, "width": round(w), "height": EDGE_H,
                        "layer": i["layer"], "name": "PlatEdge", "x": round(x),
                        "y": round(top) - LINE_ROW, "zOrder": i["zOrder"] + (1 if i["layer"] == "Decor" else 0),
                        "numberProperties": [], "stringProperties": [], "initialVariables": owner})
    lay["instances"] += new

    rim_events = wire_rim(lay, plats, res_files)
    lay["events"] = [e for e in lay["events"] if e.get("name") != GROUP]
    lay["events"].append({
        "type": "BuiltinCommonInstructions::Group", "name": GROUP, "source": "",
        "creationTime": 0, "folded": True, "color": {"b": 110, "g": 206, "r": 255},
        "events": [
            comment(f"Canto de lo que se pisa: opacidad 0 a más de {FAR} px de Lio, "
                    f"{MAX} a menos de {NEAR}. Generado por wire_bordes_plataforma.py."),
            *follow_events(lay, moved),
            proximity_event("PlatEdge", f"(PlatEdge.Y() + {LINE_ROW})"),
            *rim_events,
        ]})
    return len(new), sorted(plats)


def main():
    shutil.copy(GAME, GAME + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    g = json.load(open(GAME, encoding="utf-8"))
    res = g["resources"]["resources"]
    for img in set(IMGS.values()):
        if not any(r["name"] == img for r in res):
            res.append({"file": f"assets/UI/{img}", "kind": "image", "metadata": "", "name": img,
                        "smoothed": False, "userAdded": True})
    res_files = {r["name"]: r["file"] for r in res}
    lays = {l["name"]: l for l in g["layouts"]}
    for name in SCENES:
        n, plats = wire(lays[name], res_files, IMGS[name])
        rim = [p for p in plats if p in RIM]
        print(f"{name}: {n} barras en {', '.join(p for p in plats if p not in RIM)}"
              + (f"; luz pintada en {', '.join(rim)}" if rim else ""))
    have = {r["name"] for r in res}
    for nm, f in res_files.items():
        if nm not in have and nm.endswith("_luz.png"):
            res.append({"file": f, "kind": "image", "metadata": "", "name": nm,
                        "smoothed": False, "userAdded": True})
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
