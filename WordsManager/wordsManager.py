from flask import Flask
from flask import jsonify
import random
from flask import request
import unicodedata

def create_app():
    app = Flask(__name__)
    return app

words = set()
substrings = []
wordsSet = set()
app = create_app()

@app.route("/api/v1/words", methods=['GET'])
def get_words():
    wordsList = random.sample(words, 10)
    return jsonify({"words" : wordsList})

@app.route("/api/v1/substring" , methods = ['GET'])
def get_substring():
    substring = random.sample(substrings,1)
    return jsonify({"substring" : substring})

@app.route("/api/v1/word", methods=['GET'])
def get_word():
    wordsList = random.sample(words, 1)
    return jsonify({"words" : wordsList})

@app.route("/api/v1/word/validate", methods=['POST'])
def validateWord():
    global words
    jsonData = request.get_json(force=True)

    if (jsonData.get("word") is None):
        return jsonify({"message" : "BAD REQUEST"}), 400
    else:
        word = quitar_tildes(jsonData["word"].strip().lower())
        if word in words:
            return jsonify({"message" : True})
        else: 
            return jsonify({"message" : False})

def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def loadWords():
    global words, substrings
    with open("palabras.txt", "r", encoding="utf-8") as file:
        words = set(quitar_tildes(line.strip()) for line in file if line.strip())
    with open("substrings.txt", "r", encoding="utf-8") as file:
        substrings = [line.strip() for line in file if line.strip()]
    return
   
if __name__ == "__main__":
    loadWords()
    app.run(debug=True)

