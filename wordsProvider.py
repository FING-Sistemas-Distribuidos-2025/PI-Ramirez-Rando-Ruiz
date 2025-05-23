from flask import Flask
from flask import jsonify
import random
from flask import request
import threading

def create_app():
    app = Flask(__name__)
    return app

words = []
wordsSet = set()
app = create_app()

@app.route("/api/v1/words", methods=['GET'])
def get_words():
    wordsList = random.sample(words, 10)
    return jsonify({"words" : wordsList})

@app.route("/api/v1/word", methods=['GET'])
def get_word():
    wordsList = random.sample(words, 1)
    return jsonify({"words" : wordsList})

def mixWords():
    global words
    words = random.shuffle(words)
    return

def insertWords(list):
    global words, wordsSet
    for i in range(0, len(list)):
        if list[i] not in wordsSet:
            wordsSet.add(list[i])
            words.append(list[i])
    return

@app.route("/api/v1/words", methods=['POST'])
def post_word():

    global words
    jsonData = request.get_json(force=True)

    if (jsonData.get('word') == None):
        return jsonify({"message": "BAD REQUEST"}), 400
    else:
        word = jsonData["word"]
        if word in wordsSet:
            return jsonify({"message" : "REPEATED"})
        wordsSet.add(word)
        words.append(word)
        return jsonify({"message" : "OK"})

@app.route("/api/v1/words/list", methods=['POST'])
def post_words():
    global words
    jsonData = request.get_json(force=True)
    if (jsonData.get('words') == None):
        return jsonify({"message": "BAD REQUEST"}), 400
    else:
        wordsRecv = jsonData["words"]
        threading.Thread(None, insertWords, args=(wordsRecv, )).start()
        return jsonify({"message" : "OK"})
    
if __name__ == "__main__":
    app.run(debug=True)