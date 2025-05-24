package com.sistemasdistribuidos.BombParty.redis;

import org.springframework.data.redis.connection.MessageListener;
import org.springframework.stereotype.Component;
import org.springframework.data.redis.connection.Message;


@Component
public class RedisMessageSubscriber implements MessageListener{

    @Override
    public void onMessage(Message message, byte[] pattern) {
        String channel = new String(message.getChannel());
        String body = new String(message.getBody());
        System.out.println("Mensaje recibido en canal " + channel + ": " + body);

        // Si querés extraer el ID de la sala:
        if (channel.startsWith("room:")) {
            String roomId = channel.substring("room:".length());
            // Lógica específica por sala
        }
    }
}