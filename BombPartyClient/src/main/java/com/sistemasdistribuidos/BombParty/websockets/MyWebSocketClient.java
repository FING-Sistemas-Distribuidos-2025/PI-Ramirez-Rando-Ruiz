package com.sistemasdistribuidos.BombParty.websockets;

import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.json.JSONObject;

import com.sistemasdistribuidos.BombParty.exceptions.GameException;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

public class MyWebSocketClient extends WebSocketClient {

    ConcurrentHashMap<String, CompletableFuture<String>> pending;

    public MyWebSocketClient(URI serverUri) throws URISyntaxException{
        super(serverUri);
        pending = new ConcurrentHashMap<>();
    }

    @Override
    public void onOpen(ServerHandshake handshake) {
        System.out.println("Conectado al servidor");
    }

    @Override
    public void onMessage(String message) {
        JSONObject json = new JSONObject(message);
        String id = json.optString("id");
        
        if (id != null) {
            CompletableFuture<String> future = pending.remove(id);
            if (future != null) {
                future.complete(message);
            } else {
                System.out.println("Respuesta inválida");
            }
        }
    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        System.out.println("Conexión cerrada: " + reason);
    }

    @Override
    public void onError(Exception ex) {
        System.err.println("Error: " + ex.getMessage());
    }

    public void insertOnPending(String id, CompletableFuture pend) {
        pending.put(id, pend);
    }

    public void removePending(String id) {
        pending.remove(id);
    }
}