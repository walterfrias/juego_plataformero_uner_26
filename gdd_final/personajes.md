# Personajes

> Apartados "Movimiento e interacción", "Salud y poder" y "Personajes no
> jugadores" de la plantilla del DDJ (Thompson, págs. 106–107). La ficha de
> Lio cubre el punto 9.b de la consigna (actualiza la ficha de la primera
> entrega).
>
> Referencia de velocidades: Lio corre a 95 px/s. Todos los personajes miden
> 32×34 px salvo el jefe (48×51 el cuerpo; 72×51 la imagen, con la motosierra).

## Lio — el personaje jugable

| | |
|---|---|
| **Nombre** | Lio (guiño a Messi; lleva la camiseta celeste y blanca) |
| **Rol en la historia** | Héroe: el único humano inmune al virus |
| **Arquetipo** | El sobreviviente reluctante / el explorador |
| **Personalidad** | Sin entrenamiento de combate, decidido; corre antes que pelear |
| **Habilidad** | Elimina zombies **cayéndoles encima** (pisotón). No tiene armas. |
| **Movimiento** | Correr, saltar y trepar postes y escaleras. **Planear** desde que encuentra la mochila de repartidor (Nivel 1). |
| **Vidas** | 3, y una cuarta si junta los 4 antídotos de un nivel |
| **Daño** | Pierde 1 vida si un zombie lo toca de costado o si lo golpea un virus o un tiro. Lo empuja hacia atrás y queda invulnerable 1 s, parpadeando. Caer a un pozo, al agua o al charco electrificado le saca 1 vida y lo devuelve al último checkpoint. |
| **Objetivo** | Llegar al foco de la infección y derrotar a Paciente Zero |
| **Estrategia** | Cruzar la ciudad, sobrevivir a la horda, juntar antídotos para tener margen y las pruebas para entender qué pasó |

**Sprite.** 32×34 px, contorno de 1 px. La base es *Forest Boy* (CC0,
OpenGameArt, rehash de *Classic Hero* de GrafxKid): recortado, reescalado y
**recoloreado a la camiseta argentina** (en el original era verde). Es el
único personaje que no es 100 % propio.

<!-- paleta:lio -->

**Animaciones:**
- Idle;
- Run;
- Jump / Fall (el pisotón usa el cuadro de caída);
- Hit;
- Death.

La **mochila** se dibuja aparte, en la espalda, y se da vuelta con él.

### Movimiento e interacción

| Con qué | Qué pasa |
|---|---|
| Zombie, desde arriba | Lo elimina (o le quita el contagio, si está infectado) y rebota. Encadenar pisotones sin tocar el piso: 100 → 200 → 400 → 800 → 1000 puntos. |
| Zombie, de costado | −1 vida y empujón. |
| Virus / minivirus / tiro | −1 vida y empujón. |
| Toldo, colchón | Rebote alto (el toldo de L3 lo sube ~84 px, por encima del policía). |
| Vapor del subte, ductos de aire | Lo elevan. |
| Horda (L1) | Funciona como **piso móvil**: se corre encima para cruzar el río. |
| Poste, escalera, cables | Se trepa / se cruza colgado por arriba. |
| Antídoto | +250 puntos; los 4 del nivel dan una vida extra. |
| Prueba del brote | Se lee la nota y queda guardada en la mochila. |
| Mochila (L1) | Desbloquea el planeo para el resto del juego. |

### Salud y poder

- **Vidas:** 3 al empezar cada nivel, más la cuarta de los antídotos. Con 0:
  Game Over y se reintenta el nivel.
- **Invulnerabilidad:** 1 s después de cada golpe.
- **Checkpoints:** de 7 a 8 por nivel; caer devuelve al último.
- **Poderes:** no hay power-ups temporales. La mochila es permanente y solo
  cambia la caída: no da doble salto ni vuelo.

## Zombies — los enemigos comunes

**Un solo comportamiento, muchas siluetas.** Todos los zombies:
- patrullan un tramo de punta a punta;
- mueren con un pisotón;
- lastiman de costado.

Lo que cambia entre ellos es el **aspecto, la manera de caminar y la
velocidad**, para que cada uno se reconozca de lejos sin sumar reglas
nuevas. Todos comparten la paleta "familia" (piel verde, ojos rojos) y
tienen 8 cuadros de caminata (la vecina, 10).

<!-- paleta:zombies -->

| Zombie | Aspecto y andar | Velocidad (px/s) | Dónde aparece |
|---|---|---|---|
| **Vecina** | Melena larga, vestido rosa roto; arrastra los pies | 18–22 | L1, L3 |
| **Obrero rengo** | Camisa azul rota, herida en el hombro; una pierna tiesa como pata de palo | 18–22 | L1 (también la "marcha"), L3 |
| **Arrastrada** | Alta y consumida, cárdigan mostaza; arrastra una pierna a los tirones | 12–22 | L1, L3 |
| **Adolescente** | Buzo con capucha, mochila al hombro; pasitos rápidos con tics | 16–26 | L1, L3 |
| **Anciana** | Muy encorvada, pañuelo, bata larga; **lentísima** | 8 | L1, L3 |
| **Obrero de obra** | Casco y chaleco reflectivo; renguera pesada | 13–18 | L1, L3 |
| **Corredor** | Ropa deportiva y vincha, volcado hacia adelante; **el más rápido** | 34–45 | final de L1, L3 |
| **Médico** | Guardapolvo abierto sobre ambo turquesa, estetoscopio; el zombie "clásico" con los brazos al frente | 20–22 | horda de L1, L2, L3 |
| **Enfermera** | Ambo verde agua, gorro de quirófano; se tambalea, un brazo muerto | 20–26 | horda de L1, L2, L3 |
| **Investigador** | Guardapolvo, antiparras y un matraz verde; encorvado y lento | 12 | horda de L1, L2, L3 |
| **Hincha** | Camiseta bordó, bufanda; camina "alentando" con los brazos arriba | 18–24 | horda de L1, L2, L3 |
| **Repartidor** | Campera, gorra y la mochila cúbica naranja; encorvado y rápido | 22–30 | horda de L1, L2, L3 |
| **Policía** | Uniforme azul, gorra; tieso, casi marcial. **En L3 dispara** | 16–22 | horda de L1, L2, L3 |

**Variaciones de comportamiento:**
- **La horda (L1):** zombies de la calle y del laboratorio que avanzan en
  bloque como una estampida. No es un enemigo: es un **piso móvil** para
  cruzar el río. Pasa en bucle.
- **El policía que dispara (L3):** si Lio está a menos de 240 px, avisa
  medio segundo (destello en la mano y un clic) y dispara un tiro a la altura
  del pecho que viaja a 150 px/s, cada ~1,7 s. Se esquiva con un salto
  planeado.
- **Zombies que entran a la arena (L3):** desde que empieza la pelea con el
  jefe entran de a uno, de cualquiera de los 13 tipos, cruzan sin darse
  vuelta y salen: una invasión que crece con cada vida que pierde el jefe
  (uno cada 1,2 / 0,95 / 0,7 s, hasta 10 / 12 / 14 a la vez). Sirven de
  trampolín.
- **Multitud de fondo (L3):** 14 zombies en silueta oscura con ojos rojos,
  en la vereda de enfrente. Son ambientación: no lastiman ni se pisan.

### El contagio (zombie + virus)

Si un virus toca a un zombie, el zombie **se contagia**:
- contorno rojo y una nube de gas;
- hay que **pisarlo dos veces** (el primer pisotón le saca el contagio);
- a los 0,8 s empieza a **escupir minivirus** a Lio si está a menos de
  200 px, uno cada 2,5 s, con un aviso de casi medio segundo (el contorno
  parpadea y suena un chispazo grave);
- se cura solo a los 6 s y queda inmune 3 s.

Límite por nivel: cada zombie se contagia **1 vez en L1, 2 en L2** y sin
límite en L3.

## Virus — los obstáculos voladores

| | Virus volador | Minivirus |
|---|---|---|
| **Aspecto** | Coronavirus de 16×16, 6 cuadros: el cuerpo "respira" y las 14 espigas vibran. Paleta rosa/roja de 4 tonos. | El mismo sprite. |
| **Movimiento** | **Recorrido fijo** según el lugar: ascensor (sube y baja), péndulo (barre y baja en el medio), ocho o círculo. Pensado como obstáculo de **timing**: la espera máxima es ~1 s. | **Persigue** a Lio: vuela a 55 px/s y cada nuevo rumbo apunta hacia él (±35°). Vive 5 s en L1 y 8 s en L2/L3, y se desvanece. |
| **De dónde sale** | Puesto en el nivel (5 en L1, 3 en L2, 3 en L3). | Lo escupe un zombie contagiado, sale de un **tubo de contención roto** (L2), lo escupe el jefe o cae del cielo de la arena. |
| **Qué hace** | −1 vida y empujón. **Contagia** a los zombies que toca. | −1 vida y empujón. No contagia. |

Los dos **brillan más cuanto más cerca está Lio** (ámbar en la calle, verde
en el laboratorio). No se pueden eliminar: se esquivan.

<!-- paleta:virus -->

## Paciente Zero — el jefe final

**Quién es.** El científico que trabajaba en el laboratorio del Nivel 2 y
escribió el diario. Soltó el virus a propósito en el festejo del Obelisco:
quería "un ejército que no protesta, no vota, no pide aumento". Es un zombie
más, dibujado con las mismas piezas que el médico y el investigador, pero
**una vez y media más grande** (el cuerpo, 48×51):
- mata de pelo negro, anteojos y ojos rojos;
- **guardapolvo abierto con la camiseta de Argentina**, como Lio, del otro
  lado;
- una **motosierra** prendida, grande: la espada (con la cadena arriba y
  abajo) es casi tan larga como su cuerpo. Para que entre, la imagen mide
  72×51; la colisión sigue siendo solo el cuerpo, así que la motosierra no
  lastima.

**Animaciones** (26 cuadros, como los zombies, que tienen 8 de caminata):
- Walk (8 cuadros, la motosierra al frente con la cadena girando);
- Carga (6: se agacha, levanta la motosierra y la acelera, sale humo): es el
  aviso antes de embestir;
- Embiste (4: corre inclinado, con el guardapolvo al viento y chispas en la
  punta);
- Expuesto (8: de rodillas, la motosierra trabada que vibra, estrellitas =
  "pisalo").

<!-- galeria:jefe -->

<!-- paleta:jefe -->

**Patrón de combate** (pensado para un juego donde solo se ataca saltando):

| Estado | Qué hace | Fase 3 (3 vidas) | Fase 2 | Fase 1 |
|---|---|---|---|---|
| Camina | Va hacia Lio | 35 px/s | 45 px/s | 55 px/s |
| Apunta | Aviso: se agacha, contorno rojo, chispazo | 1,0 s | 0,85 s | 0,7 s |
| Embiste | Carga en línea recta | 170 px/s | 205 px/s | 240 px/s, **dos veces**: la primera hacia el otro lado, rebota, y la segunda se clava del lado de Lio |
| Trabado | La motosierra se le traba en una pila de patrulleros: **única ventana para pisarlo**; de costado no lastima | 3,0 s | 2,6 s | 2,2 s |

**Cómo cambia cada fase:**
- **Fase 3:** cartel "¡PISALO!" mientras está clavado. Ya entran zombies
  (uno cada 1,2 s, hasta 10).
- **Fase 2:** escupe virus al desclavarse; más zombies (cada 0,95 s, hasta 12).
- **Fase 1:** se agranda (×1,15) y hace la doble embestida; la invasión es
  máxima (cada 0,7 s, hasta 14).
- **En las tres:** cae un coronavirus del cielo cada 4 s (como mucho 3 a la
  vez), salvo mientras el jefe está clavado.

<!-- capturas:jefe -->

**Al morir** suelta la séptima prueba, "Última página". La victoria llega al
leerla.

**Cómo se llegó a esta pelea.** La primera versión (un ciclo
telegrafía → ataque → expuesto, como la del avance) "no se entendía y no
era entretenida" en el playtest de punta a punta. Además, si quedaba
expuesto contra el borde de la arena, abajo de las estatuas, costaba
pisarlo. La pelea nueva hace que el jefe **se clave solo en un lugar
visible**. Los bustos se corrieron 22 px para que nunca quede debajo de
una plataforma.

## Galería

Todos los personajes, salvo la base de Lio, se dibujaron por código (Python +
Pillow), sin IA de imagen. Tiras de caminata de 8 cuadros (la vecina, 10):

<!-- galeria:personajes -->

### Antídoto y mochila

Los dos objetos de la primera entrega, con sus paletas:

<!-- paleta:antidoto -->

<!-- paleta:mochila -->
