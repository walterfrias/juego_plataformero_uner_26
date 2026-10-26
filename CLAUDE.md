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
- **Jugar sin abrir GDevelop:** `scripts/jugar_web.sh` exporta a
  `/tmp/paciente-zero-web`, inyecta `window.__game` y sirve en
  `http://localhost:8765/index.html`. Trucos de consola (saltar de escena,
  variables, teletransporte, capas) documentados en su cabecera.

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
  se perdió trabajo el 06/09; el 18/10 estuvo abierto durante tres
  scripts y por suerte no guardó). Los wire scripts nuevos llaman a
  `asegurar_gdevelop_cerrado()` (`scripts/gdevelop_cerrado.py`) y cortan si
  lo encuentran abierto: agregarlo a todo script que escriba game.json.
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
- **Escaleras (Ladder):** agarrarse lo decide la tecla **Ladder**, no Up
  (`_checkTransitionOnLadder`). La W simulaba solo Up: con WASD no se
  trepaba ningún poste (ni en L1). `fix_w_escalera.py` agrega
  `PlatformBehavior::SimulateLadderKey` al evento de la W en todas las escenas.
- **Paredes que tocan el piso por el costado no frenan:** una plataforma
  maciza vertical cuya base está a la altura del piso (la pared de 350 px de
  la arena de L3, una valla) el motor la toma como piso: deja de ser
  obstáculo o "sube" a Lio arriba de la pared. Límites de nivel/arena: por
  evento (`PosX < x → SetX x`), no con plataformas.
- **En L2 y L3 Lio tiene la MOCHILA (viene de L1) y planea:** mantener J
  cayendo → MaxFallingSpeed 80 (si no, 600). Saltando y planeando está ~0.8 s
  en el aire; sin mochila, ~0.38 s. Todo lo que dependa del tiempo en el aire
  se prueba con `TieneMochila = 1` (global) y entrando a la escena desde otra
  (el Once que habilita el planeo lo lee al empezar). Para que el robot planee
  hay que apretar J "de verdad": `game.getInputManager().onKeyPressed(74)`
  (el planeo usa KeyFromTextPressed, no los controles simulados).
- **Probar timing con un robot DENTRO del juego**
  (`gdjs.registerRuntimeScenePostEventsCallback` + `simulateRightKey` /
  `simulateJumpKey` del PlatformerObject): reacciona en el mismo frame. Con
  puppeteer leyendo el estado por CDP llega tarde y el fallo es del robot.
- **Toggles:** dos eventos hermanos `tecla & X=0 → X=1` y `tecla & X=1 →
  X=0` se deshacen en el mismo frame. Usar un evento padre con
  sub-eventos y un estado intermedio (ver `scripts/fix_pause_toggle.py`).
- **Acciones de extensiones de objeto** (p. ej. `XOffset`/`YOffset` de
  TiledSprite) llevan el prefijo de la extensión en el tipo:
  `TiledSpriteObject::XOffset`. Sin él, la acción se descarta al compilar.
  Lo mismo la opacidad: `Opacity` es solo de Sprite; en TiledSprite es
  `TiledSpriteObject::SetOpacity` (la niebla de L1 estuvo a 255 hasta el
  16/10; el Diagnostic report de GDevelop sí lo marca).
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
- **Reloj y TOP 5 con iniciales (25/10, última mejora):**
  - Reloj en `wire_score_hud.py`: "TIEMPO m:ss" debajo de los puntos, se
    congela con time scale 0 (pausa, notas). Sin límite: tiempo `PAR` por
    nivel (L1 300 s, L2/L3 360 s) y al ganar +10 por segundo que sobra
    (línea TIEMPO del desglose); pasado el par se pone rojo. Calibrar el
    par con los tiempos de los playtests.
  - `wire_top5.py` (después de `wire_score_hud.py`): tabla TOP 5 arriba a
    la izquierda del menú (reemplaza "RÉCORD 000000"). La partida termina al
    volver al menú (victoria final, Game Over → ESC, M en la pausa); cuenta
    el último puntaje del HUD (global `PuntajeCorte`). Si entra, el panel
    pide 3 iniciales (↑↓ letra, → / Enter siguiente, ← vuelve; arranca con
    las últimas usadas). Storage PacienteZero: top_p1..5, top_n1..5, ini.
    Verificado con puppeteer (orden, persistencia, Game Over → ESC).
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

- **Minivirus (15/10):** `wire_minivirus.py` (L1/L2/L3). El zombie
  infectado (`Infected=1`) escupe 1 virus (mismo sprite y tamaño que los
  voladores) si Lio está a <200 px: 0.8 s después del contagio y cada
  2.5 s, con aviso de 0.45 s (contorno que parpadea + chispazo grave).
  Vuela como los voladores (55 px/s, rumbo nuevo cada 1.5-2.5 s) pero cada
  rumbo apunta a Lio ±35°; vida de 5 s en L1 (bajada el 15/10 porque el final se hacía difícil) y 8 s en L2/L3; se desvanece al final. Brilla por
  cercanía como los bordes de plataforma (efecto Glow, outerStrength 0→3
  entre 150 y 40 px; ámbar L1, verde L2/L3); los virus voladores (grupo
  `Virus`) brillan igual, sin cambiar su vuelo. Jefe: escupe en el estado 0
  (aviso con contorno desde 0.5 s, escupe a 1.0 s) desde BossHP 2: 1 virus,
  2 con BossHP 1. Golpe = −1 vida, Invuln 1 s, knockback de 40 px. No se
  pisan ni contagian zombies. Var de objeto `Spit` en los zombies, scene
  var `BossSpit` en L3. Verificado en runtime (puppeteer). Playtest de L1 (15/10, usuario): muy
  entretenido con varios virus a la vez, se esquivan saltando por encima.
  Falta playtest de L2/L3 y del jefe.

- **Noche del Nivel 1 (15/10):** `gen_noche_n1.py` + `gen_luz_luna.py`
  (+ `gen_sfx.py` → `fuego_sfx()`) → `wire_noche_n1.py`. Idea: oscurecer
  todo y devolver la luz solo donde importa.
  - Fondo: cielo con degradé, nubes a la deriva delante de la Luna, efecto
    `Adjustment` (objeto) que oscurece y desatura más cuanto más lejos
    (City*, Obelisco), 3 tiras de niebla sobre la base de cada skyline.
    El muro, el caño y el río también van oscurecidos (en sombra).
  - Fuego: 6 tachos con llama animada + halo que titila (capa nueva
    `Atmos` en L1), 4 de ellos agregados con la var de instancia `Noche`.
    También 3 incendios lejanos con humo (parallax f=0.2), conos de luz de
    sodio en los 5 faroles (el de x=526 falla) y un crepitar en loop en el
    canal 3 según la cercanía a un fuego.
  - Luna horneada: los props de L1 usan copias `*_luna.png` (canto de
    arriba frío, derecha 30 %, izquierda en sombra), y Lio y los zombies
    llevan un tinte frío (`ChangeColor`) que se entibia cerca de un fuego.
    Árboles y faroles quedan sin luna (sus `*_luz.png` salen del original).
  - `wire_levels23.py` ignora el grupo gracias a la var `NocheCalor`
    (`L1_ONLY_VARS`), así un `--force` no lleva el tinte al lab.
  - Falta playtest: niebla (Alpha 170/130/70), brillo de los fondos,
    intensidad de los halos y volumen del fuego.

- **Virus con patrón fijo (16/10):** `wire_virus_patron.py` (L1/L2). Playtest
  (hija del usuario): esperar al vuelo random era "frustrante" (simulado:
  esperas de hasta 4-5 s). Ahora `X = CX + AX·sin(t·WX+PX)`, `Y = CY +
  AY·sin(t·WY+PY)` con vars de objeto y scene var `VirusT` (+TimeDelta, se
  congela en pausa): L1 ascensor (V3), péndulo (V4), ascensor en el medio
  del puente x=926 (V2; era un ocho en x=850 que contagiaba a ZombieM/N y
  se juntaban zombies escupiendo), dos círculos opuestos al final (V5/V1); L2 ocho, péndulo, círculo. Espera máx ~1 s.
  Los minivirus siguen erráticos (contraste: obstáculo de timing vs
  amenaza que persigue). Re-correr después de `wire_levels23.py --force`.
  Falta playtest.

- **Fix L1 (16/10):** `fix_n1_horda_piso_end3.py` (idempotente). HordaPiso
  (el jumpthru invisible de la horda) solo es plataforma con HordaActive
  1-2; antes flotaba invisible en el aire pasando a la anciana (estado 0) y
  después de la horda (estado 3). Sacada la instancia de ZombieEnd3 (usaba
  el sprite de ZombieT, exclusivo del jefe). ZombieMarcha de x=-6 → x=340.

- **Ciudad por los ventanales de L2 (16/10):** `gen_lab_ventanal.py` →
  `wire_lab_ventanal.py`. LabFar de L2 usa `lab_far_ventanal.png` (2
  ventanales de 94x90 por tile, vidrio casi transparente); L3 sigue con
  `lab_far.png`. Capa nueva `BG_city` (detrás de BG_far) con copias de la
  noche de L1 (cielo, nubes, Luna, City*, 5 incendios + humo), 40 px más
  arriba (piso alto) y el mismo parallax; la pared va 1:1. `LabVentanaLuz`:
  resplandor anaranjado bajo cada ventanal que titila. Re-correr después
  de `wire_levels23.py --force`. Falta playtest.

- **Subsuelo del lab (18/10, L2/L3):** `gen_lab_subsuelo.py` →
  `wire_lab_subsuelo.py`. El bloque negro bajo el piso pasa a ser el corte
  del edificio: `LabSubsuelo` (TiledSprite, uno por tramo de Ground, filas
  16..95) con losa, ducto, cañerías y sala de contención; tubos
  `Contencion` / `ContencionRota` (virus que flota adentro, cuadro inicial
  al azar) con halo `ContencionGlow` que late (los rotos titilan). L2: 33
  tubos (5 rotos), L3: 5 (2 rotos, solo decorado). **En L2 los rotos
  estallan:** Lio pasa por encima o por delante (|dx| < 20 px) → tiembla
  0.6 s con crujido → anim `Vacia`, se apaga el halo y sale un `MiniVirus`
  apuntado a Lio, que lo persigue desde atrás (lógica de
  `wire_minivirus.py`, que tiene que correr antes). Var `Estado` 0/1/2, una
  vez por tubo. Ningún roto a <100 px de un hueco (knockback).
  **Ducto jugable (L2, tramo 928..1350):** boca de 28 px en 966..994 con
  bordes de peligro (`EscotillaBorde`; caer ahí no mata), corredor 966..1268
  en la sala de contención (piso invisible `SubsueloPiso` en y 192, techo =
  losa de Ground de 16 px), salida por un `AirFlow` + `Vent` en 1236..1268
  (82 px de piso hasta el hueco de 1350). El antídoto del estante alto
  (x 1195) bajó al corredor (siguen siendo 4). Patrullas: ZombieInv
  1000..1150, ZombieEnf arranca en 1290 y patrulla 1272..1330. El script
  restaura el Ground original antes de re-aplicar (uuid fijos) y calcula
  los tubos con el piso original. Verificado con teclas: entrar, tubo que
  estalla detrás, antídoto, salir flotando, pisar a la enfermera.
  Re-correr después de `wire_levels23.py --force` y de `wire_minivirus.py`.

- **Pistones en lugar de camillas, y pozos (18/10, L2):** las camillas
  flotaban (ni colgadas de un pórtico convencían) y no eran divertidas.
  `gen_lab_piston.py` → `wire_lab_pistones.py` (saca las Camilla y sus
  PlatEdge; re-correr después de `wire_levels23.py --force`): `Piston`
  (40x10, plataforma maciza) + `PistonVastago`, 2 en el pozo de 140 y 3 en
  el de 200, huecos de 20 px. `Y = 110 + 200·max(0, sin(t·W+Ph))^1.5`:
  media vuelta arriba al ras del piso, media hundido (quedarse = caer).
  Aviso: luces rojas desde sin = −0.85 (~0.5 s antes de bajar). Desfase en
  ola LAG = 2.0 rad: cuando el tuyo se pone rojo, el de adelante acaba de
  subir en verde. Robot dentro del juego (jugador prudente: se frena en el
  borde, salta parado, no salta a uno en rojo): 10/10 cruces sin perder
  vidas. **Lio salta ~28 px PARADO** (40-45 con carrera). Pozos:
  `PozoFondo` + `PozoBordeL/R` en los 7 pozos de L2 (en
  `wire_lab_subsuelo.py`), antes se veía un bloque violeta.

- **Luces de ambiente del lab (18/10, L2/L3):** `gen_lab_ambiente.py` →
  `wire_lab_ambiente.py` (después de `wire_lab_luces.py`). Todo en `Atmos`
  por encima de `LabSombra` (si no, la sombra lo apaga). Zonas oscuras:
  `LuzTanque` (halo verde de los tanques de lab_near + charco en el piso,
  burbujea) y `LuzMonitor` (cian, parpadeo corto ocasional). Zona de
  ALARMA (L2 2940..3800 y la arena de L3): `Baliza` en los pilares (cada
  112 px desde LabFar.x) con `BalizaHaz` que barre ±60° (`SetAngle`, origen
  y centro en la punta) y `AlarmaTinte` rojo que late; en L3 late más rápido
  según `BossHP` (3 + (3 − BossHP)·1.5 rad/s, medido: 2 → 4 picos en 4 s);
  se apaga con Won. Falta playtest: intensidad del tinte (máx 38), si los
  haces distraen al pelear con el jefe.

- **Nivel 3 nuevo: recorrido + arena del Obelisco (18/10):** diseño como
  datos en `scripts/l3_recorrido.py` (la maqueta y el cableo leen lo mismo);
  `gen_l3_calle.py` (valla, tablón y caño de andamio) → `wire_l3_recorrido.py`.
  El recorrido va en **x negativas** (−2140..0) y la arena queda en 0..480: la
  lógica del jefe no se tocó. Tramos: salida del lab → calle del hospital →
  plaza (puente) → obra en la 9 de Julio (poste, cables, hierros) → llegada
  (zombies que marchan) → arena (Obelisco, andamios). Sistemas copiados de
  L2: grupo Zombies (policía, hincha, repartidor en la calle; médico en el
  lab: patrulla, pisotón, choque, contagio, gas) y Virus (golpe; patrón en
  `wire_virus_patron.py`, escupitajos de infectados en `wire_minivirus.py`).
  El jefe duerme (`BossActivo`) hasta que Lio entra (X ≥ 10): valla, cámara
  trabada, checkpoint y cartel. 5 checkpoints. Verificado con teclas reales:
  hueco con carrera, poste + cables, entrar y no poder volver, paredes. **No usar `wire_levels23.py --force`**: regenera L3 como
  arena sola.
  Orden si se regenera L3: `wire_l3_recorrido.py` → `wire_l3_mecanicas.py` → `wire_l3_luces.py` → `wire_l3_caos.py` → `wire_virus_patron.py` →
  `wire_minivirus.py` → `wire_lab_luces.py` → `wire_lab_subsuelo.py` →
  `wire_lab_ambiente.py` → `fix_w_escalera.py` → `wire_jefe.py` → `wire_l3_arena_zombies.py` →
  `wire_jefe_jeringa.py` (siempre el último: reemplaza la pelea).
- **L3 entre edificios (18/10):** "no en la costanera sino entre edificios".
  `gen_l3_fachadas.py` (fachadas porteñas: francés, departamentos de los 60, PH,
  bar de esquina con vidrieras cálidas; tapiadas, vidrios rotos, cruces de
  cuarentena; corte de calle y su pozo) → `wire_l3_recorrido.py` (ubicación en
  `l3_recorrido.FACHADAS`, capa BG_near, sin colisión). Calle del hospital y
  Corrientes cerradas entre edificios; la plaza y la llegada al Obelisco
  abiertas. Debajo de la vereda: corte de calle (no el muro del río). Los
  pozos de la calle llevan `PozoCalle` (si no, se veía el cielo por el pozo).
  Además, dos filas de edificios con detalle detrás de las fachadas
  (`gen_l3_ciudad_capas.py`: CiudadTrasera f 0.70 con torres, tanques y
  antenas con luz roja; CiudadMedia f 0.85 con clásicos con cúpulas,
  medianeras con publicidades despintadas, torre vidriada, alguna ventana en
  llamas), en BG_city delante de la silueta de L1: "en el centro casi no se ve
  el cielo".
- **Luces de L3 e incendios entre edificios (18/10):** `gen_l3_luces.py` →
  `wire_l3_luces.py` (después de `wire_l3_recorrido.py`). Llamas animadas,
  humo y cielo naranja sobre TECHOS REALES de las filas de fondo: el generador
  de las filas exporta `ciudad_capas.json` (edificios: tipo, x, ancho, techo) y
  el cableo elige hasta 3 por fila con el techo a la vista (no vidriadas).
  Se mueven con el parallax de su fila (X = Base + (1−F)·cámara, como el
  XOffset de la tira): quedan pegados al techo (verificado con la cámara
  corrida). z en BG_city: resplandor trasera 9, trasera 10, fuego trasera 11,
  resplandor media 12, media 13, fuego media 14. Llamas traseras ~65 % de
  opacidad, medias ~85 %. En las fachadas: luz naranja que titila detrás de
  cada tacho con fuego y luz de sodio detrás de cada farol (Decor).
- **Policía zombie que dispara a mansalva (18/10, L3):** en `wire_l3_mecanicas.py`
  (+ `gen_sfx.py → policia_sfx()`: sfx_gatillo y sfx_disparo con generador propio,
  ningún otro WAV cambió). Si Lio está a <240 px: aviso 0.5 s (destello en la
  mano + clic) y un tiro desde la MANO (altura del pecho, 150 px/s) hacia donde
  mira, cada ~1.7 s; −1 vida. Se esquiva con un salto planeado (robot con
  mochila: 7/7). Desde la cintura "no se veía natural"; ráfagas al pecho
  tenían una ventana de salto demasiado chica (3 balas ~2/6, 2 balas 5/7).
- **Zombies de todos los niveles en L3 (18/10):** en el nivel final vuelven
  todos (13, uno de cada tipo salvo el T del jefe): personal del lab
  (médico, enfermera, investigador) a la salida, vecinos de L1 (M, F) y
  policía en la calle, anciana (8 px/s) y la de pelo largo en la plaza,
  repartidor y corredor (J, 45 px/s) en Corrientes, y una marcha mezclada (N,
  O, hincha) en la llegada. Los de L1 se copian con sus dibujos y se les
  agregan las variables de patrulla del grupo Zombies (`ZOMBIES_L1` en
  `wire_l3_recorrido.py`; el corredor sale de ZombieEnd1). Verificado: las 13
  patrullas en rango y pisotón a un zombie de L1.
  **"Que esté infestada" (18/10):** 18 jugables (se sumaron 5) + una
  **multitud de fondo** de 14 (`l3_recorrido.FONDO`): al 80 % y en SILUETA
  (`gen_l3_siluetas.py`: forma plana oscura, borde de luna, ojos rojos; los
  sprites teñidos competían con los jugables), pies 2 px debajo del borde de
  la vereda (más arriba parecían flotar), en BG_near delante de las
  fachadas, grupo propio `ZombiesFondo` (NO en Zombies: no golpean ni se
  pisan), con su patrulla lenta; también hay público en la arena. Regla en
  los datos: ninguna patrulla a menos de 40 px de un checkpoint.
- **L3 sin pozos: peligros de calle (18/10):** los pozos no tenían sentido en
  una calle del centro. Calle continua y, por tramo (`l3_recorrido.py` →
  `gen_l3_mecanicas.py` → `wire_l3_mecanicas.py`, después de
  `wire_l3_recorrido.py`): **toldo que rebota**
  (BounceVel −440: sube ≈84 px, por arriba del policía zombie), **charco
  electrificado** bajo los cables de Corrientes (como caer a un pozo: −1 vida y
  al checkpoint) y **vapor del subte** (ciclo aviso/sopla/nada; eleva a 150
  px/s) que sube a **marquesinas** por arriba de los zombies que marchan.
  Ciclos con `mod(TimeFromStart() + Fase, período)`: se congelan en pausa.
  La plaza queda de respiro. Checkpoints al comienzo de cada tramo.
  Verificado en runtime: toldo (+84 px), charco (vida y checkpoint), vapor
  (sube y queda en la marquesina). Las macetas que caían se sacaron (pedido
  del usuario, 18/10): código, arte y recursos.
- **Estatuas en la arena (18/10, pedido del usuario):** las plataformas de la
  pelea son monumentos de la vía pública (`gen_l3_calle.py`): a cada lado una
  columna con la Libertad de bronce (pedestal = y 122, capitel = y 70) y un
  pedestal con un prócer con barbijo (y 96). Las superficies coinciden EXACTO
  con las 6 `Estante` de antes, que quedan invisibles (la colisión y los
  bordes por cercanía siguen): la pelea no cambió. Verificado: Lio se apoya
  en las 6 a la altura de siempre. Reemplazan a los andamios.
  **Columnas → pirámides monolito (18/10):** las dos columnas con la Libertad
  pasaron a ser pirámides escalonadas de basalto negro con runas verdes (mismo
  tope y 70 y losa y 122; los bustos quedan). La imagen tiene faldones de
  `PIR_PAD` = 14 px por lado: `fix_l3_piramides.py` corre las instancias (y
  `wire_l3_recorrido.py` ya lo hace si se regenera).
- **Jefe definitivo y Obelisco (18/10):** `gen_jefe.py` → `wire_jefe.py`.
  Paciente Zero = **el científico que empezó todo** (el usuario descartó la
  masa viral, que queda en el historial de git, commit 8fdc8aa): mata de pelo
  NEGRO, anteojos, guardapolvo abierto con la **camiseta de Argentina** debajo,
  jeringa con el líquido verde. Es **un zombie más, escalado**: se dibuja a
  32x34 con las piezas de `gen_zombies_lab.py`/`gen_zombies_wave2.py` y se
  agranda x1.5 con NEAREST a **48x51** (`ESCALA` en gen_jefe.py; era x2 = 64x68,
  "más chico" pidió el usuario). `wire_jefe.py` toma el tamaño de la imagen:
  máscaras, instancia con los pies en y 150, y la lógica de la pelea (centro,
  boca, poof, nota, tope derecho de la arena) en fracciones de
  `PacienteZero.Width()/Height()`: ya no depende del tamaño. Walk (0 y 2), Carga (1: se agacha y levanta la
  jeringa) y Expuesto (3: de rodillas, estrellitas = pisalo). La pelea no cambió. Obelisco
  de la arena: `obelisco_cerca.png` (48x176, `gen_l3_calle.py`): luna de la
  izquierda, reflector cálido abajo, cinta de cuarentena. Verificado: la
  secuencia de estados/animaciones y el pisotón con la máscara nueva.

- **Banderas y caos en la calle (18/10, L3):** `gen_l3_caos.py` →
  `wire_l3_caos.py` (después de `wire_l3_recorrido.py`). Todo decorado, sin
  colisión. 8 banderas apagadas para la noche ("sin ser exagerado"): colgadas de
  balcones de los franceses y de una ventana del bar (se mecen), un mástil en la
  pared de los deptos, una en la terraza del PH y una a cada lado de la arena en
  el pedestal del prócer. En el asfalto (capa ""), en DOS CARRILES: lo de escala 1 en el
  de atrás, arriba de la línea amarilla (ruedas en y 199, z 2/3, delante del
  cordón sin tapar a Lio); los patrulleros al doble en el de adelante: 4 autos quemados con llamas y resplandor que titila, 2 patrulleros con
  sirena roja/azul y su reflejo (al doble y más abajo, ruedas en y 246: más
  cerca de la cámara, pedido del usuario; `ESCALA` en el script) y en
  llamas: el fuego DETRÁS de la carrocería (asoma sobre el techo, la sirena sigue
  adelante) y humo propio (`HumoAuto`, capa Atmos) que se desvanece a media pantalla, colectivo cruzado, taxi volcado, conos, cubierta
  y escombros. Ubicación en `CALLE` / `BANDERAS` del script.
  En la arena, 6 coronavirus gigantes de fondo alrededor del Obelisco
  (`VirusFondo`, sprite del virus x2/x3, Decor z −1 detrás del Obelisco y las
  estatuas, tinte 110;140;120 + opacidad 175, flotan y giran; no son del grupo
  Virus: no dañan).
  Orden de L3: agregar `wire_l3_caos.py` después de `wire_l3_luces.py`.

- **Zombies que no paran de entrar a la arena (18/10, L3):**
  `wire_l3_arena_zombies.py` ("me sirven de plataforma"). Durante la pelea
  (BossActivo 1, BossDown 0, Won 0) entra uno cada 1.8 s alternando el lado
  (izq. detrás de la barricada, der. desde afuera), máx 7 (era 3 s / 4: "más
  zombies que entren"); cruzan sin darse
  vuelta (30-40 px/s) y se borran al salir; al ganar hacen poof. Grupo Zombies:
  pisarlos = trampolín + cadena de puntos; de costado = −1 vida. Tipos que rotan:
  TODOS los NPC del juego (los 13 del grupo; el policía que entra no dispara:
  no tiene el timer "Fuego", que solo arranca en los puestos al cargar). Además cae del cielo de la arena un
  **coronavirus de los que se desvanecen** (`MiniVirus`, persigue a Lio, −1 vida) cada
  4 s, máx 3 contando los del jefe (`VIRUS_CADA`/`MAX_VIRUS`); al ganar se borran. Var de objeto `Arena` = 1 (los
  del recorrido no se tocan); escena ArenaT/ArenaLado/ArenaTipo/ArenaZ, reloj con
  TimeDelta (se congela en pausa). Verificado: entran, cruzan, salen; pisotón
  rebota a Lio de y 90 a y 18. Falta playtest (dificultad con el jefe).

- **Pintadas en el muro de la costanera (19/10, L1):** `gen_grafitis_n1.py` →
  `wire_grafitis_n1.py` (independiente, idempotente, REVERT=1 las saca).
  Datos y ubicación en `PINTADAS` del generador. Letra de pincel dibujada por
  trazos (sobremuestreo + reducción), estilo de las referencias que pasó el
  usuario en la raíz del repo: "LAS MALVINAS SON ARGENTINAS" blanco al comienzo
  (x 12, letra de la bandera de la semifinal), "PATRICIO REY y sus Redonditos
  de Ricota" rojo apagado en el centro (x 1166, tapa de Gulp!), el esclavo de
  Oktubre en esténcil blanco pasando el agua (x 1404, `esclavo.webp`) y
  "#YO APOYO LA LEY DE FINANCIAMIENTO UNIVERSITARIO" antes de la meta (x 2370).
  Objetos `Grafiti_*`, capa base z −2 (delante del muro, z −3), con el mismo
  efecto Noche del muro. Verificado en runtime (capturas).

- **Pelea nueva con Paciente Zero: "que se clave la jeringa" (19/10, L3):**
  `wire_jefe_jeringa.py` (el último de la cadena de L3). La pelea vieja se
  descartó entera (usuario: "muy malas"); sus 11 eventos quedan en
  `scripts/jefe_pelea_vieja.json` y `REVERT=1` los restaura. Estados: 0 camina →
  1 apunta (Carga + contorno rojo + chispazo) → 2 embiste → 3 clavado en una
  pirámide (Expuesto), única ventana para pisarlo; de costado no lastima mientras
  está clavado. Si sale a menos de 48 px de la pirámide, frena (no hay ventana
  gratis). Fases por vida: 3 lento y sin zombies; 2 más rápido, zombies, escupe
  al desclavarse; 1 se agranda x1.15 y embiste dos veces (la primera hacia el lado
  contrario a Lio, rebota, la segunda se clava del lado de Lio: de busto a busto
  NO se llega, planeando cae en x 268 y el busto der. empieza en 284). Cartel
  "PISALO!" (`PisaloText`) titilando en la fase 3. Virus del cielo en pausa
  mientras está clavado. Los bustos (Estante y 96, borde, estatua, bandera) se
  corrieron 22 px hacia el centro (132 / 284): debajo del viejo busto quedaba el
  jefe clavado sin poder pisarlo. Datos también en `wire_levels23.py` y
  `wire_l3_caos.py`. Verificado con robot: clavado en x 89 / 343, pisotón desde el
  busto en las 3 fases, doble embestida y la nota 7 al morir. Lio corre a 95 px/s.

- **Límite de contagios por nivel (19/10):** `fix_contagio_limite.py`
  (idempotente, REVERT=1). Cada zombie se contagia como mucho 1 vez en L1 y 2 en
  L2; L3 sin límite (inmunidad de 3 s, como antes). Var de objeto `Contagios` en
  los zombies del grupo Zombies; el evento del contagio pide `< límite` y suma 1
  (`LIMITES` en el script). Verificado en runtime en los 3 niveles (3 virus
  seguidos al mismo zombie: 1 / 2 / 3 contagios). Ojo al probar: el timer
  "Immune" arranca la primera vez que se consulta (3 s desde que empieza el nivel).

- **Orden de los scripts si se regenera** (todos idempotentes, GDevelop
  CERRADO): `wire_levels23.py --force` → `wire_score_hud.py` → `wire_top5.py` →
  `wire_pixel_texts.py` → `wire_mochila_niveles.py` → `wire_notas.py` →
  `wire_bordes_plataforma.py`. También re-correr `wire_notas.py` después
  de `fix_pause_toggle.py` o `wire_pause_panel.py`. `wire_lab_luces.py`,
  `wire_parallax.py`, `wire_minivirus.py`, `wire_noche_n1.py`, `wire_virus_patron.py`, `wire_lab_ventanal.py`, `wire_lab_subsuelo.py`, `wire_lab_ambiente.py` y `wire_lab_pistones.py` son independientes (re-correr
  el de luces, el de minivirus, el de virus patrón y el de ventanales después de `wire_levels23.py --force`). Arte: `gen_mochila.py`
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
7. ~~Mecánicas del jefe final~~: pelea nueva el 19/10 (ver "Pelea nueva con
   Paciente Zero"). Falta playtest del usuario. Texto original del pendiente
   (18/10, cerca del fin del ciclo):
   hoy la pelea no es entretenida y no se entiende (playtest de punta a punta
   del usuario). Falta que se lea cuándo es vulnerable y cómo dañarlo, darle
   ritmo y variedad, y arreglar el expuesto contra los bordes (queda bajo las
   estatuas y cuesta pisarlo). Detalle en `reseach.md` (18/10, cierre).
7b. **PENDIENTE: público lejano de la arena de L3** (`wire_l3_publico.py`,
   19/10): no convence al usuario, quedan tapados por las bases de los
   monumentos. Los virus de fondo achicados del mismo script sí quedan.
   Detalle y opciones en `reseach.md` (19/10).
8. ~~Bug del Tutorial~~ (planeo que dejaba a Lio cayendo lento): resuelto el
   18/10 con `fix_tutorial_planeo.py`.
9. Duración medida (25/10, usuario): 15–30 min la primera partida completa,
   según la habilidad. Falta el video pitch (hasta 5 min). Entrega final:
   **03/11/2026** (o hasta el 10/11 si no llega; antes figuraba el 31/10).
10. **Desarrollo cerrado el 25/10** (después del reloj y el TOP 5). Queda el
   GDD final: se arma sobre el avance entregado a mitad de desarrollo
   (`avance_devolucion/avance_gdd.html` → PDF), chequeado contra los
   documentos de la cátedra. Plan página por página en `reseach.md` (25/10).
