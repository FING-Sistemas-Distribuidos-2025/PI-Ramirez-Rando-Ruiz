package com.sistemasdistribuidos.BombParty.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import com.sistemasdistribuidos.BombParty.exceptions.GameException;
import com.sistemasdistribuidos.BombParty.services.SocketService;

@Controller
public class Game {
    private String viewStart = "start";
    private String viewRoom = "room";

    @Autowired
    private SocketService socketservice;

    @GetMapping("/create")
    public String create(@RequestParam(value = "name") String name, Model model) {

        String roomId = null;          
        if (name == null) {
            return "error?type=nombrevacio";
        }

        try {
            roomId = socketservice.createRoom(name);
            if (roomId == null) {
                return "error?type=roomidnulo";
            }
        } catch (GameException ex) {
            return "error?type=create";
        }
        return "redirect:/room?id=" + roomId + "&name=" + name;
    }

    @GetMapping("/join")
    public String join(@RequestParam(value = "id") String roomid,
                        @RequestParam(value = "name") String name,
                        Model model) {
                            
        if (name == null) {
            return "error?type=nombrevacio";
        }

        if (roomid == null) {
            return "error?type=idroomnulo";
        } else {
            try {
                socketservice.join(name, roomid);
            } catch (GameException ex) {
                return "error?type=join";
            }
            
        }
        return "redirect:/room?id=" + roomid + "&name=" + name;
    }

    @GetMapping("/room")
    public String room(@RequestParam(value = "id") String roomid, @RequestParam(value = "name") String name, Model model) {
        model.addAttribute("roomid", roomid);
        model.addAttribute("name", name);
        return viewRoom;
    }

    @GetMapping("/answer")
    public String rightAnswer(@RequestParam(value = "respuesta") String answer, @RequestParam(value = "name") String name, @RequestParam(value = "roomid") String roomId) {
        try {
            if (socketservice.answer(name, roomId, answer)) {
                return "fragments/right :: rightAnswer";
            } else {
                return "fragments/right :: wrongAnswer";
            }
        } catch (GameException ex) {
            return "fragments/right :: error";
        }
    }
}