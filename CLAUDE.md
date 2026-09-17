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

## Motor y herramientas

- **GDevelop**, todavía sin proyecto scaffoldeado dentro de este repo
  (a la fecha del último commit, no existe ningún `.json` de proyecto
  GDevelop todavía).
- Este repo tiene un `.mcp.json` que apunta a un servidor MCP de
  terceros, [`gb2b/gdevelop-mcp`](https://github.com/gb2b/gdevelop-mcp)
  (MIT, no oficial), clonado e instalado en
  `~/Escritorio/gdevelop-mcp/` (fuera de este repo, es una herramienta
  compartida, no un asset del juego). Ya se corrió `pnpm install` +
  `pnpm build` ahí, `dist/index.js` existe.
- **Nunca se probó el flujo end-to-end.** Primeros pasos pendientes
  apenas arranque una sesión con este MCP disponible:
  1. `sync_gdevelop_sources()`
  2. `gdevelop_overview()`
  3. `quick_start_template` con un proyecto descartable, para
     confirmar que el MCP edita bien un `.json` antes de usarlo en
     serio.
  4. Ojo: no se confirmó que Puppeteer haya bajado Chromium durante el
     install (no apareció en `~/.cache/puppeteer`) — si las tools de
     preview runtime fallan la primera vez, puede hacer falta correr
     la descarga del browser a mano dentro de
     `~/Escritorio/gdevelop-mcp`.

## Cuello de botella identificado: animación de personaje

No es el código (con asistencia de IA eso dejó de ser el límite, se
demostró armando el prototipo de naves en una semana) — es la
animación 2D de personaje (idle/salto/caída, ~32x32). La AI de
generación de imágenes no es confiable para mantener consistencia
cuadro a cuadro. Salida recomendada: usar packs CC0 de personaje ya
animado (Kenney "Pixel Platformer Pack", "Tiny Hero Sprites", "Pixel
Adventure" de pixelfrog en itch.io) en vez de dibujar o generar por
IA — mismo criterio que ya se usó para el arte de naves en el otro
repo (pack CC0 de Kenney).

## Pendiente / próximos pasos

1. Validar el MCP de GDevelop (ver arriba).
2. Definir temática/narrativa propia (sin decidir todavía).
3. Armar el GDD + ficha de personaje.
4. Diseñar los niveles (~3 + tutorial) y elegir/armar el personaje
   jugable (pack CC0 recomendado arriba).
5. Menú de opciones, ~30 min de duración total de juego.
6. Video pitch (hasta 5 min) — dejar para cuando haya algo jugable.
