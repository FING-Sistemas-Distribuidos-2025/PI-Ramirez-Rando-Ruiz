import uuid
import redis.asyncio as Redis
import redis
import asyncio
import random
import json
from game import Game
import os

# Conexión a Redis
redis_conn = None

stream_name_request = 'requestsStream'
stream_name_response = 'responsesStream'
stream_name_response_client = 'backendClientStream'
groupName = "wordsManagerGroup"

CONSUMER_NAME = os.getenv("HOSTNAME", "server")

gameList = {}


async def connect_to_redis():
    global redis_conn
    while True:
        try:
            redis_conn = await Redis.Redis(host='localhost', port=6379, db=0)
            await redis_conn.ping()
            print("Conectado a Redis.")
            return redis_conn
        except redis.exceptions.ConnectionError as e:
            await countdown(3)


async def listen():
    while True:
        try:
            
            msgs = await redis_conn.xread({"server":"$"}, count=3, block=0)
            for stream, msg in msgs: # [(groupName, [(idMensaje, data)])]
                for msgId, data in msg:
                    message = {k.decode(): v.decode() for k, v in data.items()}
                    print(f"Mensaje del cliente: {message}")
                    fromClient = message["from"]
                    action = message["action"]
                    name = message["name"]
                    await redis_conn.xdel("server", msgId)
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
                        else:
                            response = {"id": message["messageid"], "status": "NOTOK", "message": "Invalid room id"}
                    elif (action == "answer") :
                        word = message["word"]
                        roomid = message["roomId"]
                        game = gameList[roomid]
                        if (name == game.currentPlayer):
                            if game.currentSubstring in word:
                                condition = await validateWord(word)
                            else:
                                condition = False
                            if condition:
                                response = {"id": message["messageid"], "status": "OK", "message": "Correct"}
                                await nextPlayer(game)
                            else:
                                response = {"id": message["messageid"], "status": "NOTOK", "message": "Incorrect"}
                        else:
                            response = {"id": message["messageid"], "status": "NOTOK", "message": "Not current player"}
                    
                    elif (action == "disconnection"):
                        print(message)
                        roomid = message["roomId"]
                        game = gameList.get(roomid)
                        if (game != None):
                            game.disconnectionList.append(name)
                            game.listaVivos.discard(name)
                            game.listaMuertos.add(name)
                            game.players[name] = "muerto"
                            sizePlayers = len(game.listaNombres)
                            if (sizePlayers == len(game.disconnectionList)):
                                gameList.pop(game, None)
                            else:
                                if (game.currentPlayer == name):
                                    await nextPlayer(game)
                            """
                            if (sizePlayers == 1):
                                game.started = False
                                game.currentPlayer = None
                                game.currentSubstring = ""
                            elif (sizePlayers == 0):
                                gameList.pop(roomid, None)
                            else:
                                if (game.currentPlayer == name):
                                    await nextPlayer(game)
                            """
                            response = {"id": message["messageid"], "status": "OK", "message": "Disconnection", "roomid" : roomid}
                        else:
                            response = {"id": message["messageid"], "status": "NOTOK", "message": "Game not found"}
                    else:
                        response = {"id": message["messageid"], "status": "NOTOK", "message": "Bad action"}

                    print(f"Respuesta del servidor: {response}")
                    await redis_conn.xadd(stream_name_response_client + ":" + fromClient, response)
                    if (action == "join" or action == "create"):
                        asyncio.create_task(publishOnRedisWithTimer(0.5, game))
                        asyncio.create_task(publishOnRedisWithTimer(5, game))
                    elif (action == "disconnection"):
                        if game != None:
                            asyncio.create_task(publishRedis(game))

        except redis.exceptions.ConnectionError as exception:
            await connect_to_redis()
        except Exception as e:
            print(e)
            print("Error leyendo el stream")

async def publishOnRedisWithTimer(seconds, game):
    await asyncio.sleep(seconds)
    await publishRedis(game)

#Función principal del juego
async def startGame(game):
    # Mientras la cantidad de jugadores sea mayor o igual a 2,
    # el juego empezado continuará ejecutándose
    while (len(game.players) >= 2):
        # Tiempo para que se unan mas de 2 jugadores
        await countdown(20)
        game.started = True
        await publishRedis(game)
        
        await startRound(game)
        
#Función para manejar cada ronda
async def startRound(game):
    # Tiempo que dura la ronda antes de que explote la bomba
    
    while game.started:
        time = random.randint(40, 60)
        if (len(game.listaVivos) > 1):
            await nextPlayer(game)
            # Empieza el temporizador de la "bomba"
            await countdown(time)
            if (len(game.listaVivos) > 1):
                game.players[game.currentPlayer] = "muerto"
                
                game.listaVivos.discard(game.currentPlayer)
                game.listaMuertos.add(game.currentPlayer)
        # Guardar lista de jugadores en redis
            await publishRedis(game)
        else:
        # Si queda un jugador, gana
                game.winner = game.listaVivos.pop()
                game.listaVivos.add(game.winner)
                await publishRedis(game)
                game.started = False
                await disconnectPlayers(game)
                game.listaVivos = game.listaVivos | game.listaMuertos
                game.indiceJugadorActual = 0
                game.listaMuertos.clear()
                game.winner = None
                for jugador in game.players:
                    game.players[jugador] = "activo"
    return

async def disconnectPlayers(game):
    for i in game.disconnectionList:
        game.listaMuertos.discard(i)
        game.players.pop(i, None)
        game.listaNombres.remove(i)
    game.disconnectionList = []
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
    print("Iniciando")
    await connect_to_redis()
    await listen()

async def fetch_substring():
    global redis_conn
    json = {"action" : "word", "from" : CONSUMER_NAME}
    await redis_conn.xadd(stream_name_request, json)
    response = await listenAnswer()
    response = response.get("word")
    if response == None:
        return ""
    else:
        return response

async def listenAnswer():
    global redis_conn
    while True:
        response = await redis_conn.xread({stream_name_response + ":" + CONSUMER_NAME : "$"}, block=0)
        if response:
            for stream, msgs in response:
                for msgId, data in msgs:
                    data = {k.decode(): v.decode() for k, v in data.items()}
                    await redis_conn.xdel(stream_name_response + ":" + CONSUMER_NAME, msgId)
                    return data
                    
async def publishRedis(game):
    global redis_conn
    data = {"players" : game.players, "winner" : game.winner, "word" : game.currentSubstring, "currentPlayer" : game.currentPlayer}
    await redis_conn.publish(game.channel, json.dumps(data))

async def validateWord(word):
    global redis_conn
    json = {"action" : "validate", "word": word, "from" : CONSUMER_NAME}
    await redis_conn.xadd(stream_name_request, json)
    response = await listenAnswer()
    response = response.get("message")
    if (response != "True" and response != "False"):
        return False
    else:
        if response == "True":
            return True
        else:
            return False

if __name__ == "__main__":
    asyncio.run(main())
    
    #asyncio.run(countdown(60))