#!/usr/bin/env bash
# =============================================================================
# jugar_web.sh — exporta el juego a HTML5 y lo sirve en el navegador, SIN
# abrir GDevelop.
#
# Por qué funciona: GDevelop "compila" el proyecto (game/game.json) a una web
# común y corriente: index.html + el motor en JavaScript (gdjs, archivos
# Runtime*.js) + un code0.js, code1.js... por escena, con los eventos
# traducidos a JS. `gdexport` (CLI del paquete gdevelop-mcp) hace ese mismo
# export desde la terminal. Después cualquier servidor estático alcanza.
#
# Además le inyecta UNA línea al index.html:
#       window.__game = game;
# justo después de `new gdjs.RuntimeGame(...)`. Eso deja el juego entero
# accesible desde la consola del navegador (F12) para saltar de nivel, mirar
# o cambiar variables, mover a Lio, etc. Ver "TRUCOS DE CONSOLA" abajo.
# Es lo mismo que usan los tests con puppeteer (ver CLAUDE.md, "Test de
# runtime"). El build de itch.io NO lleva esta línea: este script solo
# escribe en el directorio de salida, nunca en game/ ni en dist/.
#
# Uso (desde la raíz del repo, con GDevelop CERRADO si acabás de scriptear):
#   scripts/jugar_web.sh                 # exporta a /tmp/paciente-zero-web y sirve en :8765
#   scripts/jugar_web.sh -o DIR -p 8080  # otro directorio / puerto
#   scripts/jugar_web.sh --no-export     # solo sirve el último export (más rápido)
# Abrir: http://localhost:8765/index.html     Cortar: Ctrl+C
# Directo a un nivel: http://localhost:8765/index.html?escena=Level2
#   (vale cualquier escena: Level1, Level2, Level3, Tutorial, MainMenu)
#
# Requisitos: gdexport en ~/Escritorio/gdevelop-mcp/node_modules/.bin/ y python3.
#
# -----------------------------------------------------------------------------
# TRUCOS DE CONSOLA (F12 → Console). Verificados contra el build el 18/10/2026.
# -----------------------------------------------------------------------------
#   // atajo: la escena que está corriendo
#   s = () => __game.getSceneStack().getCurrentScene()
#
#   // saltar de escena (Level1, Level2, Level3, Tutorial, MainMenu)
#   __game.getSceneStack().replace("Level2", true)
#
#   // variables de ESCENA (Lives, Antidotes, LevelScore, BossHP en L3, ...)
#   s().getVariables().get("Lives").setNumber(9)
#   s().getVariables().get("Lives").getAsNumber()
#
#   // variables GLOBALES (Nota1..Nota7, TieneMochila, Puntaje, Record, ...)
#   __game.getVariables().get("Nota4").setNumber(1)
#
#   // teletransportar a Lio (x, y en px de la escena; el piso de L2 está en y=110)
#   p = s().getObjects("Player")[0]; p.setPosition(1700, 60)
#
#   // tocar el comportamiento de plataforma (velocidad 95, salto 350)
#   p.getBehavior("PlatformerObject").setJumpSpeed(900)   // súper salto
#   p.getBehavior("PlatformerObject").setMaxSpeed(250)    // correr rápido
#
#   // cámara lenta / congelar una capa ("" es la capa de juego)
#   s().getLayer("").setTimeScale(0.3)
#
#   // ocultar una capa para ver qué aporta (Atmos = luces/sombras, BG_city ...)
#   s().getLayer("Atmos").show(false)
#
#   // borrar todos los zombies de un tipo. OJO: iterar sobre una COPIA
#   // ([...]); si se borra recorriendo la lista original se saltea la mitad.
#   [...s().getObjects("ZombieEnf")].forEach(o => o.deleteFromScene(s()))
#
#   // contar instancias / ver dónde está la cámara
#   s().getObjects("ZombieMed").length
#   s().getLayer("").getCameraX()
#
# Nada de esto se guarda: al recargar la página el juego vuelve a como está
# en game/game.json. Para cambios permanentes: scripts wire_*.py o el MCP.
# =============================================================================
set -euo pipefail

OUT=/tmp/paciente-zero-web
PORT=8765
EXPORT=1
GDEXPORT="$HOME/Escritorio/gdevelop-mcp/node_modules/.bin/gdexport"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o) OUT="$2"; shift 2 ;;
    -p) PORT="$2"; shift 2 ;;
    --no-export) EXPORT=0; shift ;;
    -h|--help) sed -n '2,68p' "$0"; exit 0 ;;
    *) echo "opción desconocida: $1 (ver --help)" >&2; exit 1 ;;
  esac
done

# Aviso (no bloquea): si GDevelop está abierto, game.json en disco puede no
# tener lo último que se ve en el editor.
if pgrep -fa -i gdevelop | grep -qv -e gdevelop-mcp -e gdexport -e jugar_web; then
  echo "aviso: parece que GDevelop está abierto; se exporta lo que hay GUARDADO en game.json"
fi

if [[ $EXPORT == 1 ]]; then
  [[ -x "$GDEXPORT" ]] || { echo "no encuentro gdexport en $GDEXPORT" >&2; exit 1; }
  mkdir -p "$OUT"
  echo "exportando game/game.json → $OUT ..."
  "$GDEXPORT" -p "$REPO/game/game.json" -o "$OUT"

  # Inyecta window.__game (idempotente: si ya está, no la repite).
  if ! grep -q "window.__game = game;" "$OUT/index.html"; then
    sed -i '/new gdjs.RuntimeGame(/a\        window.__game = game;' "$OUT/index.html"
  fi
  grep -q "window.__game = game;" "$OUT/index.html" \
    || { echo "no pude inyectar window.__game (¿cambió el index.html del export?)" >&2; exit 1; }

  # Arranque directo en una escena con ?escena=Level2 en la URL: cambia la
  # escena inicial (firstLayout, normalmente MainMenu) ANTES de crear el
  # juego. Si el nombre no existe se ignora y arranca en el menú.
  if ! grep -q "__escenaURL" "$OUT/index.html"; then
    sed -i '/var game = new gdjs.RuntimeGame(/i\        var __escenaURL = new URLSearchParams(location.search).get("escena");\n        if (__escenaURL \&\& gdjs.projectData.layouts.some(function (l) { return l.name === __escenaURL; }))\n            gdjs.projectData.firstLayout = __escenaURL;' "$OUT/index.html"
  fi

  # Instrucciones que el motor descartó al compilar (fallan en silencio en el
  # juego; ver "Reglas aprendidas" en CLAUDE.md).
  if grep -l "Unknown" "$OUT"/code*.js >/dev/null 2>&1; then
    echo "OJO: hay instrucciones 'Unknown' en el JS compilado:"
    grep -l "Unknown" "$OUT"/code*.js
  fi
fi

[[ -f "$OUT/index.html" ]] || { echo "no hay export en $OUT (correr sin --no-export)" >&2; exit 1; }

echo
echo "  ▶  http://localhost:$PORT/index.html     (Ctrl+C para cortar)"
echo "  ▶  directo a un nivel: http://localhost:$PORT/index.html?escena=Level2"
echo "     consola: F12 → __game.getSceneStack().replace(\"Level2\", true)"
echo
cd "$OUT"
exec python3 -m http.server "$PORT"
