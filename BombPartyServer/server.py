import redis
import websockets
import asyncio
import random
from websockets import serve
import requests
import time
import http.client
import httpx

urlSubstring = "http://localhost:5000/api/v1/substring"
"""
    Listas:
        - Lista de sockets = [websocket1 , websocket2,... ]
    Diccionarios:
        - Diccionario de jugadores = {"nombreJugador" : "estado"}
        - Diccionario de nombres = {"websocket" : "nombreJugador"}
"""

# Conexión a Redis
redis_conn = redis.Redis(host='localhost', port=6379, db=0)

listaSockets = []
listaJugadores = {}
listaVivos = set()
listaMuertos = set()
listaNombres = {}
currentPlayer = None
currentWord = None
gameStarted = False
indiceJugadorActual = 0
client = httpx.AsyncClient()
#Handler para manejar mensajes desde los clientes
async def handler(websocket):
    global listaSockets, listaVivos, listaMuertos, listaNombres, listaJugadores
    #Verificamos si el jugador esta agregado en la lista de jugadores
    try:  
        async for message in websocket:
            # Si hay una nueva conexión que no se encuentra en la lista de jugadores
            # la agregamos a la lista y le designamos un nombre
            if websocket not in listaJugadores:
                jugador = message
                listaSockets.append(websocket)
                listaNombres[websocket] = jugador
                # Si el juego empezó, estará en estado de espera
                if (gameStarted):
                    listaJugadores[jugador] = "espera"
                    listaMuertos.add(jugador)
                # Si el juego aún no empieza, se lo pone en estado activo,
                # cuando el juego empiece, será parte de este
                else:
                    listaJugadores[jugador] = "activo"
                    listaVivos.add(jugador)
                # El juego no comienza hasta que hayan como mínimo 2 jugadores
                if len(listaSockets) == 2 and not gameStarted:
                    await game()
            # Si la conexión ya existe, y es del jugador actual, se compara
            # la palabra, si es correcta, le toca al siguiente jugador
            else: 
                if (listaNombres[websocket] == currentPlayer):
                    if message == currentWord:
                        await nextPlayer()
            await websocket.send("OK")  
    #Si se cierra la conexión, se elimina al jugador de las listas
    except websockets.exceptions.ConnectionClosed:
        listaSockets.remove(websocket)
        listaJugadores.pop(listaNombres[websocket])
        listaNombres.pop(websocket)
        listaMuertos.discard(listaNombres[websocket])
        listaVivos.discard(listaNombres[websocket])
    finally:
        pass
    
#Función principal del juego
async def game():
    global gameStarted
    # Mientras la cantidad de jugadores sea mayor o igual a 2,
    # el juego empezado continuará ejecutándose
    while (len(listaJugadores) >= 2):
        # Tiempo para que se unan mas de 2 jugadores
        await countdown(60)
        gameStarted = True
        redis_conn.hset("playerList", mapping=listaJugadores)

        await startRound()
        
#Función para manejar cada ronda
async def startRound():
    global listaJugadores, gameStarted, listaMuertos, listaVivos
    # Tiempo que dura la ronda antes de que explote la bomba
    time = random.randint(20, 45)
    await nextPlayer()
    # Empieza el temporizador de la "bomba"
    await countdown(time)
    while gameStarted:
        listaJugadores[listaNombres[listaSockets[indiceJugadorActual]]] = "muerto"
        listaVivos.discard(currentPlayer)
        listaMuertos.add(currentPlayer)
        # Guardar lista de jugadores en redis
        redis_conn.hset("playerList", mapping=listaJugadores)

        # Si queda un jugador, gana
        if (len(listaVivos) == 1):
            redis_conn.hset("ganador", listaVivos.pop())
            gameStarted = False
            listaVivos = listaVivos | listaMuertos
            listaMuertos.clear()
            for jugador in listaJugadores:
                listaJugadores[jugador] = "activo"
    return

# Se selecciona al siguiente jugador dentro de la partida,
# este se seleccionará dentro de la lista de jugadores vivos
async def nextPlayer():
    global currentPlayer,indiceJugadorActual,currentWord
    currentPlayer, indiceJugadorActual = await selectNextAlivePlayer()
    response = requests.get(urlSubstring)
    currentWord = response.json()["substring"][0]
    # Guardar en redis
    redis_conn.set("currentWord", currentWord)
    redis_conn.set("currentPlayer", currentPlayer)

async def selectNextAlivePlayer():
    global indiceJugadorActual

    total = len(listaSockets)
    for i in range(1, total + 1):
        idx = (indiceJugadorActual + i) % total
        nombre = listaNombres[listaSockets[idx]]
        if nombre in listaVivos:
            return nombre, idx

    return None, -1  # No hay jugadores vivos
    
# Temporizador
async def countdown(segundos):
    for i in range(segundos, 0, -1):
        await asyncio.sleep(1)

async def main():
    for _ in range(10):
        result = await fetch_substring()
    async with serve(handler , "localhost" , 9000) as server:
        await server.serve_forever()
    await client.aclose()

async def fetch_substring():
    global client
    response = await client.get(urlSubstring)
    return response.json()["substring"][0]

if __name__ == "__main__":
    asyncio.run(main())
    
    #asyncio.run(countdown(60))