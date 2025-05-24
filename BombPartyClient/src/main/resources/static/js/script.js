const palabras = ["manzana", "computadora", "reloj", "jirafa", "pintura", "fuego", "avión"];
const wordElement = document.getElementById("word");
const inputElement = document.getElementById("input");
const timerElement = document.getElementById("timer");

let tiempo = 5;
let timer;
let palabraActual = "";

function nuevaPalabra() {
  palabraActual = palabras[Math.floor(Math.random() * palabras.length)];
  wordElement.textContent = palabraActual;
  inputElement.value = "";
  tiempo = 5;
  actualizarTemporizador();
  if (timer) clearInterval(timer);
  timer = setInterval(cuentaAtras, 1000);
}

function cuentaAtras() {
  tiempo--;
  actualizarTemporizador();
  if (tiempo <= 0) {
    clearInterval(timer);
    wordElement.classList.add("wrong");
    setTimeout(() => {
      wordElement.classList.remove("wrong");
      nuevaPalabra();
    }, 1000);
  }
}

function actualizarTemporizador() {
  timerElement.textContent = `Tiempo: ${tiempo}`;
}

inputElement.addEventListener("keyup", function (e) {
  if (e.key === "Enter") {
    if (inputElement.value.trim().toLowerCase() === palabraActual.toLowerCase()) {
      wordElement.classList.add("correct");
      clearInterval(timer);
      setTimeout(() => {
        wordElement.classList.remove("correct");
        nuevaPalabra();
      }, 500);
    } else {
      inputElement.value = "";
    }
  }
});

// Iniciar juego
nuevaPalabra();
