#!/usr/bin/env python3
"""
CodeQuest — Web Edition
A browser-based math + coding adventure game for kids.
Zero dependencies — uses only Python stdlib (http.server).
Kids play on their phone browser at http://localhost:8085

Usage:
  python3 server.py
  # Then open browser to http://localhost:8085
"""

import json
import random
import os
import time
import math
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ═══════════════════════════════════════════════════════════
#  GAME LOGIC
# ═══════════════════════════════════════════════════════════

GAMES = {}  # session_id -> game state

MONSTERS = [
    {"name": "Slime", "emoji": "🟢", "hp": 20, "atk": 5, "xp": 10, "min_level": 1},
    {"name": "Bat Swarm", "emoji": "🦇", "hp": 30, "atk": 8, "xp": 15, "min_level": 1},
    {"name": "Goblin Scout", "emoji": "👺", "hp": 40, "atk": 10, "xp": 20, "min_level": 2},
    {"name": "Stone Golem", "emoji": "🗿", "hp": 60, "atk": 15, "xp": 30, "min_level": 3},
    {"name": "Fire Imp", "emoji": "🔥", "hp": 50, "atk": 18, "xp": 35, "min_level": 3},
    {"name": "Ice Wraith", "emoji": "👻", "hp": 70, "atk": 20, "xp": 40, "min_level": 4},
    {"name": "Shadow Knight", "emoji": "⚔️", "hp": 90, "atk": 25, "xp": 55, "min_level": 5},
    {"name": "Dragon Whelp", "emoji": "🐉", "hp": 120, "atk": 30, "xp": 70, "min_level": 6},
    {"name": "Crystal Titan", "emoji": "💎", "hp": 300, "atk": 40, "xp": 150, "min_level": 8},
]

CODING_PUZZLES = [
    {"level": 1, "prompt": "Print the number 42 to open the gate.", "code": "print(____)", "answer": "42", "hint": "Just type 42", "explain": "print() shows text on screen."},
    {"level": 2, "prompt": "Create a variable called 'score' with value 100.", "code": "____ = 100", "answer": "score", "hint": "Variable names go on the left of =", "explain": "Variables store data."},
    {"level": 3, "prompt": "Add 5 and 10, print the result.", "code": "print(5 ____ 10)", "answer": "+", "hint": "What symbol means 'add'?", "explain": "+ adds numbers."},
    {"level": 4, "prompt": "Check if 7 is greater than 3.", "code": "print(7 ____ 3)", "answer": ">", "hint": "What symbol means 'greater than'?", "explain": "> compares values."},
    {"level": 5, "prompt": "Multiply 6 by 7 and print it.", "code": "print(6 ____ 7)", "answer": "*", "hint": "What symbol means 'multiply'?", "explain": "* multiplies."},
    {"level": 6, "prompt": "Make a list with 1, 2, 3", "code": "nums = ____", "answer": "[1, 2, 3]", "hint": "Lists use [ ] with commas", "explain": "Lists store multiple items."},
    {"level": 7, "prompt": "Print the length of 'dragon'", "code": "print(____('dragon'))", "answer": "len", "hint": "What function tells you length?", "explain": "len() returns length."},
    {"level": 8, "prompt": "Print numbers 0 to 4 with a loop", "code": "for i in ____(5):", "answer": "range", "hint": "What generates number sequences?", "explain": "range() makes sequences."},
    {"level": 9, "prompt": "Make a variable called name equal to the word hero", "code": "____ = \"hero\"", "answer": "name", "hint": "Pick a label for the word", "explain": "Strings go in quotes."},
    {"level": 10, "prompt": "Check if 10 equals 10", "code": "print(10 ____ 10)", "answer": "==", "hint": "Two equals signs mean is the same as", "explain": "== compares for equality."},
    {"level": 11, "prompt": "Join the words cat and dog with +", "code": "print(\"cat\" ____ \"dog\")", "answer": "+", "hint": "The + sign joins strings too", "explain": "+ concatenates text."},
    {"level": 12, "prompt": "Make a list of three colors", "code": "colors = [____, ____, ____]", "answer": "\"red\", \"green\", \"blue\"", "hint": "Separate items with commas inside [ ]", "explain": "Lists hold many values."},
]

STORY = [
    {"stage": 0, "title": "🏔️ The Entrance", "text": "You stand at the mouth of the Crystal Caverns. Legends say ancient knowledge is buried deep within — math formulas carved in stone, code etched in crystal. Monsters guard the treasures. Only the clever may pass."},
    {"stage": 1, "title": "🔵 The Blue Caverns", "text": "You descend into the first chamber. Stalactites glow with faint blue light. Slimes and bats skitter in the shadows."},
    {"stage": 2, "title": "🟢 The Green Tunnels", "text": "Deeper now. The crystals shift from blue to green. Goblins patrol these tunnels. A locked door blocks the path — it needs code to open."},
    {"stage": 3, "title": "❄️ The Frozen Depths", "text": "The temperature drops. Ice formations glitter on the walls. Stronger monsters dwell here."},
    {"stage": 4, "title": "💎 THE CRYSTAL TITAN", "text": "You've reached the deepest chamber. A massive figure towers over you — the Crystal Titan. 'Prove your mind is worthy,' it booms."},
    {"stage": 5, "title": "👑 VICTORY", "text": "The Crystal Titan crumbles into sparkling dust. The Knowledge Crystal floats toward you. You grasp it. You are the Champion of the Crystal Caverns!"},
]

DIFFICULTY = {
    "easy": {"max": 20, "neg": False, "frac": False, "xp_mult": 1.2, "label": "Adventurer (8-10)"},
    "normal": {"max": 100, "neg": False, "frac": True, "xp_mult": 1.0, "label": "Hero (10-13)"},
    "hard": {"max": 500, "neg": True, "frac": True, "xp_mult": 0.8, "label": "Legend (13-15)"},
}

SPELLS = [
  {"name":"Spark Bolt","color":"#4dd0e1","mult":1.0,"desc":"steady","cat":"Arithmetic","type":"arcane"},
  {"name":"Flame Burst","color":"#ff7043","mult":1.6,"desc":"big hit","cat":"Multiplication","type":"fire"},
  {"name":"Frost Lance","color":"#4dd0e1","mult":1.25,"desc":"strong","cat":"Division","type":"ice"},
  {"name":"Stone Smash","color":"#a1887f","mult":1.4,"desc":"heavy","cat":"Addition","type":"arcane"},
  {"name":"Venom Spray","color":"#9ccc65","mult":1.15,"desc":"toxic","cat":"Subtraction","type":"arcane"},
  {"name":"Shadow Strike","color":"#ab47bc","mult":1.8,"desc":"risky!","cat":"Power","type":"lightning"},
]
def roll_spells(math_cat):
    import random as _r
    cat_map={"Arithmetic":"Spark Bolt","Multiplication":"Flame Burst","Division":"Frost Lance","Addition":"Stone Smash","Subtraction":"Venom Spray","Power":"Shadow Strike"}
    primary=cat_map.get(math_cat,"Spark Bolt")
    pool=[sp for sp in SPELLS if sp["name"]!=primary]
    _r.shuffle(pool)
    return [next(sp for sp in SPELLS if sp["name"]==primary)]+pool[:2]
CLASSES={
 "mage":    {"name":"Mage","glyph":"X","color":"#8b5cf6","emoji":"*","desc":"Glass cannon. +3 atk, +25% spell dmg. Fragile (80hp). Special OVERLOAD: next spell x2.","hp":80,"atk":13,"spell_mult":1.25,"special":"overload"},
 "knight":  {"name":"Knight","glyph":"S","color":"#f59e0b","emoji":"#","desc":"Tank. 140hp +1 potion. Special BULWARK: heal 30% + no dmg next hit.","hp":140,"atk":9,"spell_mult":1.0,"special":"bulwark"},
 "ranger":  {"name":"Ranger","glyph":"R","color":"#22c55e","emoji":"@","desc":"Balanced. +10% spell dmg, extra potion. Special MULTISHOT: hit twice.","hp":110,"atk":11,"spell_mult":1.1,"special":"multishot"},
 "healer":  {"name":"Healer","glyph":"H","color":"#06b6d4","emoji":"+","desc":"Support. Regen 6hp/turn +1 potion. Special GREAT HEAL: +40% hp.","hp":100,"atk":8,"spell_mult":1.0,"special":"great_heal"},
}
SPECIAL_NAMES={"overload":"OVERLOAD","bulwark":"BULWARK","multishot":"MULTISHOT","great_heal":"GREAT HEAL"}

# CENTRALIZED TUNING CONFIG (ARCH #2: no magic numbers in logic)
CONFIG = {
    "damage": {
        "rand_min": 0, "rand_max": 5,
        "streak_threshold": 3, "streak_bonus_per": 2,
        "special_mult": {"overload": 2.0, "multishot": 2.0},
        "bulwark_heal_frac": 0.30, "great_heal_frac": 0.40,
        "min_damage": 1,
    },
    "combat": {
        "hero_iframe_turns": 0,
        "boss_telegraph_turns": 1,
        "boss_active_frames": 1,
    },
    "combo": {
        "threshold": 3,
        "charge_mult": 1.6,
        "max_charges": 3,
    },
    "crit": {
        "window": 3.0,          # answer within this many seconds for +50% crit
        "mult": 1.5,            # critical damage multiplier
        "time_limit": 10.0,     # client countdown bar length (seconds)
    },
    "defense": {
        "parry_reduction": 0.70,   # damage mitigated when Bulwark-parried during windup
        "bulwark_full_negate": True,  # Knight BULWARK special fully negates the parried hit
    },
    "pools": {"max_particles": 400, "max_projectiles": 64, "max_shockwaves": 24},
    "boss": {"phase2_ratio": 0.50, "phase3_ratio": 0.25},
}

# PURE COMBAT FORMULAS (no mutation -> unit-testable)
def calc_spell_damage(attack, spell_mult, special_mult, streak, cfg=None):
    c = cfg or CONFIG
    base = attack + random.randint(c["damage"]["rand_min"], c["damage"]["rand_max"])
    dmg = int(round(base * spell_mult * special_mult))
    if streak >= c["damage"]["streak_threshold"]:
        dmg += streak * c["damage"]["streak_bonus_per"]
    return max(c["damage"]["min_damage"], dmg)

def resolve_special(special, armed, ready, max_hp, cfg=None):
    c = cfg or CONFIG
    out = {"consume": False, "dmg_mult": 1.0, "heal": 0, "message": "", "message_type": "special"}
    if not (armed and ready):
        return out
    if special in c["damage"]["special_mult"]:
        out["dmg_mult"] = c["damage"]["special_mult"][special]
        out["message"] = "%s! Spell x%dx!" % (SPECIAL_NAMES.get(special, special).upper(), int(out["dmg_mult"]))
        out["consume"] = True
    elif special == "bulwark":
        h = int(max_hp * c["damage"]["bulwark_heal_frac"])
        out["heal"] = h; out["message"] = "BULWARK! +%d HP, braced!" % h; out["consume"] = True
    elif special == "great_heal":
        h = int(max_hp * c["damage"]["great_heal_frac"])
        out["heal"] = h; out["message"] = "GREAT HEAL! +%d HP!" % h; out["consume"] = True
    return out
BOSSES={
 1:{"id":"goblin_king","name":"Goblin King","emoji":"⾝","biome":"Green Tunnels","hp":220,"atk":28,"xp":300,"color":"#2ecc71","mechanic":"adds","draw":"goblin","taunt":"The Goblin King blocks the path!"},
 3:{"id":"frost_warden","name":"Frost Warden","emoji":"❄","biome":"Frozen Depths","hp":320,"atk":34,"xp":420,"color":"#5dade2","mechanic":"chill","draw":"frost","taunt":"The Frost Warden awakens!"},
 4:{"id":"crystal_titan","name":"Crystal Titan","emoji":"Ὀe","biome":"Deep Cavern","hp":440,"atk":42,"xp":700,"color":"#9b59b6","mechanic":"enrage","draw":"crystal","taunt":"The Crystal Titan towers!"},
}
# Signature telegraphed boss moves (ARCH #2: centralized tuning). Each boss picks a move on windup;
# on a failed dodge the move's mult scales the strike and its effect may apply. Dodging avoids all of it.
MOVES = {
  "goblin_king": [
    {"name": "Club Slam", "mult": 1.3, "effect": None},
    {"name": "Warcry", "mult": 1.0, "effect": "frighten"},  # small hit + breaks your streak
  ],
  "frost_warden": [
    {"name": "Frost Nova", "mult": 1.1, "effect": "chill"},  # hit + weakens next spell
    {"name": "Ice Lance", "mult": 1.4, "effect": None},
  ],
  "crystal_titan": [
    {"name": "Crystal Crush", "mult": 1.6, "effect": None},  # massive, but fully dodgeable
    {"name": "Prism Burst", "mult": 1.2, "effect": "blind"},  # hit + lowers streak bonus
  ],
}
def spawn_boss(stage, player_level):
    b=BOSSES.get(stage)
    if not b: b=BOSSES[4]
    return {"name":b["name"],"emoji":b["emoji"],"hp":b["hp"]+player_level*30,"max_hp":b["hp"]+player_level*30,"atk":b["atk"]+player_level*3,"xp":b["xp"],"boss_id":b["id"],"biome":b["biome"],"color":b["color"],"mechanic":b["mechanic"],"draw":b["draw"],"taunt":b["taunt"],
            "moves":MOVES.get(b["id"],[]),"current_move":None}
def apply_class(g,cls):
    c=CLASSES.get(cls,CLASSES["knight"])
    g["hero_class"]=cls; g["class_name"]=c["name"]; g["class_color"]=c["color"]; g["class_emoji"]=c["emoji"]
    g["max_hp"]=c["hp"]; g["hp"]=c["hp"]; g["attack"]=c["atk"]; g["spell_mult"]=c["spell_mult"]
    g["special"]=c["special"]; g["special_ready"]=True; g["bulwark_active"]=False; g["regen"]=6 if cls=="healer" else 0
    return g
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def gen_math(difficulty, player_level):
    cfg = DIFFICULTY[difficulty]
    mx = cfg["max"]
    types = ["addition", "subtraction"]
    if player_level >= 2: types.append("multiplication")
    if player_level >= 3: types.append("division")
    if player_level >= 4: types.append("algebra")
    if player_level >= 5 and cfg["frac"]: types.append("fractions")
    ptype = random.choice(types)

    if ptype == "addition":
        a, b = random.randint(1, mx), random.randint(1, mx)
        return {"q": f"What is {a} + {b}?", "a": str(a+b), "cat": "Addition ➕"}
    elif ptype == "subtraction":
        a = random.randint(1, mx)
        b = random.randint(1, a if not cfg["neg"] else mx)
        return {"q": f"What is {a} - {b}?", "a": str(a-b), "cat": "Subtraction ➖"}
    elif ptype == "multiplication":
        a = random.randint(2, min(20, mx//5))
        b = random.randint(2, min(15, mx//10))
        return {"q": f"What is {a} × {b}?", "a": str(a*b), "cat": "Multiplication ✖️"}
    elif ptype == "division":
        b = random.randint(2, 12)
        r = random.randint(2, mx//b)
        return {"q": f"What is {b*r} ÷ {b}?", "a": str(r), "cat": "Division ➗"}
    elif ptype == "algebra":
        if difficulty != "hard":
            x = random.randint(1, mx)
            b = random.randint(1, mx)
            if random.choice([True, False]):
                return {"q": f"If x + {b} = {x+b}, what is x?", "a": str(x), "cat": "Algebra 🔤"}
            else:
                return {"q": f"If x - {b} = {x}, what is x?", "a": str(x+b), "cat": "Algebra 🔤"}
        else:
            x = random.randint(2, 20)
            c = random.randint(2, 5)
            k = random.randint(1, 10)
            return {"q": f"If {c}x + {k} = {c*x+k}, what is x?", "a": str(x), "cat": "Algebra 🔤"}
    elif ptype == "fractions":
        ds = [2, 4, 3, 6, 8]
        d1 = random.choice(ds)
        d2 = random.choice([d for d in ds if d != d1])
        lcm = d1 * d2 // gcd(d1, d2)
        n1 = random.randint(1, d1-1)
        n2 = random.randint(1, d2-1)
        rn = n1 * (lcm//d1) + n2 * (lcm//d2)
        return {"q": f"What is {n1}/{d1} + {n2}/{d2}? (answer as fraction)", "a": f"{rn}/{lcm}", "cat": "Fractions 🍕"}
    a, b = random.randint(1, mx), random.randint(1, mx)
    return {"q": f"What is {a} + {b}?", "a": str(a+b), "cat": "Addition ➕"}

def spawn_monster(player_level, boss=False):
    if boss:
        return spawn_boss(4, player_level)
    avail = [m for m in MONSTERS if m["min_level"] <= player_level + 1 and m["name"] != "Crystal Titan"]
    t = random.choice(avail)
    scale = 1 + (player_level - t["min_level"]) * 0.15
    return {"name": t["name"], "emoji": t["emoji"], "hp": int(t["hp"]*scale), "max_hp": int(t["hp"]*scale), "atk": int(t["atk"]*scale), "xp": int(t["xp"]*scale)}

def new_game(name, difficulty):
    return {
        "name": name,
        "hp": 100, "max_hp": 100,
        "level": 1, "xp": 0, "xp_to_next": 50,
        "gems": 0, "potions": 3, "attack": 10,
        "difficulty": difficulty,
        "battles_won": 0, "puzzles_solved": 0, "math_solved": 0,
        "rooms_cleared": 0, "streak": 0, "best_streak": 0,
        "story_stage": 0,
        "mode": "explore",  # explore, battle, puzzle, shop, rest, treasure, boss, victory, defeat
        "monster": None,
        "current_problem": None,
        "current_puzzle": None,
        "puzzle_attempts": 0,
        "choices": None,
        "boss_phase": 0,
        "last_spell": "",
        "fork_left": "",
        "hero_class": "knight", "class_name": "Knight", "class_color": "#f59e0b", "class_emoji": "#",
        "special": "bulwark", "special_ready": True, "special_armed": False, "bulwark_active": False, "regen": 0, "spell_mult": 1.0,
        "fork_right": "",
        "battle_round": 0,
        "boss_telegraph": 0, "boss_pending_dmg": 0, "current_move": None,  # combat lifecycle: windup + signature move tracking
        "charges": 0, "combo_threshold": CONFIG["combo"]["threshold"], "charged_this_hit": False,  # INTERACTIVE MECHANIC: answer-combo -> charged spell
        "crit_this_hit": False, "last_response_time": None,  # RESPONSE COUNTDOWN: first-3s crit
        "defended": False,  # ACTIVE DEFENSE: Bulwark parry during enemy windup
        "message": "",
        "message_type": "info",
    }

def get_story_for_room(rooms):
    triggers = {1: 0, 3: 1, 6: 2, 10: 3, 14: 4}
    return triggers.get(rooms)

def check_levelup(g):
    while g["xp"] >= g["xp_to_next"]:
        g["xp"] -= g["xp_to_next"]
        g["level"] += 1
        g["max_hp"] += 20
        g["hp"] = g["max_hp"]
        g["attack"] += 5
        g["potions"] += 1
        g["xp_to_next"] = int(g["xp_to_next"] * 1.5)
        g["message"] = f"⭐ LEVEL UP! Now level {g['level']}! HP +20, ATK +5, +1 potion!"
        g["message_type"] = "levelup"

# ═══════════════════════════════════════════════════════════
#  API ACTIONS
# ═══════════════════════════════════════════════════════════

def action_start(name, difficulty, cls="knight"):
    g = new_game(name or "Hero", difficulty or "normal")
    apply_class(g, cls)
    sid = str(int(time.time() * 1000)) + str(random.randint(0, 999))
    GAMES[sid] = g
    stage = get_story_for_room(0)
    if stage is not None:
        g["story_stage"] = stage
    g["message"] = f"Welcome, {g['name']}! Press EXPLORE to begin your adventure!"
    return sid, g

def action_restore(state):
    """Re-seed a game from a full client-saved state (survives server restart)."""
    g=dict(state)
    sid=str(uuid.uuid4())
    GAMES[sid]=g
    return sid,g

def action_defend(g):
    """ACTIVE DEFENSE: tap Bulwark during the enemy attack windup (boss_telegraph) to parry/reduce the telegraphed strike."""
    g["defended"] = False
    if g["mode"] == "boss" and g.get("boss_telegraph"):
        mv = g.get("current_move") or "strike"
        pdmg = g.get("boss_pending_dmg") or (g["monster"]["atk"] + random.randint(0, 3))
        # Full negate if Knight BULWARK special is ready; else flat parry reduction
        if g.get("special") == "bulwark" and g.get("special_ready"):
            reduced = 0
            g["special_ready"] = False
            g["message"] = "\U0001F6E1 BULWARK! You slam your guard up and FULLY parry the %s! (special spent)" % mv
        else:
            reduced = int(round(pdmg * (1 - CONFIG["defense"]["parry_reduction"]))) if False else int(round(pdmg * (1 - CONFIG["defense"]["parry_reduction"])))
            g["message"] = "\U0001F6E1 BULWARK! You parry the %s for %d dmg (mitigated %d%%)!" % (mv, reduced, int(CONFIG["defense"]["parry_reduction"] * 100))
        g["hp"] -= reduced
        g["boss_telegraph"] = 0
        g["boss_pending_dmg"] = 0
        g["current_move"] = None
        g["defended"] = True
        g["message_type"] = "defend"
        # small heal flavor for bulwark class
        if g.get("special") == "bulwark":
            g["hp"] = min(g["max_hp"], g["hp"] + int(g["max_hp"] * 0.10))
    else:
        g["message"] = "\U0001F6E1 You raise your guard, but there is no incoming attack to block."
        g["message_type"] = "info"
    return g


def action_explore(g):
    if g["mode"] in ("battle", "boss", "puzzle", "shop", "fork"):
        g["message"] = "⚠️ You're in the middle of something! Finish it first."
        g["message_type"] = "miss"
        return g
    g["message"] = ""
    g["message_type"] = "info"
    room = g["rooms_cleared"] + 1

    # Story trigger
    stage = get_story_for_room(room)
    if stage is not None:
        g["story_stage"] = stage
        if stage in BOSSES:
            g["mode"] = "boss"
            g["monster"] = spawn_boss(stage, g["level"])
            g["battle_round"] = 0
            g["current_problem"] = gen_math(g["difficulty"], g["level"] + 2)
            g["choices"] = roll_spells(g["current_problem"]["cat"])
            g["boss_phase"] = 1
            return g

    # Path fork (interactive choice)
    if random.random() < 0.15 and room < 14 and g["story_stage"] < 4:
        opts=["treasure","battle","rest","puzzle"]
        random.shuffle(opts)
        g["mode"]="fork"
        g["fork_left"]=opts[0]
        g["fork_right"]=opts[1]
        return g
    # Final boss
    if g["story_stage"] >= 4 and g["story_stage"] < 5 and room >= 14 and g.get("monster") is None:
        g["mode"] = "boss"
        g["monster"] = spawn_boss(4, g["level"])
        g["battle_round"] = 0
        g["current_problem"] = gen_math(g["difficulty"], g["level"] + 2)
        g["choices"] = roll_spells(g["current_problem"]["cat"])
        g["boss_phase"] = 1
        return g

    # Random room
    roll = random.random()
    if roll < 0.45:
        g["mode"] = "battle"
        g["monster"] = spawn_monster(g["level"])
        g["battle_round"] = 0
        g["current_problem"] = gen_math(g["difficulty"], g["level"])
        g["choices"] = roll_spells(g["current_problem"]["cat"])
        g["message"] = f"{g['monster']['emoji']} A wild {g['monster']['name']} appears!"
    elif roll < 0.70:
        g["mode"] = "puzzle"
        lvl = min(g["level"], len(CODING_PUZZLES))
        g["current_puzzle"] = CODING_PUZZLES[lvl - 1].copy()
        g["puzzle_attempts"] = 0
    elif roll < 0.82:
        gems = random.randint(3, 10)
        g["gems"] += gems
        if random.random() < 0.4:
            g["potions"] += 1
            g["message"] = f"📦 Treasure! +{gems} gems, +1 potion!"
        else:
            g["message"] = f"📦 Treasure! +{gems} gems!"
        g["message_type"] = "treasure"
        g["rooms_cleared"] += 1
    elif roll < 0.92:
        heal = int(g["max_hp"] * 0.3)
        g["hp"] = min(g["max_hp"], g["hp"] + heal)
        g["message"] = f"⛺ Rest. +{heal} HP."
        g["rooms_cleared"] += 1
    else:
        g["mode"] = "shop"
    return g

def action_answer(g, answer, choice=None, response_time=None):
    answer = answer.strip()
    if g["mode"] == "battle" or g["mode"] == "boss":
        prob = g["current_problem"]
        if answer.lower() == prob["a"].lower():
            sm = g.get("choices") and g["choices"][int(choice)]["mult"] if (g.get("choices") and choice not in (None,"")) else 1.0
            sm = sm if sm else 1.0
            sp = resolve_special(g.get("special"), g.get("special_armed"), g.get("special_ready"), g["max_hp"])
            dmg = calc_spell_damage(g["attack"], sm, sp["dmg_mult"], g["streak"])
            # RESPONSE COUNTDOWN CRIT: answer within crit.window seconds -> +50%
            g["last_response_time"] = response_time
            g["crit_this_hit"] = False
            if response_time is not None and response_time <= CONFIG["crit"]["window"]:
                dmg = int(round(dmg * CONFIG["crit"]["mult"]))
                g["crit_this_hit"] = True
            if sp["consume"]:
                g["special_ready"] = False
                if sp["heal"]:
                    g["hp"] = min(g["max_hp"], g["hp"] + sp["heal"])
                    if g.get("special") == "bulwark":
                        g["bulwark_active"] = True
                g["message"] = sp["message"]; g["message_type"] = "special"
            ch = g.get("choices")
            if ch not in (None, ""):
                try:
                    ci = int(choice)
                    if 0 <= ci < len(ch):
                        g["last_spell"] = ch[ci]["name"]
                except (ValueError, TypeError):
                    pass
            g["streak"] += 1
            g["best_streak"] = max(g["best_streak"], g["streak"])
            g["math_solved"] = g.get("math_solved", 0) + 1
            if g["streak"] >= CONFIG["damage"]["streak_threshold"]:
                bonus = g["streak"] * CONFIG["damage"]["streak_bonus_per"]
                dmg += bonus
                g["message"] = "🔥 STREAK x%d! +%d bonus!" % (g["streak"], bonus)
            else:
                g["message"] = "✅ Correct! %d damage!" % dmg
            # ANSWER COMBO -> CHARGED SPELL (every `threshold` consecutive corrects)
            g["charges"] = min(CONFIG["combo"]["max_charges"], g.get("charges", 0) + 1)
            g["charged_this_hit"] = False
            if g["charges"] >= CONFIG["combo"]["threshold"]:
                g["charges"] = 0
                cm = CONFIG["combo"]["charge_mult"]
                dmg = int(round(dmg * cm))
                g["charged_this_hit"] = True
                g["message"] = "\u26a1 CHARGED SPELL! x%d \u2014 %d dmg!" % (int(cm), dmg)
            # RESPONSE COUNTDOWN CRIT: stamp the crit into the final message
            if g.get("crit_this_hit"):
                g["message"] = "\u26a1 CRIT! x%.1f \u2014 " % CONFIG["crit"]["mult"] + g["message"]
            if g["mode"] == "boss" and g.get("boss_telegraph"):
                g["boss_telegraph"] = 0
                g["boss_pending_dmg"] = 0
                g["message"] = "\U0001F938 DODGE! You answer true and leap aside \u2014 " + g["monster"]["name"] + "'s strike misses! " + g["message"]
            g["monster"]["hp"] -= dmg
            if g["mode"] == "boss" and g["monster"]["hp"] <= 0 and g["story_stage"] < 5:
                is_final = g["monster"].get("boss_id") == "crystal_titan"
                g["mode"] = "explore"
                if is_final:
                    g["story_stage"] = 5
                    g["message"] = "The Crystal Titan falls! You are CHAMPION!"
                    g["message_type"] = "win"
                    return g
                else:
                    g["rooms_cleared"] += 1
                    g["message"] = f"You defeated the {g['monster']['name']}! The path opens deeper into the caverns."
                    g["message_type"] = "win"
                    return g
            g["message_type"] = "hit"
            if g["monster"]["hp"] <= 0:
                xp = int(g["monster"]["xp"] * DIFFICULTY[g["difficulty"]]["xp_mult"])
                gems = random.randint(1, 3)
                g["xp"] += xp
                g["gems"] += gems
                g["battles_won"] += 1
                was_boss = g["mode"] == "boss"
                g["mode"] = "explore"
                g["rooms_cleared"] += 1
                if was_boss:
                    if g["monster"].get("boss_id") == "crystal_titan":
                        g["story_stage"] = 5
                        g["message"] = "👑 CHAMPION! You defeated the Crystal Titan and claimed the Knowledge Crystal!"
                    else:
                        g["message"] = f"🏆 You defeated the {g['monster']['name']}! Deeper you go..."
                else:
                    g["message"] = f"🎉 Victory! +{xp} XP, +{gems} gems!"
                g["message_type"] = "victory"
                check_levelup(g)
                return g
        else:
            g["streak"] = 0
            g["charges"] = 0
            g["charged_this_hit"] = False
            if g["mode"] == "boss" and g.get("boss_telegraph"):
                m_dmg = g.get("boss_pending_dmg") or (g["monster"]["atk"] + random.randint(0, 3))
                g["hp"] -= m_dmg
                mv_name = g.get("current_move") or "strike"
                eff = None
                for _m in (g["monster"].get("moves") or []):
                    if _m["name"] == mv_name:
                        eff = _m.get("effect"); break
                if eff == "chill":
                    g["spell_mult"] = max(0.5, g.get("spell_mult", 1.0) - 0.3)
                    g["message"] = f"\U0001F4A5 You failed to dodge the {mv_name}! {g['monster']['emoji']} hits you for {m_dmg} and CHILLS your magic (-30% next spell)!"
                elif eff == "frighten":
                    g["streak"] = 0
                    g["message"] = f"\U0001F4A5 You failed to dodge the {mv_name}! {g['monster']['emoji']} hits you for {m_dmg} and breaks your streak!"
                elif eff == "blind":
                    g["streak"] = 0
                    g["message"] = f"\U0001F4A5 You failed to dodge the {mv_name}! {g['monster']['emoji']} hits you for {m_dmg} and blinds you (streak reset)!"
                else:
                    g["message"] = f"\U0001F4A5 You failed to dodge the {mv_name}! {g['monster']['emoji']} strikes you for {m_dmg}!"
                g["message_type"] = "miss"
                g["boss_telegraph"] = 0
                g["boss_pending_dmg"] = 0
                g["current_move"] = None
            elif g["mode"] == "boss":
                moves = g["monster"].get("moves") or [{"name": "strike", "mult": 1.0, "effect": None}]
                mv = random.choice(moves)
                g["current_move"] = mv["name"]
                g["boss_telegraph"] = CONFIG["combat"]["boss_telegraph_turns"]
                g["boss_pending_dmg"] = int((g["monster"]["atk"] + random.randint(3, 8)) * mv["mult"])
                g["message"] = f"\u274c Wrong! Answer was {prob['a']}. {g['monster']['emoji']} winds up {mv['name']} \u2014 answer RIGHT next turn to DODGE it!"
                g["message_type"] = "miss"
            else:
                m_dmg = g["monster"]["atk"] + random.randint(0, 3)
                g["hp"] -= m_dmg
                g["message"] = f"\u274c Wrong! Answer was {prob['a']}. {g['monster']['emoji']} hits you for {m_dmg}!"
                g["message_type"] = "miss"
            if g["hp"] <= 0:
                g["hp"] = 0
                g["mode"] = "gameover"
                g["message"] = "💀 You have been defeated! Game Over."
                g["message_type"] = "defeat"
                return g
            g["battle_round"] += 1
        g["current_problem"] = gen_math(g["difficulty"], g["level"] + (2 if g["mode"] == "boss" else 0))
        if g["mode"] == "boss":
            ratio = g["monster"]["hp"] / g["monster"]["max_hp"]
            g["boss_phase"] = 3 if ratio <= 0.25 else 2 if ratio <= 0.5 else 1
            if g["boss_phase"] >= 2:
                g["monster"]["atk"] = int(g["monster"]["atk"] * 1.4)
                g["message"] += f" {g['monster']['name']} ENRAGES!"
        g["choices"] = roll_spells(g["current_problem"]["cat"])
        return g

    elif g["mode"] == "puzzle":
        p = g["current_puzzle"]
        g["puzzle_attempts"] += 1
        if answer.lower() == p["answer"].lower():
            xp = 50 + p["level"] * 20
            g["xp"] += xp
            g["gems"] += 5
            g["puzzles_solved"] += 1
            g["mode"] = "explore"
            g["rooms_cleared"] += 1
            g["message"] = f"🔓 Correct! +{xp} XP, +5 gems. {p['explain']}"
            g["message_type"] = "victory"
            check_levelup(g)
        else:
            if g["puzzle_attempts"] >= 3:
                g["hp"] -= 10
                if g["hp"] <= 0:
                    g["hp"] = 0
                    g["mode"] = "gameover"
                    g["message"] = "💀 The puzzle trap drains your last strength... Game Over."
                    g["message_type"] = "defeat"
                    return g
                g["mode"] = "explore"
                g["rooms_cleared"] += 1
                g["message"] = f"🔒 Failed! Answer was {p['answer']}. {p['explain']} -10 HP"
                g["message_type"] = "defeat"
            else:
                g["message"] = f"❌ Try again! Hint: {p['hint']}"
                g["message_type"] = "miss"
        return g

    return g

def action_fork(g, side):
    if g["mode"] != "fork":
        return g
    dest = g.get("fork_"+str(side), "treasure")
    if dest == "battle":
        g["mode"]="battle"; g["monster"]=spawn_monster(g["level"]); g["battle_round"]=0; g["current_problem"]=gen_math(g["difficulty"],g["level"]); g["choices"]=roll_spells(g["current_problem"]["cat"])
    elif dest == "puzzle":
        g["mode"]="puzzle"; lvl=min(g["level"],len(CODING_PUZZLES)); g["current_puzzle"]=CODING_PUZZLES[lvl-1].copy(); g["puzzle_attempts"]=0
    elif dest == "rest":
        heal=int(g["max_hp"]*0.3); g["hp"]=min(g["max_hp"],g["hp"]+heal); g["rooms_cleared"]+=1; g["mode"]="explore"
    else:
        gems=random.randint(3,10); g["gems"]+=gems; g["potions"]+=1; g["rooms_cleared"]+=1; g["mode"]="explore"
    return g

def action_potion(g):
    if g["potions"] > 0 and g["hp"] < g["max_hp"]:
        g["potions"] -= 1
        heal = min(50, g["max_hp"] - g["hp"])
        g["hp"] += heal
        g["message"] = f"🧪 Healed {heal} HP! ({g['potions']} left)"
        g["message_type"] = "heal"
    elif g["potions"] == 0:
        g["message"] = "No potions!"
        g["message_type"] = "miss"
    else:
        g["message"] = "HP already full!"
        g["message_type"] = "info"
    return g

def action_shop(g, choice):
    if choice == "1" and g["gems"] >= 10:
        g["gems"] -= 10
        g["potions"] += 1
        g["message"] = "Bought a potion!"
    elif choice == "2" and g["gems"] >= 20:
        g["gems"] -= 20
        g["attack"] += 3
        g["message"] = f"ATK +3! Now {g['attack']}"
    elif choice == "3" and g["gems"] >= 30:
        g["gems"] -= 30
        g["max_hp"] += 15
        g["hp"] += 15
        g["message"] = f"Max HP +15! Now {g['max_hp']}"
    elif choice == "4":
        g["message"] = "Left shop."
    else:
        g["message"] = "Not enough gems!"
        return g
    g["mode"] = "explore"
    return g

def action_special(g):
    if not g.get("special_ready"):
        g["message"]="Special not ready yet!"; g["message_type"]="info"; return g
    g["special_armed"]=True
    nm=SPECIAL_NAMES.get(g.get("special"),"SPECIAL")
    g["message"]=nm+" armed! Answer correctly to unleash it!"; g["message_type"]="special"
    return g
    g["rooms_cleared"] += 1
    g["message_type"] = "info"
    return g

# ═══════════════════════════════════════════════════════════
#  HTML/CSS/JS FRONTEND
# ═══════════════════════════════════════════════════════════

HTML_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>CodeQuest Crystal Caverns</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;user-select:none;-webkit-user-select:none;-webkit-tap-highlight-color:transparent}
body{background:#000;overflow:hidden;font-family:system-ui,sans-serif;color:#fff}
#game{position:relative;width:100vw;max-width:480px;margin:0 auto;height:100vh;max-height:800px;overflow:hidden}
canvas{display:block;width:100%;height:100%;image-rendering:pixelated;image-rendering:crisp-edges}
#ui{position:absolute;inset:0;pointer-events:none;z-index:10}
.clickable{pointer-events:auto}
.hud{position:absolute;top:0;left:0;right:0;padding:4px 6px;display:flex;gap:3px;flex-wrap:wrap;font-size:10px;font-weight:bold}
.hud .chip{background:rgba(0,0,0,0.65);padding:2px 7px;border-radius:5px;backdrop-filter:blur(4px)}
.hud .chip.hp{flex:1;min-width:70px}
.hp-mini{width:55px;height:4px;background:#333;border-radius:2px;overflow:hidden;display:inline-block;vertical-align:middle;margin-left:3px}
.hp-mini-fill{height:100%;background:#2ecc71;transition:width .4s}
.hp-mini-fill.low{background:#e74c3c}
.hp-mini-fill.mid{background:#f39c12}
.hud2{position:absolute;top:24px;left:0;right:0;padding:0 6px;display:flex;gap:3px;flex-wrap:wrap;font-size:10px;font-weight:bold}
.hud2 .chip{background:rgba(0,0,0,0.65);padding:2px 7px;border-radius:5px}
.panel{position:absolute;left:6px;right:6px;bottom:6px;background:rgba(8,8,24,0.95);border-radius:12px;padding:10px;border:1px solid rgba(100,100,255,0.15);backdrop-filter:blur(8px)}
.panel.title-screen{top:50%;transform:translateY(-50%);bottom:auto;text-align:center}
.panel h2{font-size:1.1em;margin-bottom:6px;color:#4dd0e1}
.panel p{font-size:0.8em;color:#888;margin-bottom:6px;line-height:1.4}
.panel input,.panel select{width:100%;padding:10px;border-radius:8px;border:2px solid #333;background:rgba(0,0,0,0.5);color:#fff;font-size:0.95em;margin:3px 0}
.panel input:focus{border-color:#0575E6;outline:none}
.btn{display:block;width:100%;padding:11px;border:none;border-radius:10px;font-size:0.95em;font-weight:bold;cursor:pointer;margin:3px 0;transition:transform .1s}
.btn:active{transform:scale(.96)}
.btn-primary{background:linear-gradient(135deg,#00f260,#0575E6);color:#fff}
.btn-danger{background:linear-gradient(135deg,#ff416c,#ff4b2b);color:#fff}
.btn-success{background:linear-gradient(135deg,#11998e,#38ef7d);color:#fff}
.btn-secondary{background:rgba(255,255,255,0.1);color:#ccc}
.math-box{text-align:center;margin:6px 0}
.math-cat{font-size:0.72em;color:#82b1ff;margin-bottom:2px}
.math-q{font-size:1.25em;font-weight:bold}
.code-block{background:rgba(0,0,0,0.5);border-radius:8px;padding:8px;margin:5px 0;font-family:monospace;font-size:0.9em;color:#80cbc4}
.shop-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin:5px 0}
.shop-item{background:rgba(255,255,255,0.06);border-radius:8px;padding:8px;text-align:center;cursor:pointer;transition:transform .2s}
.shop-item:active{transform:scale(.95)}
.shop-item .nm{font-size:0.75em;color:#ddd}
.shop-item .pr{font-size:0.7em;color:#ffd54f}
.msg{padding:7px;border-radius:8px;margin:5px 0;font-weight:bold;text-align:center;font-size:0.78em}
.msg-info{background:rgba(100,100,255,0.15);color:#82b1ff}
.msg-hit{background:rgba(0,255,100,0.15);color:#69f0ae}
.msg-miss{background:rgba(255,50,50,0.15);color:#ff8a80}
.msg-victory{background:rgba(255,215,0,0.15);color:#ffd54f}
.msg-defeat{background:rgba(255,50,50,0.25);color:#ff8a80}
.msg-treasure{background:rgba(255,215,0,0.15);color:#ffd54f}
.story-box{background:rgba(100,80,150,0.12);border-radius:8px;padding:7px;margin:4px 0;border-left:3px solid #7c4dff}
.story-t{font-size:0.82em;font-weight:bold;color:#b39ddb}
.story-x{font-size:0.7em;color:#9fa8da;font-style:italic;line-height:1.3}
</style>
</head>
<body>
<div id="game">
<canvas id="cv"></canvas>
<div id="ui"></div>
</div>
<script>
const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
const ui=document.getElementById('ui');
let W=480,H=800;
let SID=null,state=null,lastState=null;
let particles=[],dmgNums=[],shakeTime=0,shakeMag=0,flashColor=null,flashAlpha=0;
let animTime=0,gameMode='title';
let roomTrans=0,roomTransDir=1;
let attackAnim=0,attackAnimWho=null;
let chestAnim=0,chestOpen=false;
let bossIntro=0;
let bgOffset=0;
let monsterDeath=0;
let lowHpPulse=0;
let levelUpText="";
let levelUpTextLife=0;
let streakFire=[];
let goldRain=[];
let attackTrail=[];
let spearTrails=[];
let depth=0;
let walkAnim=0;
let potionAnim=0;
let critFlash=0;
let bossZoom=0;
let victoryStats=[];
let torchFlicker=[];
let screenShakeX=0;
let screenShakeY=0;
let hitStop=0;

// === SOUND ENGINE (Web Audio API, no files needed) ===
let audioCtx=null;
function initAudio(){if(!audioCtx)audioCtx=new(window.AudioContext||window.webkitAudioContext)()}
function beep(freq,dur,type='square',vol=0.15){
  if(!audioCtx)return;
  const o=audioCtx.createOscillator(),g=audioCtx.createGain();
  o.type=type;o.frequency.value=freq;o.connect(g);g.connect(audioCtx.destination);
  g.gain.setValueAtTime(vol,audioCtx.currentTime);
  g.gain.exponentialRampToValueAtTime(0.001,audioCtx.currentTime+dur);
  o.start();o.stop(audioCtx.currentTime+dur);
}
function sfxHit(){beep(800,0.08,'sawtooth',0.2);setTimeout(()=>beep(400,0.1,'sawtooth',0.15),60)}
function sfxHurt(){beep(200,0.15,'sawtooth',0.25);setTimeout(()=>beep(150,0.2,'sawtooth',0.2),80)}
function sfxCorrect(){beep(523,0.08,'sine',0.2);setTimeout(()=>beep(659,0.08,'sine',0.2),80);setTimeout(()=>beep(784,0.12,'sine',0.2),160)}
function sfxWrong(){beep(200,0.1,'square',0.15);setTimeout(()=>beep(150,0.15,'square',0.12),100)}
function sfxVictory(){[523,659,784,1047].forEach((f,i)=>setTimeout(()=>beep(f,0.1,'sine',0.2),i*80))}
function sfxTreasure(){[659,784,988,1319].forEach((f,i)=>setTimeout(()=>beep(f,0.08,'triangle',0.15),i*60))}
function sfxLevelUp(){[523,659,784,1047,1319].forEach((f,i)=>setTimeout(()=>beep(f,0.1,'triangle',0.2),i*50))}
function sfxDeath(){[400,300,200,100].forEach((f,i)=>setTimeout(()=>beep(f,0.2,'sawtooth',0.2),i*100))}
function sfxBoss(){[100,80,60,40].forEach((f,i)=>setTimeout(()=>beep(f,0.3,'sawtooth',0.25),i*200))}
function sfxFootstep(){beep(80+Math.random()*20,0.03,'square',0.05)}
function sfxShop(){beep(880,0.06,'sine',0.15);setTimeout(()=>beep(1100,0.06,'sine',0.1),50)}

function resize(){const r=document.getElementById('game').getBoundingClientRect();W=r.width;H=r.height;cv.width=W;cv.height=H}
window.addEventListener('resize',resize);resize();
for(let i=0;i<6;i++)torchFlicker.push(0.7+Math.random()*0.3);

// === ANIMATED SPRITE DRAWING ===

function drawPlayer(x,y,scl,hit,attacking){
  ctx.save();ctx.translate(x,y);ctx.scale(scl,scl);
  const bob=Math.sin(animTime*2.5)*2;
  ctx.translate(0,bob);
  if(hit){ctx.translate(Math.sin(animTime*50)*5,0);ctx.filter='brightness(2)'}
  if(attacking){ctx.translate(Math.sin(animTime*10)*8,0)}
  const legSwing=Math.sin(animTime*2.5)*3;
  // Cape
  ctx.fillStyle='#1a3060';ctx.beginPath();ctx.moveTo(-6,-18);ctx.quadraticCurveTo(-14+bob,0,-8+legSwing,12);ctx.lineTo(-4,12);ctx.quadraticCurveTo(-6,0,-2,-18);ctx.fill();
  // Legs (animated)
  ctx.fillStyle='#1a3060';ctx.fillRect(-9,8,7,14+legSwing);ctx.fillRect(2,8,7,14-legSwing);
  ctx.fillStyle='#333';ctx.fillRect(-9,18+legSwing,7,4);ctx.fillRect(2,18-legSwing,7,4);
  // Body
  ctx.fillStyle='#2d4a8e';ctx.fillRect(-12,-20,24,30);
  ctx.fillStyle='#1a3060';ctx.fillRect(-12,-20,24,4);
  // Belt
  ctx.fillStyle='#8B4513';ctx.fillRect(-12,4,24,4);ctx.fillStyle='#ffd700';ctx.fillRect(-2,4,4,4);
  // Head
  ctx.fillStyle='#f0d090';ctx.fillRect(-8,-30,16,12);
  // Helmet
  ctx.fillStyle='#bbb';ctx.fillRect(-10,-32,20,6);ctx.fillRect(-10,-28,20,2);
  ctx.fillStyle='#444';ctx.fillRect(-3,-30,6,4);
  ctx.fillStyle='#aaa';ctx.fillRect(-10,-34,4,4);ctx.fillRect(6,-34,4,4); // horns
  // Arms
  ctx.fillStyle='#888';ctx.fillRect(-14,-26,4,16);ctx.fillRect(10,-26,4,16);
  // Shield
  ctx.fillStyle='#444';ctx.beginPath();ctx.arc(-14,-8,8,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#2d4a8e';ctx.beginPath();ctx.arc(-14,-8,5,0,Math.PI*2);ctx.fill();
  ctx.fillStyle='#ffd700';ctx.beginPath();ctx.arc(-14,-8,2,0,Math.PI*2);ctx.fill();
  // Sword (animated swing)
  ctx.save();
  if(attacking){ctx.rotate(Math.sin(animTime*10)*0.8-0.3)}
  ctx.fillStyle='#ccc';ctx.fillRect(12,-22,3,20);ctx.fillStyle='#aaa';ctx.fillRect(11,-24,5,4);
  ctx.fillStyle='#8B4513';ctx.fillRect(9,-6,9,3);ctx.fillStyle='#ffd700';ctx.fillRect(11,-3,5,3);
  ctx.restore();
  ctx.restore();
}

function drawMonster(x,y,scl,type,hit,attacking){
  ctx.save();ctx.translate(x,y);ctx.scale(scl,scl);
  const bob=Math.sin(animTime*1.5+1)*3;
  ctx.translate(0,bob);
  if(hit){ctx.translate(Math.sin(animTime*50)*5,0);ctx.filter='brightness(2)'}
  if(attacking){ctx.translate(-Math.sin(animTime*10)*6,0)}
  const t=(type||'slime').toLowerCase();
  if(t.includes('slime')){
    const sq=Math.sin(animTime*1.5)*0.1+1;ctx.save();ctx.scale(1/sq,sq);
    ctx.fillStyle='#2ecc71';ctx.beginPath();ctx.arc(0,0,18,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#27ae60';ctx.beginPath();ctx.arc(0,3,18,0,Math.PI*2);ctx.fill();
    ctx.restore();
    ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(-5,-3,4,0,Math.PI*2);ctx.arc(5,-3,4,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#000';ctx.beginPath();ctx.arc(-5,-2,2,0,Math.PI*2);ctx.arc(5,-2,2,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle='#000';ctx.lineWidth=2;ctx.beginPath();ctx.arc(0,5,5,0,Math.PI);ctx.stroke();
  }else if(t.includes('bat')){
    ctx.fillStyle='#2c2c54';ctx.beginPath();ctx.ellipse(0,0,10,12,0,0,Math.PI*2);ctx.fill();
    const wf=Math.sin(animTime*8)*0.5+0.5;
    ctx.save();ctx.rotate(-wf*0.6);ctx.fillStyle='#2c2c54';ctx.beginPath();ctx.ellipse(-16,0,14,6,0,0,Math.PI*2);ctx.fill();ctx.restore();
    ctx.save();ctx.rotate(wf*0.6);ctx.fillStyle='#2c2c54';ctx.beginPath();ctx.ellipse(16,0,14,6,0,0,Math.PI*2);ctx.fill();ctx.restore();
    ctx.fillStyle='#e74c3c';ctx.beginPath();ctx.arc(-3,-3,2,0,Math.PI*2);ctx.arc(3,-3,2,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#fff';ctx.beginPath();ctx.moveTo(-3,3);ctx.lineTo(-1,7);ctx.lineTo(1,3);ctx.fill();
    ctx.beginPath();ctx.moveTo(-1,3);ctx.lineTo(1,7);ctx.lineTo(3,3);ctx.fill();
  }else if(t.includes('goblin')){
    ctx.fillStyle='#27ae60';ctx.fillRect(-10,-20,20,28);ctx.fillStyle='#229954';ctx.fillRect(-10,-20,20,4);
    ctx.fillStyle='#2ecc71';ctx.beginPath();ctx.arc(0,-26,10,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#27ae60';ctx.beginPath();ctx.moveTo(-10,-28);ctx.lineTo(-16,-32);ctx.lineTo(-10,-24);ctx.fill();
    ctx.beginPath();ctx.moveTo(10,-28);ctx.lineTo(16,-32);ctx.lineTo(10,-24);ctx.fill();
    ctx.fillStyle='#ff0';ctx.beginPath();ctx.arc(-3,-26,2.5,0,Math.PI*2);ctx.arc(3,-26,2.5,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#000';ctx.beginPath();ctx.arc(-3,-26,1,0,Math.PI*2);ctx.arc(3,-26,1,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle='#000';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(0,-22,3,0,Math.PI);ctx.stroke();
    ctx.fillStyle='#8B4513';ctx.fillRect(10,-10,3,18);ctx.fillStyle='#aaa';ctx.fillRect(8,-12,7,4);
  }else if(t.includes('golem')){
    ctx.fillStyle='#7f8c8d';ctx.fillRect(-14,-22,28,30);
    ctx.fillStyle='#95a5a6';ctx.fillRect(-14,-22,28,4);ctx.fillRect(-14,-10,28,3);
    ctx.strokeStyle='#555';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(-8,-18);ctx.lineTo(-4,-8);ctx.lineTo(-8,2);ctx.stroke();
    ctx.beginPath();ctx.moveTo(6,-16);ctx.lineTo(10,-6);ctx.stroke();
    ctx.fillStyle='#7f8c8d';ctx.fillRect(-8,-30,16,10);
    ctx.fillStyle='#e74c3c';ctx.fillRect(-5,-28,3,3);ctx.fillRect(2,-28,3,3);
  }else if(t.includes('dragon')){
    ctx.fillStyle='#e74c3c';ctx.beginPath();ctx.ellipse(0,0,16,14,0,0,Math.PI*2);ctx.fill();
    const wf2=Math.sin(animTime*4)*0.3+0.5;
    ctx.save();ctx.rotate(-wf2);ctx.fillStyle='#c0392b';ctx.beginPath();ctx.ellipse(-18,-4,14,5,0,0,Math.PI*2);ctx.fill();ctx.restore();
    ctx.save();ctx.rotate(wf2);ctx.fillStyle='#c0392b';ctx.beginPath();ctx.ellipse(18,-4,14,5,0,0,Math.PI*2);ctx.fill();ctx.restore();
    ctx.fillStyle='#e74c3c';ctx.beginPath();ctx.arc(0,-16,8,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#8B4513';ctx.beginPath();ctx.moveTo(-3,-22);ctx.lineTo(-5,-28);ctx.lineTo(-1,-22);ctx.fill();
    ctx.beginPath();ctx.moveTo(3,-22);ctx.lineTo(5,-28);ctx.lineTo(1,-22);ctx.fill();
    ctx.fillStyle='#ff0';ctx.beginPath();ctx.arc(-3,-16,2,0,Math.PI*2);ctx.arc(3,-16,2,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#000';ctx.beginPath();ctx.arc(-3,-16,1,0,Math.PI*2);ctx.arc(3,-16,1,0,Math.PI*2);ctx.fill();
    // Fire breath glow
    if(attacking){ctx.fillStyle='rgba(255,100,0,0.3)';ctx.beginPath();ctx.arc(-12,-12,8,0,Math.PI*2);ctx.fill()}
  }else if(t.includes('wraith')||t.includes('shadow')){
    const ga=Math.sin(animTime*2)*0.15+0.7;ctx.globalAlpha=ga;
    ctx.fillStyle=t.includes('shadow')?'#2c3e50':'#ecf0f1';
    ctx.beginPath();ctx.arc(0,-8,14,Math.PI,0);ctx.lineTo(14,10);ctx.lineTo(10,6);ctx.lineTo(6,10);ctx.lineTo(2,6);ctx.lineTo(-2,10);ctx.lineTo(-6,6);ctx.lineTo(-10,10);ctx.lineTo(-14,10);ctx.closePath();ctx.fill();
    ctx.fillStyle=t.includes('shadow')?'#e74c3c':'#000';ctx.beginPath();ctx.arc(-4,-10,2,0,Math.PI*2);ctx.arc(4,-10,2,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=1;
  }else if(t.includes('crystal')||t.includes('titan')||t.includes('boss')){
    ctx.fillStyle='#9b59b6';ctx.beginPath();ctx.arc(0,0,22,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#8e44ad';ctx.beginPath();ctx.arc(0,3,22,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#bd7ee';
    for(let a=0;a<8;a++){const ang=a*Math.PI/4+animTime*0.5;const sx=Math.cos(ang)*22,sy=Math.sin(ang)*22;ctx.save();ctx.translate(sx,sy);ctx.rotate(ang);ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(10,-5);ctx.lineTo(10,5);ctx.fill();ctx.restore()}
    ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(-5,-3,3,0,Math.PI*2);ctx.arc(5,-3,3,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#e74c3c';ctx.beginPath();ctx.arc(-5,-3,1.5,0,Math.PI*2);ctx.arc(5,-3,1.5,0,Math.PI*2);ctx.fill();
    // Glow aura
    const ag=Math.sin(animTime*2)*0.2+0.3;ctx.globalAlpha=ag;ctx.fillStyle='#9b59b6';ctx.beginPath();ctx.arc(0,0,30,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;
  }else{
    ctx.fillStyle='#e67e22';ctx.beginPath();ctx.arc(0,-4,12,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#e74c3c';ctx.beginPath();ctx.arc(0,0,10,0,Math.PI*2);ctx.fill();
    const ff=Math.sin(animTime*6)*2;ctx.fillStyle='#f39c12';ctx.beginPath();ctx.moveTo(-4,-16);ctx.lineTo(0,-22+ff);ctx.lineTo(4,-16);ctx.fill();
    ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(-3,-4,2,0,Math.PI*2);ctx.arc(3,-4,2,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#000';ctx.beginPath();ctx.arc(-3,-4,1,0,Math.PI*2);ctx.arc(3,-4,1,0,Math.PI*2);ctx.fill();
  }
  ctx.restore();
}

// === BACKGROUND SCENES ===

function drawCavernBg(){
  const g=ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,'#0a0a1a');g.addColorStop(0.5,'#1a1a2e');g.addColorStop(1,'#0f0f1a');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  // Cave ceiling stalactites
  ctx.fillStyle='rgba(40,30,60,0.4)';
  for(let i=0;i<6;i++){const x=(i*W/6+bgOffset%80)-20;ctx.beginPath();ctx.moveTo(x,H*0.28);ctx.lineTo(x+15,H*0.28);ctx.lineTo(x+7,H*0.35);ctx.fill()}
  // Floor
  ctx.fillStyle='rgba(20,15,35,0.6)';ctx.fillRect(0,H*0.7,W,H*0.3);
  ctx.fillStyle='rgba(30,20,50,0.4)';
  for(let i=0;i<4;i++)ctx.fillRect(i*W/4,H*0.72+Math.sin(i)*3,W/4-2,4);
  // Glowing crystals
  const crystals=[[0.1,0.6,8,'#4dd0e1'],[0.85,0.55,6,'#ce93d8'],[0.2,0.75,5,'#80cbc4'],[0.7,0.8,7,'#7c4dff'],[0.5,0.5,4,'#ffd54f']];
  for(const[cx,cy,sz,col]of crystals){
    const x=W*cx,y=H*cy;const glow=0.3+Math.sin(animTime+cx*10)*0.15;
    ctx.globalAlpha=glow;ctx.fillStyle=col;ctx.beginPath();ctx.moveTo(x,y-sz);ctx.lineTo(x-sz/2,y);ctx.lineTo(x+sz/2,y);ctx.closePath();ctx.fill();
    // Glow
    ctx.globalAlpha=glow*0.3;ctx.beginPath();ctx.arc(x,y-sz/2,sz*1.5,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=1;
  }
  // Floating dust particles
  for(let i=0;i<25;i++){
    const px=(i*37+animTime*15)%(W+20)-10;
    const py=(i*53+animTime*8)%H;
    const pa=0.15+Math.sin(animTime+i)*0.1;
    ctx.globalAlpha=pa;ctx.fillStyle='rgba(180,180,255,1)';ctx.beginPath();ctx.arc(px,py,1.2,0,Math.PI*2);ctx.fill();
  }
  ctx.globalAlpha=1;
}

function drawRoomTransition(){
  if(roomTrans<=0)return;
  ctx.fillStyle=`rgba(0,0,0,${roomTrans})`;
  ctx.fillRect(0,0,W,H);
}

// === CHEST ANIMATION ===

function drawChest(x,y){
  ctx.save();ctx.translate(x,y);
  const w=30,h=24;
  // Chest base
  ctx.fillStyle='#8B4513';ctx.fillRect(-w/2,-h/2,w,h);
  ctx.fillStyle='#a0522d';ctx.fillRect(-w/2,-h/2,w,4);
  // Gold trim
  ctx.fillStyle='#ffd700';ctx.fillRect(-w/2,-h/2,w,2);ctx.fillRect(-w/2,h/2-2,w,2);
  ctx.fillRect(-1,-h/2,2,h); // vertical trim
  // Lock
  ctx.fillStyle='#ffd700';ctx.fillRect(-3,-2,6,6);
  ctx.fillStyle='#000';ctx.fillRect(-1,0,2,3);
  // Lid opening
  if(chestOpen){
    const lidAng=chestAnim*Math.PI/3;
    ctx.save();ctx.translate(0,-h/2);ctx.rotate(-lidAng);
    ctx.fillStyle='#8B4513';ctx.fillRect(-w/2,-8,w,8);
    ctx.fillStyle='#ffd700';ctx.fillRect(-w/2,-8,w,2);
    // Light rays
    ctx.globalAlpha=0.3+Math.sin(animTime*5)*0.1;
    ctx.fillStyle='#ffd700';
    for(let a=-2;a<=2;a++){ctx.save();ctx.rotate(a*0.3);ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(-20,-40);ctx.lineTo(20,-40);ctx.fill();ctx.restore()}
    ctx.globalAlpha=1;
    ctx.restore();
    // Gold coins flying out
    if(chestAnim<1){
      for(let i=0;i<10;i++){
        const cy=-h/2-chestAnim*40-i*5;
        const cx=Math.sin(animTime*3+i)*15;
        ctx.fillStyle='#ffd700';ctx.beginPath();ctx.arc(cx,cy,3,0,Math.PI*2);ctx.fill();
      }
    }
  }
  ctx.restore();
}

// === BOSS INTRO ===

function drawBossIntro(){
  if(bossIntro<=0)return;
  ctx.fillStyle=`rgba(0,0,0,${bossIntro*0.8})`;
  ctx.fillRect(0,0,W,H);
  if(bossIntro>0.2){
    const f=Math.min(1,(bossIntro-0.2)*1.5);
    const zoom=1+bossZoom*0.3;
    ctx.globalAlpha=f;
    ctx.save();ctx.translate(W/2,H/2);ctx.scale(zoom,zoom);
    ctx.fillStyle='#e74c3c';ctx.font='bold 32px system-ui';ctx.textAlign='center';
    ctx.strokeStyle='#000';ctx.lineWidth=5;
    ctx.strokeText('BOSS BATTLE',0,-10);
    ctx.fillText('BOSS BATTLE',0,-10);
    ctx.font='bold 14px system-ui';ctx.fillStyle='#ffd54f';
    ctx.strokeText('Crystal Titan approaches...',0,20);
    ctx.fillText('Crystal Titan approaches...',0,20);
    // Warning stripes
    ctx.fillStyle='rgba(255,0,0,0.3)';
    for(let i=-3;i<3;i++)ctx.fillRect(-W,i*15-5,W,8);
    ctx.restore();
    ctx.globalAlpha=1;
  }
}

// === PARTICLES & EFFECTS ===

function spawnParticles(x,y,color,count){
  for(let i=0;i<count;i++){
    const ang=Math.random()*Math.PI*2;const spd=2+Math.random()*5;
    particles.push({x,y,vx:Math.cos(ang)*spd,vy:Math.sin(ang)*spd-1,life:1,color,size:2+Math.random()*4});
  }
}
function spawnDmg(x,y,amount,who){
  dmgNums.push({x,y,vy:-2,life:1,txt:'-'+amount,color:who==='player'?'#ff5252':'#69f0ae',size:18+Math.min(amount,20)});
}
function spawnHeal(x,y,amount){
  dmgNums.push({x,y,vy:-2,life:1,txt:'+'+amount,color:'#2ecc71',size:16});
}

function drawStreakFire(){
  if(streakFire.length===0)return;
  for(const f of streakFire){
    ctx.globalAlpha=f.life*0.7;ctx.fillStyle=f.color;
    ctx.beginPath();ctx.arc(f.x,f.y,f.size*(1+Math.sin(animTime*15)*0.3),0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=f.life;ctx.fillStyle='rgba(255,200,0,'+f.life*0.3+')';
    ctx.beginPath();ctx.arc(f.x,f.y,f.size*2,0,Math.PI*2);ctx.fill();
  }
  ctx.globalAlpha=1;
}
function drawSpears(){
  if(spearTrails.length===0)return;
  for(const s of spearTrails){
    ctx.globalAlpha=s.life;ctx.fillStyle=s.color;
    ctx.fillRect(s.x-1,s.y-12,2,20);
  }
  ctx.globalAlpha=1;
}
function drawGoldRain(){
  for(const g of goldRain){
    ctx.globalAlpha=g.life;ctx.fillStyle=g.color;
    ctx.beginPath();ctx.arc(g.x,g.y,g.size,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=g.life*0.5;ctx.beginPath();ctx.arc(g.x,g.y,g.size*1.5,0,Math.PI*2);ctx.fill();
  }
  ctx.globalAlpha=1;
}
function drawAttackTrail(){
  for(const t of attackTrail){
    ctx.globalAlpha=t.life*0.4;ctx.fillStyle=t.color;
    ctx.fillRect(t.x-2,t.y-15,4,30);
  }
  ctx.globalAlpha=1;
}
function drawLevelUpText(){
  if(levelUpTextLife<=0)return;
  const lt=levelUpTextLife;
  ctx.globalAlpha=lt;
  ctx.font='bold 32px system-ui';ctx.textAlign='center';
  const scl=1+(1-lt)*0.5;
  ctx.save();ctx.translate(W*2, H*0.3);ctx.scale(scl,scl);
  ctx.strokeStyle='#000';ctx.lineWidth=5;
  ctx.strokeText(levelUpText,0,0);
  ctx.fillStyle='#ce93d8';ctx.fillText(levelUpText,0,0);
  ctx.restore();
  ctx.globalAlpha=1;
}
function drawParticles(){
  for(let i=particles.length-1;i>=0;i--){
    const p=particles[i];p.x+=p.vx;p.y+=p.vy;p.vy+=0.15;p.life-=0.02;
    if(p.life<=0){particles.splice(i,1);continue}
    ctx.globalAlpha=p.life;ctx.fillStyle=p.color;ctx.beginPath();ctx.arc(p.x,p.y,p.size*p.life,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=1;
  }
}
function drawDmgNums(){
  for(let i=dmgNums.length-1;i>=0;i--){
    const d=dmgNums[i];d.y+=d.vy;d.vy*=0.95;d.life-=0.015;
    if(d.life<=0){dmgNums.splice(i,1);continue}
    ctx.globalAlpha=d.life;ctx.fillStyle=d.color;ctx.font='bold '+d.size+'px system-ui';
    ctx.textAlign='center';ctx.strokeStyle='#000';ctx.lineWidth=3;
    ctx.strokeText(d.txt,d.x,d.y);ctx.fillText(d.txt,d.x,d.y);
    ctx.globalAlpha=1;
  }
}
function drawFlash(){
  if(flashAlpha>0){ctx.fillStyle=flashColor;ctx.globalAlpha=flashAlpha;ctx.fillRect(0,0,W,H);ctx.globalAlpha=1;flashAlpha-=0.04}
  if(critFlash>0){ctx.fillStyle='#fff';ctx.globalAlpha=critFlash*0.3;ctx.fillRect(0,0,W,H);ctx.globalAlpha=1}
}

// === MAIN GAME LOOP ===

function loop(){
  animTime+=0.016;
  let ox=0,oy=0;
  if(shakeTime>0){shakeTime--;ox=(Math.random()-0.5)*shakeMag;oy=(Math.random()-0.5)*shakeMag;shakeMag*=0.88}
  if(roomTrans>0){roomTrans-=0.04;if(roomTrans<0)roomTrans=0}
  if(chestAnim>0&&chestOpen){chestAnim=Math.min(1,chestAnim+0.03)}
  if(bossIntro>0){bossIntro-=0.008;if(bossIntro<0)bossIntro=0}
  if(attackAnim>0){attackAnim-=0.05;if(attackAnim<0)attackAnim=0}
  let deathAnim=0;
  if(hitStop>0){hitStop-=0.03;if(hitStop<0)hitStop=0;animTime-=0.016}
  if(critFlash>0){critFlash-=0.05;if(critFlash<0)critFlash=0}
  if(bossZoom>0){bossZoom-=0.01;if(bossZoom<0)bossZoom=0}
  if(walkAnim>0){walkAnim-=0.02;if(walkAnim<0)walkAnim=0}
  if(potionAnim>0){potionAnim-=0.02}
  if(deathAnim>0){deathAnim+=0.04;if(deathAnim>1)deathAnim=1}
  if(monsterDeath>0){monsterDeath-=0.02;if(monsterDeath<0)monsterDeath=0}
  if(levelUpTextLife>0){levelUpTextLife-=0.015;if(levelUpTextLife<0)levelUpTextLife=0}
  if(streakFire.length>0){streakFire=streakFire.filter(f=>f.life>0);streakFire.forEach(f=>{f.y-=1;f.life-=0.02;f.x+=Math.sin(animTime*10)*2})}
  if(goldRain.length>0){goldRain=goldRain.filter(g=>g.life>0);goldRain.forEach(g=>{g.y+=g.vy;g.vy+=0.2;g.life-=0.02})}
  if(attackTrail.length>0){attackTrail=attackTrail.filter(t=>t.life>0);attackTrail.forEach(t=>{t.life-=0.035})}
  if(spearTrails.length>0){spearTrails=spearTrails.filter(t=>t.life>0);spearTrails.forEach(t=>{t.life-=0.025})}
  bgOffset+=0.5;

  ctx.save();ctx.translate(ox,oy);
  drawCavernBg();

  const cy=H*0.45;
  if(gameMode==='battle'||gameMode==='boss'){
    drawBattleScene(cy);
  }else if(gameMode==='explore'||gameMode==='shop'||gameMode==='puzzle'||gameMode==='title'||gameMode==='treasure'||gameMode==='rest'){
    // Player standing center
    drawPlayer(W*0.5,cy,2,false,false);
    // Treasure chest on treasure rooms
    if(gameMode==='treasure'||(state&&state.message_type==='treasure')){
      if(!chestOpen){chestOpen=true;chestAnim=0;sfxTreasure()}
      drawChest(W*0.5,cy-50);
    }
  }else if(gameMode==='explore'&&potionAnim>0){
    drawPlayer(W*0.5,cy,2,false,false);
    // Potion bottle above player
    ctx.save();ctx.translate(W*0.5,cy-40-potionAnim*20);
    ctx.fillStyle='#e74c3c';ctx.beginPath();ctx.ellipse(0,0,8,10,0,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#c0392b';ctx.fillRect(-3,-12,6,4);
    // Sparkles
    for(let j=0;j<5;j++){const sa=animTime*3+j*1.2;ctx.globalAlpha=potionAnim*0.5;ctx.fillStyle='#69f0ae';ctx.beginPath();ctx.arc(Math.cos(sa)*15,Math.sin(sa)*15,2,0,Math.PI*2);ctx.fill()}
    ctx.globalAlpha=1;ctx.restore();
    if(potionAnim>0)potionAnim-=0.02;
  }else if(gameMode==='gameover'){
    // Player lying down
    ctx.save();ctx.translate(W*0.5,cy);ctx.scale(2,2);ctx.rotate(Math.PI/2);
    ctx.globalAlpha=0.5;drawPlayer(0,0,1,false,false);ctx.globalAlpha=1;ctx.restore();
  }

  drawStreakFire();drawGoldRain();drawAttackTrail();drawSpears();drawLevelUpText();drawParticles();drawDmgNums();drawFlash();drawBossIntro();drawRoomTransition();
  ctx.restore();
  requestAnimationFrame(loop);
}

function drawBattleScene(cy){
  if(!state||!state.monster)return;
  const px=W*0.25,py=cy;
  const m=state.monster;const mx=W*0.72,my=cy;
  const pHit=lastState&&state.hp<lastState.hp;
  const mHit=lastState&&lastState.monster&&state.monster.hp<lastState.monster.hp;
  const pAttacking=attackAnim>0&&attackAnimWho==='player';
  const mAttacking=attackAnim>0&&attackAnimWho==='monster';
  drawPlayer(px,py,1.8,pHit,pAttacking);
  const mType=m.name.toLowerCase().split(' ')[0];
  if(monsterDeath>0){ctx.globalAlpha=monsterDeath;ctx.translate(0,monsterDeath*20);drawMonster(mx,my,1.8,mType,mHit,mAttacking);ctx.globalAlpha=1;}else{drawMonster(mx,my,1.8,mType,mHit,mAttacking);}
  // Monster HP bar
  const mPct=Math.max(0,m.hp/m.max_hp);
  ctx.fillStyle='rgba(0,0,0,0.7)';ctx.fillRect(W*0.5,cy-75,W*0.45,20);
  ctx.fillStyle=gameMode==='boss'?'#ff4444':'#ff8a80';ctx.font='bold 11px system-ui';ctx.textAlign='center';
  ctx.fillText(m.name+(gameMode==='boss'?' - BOSS':''),W*0.72,cy-63);
  ctx.fillStyle='#333';ctx.fillRect(W*0.52,cy-55,W*0.4,5);
  ctx.fillStyle=mPct>0.5?(gameMode==='boss'?'#e74c3c':'#e74c3c'):mPct>0.25?'#f39c12':'#c0392b';
  ctx.fillRect(W*0.52,cy-55,W*0.4*mPct,5);
}

loop();

// === STATE MANAGEMENT ===

async function api(action,params={}){
  initAudio();
  const body={action,sid:SID,...params};
  try{
    const res=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await res.json();
    if(data.sid)SID=data.sid;
    if(data.state){onStateChange(state,data.state);state=data.state;render()}
  }catch(e){console.error('API error:',e)}
}

function onStateChange(prev,curr){
  if(!prev){gameMode=curr.mode||'explore';return}
  // Mode change = room transition
  if(curr.mode!==prev.mode){roomTrans=1}
  // Player damage
  if(curr.hp<prev.hp){
    shakeTime=10;shakeMag=10;flashColor='#ff0000';flashAlpha=0.4;
    spawnDmg(W*0.25,H*0.38,prev.hp-curr.hp,'player');
    spawnParticles(W*0.25,H*0.42,'#ff5252',25);sfxHurt();
    attackAnim=1;attackAnimWho='monster';
  }
  // Monster damage
  if(prev.monster&&curr.monster&&curr.monster.hp<prev.monster.hp){
    spawnDmg(W*0.72,H*0.38,prev.monster.hp-curr.monster.hp,'monster');
    spawnParticles(W*0.72,H*0.42,'#ffd54f',30);sfxHit();
    attackAnim=1;attackAnimWho='player';
    for(let i=0;i<8;i++)attackTrail.push({x:W*0.25+i*12,y:H*0.45,life:1,color:curr.streak>=3?'#ff416c':'#4dd0e1'});
    for(let i=0;i<12;i++)spearTrails.push({x:W*0.25+(i*18),y:H*0.42+Math.sin(i)*5,life:1,color:'#4dd0e1'});
  }
  if(prev.monster&&(!curr.monster||curr.mode!=='battle'&&curr.mode!=='boss')&&prev.mode==='battle'){
    monsterDeath=1;spawnParticles(W*0.72,H*0.42,'#ff5252',20);spawnParticles(W*0.72,H*0.42,'#ffd54f',15);
    for(let i=0;i<15;i++)goldRain.push({x:W*0.72+(Math.random()-0.5)*40,y:H*0.4,vy:-1-Math.random()*4,size:2+Math.random()*3,color:'#ffd700',life:1});
  }
  // Level up
  if(curr.level>(prev?.level||1)){
    flashColor='#9b59b6';flashAlpha=0.5;spawnParticles(W*0.5,H*0.5,'#ce93d8',30);sfxLevelUp();
  }
  // Treasure
  if(curr.streak>=(prev?.streak||0)+1&&curr.streak>=3){
    for(let i=0;i<8;i++){streakFire.push({x:W*0.25+(Math.random()-0.5)*30,y:H*0.3+Math.random()*20,size:3+Math.random()*3,life:1,color:curr.streak>=5?'#ff416c':'#ff9800'})}
  }
  if(curr.message_type==='treasure'){flashColor='#ffd700';flashAlpha=0.3;spawnParticles(W*0.5,H*0.4,'#ffd54f',20);sfxTreasure();chestOpen=true;chestAnim=0;for(let i=0;i<25;i++){goldRain.push({x:W/2+(Math.random()-0.5)*80,y:H*0.35,vy:-1-Math.random()*5,size:2+Math.random()*4,color:'#ffd700',life:1})}}
  // Victory
  if(curr.message_type==='victory'&&curr.mode!=='boss'){flashColor='#ffd700';flashAlpha=0.3;sfxCorrect()}
  if(curr.story_stage>=5&&prev.story_stage<5){
    sfxVictory();
    for(let i=0;i<50;i++){goldRain.push({x:W*Math.random(),y:H*0.3,vy:1+Math.random()*3,size:2+Math.random()*4,color:'#ffd700',life:1})}
    victoryStats=['Battles: '+curr.battles_won,'Puzzles: '+curr.puzzles_solved,'Math: '+curr.math_solved,'Streak: '+curr.best_streak];
  }
  // Correct answer
  if(prev.mode==='battle'&&curr.mode==='explore'&&curr.message_type==='victory'){sfxVictory()}
  // Wrong answer
  if(curr.message_type==='miss'&&prev.mode==='battle'){sfxWrong()}
  // Boss intro
  if(curr.mode==='boss'&&prev.mode!=='boss'){bossIntro=1;sfxBoss();bossZoom=1}
  // Death
  if(curr.mode==='gameover'){sfxDeath();shakeTime=20;shakeMag=15;flashColor='#ff0000';flashAlpha=0.6}
  // Shop enter
  if(curr.mode==='shop'&&prev.mode!=='shop'){sfxShop()}
  // Heal
  if(curr.hp>prev.hp&&curr.message_type==='heal'){spawnHeal(W*0.25,H*0.38,curr.hp-prev.hp);sfxCorrect();potionAnim=1;for(let i=0;i<15;i++)spawnParticles(W*0.5,H*0.4,'#69f0ae',1)}
  gameMode=curr.mode||'explore';
}

function render(){
  if(!state){
    gameMode='title';
    ui.innerHTML=`<div class="panel title-screen clickable">
<h2>Start Your Adventure</h2>
<p>Enter the Crystal Caverns! Battle monsters with math, solve coding puzzles, and claim the Knowledge Crystal!</p>
<input type="text" id="name" placeholder="Your hero name" value="">
<select id="diff"><option value="easy">Adventurer (8-10)</option><option value="normal" selected>Hero (10-13)</option><option value="hard">Legend (13-15)</option></select>
<button class="btn btn-primary" onclick="api('start',{name:document.getElementById('name').value||'Hero',difficulty:document.getElementById('diff').value})">Begin Adventure</button>
</div>`;
    return;
  }
  const hpPct=(state.hp/state.max_hp)*100;
  const hpCls=hpPct>50?'':hpPct>25?'mid':'low';
  let hud=`<div class="hud clickable">`;
  hud+=`<span class="chip">⭐${state.level}</span>`;
  hud+=`<span class="chip">XP ${state.xp}/${state.xp_to_next}</span>`;
  hud+=`<span class="chip">R${state.rooms_cleared+1}</span>`;
  hud+=`<span class="chip hp">HP ${state.hp}/${state.max_hp}<span class="hp-mini"><span class="hp-mini-fill ${hpCls}" style="width:${Math.max(0,hpPct)}%"></span></span></span>`;
  hud+=`</div>`;
  hud+=`<div class="hud2 clickable">`;
  hud+=`<span class="chip">ATK${state.attack}</span>`;
  hud+=`<span class="chip">PTN${state.potions}</span>`;
  hud+=`<span class="chip">GEM${state.gems||0}</span>`;
  if(state.streak>0)hud+=`<span class="chip">🔥${state.streak}</span>`;
  hud+=`</div>`;
  let panel='';
  if(state.message)panel+=`<div class="msg msg-${state.message_type}">${state.message}</div>`;
  if(state.mode==='explore'&&state.rooms_cleared<3){
    const stories=[{"stage": 0, "title": "🏔️ The Entrance", "text": "You stand at the mouth of the Crystal Caverns. Legends say ancient knowledge is buried deep within — math formulas carved in stone, code etched in crystal. Monsters guard the treasures. Only the clever may pass."}, {"stage": 1, "title": "🔵 The Blue Caverns", "text": "You descend into the first chamber. Stalactites glow with faint blue light. Slimes and bats skitter in the shadows."}, {"stage": 2, "title": "🟢 The Green Tunnels", "text": "Deeper now. The crystals shift from blue to green. Goblins patrol these tunnels. A locked door blocks the path — it needs code to open."}, {"stage": 3, "title": "❄️ The Frozen Depths", "text": "The temperature drops. Ice formations glitter on the walls. Stronger monsters dwell here."}, {"stage": 4, "title": "💎 THE CRYSTAL TITAN", "text": "You've reached the deepest chamber. A massive figure towers over you — the Crystal Titan. 'Prove your mind is worthy,' it booms."}, {"stage": 5, "title": "👑 VICTORY", "text": "The Crystal Titan crumbles into sparkling dust. The Knowledge Crystal floats toward you. You grasp it. You are the Champion of the Crystal Caverns!"}];
    const ss=stories.find(s=>s.stage===state.story_stage);
    if(ss)panel+=`<div class="story-box"><div class="story-t">${ss.title}</div><div class="story-x">${ss.text}</div></div>`;
  }
  if(state.mode==='explore'||state.mode==='rest'||state.mode==='treasure'){
    if(state.story_stage>=5){
      panel+=`<div style="text-align:center;padding:10px"><div style="color:#ffd54f;font-size:1.15em;font-weight:bold">CHAMPION!</div><p style="font-size:0.78em;color:#999;margin:4px">Battles:${state.battles_won} Puzzles:${state.puzzles_solved} Math:${state.math_solved}</p><p style="font-size:0.78em;color:#999">Best Streak:${state.best_streak}</p><button class="btn btn-primary clickable" onclick="SID=null;state=null;render()">Play Again</button></div>`;
    }else{
      panel+=`<button class="btn btn-primary clickable" onclick="api('explore')">Explore Next Room</button>`;
      panel+=`<button class="btn btn-success clickable" onclick="api('potion')">Use Potion (${state.potions})</button>`;
    }
  }else if(state.mode==='battle'||state.mode==='boss'){
    const p=state.current_problem;
    panel+=`<div class="math-box"><div class="math-cat">${p.cat}</div><div class="math-q">${p.q}</div></div>`;
    panel+=`<input type="text" id="answer" placeholder="Your answer..." onkeypress="if(event.key==='Enter')doAnswer()">`;
    panel+=`<button class="btn btn-danger clickable" onclick="doAnswer()">Attack!</button>`;
  }else if(state.mode==='puzzle'){
    const p=state.current_puzzle;
    panel+=`<div style="font-size:0.85em;color:#80cbc4;font-weight:bold;text-align:center">Coding Puzzle (Level ${p.level})</div>`;
    panel+=`<p style="font-size:0.78em;text-align:center">${p.prompt}</p>`;
    panel+=`<div class="code-block">${p.code}</div>`;
    panel+=`<p style="font-size:0.68em;color:#666;text-align:center">Fill the blank (____)</p>`;
    panel+=`<input type="text" id="answer" placeholder="Fill the blank..." onkeypress="if(event.key==='Enter')doAnswer()">`;
    panel+=`<button class="btn btn-primary clickable" onclick="doAnswer()">Submit</button>`;
  }else if(state.mode==='shop'){
    panel+=`<div style="text-align:center;font-size:0.9em;color:#80cbc4;margin:3px">Shop</div>`;
    panel+=`<div class="shop-grid">`;
    panel+=`<div class="shop-item clickable" onclick="doShop('1')"><div class="nm">Potion</div><div class="pr">10 gems</div></div>`;
    panel+=`<div class="shop-item clickable" onclick="doShop('2')"><div class="nm">ATK +3</div><div class="pr">20 gems</div></div>`;
    panel+=`<div class="shop-item clickable" onclick="doShop('3')"><div class="nm">MaxHP +15</div><div class="pr">30 gems</div></div>`;
    panel+=`<div class="shop-item clickable" onclick="doShop('4')" style="background:rgba(80,80,80,0.2)"><div class="nm">Leave</div><div class="pr">free</div></div>`;
    panel+=`</div>`;
  }else if(state.mode==='gameover'){
    panel+=`<div style="text-align:center;padding:12px"><div style="font-size:1.3em;color:#ff5252;font-weight:bold">GAME OVER</div><p style="font-size:0.78em;color:#999;margin:3px">${state.name} fell in the Crystal Caverns...</p><p style="font-size:0.78em;color:#999">Level ${state.level} | Battles:${state.battles_won} | Puzzles:${state.puzzles_solved}</p><p style="font-size:0.78em;color:#999">Best Streak:${state.best_streak}</p><button class="btn btn-primary clickable" onclick="SID=null;state=null;render()">Play Again</button></div>`;
  }
  ui.innerHTML=hud+`<div class="panel clickable">${panel}</div>`;
  const ans=document.getElementById('answer');
  if(ans)setTimeout(()=>ans.focus(),100);
}

function doAnswer(){const v=document.getElementById('answer').value;if(v)api('answer',{answer:v})}
function doShop(c){api('shop',{choice:c})}
render();
</script>
</body>
</html>
'''

def load_html():
    """Prefer the external final_frontend.html (kept in sync with upgrades); fall back to embedded."""
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'final_frontend.html')
    if os.path.exists(p):
        try:
            return open(p, encoding='utf-8').read()
        except Exception:
            pass
    return HTML_PAGE

# ═══════════════════════════════════════════════════════════
#  HTTP SERVER
# ═══════════════════════════════════════════════════════════

class GameHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(load_html().encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                req = json.loads(body)
            except:
                req = {}

            action = req.get('action')
            sid = req.get('sid')
            g = GAMES.get(sid) if sid else None
            resp = {}

            if action == 'start':
                sid, g = action_start(req.get('name'), req.get('difficulty'), req.get('class'))
                resp['sid'] = sid
                resp['state'] = g
            elif action == 'explore' and g:
                g = action_explore(g)
                resp['state'] = g
            elif action == 'answer' and g:
                g = action_answer(g, req.get('answer', ''), req.get('choice'), req.get('response_time'))
                resp['state'] = g
            elif action == 'potion' and g:
                g = action_potion(g)
                resp['state'] = g
            elif action == 'special' and g:
                g = action_special(g)
                resp['state'] = g
            elif action == 'fork' and g:
                g = action_fork(g, req.get('side', 'left'))
                resp['state'] = g
            elif action == 'defend' and g:
                g = action_defend(g)
                resp['state'] = g
            elif action == 'shop' and g:
                g = action_shop(g, req.get('choice', '4'))
                resp['state'] = g
            elif action == 'restore':
                st=(req.get('state') or (req.get('params') or {}).get('state'))
                if st and isinstance(st,dict):
                    sid,g=action_restore(st)
                    resp['sid']=sid
                    resp['state']=g
                    try:localStorage_ignore=0
                    except:pass
                else:
                    resp['error']='No state'
            elif action == 'resume':
                if g:
                    resp['sid'] = sid
                    resp['state'] = g
                else:
                    resp['error'] = 'No saved game'
            else:
                resp['error'] = 'Invalid action'

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logs


def main():
    PORT = 8085
    server = HTTPServer(('0.0.0.0', PORT), GameHandler)
    print(f"CodeQuest server running!")
    print(f"Open: http://localhost:{PORT}")
    print(f"Share: http://YOUR_IP:{PORT}")
    print(f"Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        server.shutdown()

if __name__ == '__main__':
    main()
