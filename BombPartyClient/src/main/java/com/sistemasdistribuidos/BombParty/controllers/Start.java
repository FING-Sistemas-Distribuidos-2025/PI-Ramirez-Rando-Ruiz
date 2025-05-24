package com.sistemasdistribuidos.BombParty.controllers;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class Start {
    private String viewStart = "start";
    private String viewName = "name";

    @GetMapping("/")
    public String name() {
        return viewName;
    }

    @GetMapping("/start")
    public String start(@RequestParam (value = "name") String name, Model model) {
        model.addAttribute("name", name);
        return viewStart;
    }
        
}
