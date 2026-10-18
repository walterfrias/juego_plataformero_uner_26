#!/usr/bin/env python3
"""
gdevelop_cerrado.py  —  guarda para los scripts que escriben game/game.json.

GDevelop carga el JSON una vez y trabaja en memoria: si está ABIERTO
mientras un wire_*.py edita el archivo, al guardar (o al cerrar guardando)
pisa todo lo que hizo el script. Pasó el 06/09 (se perdió la horda v2 y el
audio) y el 18/10 casi pasa (estuvo abierto durante tres scripts; no guardó).
La regla "GDevelop CERRADO" dependía de acordarse: esto la vuelve automática.

Uso, al principio del main() de cada script que escribe game.json:
    from gdevelop_cerrado import asegurar_gdevelop_cerrado
    asegurar_gdevelop_cerrado()

Si encuentra el editor abierto corta con un mensaje y no toca nada.
Para saltearlo a propósito (p. ej. si detecta mal un proceso):
    GD_FORZAR=1 python3 scripts/wire_algo.py

También se puede correr solo:  python3 scripts/gdevelop_cerrado.py
"""
import os
import sys

# procesos que tienen "gdevelop" en el comando pero NO son el editor
NO_ES_EL_EDITOR = ("gdevelop-mcp", "gdexport", "gdevelop_cerrado", "jugar_web")


def procesos_gdevelop():
    """(pid, comando) de los procesos del editor GDevelop que están corriendo."""
    propios = {os.getpid(), os.getppid()}
    encontrados = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) in propios:
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode(errors="replace").strip()
        except OSError:
            continue                    # el proceso terminó mientras se leía
        if "gdevelop" in cmd.lower() and not any(x in cmd for x in NO_ES_EL_EDITOR):
            encontrados.append((int(pid), cmd))
    return encontrados


def asegurar_gdevelop_cerrado():
    if os.environ.get("GD_FORZAR") == "1":
        return
    abiertos = procesos_gdevelop()
    if abiertos:
        print("GDevelop está ABIERTO: si guarda, pisa lo que escriba este script en game.json.",
              file=sys.stderr)
        for pid, cmd in abiertos[:3]:
            print(f"  pid {pid}: {cmd[:100]}", file=sys.stderr)
        print("Cerralo (la app entera, sin guardar si no hiciste cambios) y volvé a correr.\n"
              "Si es un falso positivo: GD_FORZAR=1 python3 ...", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    abiertos = procesos_gdevelop()
    print("GDevelop ABIERTO" if abiertos else "GDevelop cerrado")
    for pid, cmd in abiertos:
        print(f"  pid {pid}: {cmd[:120]}")
