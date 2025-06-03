import random
import unicodedata
import redis
import os
import time
import asyncio
import redis.exceptions


r = None
def connect_to_redis():
    global r
    while True:
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            print("Conectado a Redis.")
            return r
        except redis.exceptions.ConnectionError as e:
            time.sleep(3)

connect_to_redis()

# Nombre del stream
stream_name_request = 'requestsStream'
stream_name_response = 'responsesStream'
groupName = "wordsManagerGroup"


CONSUMER_NAME = os.getenv("HOSTNAME", "wordsManager")

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
    while True:
        try:
            msgs = r.xreadgroup(groupname=groupName, consumername=CONSUMER_NAME, streams={stream_name_request : ">"}, count=10, block=5000)
            for stream, msg in msgs: # [(groupName, [(idMensaje, data)])]
                for msgId, data in msg:
                    r.xack(stream_name_request, groupName, msgId)
                    r.xdel(stream_name_request, msgId)
                    data = {k.decode(): v.decode() for k, v in data.items()}
                    action = data.get("action")
                    if action == "validate":
                        await validateWord(data)
                    elif action == "word":
                        await get_substring(data)

        except redis.exceptions.ConnectionError as exception:
            connect_to_redis()
        except Exception as e:
            print(e)
            print("Error leyendo el stream:")
            time.sleep(1)

async def answer(json, data):
    try:
        print(data)
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

if __name__ == "__main__":
    loadWords()
    asyncio.run(listen())

