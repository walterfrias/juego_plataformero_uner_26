# High Concept Document — Paciente Zero

> Documento en calidad **borrador**. Base para el GDD.
> Estructura tomada de *Videojuegos — Manual para diseñadores gráficos*
> (Thompson), págs. 86–87 (preguntas del concepto) y 92–93 (las 6 partes
> del "Concepto del juego"). Proyecto: prototipo de plataformas 2D,
> UNER — Multimedia y Juegos Web. Motor: GDevelop.

---

## 1. Descripción del juego (un párrafo)

Plataformero 2D de acción arcade con estética pixel-art. Un brote
zombie golpea la Ciudad de Buenos Aires y el/la protagonista —el/la
único/a humano/a inmune al virus— se abre paso desde la calle hasta el
foco de la infección para derrotar al **Paciente Zero**, el científico
que provocó el brote de forma deliberada. La **característica única** tiene
dos caras. Primero: no hay armas; la única forma de eliminar zombies es
saltarles sobre la cabeza (*stomp*), como en un plataformero clásico, lo
que convierte cada enemigo en un pequeño puzzle de plataformas. Segundo:
en cada nivel hay un tramo de **persecución** en el que una horda masiva
avanza como una estampida —ruido, polvo, velocidad de tren— y la única
forma de no quedar atrás es subirse arriba de la manada y correr sobre
ella como si fuera un suelo móvil. Por el camino se juntan **antídotos**
(coleccionable de gameplay: suman al marcador y dan vida extra) y se
encuentran **notas del diario de Paciente Zero**, que cuentan la historia
sin diálogos. Duración total ~30 min (tutorial + 3 niveles). **Mercado potencial:** jugadores de
plataformas clásicas y de arcades tipo *Zombies Ate My Neighbors*,
público de juegos web/navegador, y jugadores nuevos que buscan una
experiencia corta y accesible.
  
## 2. Resumen de la historia (un párrafo)

Buenos Aires amanece tomada por infectados. Lio, el/la único/a humano/a
inmune al virus, sale de su refugio para llegar al origen del brote.
Cruza la calle entre los primeros infectados, se interna en un
hospital/laboratorio donde descubre que la infección no fue un accidente,
y finalmente enfrenta al Paciente Zero, un científico que liberó el virus
para dominar a los infectados.
Al derrotarlo, el brote se detiene. Las notas de su diario, repartidas
por los niveles, van revelando ese trasfondo sin cortar la acción.

| Escena | Rol narrativo |
|---|---|
| Tutorial | Refugio seguro: se enseñan los controles sin peligro real. |
| Nivel 1 — La calle | Primer contacto con el brote. Introduce el *stomp*. |
| Nivel 2 — El interior | Hospital/laboratorio. Pistas del origen. Más enemigos + hazards. |
| Nivel 3 — Confrontación | Arena final contra el Paciente Zero. |

## 3. Plataforma

- **Objetivo:** juego **web** (navegador de escritorio), export HTML5 de GDevelop.
- Controles: teclado (flechas/WASD + salto). Sin requerimientos de hardware especiales.
- Fuera de alcance para el prototipo: móvil / táctil, consolas.

## 4. Género

- Principal: **Plataformas 2D** (acción arcade).
- Incluye tramos de **persecución / auto-scroll** (correr sobre la horda)
  que cortan el ritmo de exploración con un pico de tensión.
- Referencias de tono/mecánica: *Super Mario Bros.* (stomp, jefe con
  varios golpes), *Zombies Ate My Neighbors* (tema zombie en clave
  ligera, no survival horror), *Donkey Kong Country* (tramos de
  persecución con auto-scroll).

## 5. Público

**Público de diseño** (para quién está pensado el juego; guía las
decisiones de dificultad, tono y contenido):

- **Franja de edad:** 12+ — equivalente a **PEGI 12 / ESRB Teen**:
  violencia fantástica (zombies), sin sangre realista, tono arcade retro.
- **Perfil:** jugador casual con afinidad por el pixel-art y las
  plataformas clásicas. Abarca desde adolescentes hasta adultos de 40+.
- **Personalidad del jugador:** más curioso/explorador que competitivo;
  busca sesiones cortas y superar retos de habilidad.
- **Juegos que jugó antes:** plataformeros clásicos de consola, juegos de
  navegador, arcades retro.
- **Cómo atraer nuevos jugadores:** partida corta (~30 min), curva de
  dificultad suave con tutorial sin riesgo, mecánicas mínimas y legibles
  —una para el combate (saltar sobre el enemigo) y una para los tramos de
  persecución (correr por encima de la horda), ambas apoyadas en el mismo
  salto—, estética pixel-art reconocible.

**Contexto de evaluación** (dato real, no dirige el diseño): el prototipo
se presenta ante la cátedra y compañeros de cursada — adultos de ~25 a 50
años (promedio 30–40). No está pensado para comercializarse.

---

## 6. Concepto del juego — las 6 partes (libro, págs. 92–93)

### a. Gráficos de los componentes
- Pixel-art, sprites 32×32 (Lio: canvas 32×34 para igualar la escala de
  los zombies), resolución interna 480×270 (16:9, escalado *nearest*).
- Componentes a producir: personaje jugable (idle, run, jump, fall, hit,
  death), zombies de patrulla — varias variantes visuales del mismo
  comportamiento (walk, death) —, Paciente Zero (idle/telegraph,
  ataque, hit, death), tiles de calle / interior / arena, hazards
  (pinchos), fondo por nivel, ítem de antídoto (frasco), nota del diario
  (papel) y **horda para el tramo de persecución** (masa de zombies
  animada como una sola pieza + partículas de polvo/humo).
- Criterio de arte: **nada generado por IA.** Los sprites de enemigos y
  los props se producen de forma procedural con scripts propios (Python
  + Pillow) sobre una paleta compartida — esto da consistencia y permite
  sacar variantes rápido. El personaje jugable usa un sprite CC0
  (Forest Boy, OpenGameArt) recoloreado a celeste/blanco Argentina —
  ya no es placeholder, es el arte definitivo de Lio. El jefe (Paciente
  Zero) sigue pendiente de pase de arte propio. Tiles y fondos pueden
  apoyarse en packs CC0 (Kenney) si hace falta acelerar.

### b. Interfaz
- Menú principal: Jugar / Opciones / (Salir).
- Menú de opciones: volumen música, volumen SFX, reiniciar nivel, volver al menú.
- HUD en partida: vidas restantes (3), contador de antídotos
  (`Antídotos: 3 / 4`), indicador de nivel/checkpoint.
- Nota del diario: al recogerla, cartel de texto breve que pausa un
  instante o se cierra con una tecla.
- Pantallas: tutorial, transición entre niveles, game over, victoria
  (con % de antídotos del nivel).

### c. Historia
- Contada de forma mínima (carteles/ambiente), sin diálogos largos —
  coherente con el ritmo arcade. Ver sección 2.
- Vehículo narrativo principal: **notas del diario de Paciente Zero**
  (~2–3 por nivel). Cada una es un texto corto opcional; juntarlas todas
  no es obligatorio para terminar el juego, pero completa el trasfondo
  (por qué provocó el brote, qué buscaba). Encaja con lo que recomienda
  el libro (pág. 92: "historia limitada a los puntos que el jugador
  visita").

### d. Diseño de niveles
- Tutorial + 3 niveles, ~24–29 min en total.
- Progresión de dificultad: densidad creciente de zombies, hazard nuevo
  en Nivel 2, jefe en Nivel 3. Checkpoint a mitad de los niveles 1 y 2.
- El diseño de cada nivel se subordina a la mecánica única (stomp): los
  retos son de posicionamiento y timing de salto.
- Cada nivel incluye un **tramo de persecución sobre la horda**: la manada
  avanza como estampida y hay que avanzar por encima sin quedar atrás.
  Sirve de clímax del nivel o de transición entre zonas; nunca ocupa el
  nivel entero (detalle de implementación → GDD).
- Antídotos y notas del diario se colocan como incentivo para explorar
  rutas alternativas / plataformas opcionales (no en el camino directo a
  la meta).

### e. Mecánica de juego
- Movimiento: correr + saltar (behavior nativo *Platformer Character* de
  GDevelop; sin doble salto ni dash).
- Combate: **stomp** — eliminar zombies cayendo sobre su cabeza; el frame
  de "fall" se reusa como ataque.
- **Persecución sobre la horda:** en el tramo de estampida la masa de
  zombies funciona como plataforma móvil; el desafío son los huecos en la
  manada y las plataformas fijas del escenario a las que trepar. Quedar
  atrás (tocar el borde de pantalla) cuesta 1 vida y devuelve al
  checkpoint. Dentro de la horda no se pisa zombies: solo se corre y salta.
- Daño: se pierde 1 vida al tocar un zombie de costado; invulnerabilidad
  breve con parpadeo tras recibir daño. 3 vidas.
- Jefe: Paciente Zero telegrafía → ataca → queda expuesto un instante
  (única ventana de stomp). 3 stomps para derrotarlo, con invulnerabilidad
  entre cada uno.
- Coleccionable: **antídotos** (frascos). Un solo sistema — contador
  global en el HUD; **4 antídotos por nivel, juntar los 4 = 1 vida extra**;
  juntar todos los de un nivel = 100% en la pantalla de victoria. Sin
  tabla de récords ni guardado (fuera de alcance del prototipo).
- Objetivo de nivel: llegar a la meta con vidas > 0. Antídotos y notas
  son opcionales.
- **Mochila de repartidor** (confirmado 2026-09-12): prop/ítem único
  por nivel que desbloquea planeo (caída lenta) para el resto del
  nivel al agarrarlo — mantener Salto apretado mientras se cae baja la
  velocidad máxima de caída. No suma tecla ni animación nueva.

### f. Sonido
- Música de fondo: 1 loop general (idealmente 1 por nivel si da el tiempo).
- SFX obligatorios (colisiones, según consigna): stomp/kill de zombie,
  daño al jugador.
- SFX recomendados: salto, pickup de antídoto, golpe del jefe, victoria.
- **Fuente de audio: 100% procedural** (Python + numpy,
  `scripts/gen_sfx.py`) — mismo criterio que el arte (Pillow). Sin
  librerías CC0 de terceros, descartadas por completo (decisión
  2026-09-17/18): tanto SFX como música quedan generados por código
  propio para mantener consistencia con el resto del pipeline.

---

## 7. Decidido en este sprint

- **Título del juego: Paciente Zero** (antes pendiente; candidatos
  descartados: *PISOTÓN*, *Cero Pacientes*). Confirmado 2026-09-02.
- **Personaje jugable: Lio** (antes provisorio *Val*, luego *d10ego*
  —guiño a Maradona— renombrado 2026-09-13) — guiño a Messi, coherente
  con la ambientación porteña. Arte definitivo: sprite CC0 (Forest Boy,
  OpenGameArt) recoloreado a celeste/blanco Argentina (2026-09-14).
- Jefe final: **Paciente Zero** (antes "Paciente Cero").
- Coleccionable único: **antídotos** (contador + vida extra + 100%).
  **4 por nivel; juntar los 4 = 1 vida extra.** Sin score aparte, sin
  tabla de récords.
- Narrativa: **notas del diario** de Paciente Zero, ~2–3 por nivel,
  opcionales.
- Característica única, segunda cara: **tramo de persecución sobre la
  horda** en cada nivel (la manada como suelo móvil). Reemplaza a las
  alternativas descartadas (apilar zombies sueltos, trampas ambientales).
- Fuente de audio: **100% procedural (Python)**, sin librerías CC0
  (descartadas por completo 2026-09-17/18) ni IA-audio — SFX y música
  generados con `scripts/gen_sfx.py`, mismo criterio que el arte.
- Público de diseño: **12+ (PEGI 12 / ESRB Teen)**, casual, pixel-art /
  plataformas clásicas, adolescentes a 40+.
- **Mochila de repartidor** (2026-09-12): prop de escenario que además
  funciona como power-up de planeo (caída lenta), único por nivel.
  Sprite propio (Pillow), sin IA. Ver GDD §6.

## 8. Pendiente de definir

- Confirmar duración por nivel con playtesting.
- Ajustar el tramo de persecución con playtesting: velocidad de la horda,
  largo del tramo, penalización por quedar atrás, y si se prototipa como
  un solo objeto ancho o con instancias.
