#!/usr/bin/env python3
"""
fix_l3_piramides.py  —  las estatuas con columna de la arena de L3 pasan a ser pirámides
estilo monolito (18/10, gen_l3_calle.py). La imagen nueva tiene PIR_PAD px de faldón a cada
lado: corre las dos instancias EstatuaColumna para que el tope y la losa sigan sobre las
plataformas (Estante y 70 / y 122). Lo mismo hace wire_l3_recorrido.py si se regenera L3;
esto evita re-correr toda la cadena. Idempotente (calcula desde los Estante).
Uso:  python3 scripts/fix_l3_piramides.py   (raíz del repo, GDevelop CERRADO)
"""
import datetime
import json
import shutil

from gdevelop_cerrado import asegurar_gdevelop_cerrado

GAME = "game/game.json"
PIR_PAD = 14


def main():
    asegurar_gdevelop_cerrado()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    shutil.copy(GAME, f"{GAME}.bak-{ts}")
    d = json.load(open(GAME))
    sc = next(x for x in d["layouts"] if x["name"] == "Level3")
    est = [i for i in sc["instances"] if i["name"] == "Estante"]
    for lado, sel in (("Izq", lambda e: e["x"] < 240), ("Der", lambda e: e["x"] >= 240)):
        grupo = [e for e in est if sel(e)]
        x = min(e["x"] for e in grupo if round(e["y"]) in (70, 122)) - PIR_PAD
        for i in sc["instances"]:
            if i["name"] == f"EstatuaColumna{lado}":
                i["x"] = x
                print(f"EstatuaColumna{lado} → x {x}")
    json.dump(d, open(GAME, "w"), indent=2, ensure_ascii=False)
    open(GAME, "a").write("\n")


if __name__ == "__main__":
    main()
