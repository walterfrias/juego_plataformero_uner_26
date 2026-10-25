# GDD final — índice propuesto

Estructura: la tabla del "Documento de diseño de juego (DDJ)" de Thompson,
*Videojuegos — Manual para diseñadores gráficos*, págs. 106–107 (PDF págs.
107–108). Base de contenido: el avance del 18/09
(`avance_devolucion/avance_gdd.html`), `GDD.md`, `HIGH_CONCEPT.md` y
`reseach.md`. Formato de salida: el mismo HTML → PDF del avance.

Estado de cada apartado:
- **[avance]** ya estaba en el avance, se actualiza;
- **[nuevo]** no estaba;
- **[falta dato]** depende de algo que todavía no tenemos.

---

## 0. Portada y cumplimiento de la consigna (fuera de la tabla)

- **Cubierta** [avance]. Datos de la UNER, la cátedra, los docentes y el
  integrante. "Entrega final", versión y fecha. Ya no dice "borrador".
- **Cumplimiento de la consigna** [nuevo]. Tabla con los 10 puntos de
  `consigna.md` y dónde se cumple cada uno: plataformas 2D, individual,
  tutorial + 3 niveles, 30 min, menú de opciones, sonido, GDevelop, GDD
  (temática + ficha) y video pitch.
- **Cambios desde el avance** [nuevo]. Lista corta: el jefe definitivo,
  L2/L3, las notas, el puntaje, el reloj, el top 5, etc. El manual lo pide
  en "Apéndices" (historial de revisiones); acá va el resumen.

## 1. Marketing

| Apartado | Contenido | Estado |
|---|---|---|
| Concepto de juego | El párrafo del High Concept, corregido: la horda está **solo en L1** (el avance decía "en cada nivel"). Lo único: solo pisotón, sin armas | [avance] |
| Sinopsis del juego | Buenos Aires tomada, Lio inmune, de la costanera al laboratorio y del laboratorio al Obelisco | [avance] |
| Elementos característicos | Pisotón con cadena de puntos, correr sobre la horda, contagio virus↔zombie, mochila que planea, pruebas del brote, Buenos Aires reconocible (Obelisco, costanera, pintadas, fachadas porteñas) | [avance] |
| Mercado | Público 12+, casual, pixel-art arcade (ya estaba). Referencias: Super Mario Bros., Zombies Ate My Neighbors | [avance] |
| Plataforma | Web (HTML5 export de GDevelop), escritorio y teclado; publicado en itch.io | [avance] |

## 2. Sinopsis de la historia (DDJ)

- La historia completa [avance, reescribir]. El científico que suelta el
  virus en el festejo, la ciudad tomada, el laboratorio y el final en el
  Obelisco. La versión del avance tenía "hospital/laboratorio" y "versión
  mutada".
- Tabla de escenas con su rol narrativo: Tutorial (refugio) → L1 costanera
  → L2 laboratorio → L3 de la calle al Obelisco.

## 3. Artístico — Apariencia y ambientación

- Paleta noche, pixel-art 480×270, todo procedural con Pillow, salvo Lio
  (Forest Boy CC0 recoloreado) [avance].
- Ambientación por nivel [nuevo]:
  - **L1:** noche con luna, fuego en tachos, faroles, niebla, parallax con
    el Obelisco y pintadas en el muro;
  - **L2:** luces de terror clase B, ventanales con la ciudad, subsuelo con
    tubos de contención y zona de alarma;
  - **L3:** fachadas porteñas, ciudad en capas, incendios, banderas, caos en
    la calle, pirámides y Obelisco en la arena.
- Galería de arte [avance + nuevo]. Ya estaban los 8 zombies, los props de
  calle y el virus. Se suman el arte del lab, el de L3 y el jefe.

## 4. Juego

| Apartado | Contenido | Estado |
|---|---|---|
| Objetivo del juego | Llegar al final de cada nivel y derrotar a Paciente Zero. Objetivos secundarios: los antídotos (4 por nivel en L1/L2), las 7 pruebas y el puntaje del top 5 | [avance, ampliar] |
| Mecánica de juego | Pisotón (cadena 100→1000), daño de costado + knockback, horda como plataforma móvil, planeo con la mochila, contagio virus↔zombie (con su límite por nivel), minivirus, mecánicas de cada nivel (piso encerado, pistones, ductos, tubos que estallan, toldo, charco, vapor, policía que dispara). **El manual pide ilustrarlas** (una figura por mecánica: sprite + flecha, o un recorte del mapa) | [avance, muy ampliado] |
| Sistemas de menú | Menú principal (Jugar / Opciones / Salir + top 5), opciones (volumen de música y de efectos), pausa (reiniciar, menú, I = mochila), Game Over y victoria con desglose | [avance, ampliar] |
| Controles | A/D o ←→ mover, J o Espacio saltar (mantener = planear), W trepar, ESC/P pausa, I mochila, R reintentar. Tabla de teclas | [nuevo] |
| Información en pantalla (HUD) | Corazones, antídotos n/4, PUNTOS, TIEMPO (rojo pasado el par), vida del jefe en L3, números arcade sobre los zombies | [nuevo] |
| Movimiento e interacción | Correr, saltar, planear, trepar, rebotar en el toldo y en los zombies, agarrar antídotos, notas y la mochila | [avance, ampliar] |
| Salud y poder | 3 vidas (hasta 4 con los antídotos), −1 por golpe con invulnerabilidad de 1 s, caer = −1 y volver al checkpoint, vida extra con 4/4 antídotos | [avance, ampliar] |

## 5. Técnico — Sistemas de cámara

- Cámara que sigue a Lio con un margen y queda dentro de los límites del
  nivel. En L3 se traba al entrar a la arena y aparece la barricada.
  Parallax por velocidades (Luna 0.03 … CityNear 0.55) [nuevo].

## 6. Juego — Mundo, física y personajes

| Apartado | Contenido | Estado |
|---|---|---|
| Mundo del juego | Estructura lineal: Tutorial + 3 niveles, de izquierda a derecha, con checkpoints y rutas opcionales (antídotos, ductos, notas) | [nuevo] |
| Física del juego | Behavior Platformer de GDevelop: velocidad 95 px/s, salto 350, gravedad 900, caída máx. 600 (80 planeando). **Medido: salto de ~28 px parado y 40–45 con carrera**; de ahí el ancho de los huecos. Piso encerado de L2 | [nuevo] |
| Personajes no jugadores | **Ficha de Lio** (punto 9.b de la consigna, con la ficha de la 1.ª entrega como anexo). Lista de los 13 zombies con su comportamiento y velocidad, dónde aparecen y la multitud de fondo de L3. Virus voladores (patrón fijo) y minivirus. **Paciente Zero:** el científico, la pelea de la jeringa en 3 fases y la nota 7 | [avance, muy ampliado] |
| Equipo y efectos | Mochila (planeo + inventario), antídotos, pruebas del brote | [avance] |

## 7. Animaciones (técnico / artístico)

- Lista por personaje [nuevo]:
  - Lio: Idle, Run, Jump, Fall, Hit, Death;
  - los zombies: Walk + muerte;
  - el jefe: Walk, Carga, Expuesto;
  - el virus: 6 cuadros;
  - el antídoto, las llamas, el humo, los tubos, etc.

## 8. Guión y walkthrough

- Las **7 notas** con su texto completo (fuente: `gen_notas.py` / GDD §6) y
  dónde aparece cada una [nuevo].
- **Walkthrough nivel por nivel** [nuevo]. El manual pide "mapas de niveles,
  localización de los PNJ, encuentros, tiempo transcurrido". Un **mapa por
  nivel** armado desde `game.json`, con zombies, antídotos, notas,
  checkpoints y peligros marcados, y debajo los tramos paso a paso.
- **[falta dato]** "Tiempo transcurrido": los tiempos reales por nivel.
  Salen del reloj nuevo en tu playtest de punta a punta, y de ahí el punto
  de los 30 min.

## 9. Técnico — Programación y sonido

| Apartado | Contenido | Estado |
|---|---|---|
| Diseño de programación | GDevelop (eventos), export HTML5, edición por scripts Python + MCP, pruebas con robot dentro del juego (puppeteer). Sin entrar en el detalle de los scripts | [avance, ampliar] |
| Diseño de sonido | Todo procedural (Python + numpy). Música: menú + 1 loop para los niveles (el mismo en L1/L2/L3). SFX de colisión y de juego (pisotón, daño, salto, pickup, victoria, game over) y de ambiente (zumbido de tubos, chispazo, fuego, gatillo y disparo) | [avance, ampliar] |

## 10. Apéndices

- **Game Testing / QA** [nuevo]. Es el foco que remarcó la cátedra en la
  Pre-Alfa:
  - playtests con personas (vos, tu hija) y qué cambió por cada uno: el
    virus random era "frustrante" y pasó a patrón fijo, el jefe "no se
    entendía" y se hizo la pelea nueva, etc.;
  - pruebas con robot: pistones 10/10, tiros del policía 7/7;
  - bugs encontrados y resueltos (los "4 zombies rotos", la pausa que se
    deshacía, la W que no trepaba…).
- **Historial de revisiones** [nuevo]. Ficha (09) → avance (18/09) →
  Pre-Alfa (29/09) → final.
- **Créditos** [nuevo]. Forest Boy (CC0, OpenGameArt) y el resto propio.
  Mención del uso de IA en el código y no en el arte (ya estaba en
  "Herramientas").
- **Anexo:** la ficha de personaje de la primera entrega.

---

## Pendientes para poder cerrarlo

1. **Tus tiempos por nivel** (playtest de punta a punta con el reloj).
   También sirven para calibrar el par.
2. Decidir el **público lejano de la arena** (pendiente 7b de `CLAUDE.md`)
   o sacarlo antes de las imágenes finales.
3. Revisar este índice: qué apartado sobra, cuál falta y qué tan largo
   querés el documento.
