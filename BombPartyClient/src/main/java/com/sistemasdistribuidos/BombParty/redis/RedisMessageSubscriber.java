package com.sistemasdistribuidos.BombParty.redis;

import org.springframework.data.redis.connection.MessageListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.connection.Message;


@Component
public class RedisMessageSubscriber implements MessageListener{

    @Autowired
    private SimpMessagingTemplate messagingTemplate;

    @Override
    public void onMessage(Message message, byte[] pattern) {
        String channel = new String(message.getChannel());
        String body = new String(message.getBody());

        System.out.println("Mensaje recibido en canal " + channel + ": " + body);

        if (channel.startsWith("room:")) {
            String roomId = channel.substring("room:".length());
            messagingTemplate.convertAndSend("/topic/room/" + roomId, body);
        }
    }
}