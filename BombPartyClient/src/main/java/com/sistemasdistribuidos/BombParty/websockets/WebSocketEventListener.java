package com.sistemasdistribuidos.BombParty.websockets;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.messaging.simp.SimpMessageHeaderAccessor;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.messaging.SessionDisconnectEvent;

import com.sistemasdistribuidos.BombParty.exceptions.GameException;
import com.sistemasdistribuidos.BombParty.services.RedisService;

@Component
public class WebSocketEventListener {

    @Autowired
    private RedisService redisService;

    @EventListener
    public void handleWebSocketDisconnectListener(SessionDisconnectEvent event) throws GameException {
        SimpMessageHeaderAccessor headers = SimpMessageHeaderAccessor.wrap(event.getMessage());

        String user = (String) headers.getSessionAttributes().get("username");
        String roomId = (String) headers.getSessionAttributes().get("roomid");

        if (user != null && roomId != null) {
            System.out.println("Jugador desconectado: " + user);
            redisService.desconectar(user , roomId);
        }
    }
}
