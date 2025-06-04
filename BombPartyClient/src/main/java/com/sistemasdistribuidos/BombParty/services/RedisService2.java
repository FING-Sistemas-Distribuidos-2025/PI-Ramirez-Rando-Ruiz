package com.sistemasdistribuidos.BombParty.services;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

import javax.annotation.PostConstruct;

import org.json.JSONObject;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.connection.stream.StreamReadOptions;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sistemasdistribuidos.BombParty.exceptions.GameException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
@RequiredArgsConstructor
public class RedisService2 {

    String POD_NAME = resolvePodName();
    private final RedisTemplate<String, String> redisTemplate;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Map<String, CompletableFuture<String>> pendingRequests = new ConcurrentHashMap<>();
    private final String streamKey = "backendClientStream:" + POD_NAME;
    ObjectMapper mapper = new ObjectMapper();
    
    public String resolvePodName() {
        try {
            POD_NAME = InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException ex) {
            POD_NAME = "defaultClient";
        }
        return POD_NAME;
    }

    @PostConstruct
    public void initListener() {
        executor.execute(() -> {
            ReadOffset offset = ReadOffset.latest();
            while (true) {
                try {
                    List<MapRecord<String, Object, Object>> messages = redisTemplate
                        .opsForStream()
                        .read(StreamReadOptions.empty().block(Duration.ofSeconds(5)),
                              StreamOffset.create(streamKey, offset));
                    if (messages != null) {
                        for (MapRecord<String, Object, Object> msg : messages) {
                            String correlationId = msg.getValue().get("id").toString();
                            CompletableFuture<String> future = pendingRequests.remove(correlationId);
                            if (future != null) {
                                future.complete(mapper.writeValueAsString(msg.getValue()));
                            } else {
                                log.warn("No correlationId pendiente: {}", correlationId);
                            }

                            redisTemplate.opsForStream().delete(streamKey, msg.getId());

                            offset = ReadOffset.from(msg.getId());
                        }
                    }
                } catch (Exception e) {
                    log.error("Error leyendo del stream", e);
                }
            }
        });
    }

    public CompletableFuture<String> sendRequest(String correlationId, Map<String, String> attributes) {
        CompletableFuture<String> future = new CompletableFuture<>();
        pendingRequests.put(correlationId, future);

        Map<String, String> message = new HashMap<>(attributes);
        message.put("messageid", correlationId);
        redisTemplate.opsForStream().add("server", message);

        return future;
    }

    public String createRoom(String name) throws GameException {
        try {
            String correlationId = java.util.UUID.randomUUID().toString();

            Map<String, String> payloadMap = Map.of(
                "id", correlationId,
                "action", "create",
                "roomid", "",
                "name", name,
                "from", POD_NAME
            );

            CompletableFuture<String> future = sendRequest(correlationId, payloadMap);
            String responseStr = future.get(10, java.util.concurrent.TimeUnit.SECONDS);

            if (responseStr == null) {
                throw new GameException("Respuesta nula del servidor al crear sala");
            }

            Map<String, Object> response = mapper.readValue(responseStr, Map.class);
            if ("OK".equals(response.get("status"))) {
                return response.get("roomid").toString();
            } else {
                throw new GameException("Error al crear sala: " + response.getOrDefault("error", "desconocido"));
            }
        } catch (GameException ex) {
            throw ex;
        } catch (Exception e) {
            log.error("Error al crear sala", e);
            throw new GameException("Error al crear sala: " + e.getMessage());
        }
    }

    public boolean joinRoom(String name, String roomId) throws GameException {
        try {
            String correlationId = UUID.randomUUID().toString();

            Map<String, String> payloadMap = Map.of(
                "id", correlationId,
                "action", "join",
                "roomId", roomId,
                "name", name,
                "from", POD_NAME
            );

            CompletableFuture<String> future = sendRequest(correlationId, payloadMap);
            String responseStr = future.get(10, TimeUnit.SECONDS);

            if (responseStr == null) {
                throw new GameException("Respuesta nula del servidor al unirse a la sala");
            }

            Map<String, Object> response = mapper.readValue(responseStr, Map.class);
            if ("OK".equals(response.get("status"))) {
                return true;
            } else {
                throw new GameException("Error al unirse a la sala: " + response.getOrDefault("error", "desconocido"));
            }
        } catch (GameException ex) {
            throw ex;
        } catch (TimeoutException tex) {
            throw new GameException("Timeout al esperar respuesta del servidor");
        } catch (Exception e) {
            log.error("Error al unirse a la sala", e);
            throw new GameException("Error al unirse a la sala: " + e.getMessage());
        }
    }

    public boolean answer(String name, String roomId, String word) throws GameException {
        try {
            String correlationId = UUID.randomUUID().toString();

            Map<String, String> payloadMap = Map.of(
                "id", correlationId,
                "action", "answer",
                "roomId", roomId,
                "name", name,
                "word", word,
                "from", POD_NAME
            );

            CompletableFuture<String> future = sendRequest(correlationId, payloadMap);
            String responseStr = future.get(10, TimeUnit.SECONDS);

            if (responseStr == null) {
                throw new GameException("Respuesta nula del servidor al enviar respuesta");
            }

            Map<String, Object> response = mapper.readValue(responseStr, Map.class);
            return "OK".equals(response.get("status"));
        } catch (TimeoutException tex) {
            throw new GameException("Timeout esperando respuesta del servidor");
        } catch (Exception e) {
            log.error("Error al procesar respuesta", e);
            throw new GameException("Error esperando respuesta: " + e.getMessage());
        }
    }

    public void desconectar(String name, String roomId) throws GameException {
        try {
            String correlationId = UUID.randomUUID().toString();

            Map<String, String> payloadMap = Map.of(
                "id", correlationId,
                "action", "disconnection",
                "roomId", roomId,
                "name", name,
                "word", "",
                "from", POD_NAME
            );

            CompletableFuture<String> future = sendRequest(correlationId, payloadMap);
            String responseStr = future.get(10, TimeUnit.SECONDS);

            if (responseStr == null) {
                throw new GameException("Respuesta nula del servidor al desconectarse");
            }

            Map<String, Object> response = mapper.readValue(responseStr, Map.class);
            if ("OK".equals(response.get("status"))) {
                log.info("Usuario {} desconectado correctamente de la sala {}", name, roomId);
            } else {
                log.warn("Error al desconectar al usuario {} de la sala {}: {}", name, roomId, response.getOrDefault("error", "desconocido"));
            }
        } catch (TimeoutException tex) {
            throw new GameException("Timeout esperando respuesta del servidor");
        } catch (Exception e) {
            log.error("Error al desconectarse", e);
            throw new GameException("Error al desconectarse: " + e.getMessage());
        }
    }

}
