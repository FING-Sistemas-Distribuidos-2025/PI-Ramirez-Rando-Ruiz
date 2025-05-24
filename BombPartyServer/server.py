import uuid
import redis.asyncio as redis
import websockets
import asyncio
import random
from websockets import serve
import json
from game import Game
import httpx

urlSubstring = "http://localhost:5000/api/v1/substring"
urlValidation = "http://localhost:5000/api/v1/validate"

# Conexión a Redis
redis_conn = redis.Redis(host='localhost', port=6379, db=0)

client = httpx.AsyncClient()
gameList = {}
#Handler para manejar mensajes desde los clientes
async def handler(websocket):
    global listaSockets, listaVivos, listaMuertos, listaNombres, listaJugadores
    #Verificamos si el jugador esta agregado en la lista de jugadores
    try:  
        async for message in websocket:
            print(message)
            message = json.loads(message)
            action = message["action"]
            name = message["name"]
            if (action == "create"):
                roomid = uuid.uuid4().hex[:4]
                game = Game(roomid)
                game.listaVivos.add(name)
                game.listaNombres.append(name)
                game.players[name] = "activo"
                gameList[roomid] = game
                response = {"id": message["messageid"], "status": "OK", "message": "Created", "roomid" : roomid}
            elif (action == "join"):
                roomid = message["roomId"]
                if roomid in gameList:
                    game = gameList[roomid]
                    if (game.started == False):
                        if name not in game.listaVivos:
                            game.listaVivos.add(name)
                            game.players[name] = "activo"
                            game.listaNombres.append(name)
                            if (len(game.listaVivos) == 2 and game.starting == False):
                                game.starting = True
                                asyncio.create_task(startGame(game))
                            response = {"id": message["messageid"], "status": "OK", "message": "Joined"}
                        else:
                            response = {"id": message["messageid"], "status": "NOTOK", "message": "Name already used"}
                    else:
                        response = {"id": message["messageid"], "status": "NOTOK", "message": "Game already started"}
            elif (action == "answer") :
                word = message["word"]
                roomid = message["roomId"]
                game = gameList[roomid]
                if game.currentSubstring in word:
                    condition = await validateWord(word)
                    if condition:
                        response = {"id": message["messageid"], "status": "OK", "message": "Correct"}
                        await nextPlayer(game)
                    else:
                        response = {"id": message["messageid"], "status": "NOTOK", "message": "Incorrect"}
            else:
                response = {"id": message["messageid"], "status": "NOTOK", "message": "Bad action"}
            await websocket.send(json.dumps(response))
            if (action == "join" or action == "create"):
                asyncio.create_task(publishOnRedisWithTimer(0.5, game))
                asyncio.create_task(publishOnRedisWithTimer(5, game))
    #Si se cierra la conexión, se elimina al jugador de las listas
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        pass

async def publishOnRedisWithTimer(seconds, game):
    await asyncio.sleep(seconds)
    await publishRedis(game)

#Función principal del juego
async def startGame(game):
    # Mientras la cantidad de jugadores sea mayor o igual a 2,
    # el juego empezado continuará ejecutándose
    while (len(game.listaVivos) >= 2):
        # Tiempo para que se unan mas de 2 jugadores
        await countdown(20)
        game.started = True
        await publishRedis(game)

        await startRound(game)
        
#Función para manejar cada ronda
async def startRound(game):
    # Tiempo que dura la ronda antes de que explote la bomba
    
    while game.started:
        time = random.randint(20, 45)
        await nextPlayer(game)
        # Empieza el temporizador de la "bomba"
        await countdown(time)
        game.players[game.currentPlayer] = "muerto"
        game.listaVivos.discard(game.currentPlayer)
        game.listaMuertos.add(game.currentPlayer)
        # Guardar lista de jugadores en redis
        await publishRedis(game)

        # Si queda un jugador, gana
        if (len(game.listaVivos) == 1):
            game.winner = game.listaVivos.pop()
            await publishRedis(game)
            game.started = False
            game.listaVivos = game.listaVivos | game.listaMuertos
            game.listaMuertos.clear()
            for jugador in game.players:
                game.players[jugador] = "activo"
    return

# Se selecciona al siguiente jugador dentro de la partida,
# este se seleccionará dentro de la lista de jugadores vivos
async def nextPlayer(game):
    game.currentPlayer, game.indiceJugadorActual = await selectNextAlivePlayer(game)
    game.currentSubstring = await fetch_substring()
    # Guardar en redis
    await publishRedis(game)

async def selectNextAlivePlayer(game):
    total = len(game.players)
    for i in range(1, total + 1):
        idx = (game.indiceJugadorActual + i) % total
        nombre = game.listaNombres[idx]
        if nombre in game.listaVivos:
            return nombre, idx

    return None, -1  # No hay jugadores vivos
    
# Temporizador
async def countdown(segundos):
    for i in range(segundos, 0, -1):
        await asyncio.sleep(1)

async def main():
    game = Game("123")
    game.players["asd"] = "vivo"
    game.currentSubstring = "ad"
    game.currentPlayer = "asd"
    await publishRedis(game)
    print("iniciando")
    async with serve(handler , "localhost" , 9000) as server:
        await server.serve_forever()
    await client.aclose()

async def fetch_substring():
    global client
    response = await client.get(urlSubstring)
    return response.json()["substring"][0]

async def publishRedis(game):
    global redis_conn
    data = {"players" : game.players, "winner" : game.winner, "word" : game.currentSubstring, "currentPlayer" : game.currentPlayer}
    await redis_conn.publish(game.channel, json.dumps(data))

async def validateWord(word):
    global client
    data = {
        "word": word
    }
    response = await client.post(urlValidation, json=data)
    return response.json()["message"][0]

if __name__ == "__main__":
    asyncio.run(main())
    
    #asyncio.run(countdown(60))