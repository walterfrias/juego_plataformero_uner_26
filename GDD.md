# Documento de Diseño — Paciente Zero

> Prototipo de plataformas 2D — UNER, Multimedia y Juegos Web.
> Motor: GDevelop. Trabajo individual.
> Este documento cubre los puntos 9.a y 9.b de `consigna.md` (temática/
> narrativa y ficha de personaje), y de paso el resto del diseño
> necesario para cumplir los puntos 3, 6 y 7 (niveles, menú de
> opciones, sonido).
>
> Título confirmado: **Paciente Zero** (2026-09-02). El resto de
> textos narrativos (diario, diálogos) sigue siendo propuesta
> editable.

## 1. Tema y narrativa

Un brote zombie golpea la **Ciudad de Buenos Aires**. El/la
protagonista es **el/la único/a humano/a inmune al virus** y se abre
paso desde la calle hasta el foco de la infección, enfrentando oleadas
de infectados cada vez más densas, para encontrar y derrotar al
**Paciente Zero**: la persona (o experimento) que originó el brote.

Motivación del villano (borrador, a pulir): Paciente Zero es un
científico que provocó el brote de forma deliberada, buscando
dominar el mundo controlando a los infectados — no fue un accidente
de laboratorio.

Tono: **arcade retro pixel-art**, más cercano a "Zombies Ate My
Neighbors" que a survival horror — ligereza y ritmo de plataformas
clásico, no terror.

Arco narrativo en 3 niveles + tutorial:

| Escena | Rol narrativo |
|---|---|
| Tutorial | Punto de partida seguro (ej. una casa/refugio) donde se enseñan los controles sin peligro real. |
| Nivel 1 — La calle | Primer contacto con el brote. Zombies sueltos, pocos obstáculos. Introduce la mecánica de stomp. |
| Nivel 2 — El interior | Un hospital o laboratorio, donde se empieza a entender el origen del brote (pistas ambientales, opcional). Más densidad de enemigos y algún hazard de plataforma (pinchos, huecos). |
| Nivel 3 — Confrontación | Arena final. Combate contra el Paciente Zero. |

## 2. Ficha del personaje jugable

- **Nombre:** d10ego (guiño a Diego Maradona / la camiseta N°10 —
  coherente con la ambientación en Buenos Aires)
- **Rol:** único/a humano/a inmune al virus, sin entrenamiento de
  combate — su única arma es su propio peso: elimina zombies saltando
  sobre sus cabezas (stomp), igual que un plataformero clásico.
- **Vidas:** 3 (a confirmar con duración de nivel)
- **Daño:** pierde una vida al tocar un zombie por el costado o
  recibir un golpe; invulnerabilidad breve tras recibir daño
  (estándar en GDevelop: timer + parpadeo).
- **Movimiento:** correr, saltar — behavior nativo `Platformer
  Character` de GDevelop, sin habilidades extra (doble salto, dash)
  para no ampliar el scope de animación.
- **Animaciones necesarias (mínimo):** idle, run, jump (subida),
  fall (bajada), hit/damage, death. El stomp puede reusar el frame de
  "fall" — no hace falta una animación de ataque dedicada, coherente
  con la mecánica elegida.
- **Tamaño de sprite:** 32x32 (confirmado).

## 3. Enemigos

### Zombie (infectado)
- **Un solo comportamiento, varias variantes visuales.** Todos
  patrullan una plataforma de punta a punta (invierten dirección al
  llegar al borde de su tramo), mueren de un stomp y dañan al jugador
  por contacto lateral. Lo que cambia entre variantes es el *aspecto*
  y la *velocidad de patrulla* (una lectura rápida de personaje: un
  oficinista, una anciana encorvada, un obrero rengo, un corredor
  volcado hacia adelante, un adolescente con tics, etc.), no las reglas.
- Sirven para poblar la ciudad y dar variedad de silueta sin sumar
  mecánicas nuevas ni trabajo de diseño por enemigo.
- Animaciones por variante: walk (8 frames), death (reusa un frame de
  walk o squash simple).

### Paciente Zero (jefe final, Nivel 3)
- Versión mutada/más grande del zombie común — puede reusar la
  paleta y la estructura de sprite de los zombies para ahorrar trabajo
  de arte, escalado o con detalles extra.
- **Patrón de combate** (pensado para la mecánica de solo-stomp):
  1. Telegrafía un ataque (ej. se agacha 1 segundo antes de embestir).
  2. Ataca (embestida horizontal o "pisada" que el jugador esquiva
     saltando).
  3. Tras el ataque queda expuesto un instante — única ventana para
     stompearlo.
  - Necesita **3 stomps** para morir, con breve invulnerabilidad
    entre cada uno (mismo patrón que jefes clásicos de plataformas
    tipo Bowser/Koopa).
- Animaciones mínimas: idle/telegraph, ataque, hit, death.

## 4. Niveles — estructura y tiempos

Objetivo: **30 minutos totales** de juego (punto 4 de la consigna).

| Nivel | Duración estimada | Contenido |
|---|---|---|
| Tutorial | ~3–5 min | Correr, saltar, stomp de práctica sobre 1-2 zombies "de entrenamiento", sin posibilidad real de perder. |
| Nivel 1 | ~7–8 min | Plataformas simples, zombies de patrulla (varias variantes visuales del mismo comportamiento), checkpoint a mitad de nivel. |
| Nivel 2 | ~7–8 min | Más densidad de zombies, 1 hazard nuevo (pinchos/huecos), checkpoint. |
| Nivel 3 (boss) | ~7–8 min | Arena de combate contra Paciente Zero + pantalla de victoria. |

Total: ~24–29 min, dentro del margen pedido.

## 5. Menú de opciones (punto 6 de la consigna)

Mínimo viable:
- Volumen de música
- Volumen de efectos (SFX)
- Reiniciar nivel actual
- Salir / volver al menú principal

## 6. Coleccionables y narrativa ambiental

Decidido en la lluvia de ideas del HCD (ver `HIGH_CONCEPT.md`).

### Antídotos (único coleccionable de gameplay)
- Frascos repartidos por los niveles, en rutas alternativas / plataformas
  opcionales (no en el camino directo a la meta).
- Un solo sistema: contador global en el HUD (`Antídotos: 3 / 4`).
- **4 antídotos por nivel; juntar los 4 = 1 vida extra** (confirmado
  2026-09-02).
- Juntar todos los de un nivel = 100% en la pantalla de victoria.
- **Sin** tabla de récords ni guardado en disco (fuera de alcance).

### Mochila de repartidor (power-up de planeo, confirmado 2026-09-12)
- Prop de escenario ambientado en la ciudad (delivery), no un
  coleccionable de conteo como el antídoto: es un ítem único por nivel
  que **desbloquea una habilidad para el resto del nivel** al agarrarlo.
- Efecto: mientras cae, si el jugador mantiene apretado Salto (Space),
  la velocidad máxima de caída baja de 600 a 80 px/s (behavior
  `PlatformerObjectBehavior`, propiedad `MaxFallingSpeed`) — planeo /
  caída lenta. No agrega tecla nueva ni animación nueva (reusa el
  frame de Fall).
- No es doble salto ni vuelo libre: sigue sin poder subir, solo cae
  más despacio. Mantiene la decisión original de no ampliar el scope
  de animación (ver §2), a costa de tocar una sola propiedad física.
- Sprite: pixel-art propio (Python + Pillow, `scripts/gen_mochila.py`),
  estética de mochila térmica de delivery en naranja vivo con parche
  blanco y una "R", correas negras. No es un asset CC0 ni generado por
  IA — mismo criterio que zombies y antídoto.
- Wiring: `scripts/wire_mochila.py` (Nivel 1, 1 instancia en x=950,y=96,
  junto al 3er antídoto sobre el pozo de agua).

### Notas del diario de Paciente Zero (narrativa)
- ~2–3 por nivel. Al recogerlas, cartel de texto breve.
- Opcionales: no hacen falta para terminar el juego, pero completan el
  trasfondo del villano (por qué provocó el brote).
- Es el vehículo narrativo principal — evita diálogos largos, coherente
  con el ritmo arcade y con el libro (pág. 92).

## 7. Sonido (punto 7 de la consigna — mínimo música de fondo + colisiones)

- Música de fondo: 1 loop general (o 1 por nivel si da el tiempo).
- SFX obligatorios por la consigna (colisiones): stomp/kill de
  zombie, daño al jugador.
- SFX adicionales recomendados: salto, pickup de antídoto, golpe/hit
  del jefe, victoria.
- **Fuente: librerías CC0** (Kenney Audio, freesound.org, packs GDC de
  Sonniss) — mismo criterio que el arte. SFX/música propios solo si
  sobra tiempo.

## 8. Pendiente de definir

- Motivación del Paciente Zero (borrador en §1, "a pulir" — texto
  final del diario/cinemáticas cuando se escriban las notas
  narrativas).
- Nº de notas de diario reales por nivel (hoy: "~2-3", placeholder).

### Ya confirmados (2026-09-02)
- Título: **Paciente Zero**. Nombre del jugable: **d10ego**. Balance
  de antídotos: 4 por nivel, los 4 = 1 vida extra (ver §6).
- Mecánica del hueco forzado (Nivel 1, Tier 2): si el jugador no está
  parado sobre la horda al cruzar y cae al río, **pierde 1 vida y
  reaparece en un checkpoint justo antes del hueco** (no es muerte
  instantánea ni un simple empujón). Implica agregar un spawn point /
  variable de checkpoint antes del tramo x[1730..1970] — pendiente de
  implementación, ver `reseach.md`.
