const params = new URLSearchParams(window.location.search);
const roomId = params.get("id");
const userName = params.get("name");
const socket = new SockJS('/ws');
const stompClient = Stomp.over(socket);

stompClient.connect({}, function (frame) {

    stompClient.subscribe("/topic/room/" + roomId, function (message) {
        const data = JSON.parse(message.body);
        console.log(data)
        document.getElementById("currentPlayer").innerText = data.currentPlayer;
        document.getElementById("currentSubstring").innerText = data.word;

        const lista = document.getElementById("players");
        lista.innerHTML = "";

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
        });

        if (data.currentPlayer !== userName) {
            document.getElementById("sendWord").hidden = true;
        } else {
            document.getElementById("sendWord").hidden = false;
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
