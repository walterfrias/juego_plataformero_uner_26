# juego_plataformero_uner_26

Trabajo final de la Tecnicatura Universitaria en Desarrollo Web (UNER),
materia Multimedia y Juegos Web. Prototipo de videojuego web, género
**plataformas 2D**, con motor **GDevelop** (según lo sugerido por la
cátedra).

Plazo de entrega: 01/09 al 31/10/2026.

## Estado

Recién creado — todavía sin proyecto de GDevelop scaffoldeado. Ver
`reseah.md` (no versionado, bitácora personal) para el detalle de cómo
se llegó a esta decisión.

## Motor

Se elige GDevelop en vez de Godot: es el motor que la consigna nombra
explícitamente ("similar a GDevelop o Construct3"), no deja dudas de
cumplimiento, y trae de fábrica el comportamiento "Platformer
Character" (gravedad, salto, colisión con plataformas) que resuelve la
parte de físicas.

## MCP

Este repo tiene un `.mcp.json` apuntando al servidor MCP de terceros
[`gb2b/gdevelop-mcp`](https://github.com/gb2b/gdevelop-mcp) (clonado e
instalado en `~/Escritorio/gdevelop-mcp`, fuera de este repo), para
poder editar el proyecto de GDevelop asistido por IA de forma similar
a como se trabajó con código en el proyecto Phaser anterior.
