# Contexto del proyecto

Trabajo final de la Tecnicatura Universitaria en Desarrollo Web (UNER),
materia Multimedia y Juegos Web. Prototipo de videojuego web, género
**plataformas 2D**, motor **GDevelop**. Plazo de entrega: 01/09 al
31/10/2026, trabajo individual.

**Historial completo de decisiones:** leer `reseach.md` en la raíz de
este repo (no versionado, es la bitácora personal del usuario) antes
de asumir nada sobre el estado del proyecto — ahí está todo el
razonamiento de por qué se llegó hasta acá.

## Resumen ejecutivo (por si no da tiempo de leer `reseach.md` entero)

- Existía un repo hermano (`~/Escritorio/juego-plataformas-uner`) con
  un shoot 'em up de naves espaciales hecho en Phaser 3 — se evaluó
  usarlo para la cursada pero se descartó: la consigna pide género
  "plataformas 2D" y motor "web, similar a GDevelop o Construct3, para
  que haya igualdad de condiciones en la hora de desarrollo", y un
  shooter en Phaser (framework de código) no cumplía ninguna de las
  dos cosas de forma inequívoca. **Ese repo sigue existiendo como
  proyecto personal del usuario, aparte de la cursada — no tocar ni
  mezclar con este.**
- Este repo (`juego_plataformero_uner_26`) es el que sí se entrega:
  plataformero real, motor GDevelop (elegido en vez de Godot porque
  Godot es código puro y no resuelve la cláusula de "igualdad de
  condiciones"; GDevelop está nombrado explícitamente en la consigna y
  trae de fábrica el behavior "Platformer Character").
- El mail enviado a la cátedra sobre la versión naves/Phaser quedó sin
  respuesta y sin seguimiento — **decisión final: no hace falta
  avisar el pivot.** El juego de naves queda como proyecto personal
  del usuario, fuera de la cursada; para la materia se entrega
  directamente este repo (plataformero/GDevelop), sin depender de
  ninguna respuesta de la cátedra.

## El juego: "Paciente Zero"

- Plataformero 2D, Buenos Aires tomada por un virus zombie. El
  protagonista es **Lio** (inmune; guiño a Messi).
- Proyecto GDevelop en `game/game.json`, resolución **480x270**.
  Escenas: `MainMenu` → `Tutorial` → `Level1` → `Level2` (laboratorio)
  → `Level3` (jefe Paciente Zero) → `MainMenu`.
- Docs de diseño: `GDD.md`, `HIGH_CONCEPT.md`, `consigna.md`. Ficha de
  personaje (primera entrega) en `primer_entrega/`.
- **Arte:** zombies, props y fondos son 100% procedurales (Pillow,
  `scripts/gen_*.py`, paleta en `scripts/palette_night.py`). El player
  es la excepción: sprite CC0 "Forest Boy" (OpenGameArt) recoloreado a
  celeste/blanco (créditos en `game/assets/Player/CREDITS.txt`). Se
  descartó generar sprites con IA de imagen (inconsistencia cuadro a
  cuadro).
- **Audio:** 100% procedural (Python + numpy, `scripts/gen_sfx.py`).
  Se descartó CC0 para música y SFX.
- Build web publicado como DRAFT/secret en
  `walterfrias.itch.io/paciente-zero`. Los exports van a `dist/`
  (gitignored) con `gdexport`, que viene dentro de
  `~/Escritorio/gdevelop-mcp/node_modules/.bin/`. No hay `butler`: el
  zip se sube a mano.

## Motor y herramientas

- `.mcp.json` apunta a [`gb2b/gdevelop-mcp`](https://github.com/gb2b/gdevelop-mcp)
  (MIT, no oficial), instalado en `~/Escritorio/gdevelop-mcp/` (fuera
  de este repo). Validado end-to-end y en uso habitual.
- Dos formas de editar `game/game.json`:
  - Scripts `scripts/wire_*.py` (históricos): hacen backup `.bak-<ts>`,
    son idempotentes y editan el JSON directo.
  - Desde el 19/09 se usa sobre todo `mcp__gdevelop__edit_project`
    (con `dryRun` y backup automático), verificando con
    `validate_project`.

## Reglas aprendidas (fallan en silencio si se ignoran)

- **GDevelop tiene que estar CERRADO** antes de editar el JSON por
  script o por MCP. Si está abierto, al guardar pisa los cambios (así
  se perdió trabajo el 06/09).
- **Comillas en parámetros:** los de tipo "expresión de string"
  (nombre de escena, nombre de efecto, timers) necesitan comillas
  escapadas (`"\"Level1\""`); si no, compilan a `""`. Otros tipos
  (p. ej. `mouse`: `"Left"`) se rompen CON comillas de más. No
  adivinar: verificar el JS compilado con
  `preview_scene(keepExport:true)` + grep sobre `code0.js`.
  `validate_project` no detecta este bug.
- **Instrucciones legacy de behavior** (AddCondition/AddAction) van sin
  el segmento del behavior en `type.value`
  (`PlatformBehavior::IsFalling`).
- **`edit_project`:** para reemplazar un array, el path es el nombre
  del array (`"effects"`). La notación con índice (`"effects[0]"`) crea
  una clave literal nueva, que no hace nada.
- **`ForEach`:** el motor lee el objeto de la clave `"object"`. El
  esquema del MCP usa `"objectsToPick"`, que el motor ignora (el evento
  compila vacío). Poner las dos claves.
- **Selección de instancias:** una condición sobre un objeto filtra sus
  instancias, y las acciones sobre ese mismo objeto solo afectan a las
  filtradas. Para actuar sobre todas, usar un evento cuyas condiciones no
  lo mencionen (así se arregló el bug de los "4 zombies rotos").
- **Toggles:** dos eventos hermanos `tecla & X=0 → X=1` y `tecla & X=1 →
  X=0` se deshacen en el mismo frame. Usar un evento padre con
  sub-eventos y un estado intermedio (ver `scripts/fix_pause_toggle.py`).
- **Acciones de extensiones de objeto** (p. ej. `XOffset`/`YOffset` de
  TiledSprite) llevan el prefijo de la extensión en el tipo:
  `TiledSpriteObject::XOffset`. Sin él, la acción se descarta al compilar.
- Un efecto arranca deshabilitado solo si su definición trae
  `"disabled": true`; un evento `Once` no alcanza.
- `ChangeColor` es un tint multiplicativo: sobre la paleta noche solo
  oscurece. Para resaltar un objeto se usa el efecto `Outline`.

## Estado (al 27/09/2026)

- **Nivel 1 cerrado, playtesteado y aprobado por los profes**:
  - horda, virus voladores, puentes, antídoto;
  - combate corregido (stomp con `IsFalling`, knockback, anim `Hit`);
  - controles WASD+J y mirror;
  - contagio zombie↔virus: Outline rojo, gas, 2 golpes, cura a los 6s
    e inmunidad de 3s.
- **Tutorial** implementado y probado.
- **Nivel 2 y Nivel 3 jugables (primer corte).** Se regeneran con, en
  este orden: `gen_lab.py` → `gen_zombies_lab.py` →
  `gen_zombies_horda.py` → `wire_n1_horda_lab.py` →
  `fix_pause_toggle.py` → `wire_levels23.py --force`. Ojo: `--force`
  regenera L2/L3 desde cero y pisa los cambios hechos a mano. Detalle en
  `reseach.md` (27/09).
- Nivel 2 (~3800 px): pasillos con huecos y estantes, **piso encerado**
  (resbala), **camillas móviles** sobre huecos anchos y **ductos de aire**
  (uno obligatorio para pasar un gabinete, otro opcional con antídoto).
- La horda del Nivel 1 mezcla personal del laboratorio (médico,
  enfermera, investigador) con 3 zombies exclusivos de la horda (hincha,
  repartidor, policía). Te daña si te choca de costado (−1 vida); se
  cruza el río montado encima. El Nivel 2 tiene solo personal del lab.
  **ZombieT es exclusivo del jefe** Paciente Zero.

## Pendiente / próximos pasos

1. Entrega de avance el **martes 29/09**: los 3 niveles jugables y el
   flujo completo. Falta el playtest a mano de L2/L3 y el re-export a
   itch.io.
2. Pulido del menú de pausa (sin fondo, se lee regular). El bug de
   ESC/P quedó resuelto el 27/09 (era un toggle que se deshacía en el
   mismo frame, ver `reseach.md`).
3. Pulido de L2/L3: música propia, cartel de meta de L2, más contenido
   (objetivo ~7 min por nivel), calibrar el jefe.
4. ~30 min de juego total y video pitch (hasta 5 min). Entrega final:
   31/10/2026.
