const palabras = ["manzana", "computadora", "reloj", "jirafa", "pintura", "fuego", "avión"];
const wordElement = document.getElementById("word");
const inputElement = document.getElementById("input");
const timerElement = document.getElementById("timer");

let tiempo = 5;
let timer;
let palabraActual = "";


// Iniciar juego
nuevaPalabra();
