package com.sistemasdistribuidos.BombParty.services;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Service;

@Service
public class UsersService {
    private Map<String, List<String>> usersRooms = new ConcurrentHashMap<>();;

    public void insertUserRoom(String name, String room) {
        List<String> list = usersRooms.get(room);
        if (list == null) {
            list = new ArrayList<>(List.of(name));
            usersRooms.put(room, list);
        } else {
            list.add(name);
        }
        
    }

    public void deleteUserRoom(String room) {
        usersRooms.remove(room);
    }
}
