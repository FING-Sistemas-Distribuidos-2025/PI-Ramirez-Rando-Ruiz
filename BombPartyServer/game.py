class Game:
    def __init__(self, id):
        self.started = False
        self.starting = False
        self.players = {}
        self.indiceJugadorActual = 0
        self.listaNombres = []
        self.listaVivos = set()
        self.channel = "room:" + id
        self.listaMuertos = set()
        self.currentPlayer = None
        self.currentSubstring = ""
        self.roomId = id
        self.winner = None    