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
- **BitmapText:** la acción de texto es `BitmapText::BitmapTextObject::SetText`
  (`BitmapText::SetText` se descarta al compilar; `BitmapText::SetTint`
  sí va sin el segmento del objeto). Fuente del HUD: `gen_font.py`.
- Un efecto arranca deshabilitado solo si su definición trae
  `"disabled": true`; un evento `Once` no alcanza.
- `ChangeColor` es un tint multiplicativo: sobre la paleta noche solo
  oscurece. Para resaltar un objeto se usa el efecto `Outline`.
- **La opacidad de instancia** (`"opacity"` en `numberProperties`) **no la
  respeta el runtime en los Sprite** (quedan en 255). Ponerla en una var de
  objeto y aplicarla con la acción `Opacity` por evento.
- **Time scale 0 congela los timers** (de escena y de objeto). Para medir
  tiempo con el juego congelado (popup de nota) contar frames en una var.
- **Cerrar un popup con la misma tecla que salta (J/Espacio):** cerrar al
  SOLTAR (`KeyFromTextReleased`) y bloquear controles mientras está
  abierto (`IgnoreDefaultControls` + condición en los eventos WASD/J). Si
  no, la tecla queda "guardada" y Lio salta al despausar.
- **Guardas sobre eventos existentes** (NotaOpen=0, MochilaOpen=0 en la
  pausa/controles): el script tiene que sacar su propio grupo ANTES de
  buscar, o se matchea a sí mismo al re-correr (pasó con wire_notas.py).
- Para probar, **mover al Player de verdad** (teclas), no solo
  teletransportarlo encima: así se vio que la nota 6 arriba del gabinete
  era inalcanzable en la práctica.
- **Test de runtime:** `gdexport` al scratchpad, inyectar
  `window.__game = game;` en `index.html` después de `new
  gdjs.RuntimeGame`, servir con `python3 -m http.server` y manejar con el
  puppeteer de `~/Escritorio/gdevelop-mcp/node_modules/puppeteer`
  (`getSceneStack().replace(...)`, leer vars/objetos, capturas). Grep de
  "Unknown" en `code*.js` para instrucciones descartadas.

## Estado (al 14/10/2026)

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

- **Puntaje + HUD (09/10):** `gen_font.py` → `wire_score_hud.py`
  (idempotente; re-correrlo después de `wire_levels23.py --force`).
  Stomp +100 con cadena sin tocar el piso (100/200/400/800/1000),
  antídoto +250, números estilo arcade; al ganar: meta +1000, +500 por vida, +1000
  con 4/4 antídotos; en la victoria de L3, +1000 con las 7 pruebas. `LevelScore` (escena) pasa a `Puntaje` (global)
  recién al ganar; récord único en storage del navegador, visible en el
  menú. Detalle en `reseach.md` (09/10).
- **Textos en fuente pixel (14/10):** `wire_pixel_texts.py` (después de
  `wire_score_hud.py`): tutorial y carteles de victoria/Game Over en
  BitmapText; ya no queda ningún TextObject.
- **Mochila de repartidor (14/10):** en la espalda y gira con Lio
  (`wire_mochila_back.py`). Desde que se agarra en L1 queda para todo el
  juego (global `TieneMochila`, `wire_mochila_niveles.py`): planeo + espalda
  en L2/L3; si muere en L1 arranca con ella; "Jugar" la resetea. La del
  Tutorial es de práctica.
- **Pruebas del brote (14/10, completo):** 7 notas del diario de Paciente
  Zero (textos en GDD §6 y en `gen_notas.py`, fuente única; arte con el
  texto horneado en `game/assets/UI/Notas/`). `wire_notas.py`:
  - L1: notas 2 (x≈1010, junto a la mochila), 1 (x≈1232), 3 (x≈2220).
    L2: 4 (estante largo), 5 (ducto opcional), 6 (piso tras el gabinete).
    L3: la 7 la suelta el jefe al morir; la victoria espera a que se lea
    (evento original con condiciones BossDown/Nota7/NotaOpen; si ya la
    tenía, victoria inmediata).
  - Al agarrar: time scale 0 + popup (se cierra soltando J/Espacio/Enter/
    ESC o solo a los 6 s). Globals `Nota1..7`, no reaparecen al morir;
    "Jugar" las resetea.
  - Pausa → **I: MOCHILA** (inventario) en L1/L2/L3: nota grande + 7
    casilleros, ← → elige, I/ESC/P vuelven. La ayuda de la pausa lleva el
    sprite de la mochila.
  - Bonus **PRUEBAS 7/7 +1000** en la victoria de L3 (`wire_score_hud.py`).

- **Bordes de plataforma por cercanía (14/10, L1/L2/L3):**
  `gen_borde_plataforma.py` + `gen_luz_borde.py` → `wire_bordes_plataforma.py
  [Escena]`. Árboles y faroles: copia `<Nombre>Luz` del sprite con luz de
  borde pintada (variante B elegida por el usuario). El resto: barra ámbar
  sobre el canto de la máscara de colisión (menos Ground, Poste,
  HordaPiso). Opacidad según la distancia a Lio (NEAR 40 / FAR 150 / MAX
  230). Ámbar en L1, verde tóxico en el lab (L2/L3); las barras de las
  camillas las siguen (MOVERS en el script).

- **Parallax del fondo de L1 (14/10):** `gen_city_bg.py` (tira nueva
  `city_farthest.png`) → `wire_parallax.py`. Capa nueva `BG_farthest`
  (detrás de BG_far, con la Luna). Las capas siguen a la cámara 1:1 y se
  mueven los objetos: XOffset de las tiras y X de Obelisco/Luna según
  `CameraCenterX("")` (compila a `getCameraX`, centro de cámara). Velocidad
  relativa: Luna 0.03, CityFarthest 0.12, Obelisco 0.15, CityFar 0.30,
  CityNear 0.55. El Obelisco recorre la pantalla de x=372 a 39 en todo el
  nivel (acompaña como en el menú).

- **Luces de terror clase B en el lab (14/10):** `gen_lab_luces.py` →
  `wire_lab_luces.py`. Capa nueva `Atmos` (entre la de juego y la UI) con
  la sombra de zonas a oscuras (`LabSombra`, ~55 %) y los conos
  (`LampGlow`); carcasas (`LampFixture`) en Decor. Tubos estables,
  intermitentes (ráfagas, ~91 % prendidos) y rotos (destellos, ~7 %), con
  ruido pseudoaleatorio sobre `TimeFromStart()`. L2: 13 tubos, zonas
  oscuras en el piso encerado y en el tramo final; L3: 2 tubos + arena
  un poco más oscura. Sonido (`gen_sfx.py` → `lab_sfx()`, con generador
  aleatorio propio para no alterar los demás WAV): `sfx_zumbido` en loop
  en el canal de sonido 2, volumen según la cercanía a un tubo PRENDIDO
  (mudo en pausa / nota / fin); `sfx_chispazo` (pitch al azar) cuando un
  tubo cambia de estado a menos de 240 px de Lio.

- **Orden de los scripts si se regenera** (todos idempotentes, GDevelop
  CERRADO): `wire_levels23.py --force` → `wire_score_hud.py` →
  `wire_pixel_texts.py` → `wire_mochila_niveles.py` → `wire_notas.py` →
  `wire_bordes_plataforma.py`. También re-correr `wire_notas.py` después
  de `fix_pause_toggle.py` o `wire_pause_panel.py`. `wire_lab_luces.py` y
  `wire_parallax.py` son independientes (re-correr el de luces después de
  `wire_levels23.py --force`). Arte: `gen_mochila.py`
  antes de `gen_menu_ui.py` (la ayuda de la pausa usa `mochila_worn.png`);
  `gen_notas.py`, `gen_borde_plataforma.py`, `gen_luz_borde.py`.

## Entregas

- **Pre-entrega Pre-Alfa (29/09/2026):** prototipo funcional con core
  loop, física base y estructura inicial de niveles, más el foco de la
  cátedra en **Game Testing** (validación de mecánicas, detección
  temprana de errores y playtesting). Build:
  `dist/PacienteZero-HTML5-PreAlfa-20260929.zip`. Detalle y lo que falta
  (playtesting con usuarios reales) en `reseach.md`.

## Pendiente / próximos pasos

1. **Playtesting con usuarios reales** (lo que falta de la fase Pre-Alfa):
   planilla de feedback, contadores de muertes/tiempo por nivel, informe
   de QA.
2. ~~Pulido del menú de pausa~~ hecho el 29/09: MainMenu rediseñado
   (`gen_menu_ui.py` + `wire_main_menu_v2.py`) y la pausa de L1/L2/L3
   usa el mismo panel (`wire_pause_panel.py`: mismos nombres de objeto,
   ahora Sprites, así la lógica del toggle ESC/P no cambió). Luna del
   menú también en Level1 junto al obelisco (`wire_luna_level1.py`).
3. Pulido de L2/L3: música propia, cartel de meta de L2, más contenido
   (objetivo ~7 min por nivel), calibrar el jefe.
4. **Playtest de lo hecho el 14/10** (jugar de punta a punta):
   - notas 1 y 3 de L1 caen en patrullas de zombies (¿riesgo/recompensa o
     molesto?); notas 4 y 5 de L2: ¿bien escondidas?;
   - 6 s del popup: ¿alcanzan?;
   - planeo en L2: puede facilitar los huecos de las camillas;
   - bordes por cercanía: calibrar NEAR/FAR/MAX y el verde del lab;
   - el velo de la pausa / popup (pause_dim) oscurece poco: ¿subirlo?
   - parallax de L1: velocidades y si la base del Obelisco "flota";
   - luces del lab: oscuridad de las zonas (140 / 90) y volumen del
     zumbido (0.05 + 0.3) y de los chispazos.
5. Re-export y subida del build a itch.io con todo lo nuevo.
6. **Congelamiento de funciones (acordado el 14/10):** de acá a la
   entrega solo pulido, balance y bugs; lo único "nuevo" admitido es
   contenido con piezas existentes si el playtest muestra que no se llega
   a los 30 min de la consigna. Contenido congelado el 28/10.
7. ~30 min de juego total y video pitch (hasta 5 min). Entrega final:
   31/10/2026.
