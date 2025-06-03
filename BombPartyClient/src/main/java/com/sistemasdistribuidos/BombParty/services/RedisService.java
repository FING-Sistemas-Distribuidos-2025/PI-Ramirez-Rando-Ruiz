package com.sistemasdistribuidos.BombParty.services;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.RecordId;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.connection.stream.StreamReadOptions;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.annotation.JsonTypeInfo.None;
import com.sistemasdistribuidos.BombParty.exceptions.GameException;


@Service
public class RedisService {

    String pod;

    @Autowired
    private StringRedisTemplate redisTemplate;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    public Object get(String key) {
        return redisTemplate.opsForValue().get(key);
    }

    public RedisService() {
        try {
            this.pod = InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException ex) {
            this.pod = "defaultClient";
        }
    }

    public CompletableFuture<MapRecord<String, Object, Object>> write(String stream, Map<String, String> data) {
        Map<String, Object> converted = new HashMap<>();
        data.forEach(converted::put);
        RecordId id = redisTemplate.opsForStream().add(MapRecord.create(stream, converted));
        Duration timeout = Duration.ofSeconds(10);
        
        return CompletableFuture.supplyAsync(() -> {
            List<MapRecord<String, Object, Object>> messages = redisTemplate.opsForStream()
                .read(StreamReadOptions.empty().block(timeout).count(1),
                StreamOffset.create("backendClientStream:" + pod, ReadOffset.from("0-0")));

            if (messages != null && !messages.isEmpty()) {
                return messages.get(0);
            }
            return null;
        }, executor);
    }

    public void delete(String stream, RecordId id) {
        redisTemplate.opsForStream().delete(stream, id);
    }

    public String createRoom(String name) throws GameException {

        String id = UUID.randomUUID().toString();
        CompletableFuture<MapRecord<String, Object, Object>> future;
        HashMap json = new HashMap<>();
        json.put("messageid", id);
        json.put("action", "create");
        json.put("roomid", "");
        json.put("name", name);
        json.put("from", pod);
        
        try {
            MapRecord<String, Object, Object> msgReceived;
            future = write("server", json);
            msgReceived = future.get();
            RecordId msgId = msgReceived.getId();
            delete("backendClientStream:" + pod, msgId);
            Map<Object, Object> msg;
            if (msgReceived != null) {
                msg = msgReceived.getValue();
                if (msg.get("status").equals("OK")) {
                System.out.println("Room created: " + msg.get("roomid").toString());
                return msg.get("roomid").toString();
                } else {
                    throw new GameException("Error esperando respuesta");
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            throw new GameException("Error esperando respuesta");
        }
        return null;
    }
    

    public boolean join(String name , String roomId) throws GameException {

        String id = UUID.randomUUID().toString();
        CompletableFuture<MapRecord<String, Object, Object>> future;
        HashMap json = new HashMap<>();
        json.put("messageid", id);
        json.put("action", "join");
        json.put("roomId", roomId);
        json.put("name", name);
        json.put("from", pod);
        
        try {
            MapRecord<String, Object, Object> msgReceived;
            future = write("server", json);
            msgReceived = future.get();
            RecordId msgId = msgReceived.getId();
            delete("backendClientStream:" + pod, msgId);
            Map<Object, Object> msg;
            if (msgReceived != null) {
                msg = msgReceived.getValue();
                if (msg.get("status").equals("OK")) {
                    return true;
                } else {
                    throw new GameException("Error esperando respuesta");
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            throw new GameException("Error esperando respuesta");
        }
        return false;
    }

    public boolean answer(String name, String roomId, String word) throws GameException {

        String id = UUID.randomUUID().toString();
        CompletableFuture<MapRecord<String, Object, Object>> future;
        HashMap json = new HashMap<>();
        json.put("messageid", id);
        json.put("action", "answer");
        json.put("roomId", roomId);
        json.put("name", name);
        json.put("word", word);
        json.put("from", pod);
        
        try {
            MapRecord<String, Object, Object> msgReceived;
            future = write("server", json);
            msgReceived = future.get();
            RecordId msgId = msgReceived.getId();
            delete("backendClientStream:" + pod, msgId);
            Map<Object, Object> msg;
            if (msgReceived != null) {
                msg = msgReceived.getValue();
                if (msg.get("status").equals("OK")) {
                    return true; 
                } else {
                    return false;
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            throw new GameException("Error esperando respuesta");
        }
        return false;
    }


    public void desconectar(String name , String roomId) throws GameException{

        String id = UUID.randomUUID().toString();
        CompletableFuture<MapRecord<String, Object, Object>> future;
        HashMap json = new HashMap<>();
        json.put("messageid", id);
        json.put("action", "disconnection");
        json.put("roomId", roomId);
        json.put("name", name);
        json.put("word", "");
        json.put("from", pod);
        
        try {
            MapRecord<String, Object, Object> msgReceived;
            future = write("server", json);
            msgReceived = future.get();
            RecordId msgId = msgReceived.getId();
            delete("backendClientStream:" + pod, msgId);
            Map<Object, Object> msg;
            if (msgReceived != null) {
                msg = msgReceived.getValue();
                if (msg.get("status").equals("OK")) {
                System.out.println("Usuario desconectado correctamente de la sala" + roomId);
                } else {
                    System.out.println("Podría haber ocurrido un error al desconectar de la sala " + roomId);
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            throw new GameException("Error esperando respuesta");
        }
    }

    
}
