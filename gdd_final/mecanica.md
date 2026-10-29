# Objetivo y mecánica de juego

> Apartados "Objetivo del juego" y "Mecánica de juego" de la plantilla del
> DDJ (Thompson, pág. 107: "enumera e ilustra las mecánicas que se van a
> utilizar").

## Objetivo

- **Principal:** llegar a la meta de cada nivel y, al final, derrotar a
  Paciente Zero al pie del Obelisco.
- **Secundarios (opcionales):**
  - juntar los **4 antídotos** de cada nivel (vida extra y +1000);
  - encontrar las **7 pruebas del brote** (la historia completa y +1000);
  - hacer **puntaje y tiempo** para entrar en el TOP 5.
- **Derrota:** quedarse sin vidas → Game Over y se reintenta el nivel.

## Bucle principal

Avanzar → leer el obstáculo que viene (un zombie, un virus, un pozo, un
pistón) → resolverlo **saltando**: pisar, esquivar o subirse → pasar un
checkpoint → seguir hasta la meta → desglose del puntaje → siguiente nivel.

Todo se resuelve con **moverse y saltar**: no hay botón de ataque. Cada
mecánica nueva es una variación de "cuándo y dónde saltar".

## Mecánicas

| | Mecánica | Cómo funciona |
|---|---|---|
| ![](obj:Level1/ZombieF) | **Pisotón** | Caerle encima a un zombie lo elimina y rebota a Lio. De costado, el zombie lastima. |
| ![](obj:Level1/ZombieN) | **Cadena de pisotones** | Pisar varios zombies sin tocar el piso: 100 → 200 → 400 → 800 → 1000 puntos, y el sonido sube de tono. |
| ![](obj:Level1/Virus1) | **Virus volador** | Recorrido fijo (ascensor, péndulo, ocho, círculo): obstáculo de timing que se esquiva. Lastima a Lio y **contagia zombies**. |
| ![](obj:Level2/ZombieMed) | **Contagio** | Un zombie contagiado (contorno rojo y gas) necesita **dos pisotones** y escupe minivirus que persiguen a Lio. Se cura a los 6 s. |
| ![](obj:Level1/HordaZombieHin) | **La horda** (L1) | Una estampida de zombies cruza el río en bucle: se corre **encima** como si fuera un piso móvil. |
| ![](obj:Level1/Mochila) | **Mochila y planeo** | Desde que se encuentra (L1), mantener el salto mientras se cae baja la caída de 600 a 80 px/s. |
| ![](obj:Level1/Antidoto) | **Antídotos** | 4 por nivel, en rutas opcionales (en L3, uno por tramo de la calle). Los 4 dan una vida extra. |
| ![](obj:Level1/NotaPick) | **Pruebas del brote** | 7 notas que congelan el juego al agarrarlas y quedan en la mochila. |
| ![](obj:Level1/Poste) | **Postes y cables** | Se trepa el poste y se cruza por arriba de los cables, sobre el agua (L1) o el charco (L3). |
| ![](obj:Level1/Colchon) | **Rebote** | El colchón (L1) y el toldo (L3) lanzan a Lio hacia arriba. |
| ![](obj:Level2/WetSign) | **Piso encerado** (L2) | Resbala: cuesta frenar antes de un zombie o de un pozo. |
| ![](obj:Level2/ContencionRota) | **Tubo que estalla** (L2) | Al pasar por encima, el tubo roto se rompe y suelta un virus que persigue desde atrás. |
| ![](obj:Level2/Vent) | **Ductos de aire** (L2) | Elevan a Lio: uno es obligatorio, para pasar el gabinete, y otros llevan a rutas opcionales. |
| ![](obj:Level2/Piston) | **Pistones** (L2) | Suben al ras del piso y se hunden. Luz verde = firme, roja = está por bajar. |
| ![](obj:Level3/Charco) | **Charco electrificado** (L3) | Pisarlo es como caer a un pozo: −1 vida y al checkpoint. |
| ![](obj:Level3/Vapor) | **Vapor del subte** (L3) | Ciclo aviso → sopla → nada; eleva a Lio a las marquesinas. |
| ![](obj:Level3/ZombiePol) | **Policía que dispara** (L3) | Aviso de medio segundo y un tiro al pecho: se esquiva con un salto planeado. |
| ![](obj:Level3/PacienteZero) | **El jefe** (L3) | Embiste con la motosierra y se le traba en una pila de patrulleros: esa es la única ventana para pisarlo. |

<!-- capturas:mecanicas -->

## Curva de dificultad

Cada nivel suma pocas mecánicas nuevas y reusa las anteriores:

| Escena | Mecánicas nuevas | Qué exige |
|---|---|---|
| Tutorial | Caminar, saltar, trepar, planear, pisotón | Nada: no se puede perder. |
| Nivel 1 | Virus volador, contagio, puentes, postes y cables, la horda, la mochila | Leer patrones simples y cruzar el río sobre la horda. |
| Nivel 2 | Pozos con vidrios, tubos que estallan, ductos, piso encerado, pistones | **Timing**: frenar a tiempo y leer las luces de los pistones. |
| Nivel 3 | Policía que dispara, toldo, charco, vapor y marquesinas, el jefe | Todo junto: los 13 tipos de zombie y una pelea final en 3 fases que se pone más rápida. |
