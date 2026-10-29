# Apartados de marketing, arte y técnica

> Completa la plantilla del DDJ (Thompson, págs. 106–107) con los apartados
> cortos: marketing, apariencia y ambientación, cámara, mundo y física,
> animaciones, programación, sonido y créditos.

## 1. Marketing

**Concepto de juego.** Plataformero 2D de acción arcade en pixel-art. Un
virus zombie toma Buenos Aires y Lio, el único inmune, cruza la ciudad para
enfrentar al científico que lo soltó. Lo que lo distingue:
- **No hay armas**: los zombies se eliminan cayéndoles encima, así que cada
  enemigo es un pequeño problema de plataformas.
- En el Nivel 1 hay que **cruzar el río corriendo encima de una estampida
  de zombies**.

**Elementos característicos de la jugabilidad:**
- el pisotón con cadena de puntos;
- la horda como piso móvil;
- el contagio virus↔zombie (un zombie contagiado se vuelve más duro y
  escupe virus);
- la mochila que permite planear;
- 7 pruebas opcionales que cuentan la historia;
- reloj con bonus por rapidez y TOP 5 con iniciales;
- una Buenos Aires reconocible: costanera, Corrientes, el Obelisco,
  pintadas y fachadas porteñas.

**Consideraciones de mercado:**

| | |
|---|---|
| **Público** | 12+ (equivalente a PEGI 12): violencia fantástica sin sangre. Jugador casual, curioso más que competitivo, con afinidad por el pixel-art y las plataformas clásicas, de adolescentes a adultos de 40+. |
| **Atractivo** | Partida corta (15–30 min la primera vez), tutorial sin riesgo, dos mecánicas que se entienden en segundos (pisotón y correr sobre la horda) y la identidad local, que es poco común en el género. |
| **Referentes** | *Super Mario Bros.* (el pisotón como único ataque), *Zombies Ate My Neighbors* (el tono: zombies con humor, sin terror), *Donkey Kong Country* (montarse sobre el escenario en movimiento). |
| **Oportunidad** | Juego web gratuito, sin instalación: se juega desde un link de itch.io, lo que facilita compartirlo y probarlo con gente. |

**Plataforma.** Navegador de escritorio (export HTML5 de GDevelop), con
teclado. Publicado en itch.io. Quedan fuera de alcance: móvil y pantalla
táctil, y consolas.

## 2. Apariencia y ambientación

**Estilo.** Pixel-art a **480×270** (un cuarto de 1920×1080), contorno
de 1 px y sprites de 32×34. **Paleta de noche**: azules y violetas oscuros,
con la luz como acento (ámbar del fuego y los faroles, verde tóxico del
laboratorio, rojo de las alarmas). El criterio general: **oscurecer todo y
devolver la luz solo donde importa**, para que Lio, los zombies y las
plataformas se lean contra el fondo.

**Cómo se hizo el arte.** Todo el arte (zombies, jefe, props, fondos, luces,
notas, interfaz y la fuente pixel) se **generó por código** con Python y la
librería Pillow, sobre una paleta compartida. No se usaron packs de terceros
ni generadores de imágenes por IA: se descartaron porque no mantienen el
personaje igual de un cuadro al otro. La única excepción es la base del sprite
de Lio (CC0, ver Créditos).

| Escena | Ambientación |
|---|---|
| **Menú** | Skyline de noche en movimiento, la Luna, el Obelisco, zombies que caminan detrás de Lio. Subtítulo: "Buenos Aires — Noche cero". |
| **Nivel 1 — La costanera** | Noche con luna y nubes, niebla sobre el río, fuego en tachos y faroles de sodio. Ciudad en 4 planos de **parallax** (la Luna casi quieta, el Obelisco acompañando de lejos). Incendios lejanos con humo. La luna "pinta" el borde de arriba de cada objeto; Lio y los zombies toman un tinte frío que se entibia cerca del fuego. Pintadas en el muro. |
| **Nivel 2 — El laboratorio** | Luces de terror clase B: tubos que fallan, se cortan y chispean, con su zumbido. Zonas a oscuras con islas de luz verde (tanques) y cian (monitores). Por los ventanales se ve la ciudad de noche. Debajo del piso, el **subsuelo**: cañerías y tubos de contención con virus flotando, algunos rotos. Al final, **zona de alarma** con balizas rojas que barren. |
| **Nivel 3 — Del lab al Obelisco** | El centro **entre edificios**: fachadas porteñas (francés, departamentos de los 60, PH, bar de esquina), tapiadas, con vidrios rotos y cruces de cuarentena. Detrás, dos filas de edificios en parallax con cúpulas, tanques, antenas e incendios en los techos. En la calle: autos quemados, patrulleros con sirena, un colectivo cruzado, un taxi volcado, conos, pilas de escombros, tachos de basura volcados y rotos, bolsas y basura desparramada (algunos, en el carril más cercano a la cámara, en llamas), y 8 banderas argentinas apagadas para la noche. Una multitud de infectados en silueta en la vereda de enfrente. **Arena, la 9 de Julio:** el Obelisco con reflector y cinta de cuarentena; detrás, la torre crema del ex Ministerio de Obras Públicas con el **mural de Evita**; a los costados, dos **pilas de patrulleros** destruidos (una barricada policial que se vino abajo) que humean, con la sirena que todavía titila; bustos de próceres con barbijo y coronavirus gigantes flotando en el cielo. |

## 3. Sistema de cámara

- La cámara **sigue a Lio** dentro de los límites del nivel: no muestra lo
  que hay antes del inicio ni después de la meta.
- Al entrar a la arena del Nivel 3, los límites se cierran a la arena
  (480 px, una pantalla exacta): la cámara **queda fija** y la barricada
  impide volver.
- **Parallax:** las capas del fondo se mueven a distinta velocidad según la
  distancia. En L1: Luna 0,03, ciudad más lejana 0,12, Obelisco 0,15,
  ciudad lejana 0,30, ciudad cercana 0,55. El mismo sistema se usa en los
  ventanales de L2 y en las filas de edificios de L3.

## 4. Mundo y física del juego

**Estructura del mundo.** Lineal, de izquierda a derecha: Tutorial + 3
niveles en secuencia, cada uno con 7–8 checkpoints. Se ramifica en
**rutas opcionales cortas** que vuelven al camino principal: antídotos
altos, el corredor del subsuelo y los ductos de L2, notas escondidas.

**Física** (comportamiento *Platformer Character* de GDevelop):

| Parámetro | Valor |
|---|---|
| Velocidad máxima | 95 px/s |
| Aceleración / frenado | 300 / 1500 px/s² (en el piso encerado frena mucho menos) |
| Velocidad de salto | 350 px/s |
| Gravedad | 900 px/s² |
| Caída máxima | 600 px/s (80 planeando) |
| Alcance medido | ~37 px de alto; ~28 px de largo parado, 40–45 con carrera |

Las reglas de diseño de niveles salen de esos números: huecos de hasta 28
px sin ayuda; los más anchos llevan puente, cables, la horda o pistones.

**Equipo y efectos personales.** No hay armas ni power-ups temporales. Lo
que se lleva:
- **la mochila**: planeo e inventario de las pruebas, permanente desde el
  Nivel 1;
- **los antídotos**: puntos y la vida extra con 4/4;
- **las pruebas del brote.**

## 5. Animaciones

| Personaje / objeto | Animaciones (cuadros) |
|---|---|
| Lio | Idle (11), Run (12), Jump (1), Fall (1, también el pisotón), Hit (7), Death (7) |
| Zombies (13 tipos) | Walk (8; la vecina, 10). Al morir: ráfaga de "píxeles" del color del zombie. |
| Multitud de fondo (L3) | Walk (8–10), en silueta |
| Paciente Zero | Walk (8), Carga (6), Embiste (4), Expuesto (8) |
| Virus / minivirus | Idle (6): el cuerpo respira y las espigas vibran |
| Antídoto, mochila, nota en el piso | Idle (6) |
| Tubos de contención | Idle (4); el roto, además, Vacía (1) |
| Pistón, toldo | 2 cuadros (luces verde/roja; rebote) |
| Fuego, humo, chispas, banderas, sirenas | 2 a 6 cuadros |

Además hay efectos que no son cuadros: el contorno de color (contagio, aviso
del jefe), el brillo por cercanía de los virus y los bordes de plataforma, y
partículas (el gas del contagio, el humo de la horda, la ráfaga al morir un zombie).

## 6. Diseño de programación

- **Motor: GDevelop**, con lógica en **eventos** (sin código escrito a
  mano dentro del motor). Comportamientos nativos: *Platformer Character*
  para Lio y *Platform* para las plataformas (maciza, atravesable desde
  abajo, escalera).
- **Objetos:** Sprite, TiledSprite (pisos, fondos repetidos), BitmapText (la
  fuente pixel del HUD) y emisores de partículas. **Efectos de
  render:** Outline, Glow y Adjustment.
- **Export:** HTML5, publicado en itch.io.
- **Cómo se trabajó el proyecto.** Además del editor, el proyecto (un
  archivo JSON) se editó con **scripts de Python**: cada script hace una
  copia de seguridad, se puede volver a correr sin duplicar nada y
  verifica que el editor esté cerrado. También se usó un servidor MCP para
  GDevelop que permite inspeccionarlo y editarlo desde un asistente.
- **Pruebas:** con Puppeteer sobre el juego exportado y un robot dentro del
  juego, más la revisión del código compilado (ver el apéndice de Game
  Testing).
- **Datos guardados en el navegador:** el TOP 5, las últimas iniciales y el
  récord.
- **Uso de IA** (permitido por la cátedra):
  - **Qué hizo:** asistió en escribir el código: los scripts que generan el
    arte y el sonido, los que editan el proyecto y los de prueba (Claude
    Code, con el servidor MCP para GDevelop).
  - **Qué no hizo:** el arte y el sonido **no** salen de generadores de IA:
    los dibujan y sintetizan esos scripts. La lógica del juego son eventos
    de GDevelop.
  - **Las decisiones fueron del autor:** el diseño, los niveles, los
    personajes, la historia y los textos, qué entra y qué se descarta, y el
    playtest. Cada cambio partió de un pedido o de una prueba del autor, y
    quedó registrado en la bitácora del proyecto.

## 7. Diseño de sonido

Todo el audio es **procedural**: sintetizado con Python y numpy en estilo
chiptune. No se usaron bancos de sonidos (se descartó el material CC0) ni audio
generado por IA.

| Tipo | Sonidos |
|---|---|
| **Música** | Tema del menú (también en el Tutorial) y un loop para los niveles. |
| **Colisiones** | Pisotón (sube de tono con cada pisotón encadenado), daño de Lio, agarrar antídoto o nota. |
| **Juego** | Salto, selección en menús, victoria, game over. |
| **Ambiente** | Zumbido de los tubos del lab (en loop, más fuerte cerca de un tubo prendido), chispazo cuando un tubo cambia de estado, crepitar del fuego en L1 (más fuerte cerca de un tacho). |
| **Avisos** | Chispazo grave antes de que un zombie contagiado escupa; gatillo y disparo del policía. |

El volumen de música y de efectos se ajusta en Opciones y en la pausa. El
zumbido del laboratorio se calla en la pausa, en las notas y al terminar el
nivel.

## 8. Créditos

| | |
|---|---|
| **Diseño, programación, arte y sonido** | Walter Frías |
| **Sprite base de Lio** | *Forest Boy — Platformer Animated Character* de patvanmackelberg (rehash de *Classic Hero* de GrafxKid), OpenGameArt.org, **CC0** (dominio público). Recortado, reescalado y recoloreado. |
| **Motor** | GDevelop (open source) |
| **Herramientas** | Python, Pillow, numpy, Puppeteer, servidor MCP para GDevelop (gb2b/gdevelop-mcp, MIT), Claude Code (asistencia en el código) |
| **Testing** | Los docentes de la cátedra (Nivel 1) y una jugadora de 10 años |
| **Cátedra** | Multimedia y Juegos en Web, Tecnicatura Universitaria en Desarrollo Web, UNER. Docentes: Fabien M. Pineda, Hernan I. Hernandez, Juan I. Carubia. |

## 9. Historial de revisiones

| Fecha | Versión |
|---|---|
| 26/08/2026 | Primer GDD y High Concept (en el repositorio) |
| Sep. 2026 | Ficha de personaje (primera entrega) |
| 18/09/2026 | Avance del GDD + High Concept, para devolución |
| 29/09/2026 | Pre-entrega Pre-Alfa |
| 03/11/2026 | GDD final (este documento) |
