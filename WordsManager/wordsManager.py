import random
import unicodedata
import redis.asyncio as redis
import os
import time
import asyncio
import redis.exceptions


r = None
async def connect_to_redis():
    global r
    while True:
        try:
            r = redis.Redis(host='redis-service', port=6379, db=0)
            r.ping()
            print("Conectado a Redis.")
            return r
        except redis.exceptions.ConnectionError as e:
            time.sleep(3)

# Nombre del stream
stream_name_request = 'requestsStream'
stream_name_response = 'responsesStream'
groupName = "wordsManagerGroup"


CONSUMER_NAME = os.getenv("HOSTNAME", "wordsManager")
async def createGroups():
    try:
        r.xgroup_create(name=stream_name_request, groupname=groupName, id='0-0', mkstream=True)
    except redis.exceptions.ResponseError as exception:
        if "BUSYGROUP" in str(exception):
            pass

    try:
        r.xgroup_create(name=stream_name_response, groupname=groupName, id='0-0', mkstream=True)
    except redis.exceptions.ResponseError as exception:
        if "BUSYGROUP" in str(exception):
            pass

async def listen():
    await connect_to_redis()
    await createGroups()
    while True:
        try:
            msgs = await asyncio.to_thread(r.xreadgroup, groupname=groupName, consumername=CONSUMER_NAME, streams={stream_name_request: ">"}, count=10, block=2000)
            if msgs == []:
                pending_msgs = await asyncio.to_thread(r.xreadgroup, groupname=groupName, consumername=CONSUMER_NAME, streams={stream_name_request: "0"}, count=10, block=2000)
                msgs = pending_msgs
            for stream, msg in msgs: # [(groupName, [(idMensaje, data)])]
                for msgId, data in msg:
                    r.xack(stream_name_request, groupName, msgId)
                    r.xdel(stream_name_request, msgId)
                    data = {k.decode(): v.decode() for k, v in data.items()}
                    action = data.get("action")
                    if action == "validate":
                        asyncio.create_task(validateWord(data))
                    elif action == "word":
                        asyncio.create_task(get_substring(data))
        except redis.exceptions.ConnectionError as exception:
            await connect_to_redis()
        except Exception as e:
            print(e)
            print("Error leyendo el stream:")
            asyncio.sleep(1)

async def answer(json, data):
    try:
        msgId = r.xadd(stream_name_response + ":" + data.get("from"), json)
        return
    except redis.exceptions.ConnectionError as e:
        print("Error al enviar respuesta a redis:", e)
    
words = set()
substrings = []
wordsSet = set()

async def get_substring(data):
    substring = random.sample(substrings,1)
    await answer({"word" : substring[0]}, data)
    return

async def validateWord(jsonData):
    global words

    if (jsonData.get("word") is None):
        await answer({"message" : "BAD REQUEST"}, jsonData)
    else:
        word = await quitar_tildes(jsonData["word"].strip().lower())
        if word in words:
            await answer({"message" : "True"}, jsonData)
        else: 
            await answer({"message" : "False"}, jsonData)
    return

async def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def quitar_tildesNotAsync(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def loadWords():
    global words, substrings
    with open("palabras.txt", "r", encoding="utf-8") as file:
        words = set(quitar_tildesNotAsync(line.strip()) for line in file if line.strip())
    with open("substrings.txt", "r", encoding="utf-8") as file:
        substrings = [line.strip() for line in file if line.strip()]
    return

async def main():
    await listen()

if __name__ == "__main__":
    loadWords()
    asyncio.run(main())

