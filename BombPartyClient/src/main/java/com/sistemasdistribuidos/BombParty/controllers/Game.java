package com.sistemasdistribuidos.BombParty.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import com.sistemasdistribuidos.BombParty.exceptions.GameException;
import com.sistemasdistribuidos.BombParty.services.RedisService;
import com.sistemasdistribuidos.BombParty.services.SocketService;

@Controller
public class Game {
    private String viewStart = "start";
    private String viewRoom = "room";
    private String viewName = "name";

    @Autowired
    private SocketService socketservice;

    @Autowired
    private RedisService redisService;

    @GetMapping("/create")
    public String create(@RequestParam(value = "name") String name, Model model) {

        String roomId = null;          
        if (name.isEmpty() || name.isEmpty()) {
            model.addAttribute("error", "Error al cargar el nombre de usuario.");
            return viewName;
        }

        try {
            roomId = redisService.createRoom(name);
            if (roomId == null || roomId.isEmpty()) {
                model.addAttribute("error", "Error al crear la sala.");
            }
        } catch (GameException ex) {
            model.addAttribute("error", "Se produjo un error inesperado.");
        }
        return "redirect:/room?id=" + roomId + "&name=" + name;
    }

    @GetMapping("/join")
    public String join(@RequestParam(value = "id") String roomid,
                        @RequestParam(value = "name") String name,
                        Model model) {
                            
        if (name.isEmpty() || name.isEmpty()) {
            model.addAttribute("error", "Error al cargar el nombre de usuario.");
            return viewName;
        }

        if (roomid == null || roomid.isEmpty()) {
            model.addAttribute("error", "Debe ingresar el número de sala.");
            model.addAttribute("name", name);
            return viewStart;
        } else {
            try {
                if (!redisService.join(name, roomid)) {
                    model.addAttribute("error", "El número de sala es incorrecto.");
                    model.addAttribute("name", name);
                    return viewStart;
                }
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
            if (redisService.answer(name, roomId, answer)) {
                return "fragments/right :: rightAnswer";
            } else {
                return "fragments/right :: wrongAnswer";
            }
        } catch (GameException ex) {
            return "fragments/right :: error";
        }
    }
}