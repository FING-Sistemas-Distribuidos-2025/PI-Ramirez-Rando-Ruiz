# BombParty
Proyecto para la materia "Sistemas Distribuidos" del año 2025

## Integrantes
- Ramirez Victor
- Rando Tomás
- Ruiz Joaquin

## Descripción
El proyecto se basa en una simplificación del juego Bomb Party. En este, se contará con un grupo de jugadores, los cuales deberán escribir la palabra que aparece en pantalla correctamente.

La partida del juego se dividirá en rondas, donde en cada ronda se elimina a un jugador hasta que solo quede uno, que resultará ganador. Cada ronda tiene una duración aleatoria de tiempo, y durante estas, cada jugador debe escribir la palabra que le aparece en pantalla lo más rápido posible en su respectivo turno, cuando el temporizador llega a 0 (los jugadores no verán el temporizador), el jugador al que le tocaba escribir, pierde. 

![Esquema](images/esquema.jpg)
## Diseño
Para la implementación del proyecto contaremos con cuatro componentes principales, cada uno cumpliendo su función específica. Estos son:
- Cliente: Es el componente web encargado de leer las palabras y los datos desde Redis. Además, se encarga de enviar los datos del jugador al servidor.
- Servidor: El servidor se encargará de gestionar la partida, junto a sus jugadores. Se encargará, entre otras cosas, de proveer palabras a los clientes mediante Redis, gestionar el tiempo de cada ronda, validar las respuestas de los jugadores y mantener la lista de usuarios.
- Redis: Es el medio de comunicación del servidor hacia los clientes. Posee información vital para cada ronda. Por ejemplo, el jugador actual, la lista de jugadores con su respectivo estado, la palabra actual y el ganador de la partida.
- Proveedor de palabras: Es el compontente que brinda palabras al servidor.