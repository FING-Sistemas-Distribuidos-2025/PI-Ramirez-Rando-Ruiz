const params = new URLSearchParams(window.location.search);
const roomId = params.get("id");
const userName = params.get("name");
const socket = new SockJS('/ws');
const stompClient = Stomp.over(socket);

stompClient.connect({ username: userName, roomid: roomId }, function (frame) {

    stompClient.subscribe("/topic/room/" + roomId, function (message) {
        console.log(message)
        const data = JSON.parse(message.body);
        
        document.getElementById("currentPlayer").innerText = data.currentPlayer;
        document.getElementById("currentSubstring").innerText = data.word;

        const lista = document.getElementById("players");
        lista.innerHTML = "";

        let userState = null;

        Object.entries(data.players).forEach(([jugador, estado]) => {
            const card = document.createElement("div");
            card.classList.add("player-card");

            const infoDiv = document.createElement("div");
            infoDiv.classList.add("player-info");

            const estadoSpan = document.createElement("span");

            const img = document.createElement("img");
        
            if (estado === "activo") {
              img.src = "/imgs/face-smile-svgrepo-com.svg";
              img.alt = "Vivo";
              card.classList.add("alive");
              estadoSpan.innerText = "Vivo"
              estadoSpan.classList.add = "text-success";
            } else {
              img.src = "/imgs/face-dead-svgrepo-com.svg";
              img.alt = "Muerto";
              card.classList.add("dead");
              estadoSpan.innerText = "Muerto";
              estadoSpan.classList.add = "text-danger"
            }
            
            img.classList.add("player-icon");

            const nombreSpan = document.createElement("span");
            nombreSpan.innerText = jugador;

            infoDiv.appendChild(img);
            infoDiv.appendChild(nombreSpan);

            card.appendChild(infoDiv);
            card.appendChild(estadoSpan);

            lista.appendChild(card);

            if (jugador === userName) {
                userState = estado;
    }
        });

        const sendForm = document.getElementById("sendWord");
        const input = sendForm.querySelector('input[name="respuesta"]');
        const button = sendForm.querySelector('button[type="submit"]');

        const isUserTurn = data.currentPlayer === userName;
        const isUserAlive = userState === "activo";

        // Deshabilito el input y el enviar si no es el turno del jugador
        sendForm.hidden = !(isUserTurn && isUserAlive);
        input.disabled = !(isUserTurn && isUserAlive);
        button.disabled = !(isUserTurn && isUserAlive);

        if (isUserTurn && isUserAlive) {
            input.value = ""; // Limpiar campo de entrada
            input.focus();
        }

        const winnerMessage = document.getElementById("winnerMessage");
        const turnMessage = document.getElementById("turnMessage");


        if (data.winner) {
            turnMessage.style.display = "none";
            winnerMessage.innerText = `🎉 ¡${data.winner} ha ganado la partida!`;
            winnerMessage.style.display = "block";

            sendForm.hidden = true;
            input.disabled = true;
            button.disabled = true;
            input.value = "";
        } else {
            winnerMessage.style.display = "none"; // Ocultar si aún no hay ganador
            turnMessage.style.display = "block"; 
        }

    });
});

let timeoutid;
document.getElementById("sendWord").addEventListener("submit", function(e) {
        e.preventDefault(); 

        const formData = new FormData(this);
        const respuesta = formData.get("respuesta");
        if (document.getElementById("currentPlayer").innerText === userName) {
            fetch(`/answer?respuesta=${encodeURIComponent(respuesta)}&name=${encodeURIComponent(userName)}&roomid=${encodeURIComponent(roomId)}`)
            .then(response => response.text())
            .then(html => {
                document.getElementById("answer").innerHTML = html;
            })
            .catch(error => console.error('Error:', error));

            if (timeoutid) {
                clearTimeout(timeoutid);
            }
            timeoutid = setTimeout(() => {
                document.getElementById('answer').innerHTML = '';
                timeoutid = null;
            }, 5000)
        }
        
});



function cargarRespuestaCorrecta() {
    if (document.getElementById("currentPlayer").innerText === userName) {
        fetch('/answer')
            .then(response => response.text())
            .then(html => {
                document.getElementById('answer').innerHTML = html;
            });
        
    }
}
