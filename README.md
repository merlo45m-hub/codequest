# CodeQuest: Crystal Caverns

A kid-friendly HTML5 math + coding adventure game that runs entirely in the browser.
Battle monsters with arithmetic, solve coding puzzles, and descend through themed
cavern zones to defeat the Crystal Titan. Built for touch (mobile-first) with haptics.

## Play it
No build step, no dependencies.

    python3 server.py

Then open in your phone/desktop browser:

    http://localhost:8085

(On the same WiFi as the server, use its LAN IP, e.g. http://192.168.x.x:8085)

## Features
- Parallax living world: roaming critters, torches, fog, embers, day/night mood
- Explorable room map with connected zones and landmarks (shop / shrine / boss gate)
- Combat spectacle: spell projectiles, streak shockwaves, screen shake, hit-stop
- Boss entrance spectacle (Crystal Titan)
- Glass HUD with HP / XP bars and zone readout
- Animated title screen
- Touch controls + haptics (vibration on hit / level-up / death / boss)
- Persistent backend: auto-starts and self-heals via the host supervisor

## Tech
- `final_frontend.html` — the entire game (canvas 2D, vanilla JS, no asset files)
- `server.py` — Python standard-library HTTP server + game logic API (no pip installs)

## How it works
The server holds game state (rooms, monsters, math problems, coding puzzles). The
frontend calls a tiny JSON API (`start`, `explore`, `answer`, `potion`, `shop`, ...)
and renders the world. Progress is saved per session id in the browser.

Made for Amelie. Built by the Chief of Staff stack.
