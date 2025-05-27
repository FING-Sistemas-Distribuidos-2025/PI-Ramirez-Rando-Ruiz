package com.sistemasdistribuidos.BombParty.services;

import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.sistemasdistribuidos.BombParty.websockets.MyWebSocketClient;
import com.sistemasdistribuidos.BombParty.exceptions.GameException;
import javax.annotation.PostConstruct;
import java.net.URI;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

@Service
public class SocketService {

    private MyWebSocketClient client;
    
    @Autowired
    private UsersService userService;

    @PostConstruct
    public void init() throws Exception {
        client = new MyWebSocketClient(new URI("ws://localhost:9000"));
        client.connectBlocking();
    }

    public void sendMsg(String msg) {
        if (client != null && client.isOpen()) {
            client.send(msg);
        }
    }

    public String createRoom(String name) throws GameException {

        if (client != null && client.isOpen()) {
            String id = UUID.randomUUID().toString();
            CompletableFuture<String> future = new CompletableFuture<>();
            client.insertOnPending(id, future);
            JSONObject json = new JSONObject();
            json.put("messageid", id);
            json.put("action", "create");
            json.put("roomid", "");
            json.put("name", name);
            String jsonString = json.toString();

            client.send(jsonString);

            try {
                String rta = future.get(5, TimeUnit.SECONDS);
                json = new JSONObject(rta);
                client.removePending(id);
                System.out.println(json.getString("status"));
                if (json.getString("status").equals("OK")) {
                    System.out.println("Room created: " + json.getString("roomid"));
                    return json.getString("roomid");
                }
            } catch (TimeoutException e) {
                client.removePending(id);
                throw new GameException("Timeout esperando respuesta");
            } catch (Exception e) {
                client.removePending(id);
                throw new GameException("Error esperando respuesta");
            }
        }
        return null;
    }
    

    public boolean join(String name , String roomId) throws GameException {
        if (client != null && client.isOpen()) {
            String id = UUID.randomUUID().toString();
            CompletableFuture<String> future = new CompletableFuture<>();
            client.insertOnPending(id, future);
            JSONObject json = new JSONObject();
            json.put("messageid", id);
            json.put("action", "join");
            json.put("roomId", roomId);
            json.put("name", name);
            String jsonString = json.toString();

            client.send(jsonString);

            try {
                String rta = future.get(5, TimeUnit.SECONDS);
                json = new JSONObject(rta);
                client.removePending(id);
                System.out.println(json.getString("status"));
                
                if (json.getString("status").equals("OK")) {
                    return true;
                }
            } catch (TimeoutException e) {
                client.removePending(id);
                throw new GameException("Timeout esperando respuesta");
            } catch (Exception e) {
                client.removePending(id);
                throw new GameException("Error esperando respuesta");
            }
        }
        return false;
    }

    public boolean answer(String name, String roomId, String word) throws GameException {
        if (client != null && client.isOpen()) {
            String id = UUID.randomUUID().toString();
            CompletableFuture<String> future = new CompletableFuture<>();
            client.insertOnPending(id, future);
            JSONObject json = new JSONObject();
            json.put("messageid", id);
            json.put("action", "answer");
            json.put("roomId", roomId);
            json.put("name", name);
            json.put("word", word);
            String jsonString = json.toString();

            client.send(jsonString);

            try {
                String rta = future.get(5, TimeUnit.SECONDS);
                json = new JSONObject(rta);
                client.removePending(id);
                if (json.getString("status").equals("OK")) {
                    return true;
                } else {
                    return false;
                }
            } catch (TimeoutException e) {
                client.removePending(id);
                throw new GameException("Timeout esperando respuesta");
            } catch (Exception e) {
                client.removePending(id);
                throw new GameException("Error esperando respuesta");
            }
        } else {
            throw new GameException("Conexión con el servidor perdida.");
        }
    }

    public void desconectar(String name , String roomId) throws GameException{

        String id = UUID.randomUUID().toString();
        CompletableFuture<String> future = new CompletableFuture<>();
        client.insertOnPending(id, future);
        JSONObject json = new JSONObject();
        json.put("messageid", id);
        json.put("action", "disconnection");
        json.put("roomId", roomId);
        json.put("name", name);
        json.put("word", "");
        String jsonString = json.toString();
        client.send(jsonString);

        try {
            String rta = future.get(5, TimeUnit.SECONDS);
            json = new JSONObject(rta);
            client.removePending(id);
            if (json.getString("status").equals("OK")) {
                System.out.println("Usuario desconectado correctamente de la sala" + roomId);
            }
        } catch (TimeoutException e) {
            client.removePending(id);
            throw new GameException("Timeout esperando respuesta");
        } catch (Exception e) {
            client.removePending(id);
            throw new GameException("Error esperando respuesta");
        }

    }
}