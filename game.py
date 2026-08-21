#!/usr/bin/env python3
"""
CodeQuest — The Crystal Caverns
A story-driven adventure game where kids battle monsters with math
and solve coding puzzles to unlock doors and treasure.

Runs in terminal. Uses rich library for colors and panels.
No external dependencies beyond rich + stdlib.

Players:
  - Battle monsters by solving math problems (arithmetic, fractions, algebra)
  - Solve coding puzzles to unlock doors (fill in the blank Python)
  - Collect gems, level up, beat the boss
  - Ages 10-15, adjustable difficulty

Usage:
  python3 game.py
  python3 game.py --difficulty easy    # ages 8-10
  python3 game.py --difficulty hard    # ages 13-15
"""

import random
import time
import os
import json
import sys
from dataclasses import dataclass, field
from enum import Enum

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.columns import Columns
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


# ═══════════════════════════════════════════════════════════
#  GAME DATA
# ═══════════════════════════════════════════════════════════

class Difficulty(Enum):
    EASY = "easy"      # ages 8-10
    NORMAL = "normal"  # ages 10-13
    HARD = "hard"      # ages 13-15


DIFFICULTY_CONFIG = {
    Difficulty.EASY: {
        "math_max": 20,
        "allow_negatives": False,
        "allow_fractions": False,
        "algebra_simple": True,
        "code_blank难度": 1,  # fill in single value
        "xp_multiplier": 1.2,
        "label": "Adventurer (ages 8-10)",
    },
    Difficulty.NORMAL: {
        "math_max": 100,
        "allow_negatives": False,
        "allow_fractions": True,
        "algebra_simple": True,
        "code_blank难度": 2,  # fill in expression
        "xp_multiplier": 1.0,
        "label": "Hero (ages 10-13)",
    },
    Difficulty.HARD: {
        "math_max": 500,
        "allow_negatives": True,
        "allow_fractions": True,
        "algebra_simple": False,
        "code_blank难度": 3,  # fill in logic
        "xp_multiplier": 0.8,
        "label": "Legend (ages 13-15)",
    },
}


MONSTERS = [
    {"name": "Slime", "emoji": "🟢", "hp": 20, "atk": 5, "xp": 10, "min_level": 1},
    {"name": "Bat Swarm", "emoji": "🦇", "hp": 30, "atk": 8, "xp": 15, "min_level": 1},
    {"name": "Goblin Scout", "emoji": "👺", "hp": 40, "atk": 10, "xp": 20, "min_level": 2},
    {"name": "Stone Golem", "emoji": "🗿", "hp": 60, "atk": 15, "xp": 30, "min_level": 3},
    {"name": "Fire Imp", "emoji": "🔥", "hp": 50, "atk": 18, "xp": 35, "min_level": 3},
    {"name": "Ice Wraith", "emoji": "👻", "hp": 70, "atk": 20, "xp": 40, "min_level": 4},
    {"name": "Shadow Knight", "emoji": "⚔️", "hp": 90, "atk": 25, "xp": 55, "min_level": 5},
    {"name": "Dragon Whelp", "emoji": "🐉", "hp": 120, "atk": 30, "xp": 70, "min_level": 6},
    {"name": "Crystal Titan", "emoji": "💎", "hp": 200, "atk": 40, "xp": 150, "min_level": 8},
]

CODING_PUZZLES = [
    {
        "level": 1,
        "prompt": "A door sealed by code. The inscription reads:\n'Print the number 42 to open the gate.'",
        "code_template": "print({blank})",
        "answer": "42",
        "hint": "Just type the number 42",
        "explanation": "print() displays whatever you put inside the parentheses.",
    },
    {
        "level": 2,
        "prompt": "A treasure chest locked by code.\n'Create a variable called score with value 100.'",
        "code_template": "{blank} = 100",
        "answer": "score",
        "hint": "Variable names go on the left side of =",
        "explanation": "Variables store data. The name goes left, the value goes right.",
    },
    {
        "level": 3,
        "prompt": "A bridge appears when you solve this:\n'Add 5 and 10, then print the result.'",
        "code_template": "print(5 {blank} 10)",
        "answer": "+",
        "hint": "What symbol means 'add' in Python?",
        "explanation": "The + operator adds numbers together in Python.",
    },
    {
        "level": 4,
        "prompt": "A dark tunnel. The torch code reads:\n'Check if 7 is greater than 3. Print True or False.'",
        "code_template": "print(7 {blank} 3)",
        "answer": ">",
        "hint": "What symbol means 'greater than'?",
        "explanation": "The > operator compares two values. 7 > 3 is True.",
    },
    {
        "level": 5,
        "prompt": "A magic door. The spell requires:\n'Multiply 6 by 7 and print the answer.'",
        "code_template": "print(6 {blank} 7)",
        "answer": "*",
        "hint": "What symbol means 'multiply' in Python?",
        "explanation": "The * operator multiplies numbers. 6 * 7 = 42.",
    },
    {
        "level": 6,
        "prompt": "A locked vault. The code needs:\n'Create a list with three numbers: 1, 2, 3'",
        "code_template": "my_list = {blank}",
        "answer": "[1, 2, 3]",
        "hint": "Lists use square brackets with commas between items",
        "explanation": "Lists store multiple items. Use [ ] with commas: [1, 2, 3]",
    },
    {
        "level": 7,
        "prompt": "The final gate before the boss:\n'Print the length of the word \"dragon\"'",
        "code_template": "print({blank}(\"dragon\"))",
        "answer": "len",
        "hint": "What function tells you how long something is?",
        "explanation": "len() returns the length. len(\"dragon\") = 6.",
    },
    {
        "level": 8,
        "prompt": "The Crystal Titan's seal:\n'Use a for loop to print each number from 0 to 4'\n(Fill in the missing function)",
        "code_template": "for i in {blank}(5):\n    print(i)",
        "answer": "range",
        "hint": "What function generates a sequence of numbers?",
        "explanation": "range(5) generates 0,1,2,3,4. Perfect for loops!",
    },
]

# ═══════════════════════════════════════════════════════════
#  MATH PROBLEM GENERATOR
# ═══════════════════════════════════════════════════════════

def generate_math_problem(difficulty: Difficulty, player_level: int):
    """Generate a math problem scaled to difficulty and player level."""
    cfg = DIFFICULTY_CONFIG[difficulty]
    max_val = cfg["math_max"]
    
    # Problem types unlock as player levels up
    problem_types = ["addition", "subtraction"]
    if player_level >= 2:
        problem_types.append("multiplication")
    if player_level >= 3:
        problem_types.append("division")
    if player_level >= 4 and cfg["algebra_simple"]:
        problem_types.append("algebra")
    if player_level >= 5 and cfg["allow_fractions"]:
        problem_types.append("fractions")
    
    ptype = random.choice(problem_types)
    
    if ptype == "addition":
        a = random.randint(1, max_val)
        b = random.randint(1, max_val)
        return f"What is {a} + {b}?", str(a + b), "Addition"
    
    elif ptype == "subtraction":
        a = random.randint(1, max_val)
        b = random.randint(1, a if not cfg["allow_negatives"] else max_val)
        if not cfg["allow_negatives"]:
            b = min(b, a)
        return f"What is {a} - {b}?", str(a - b), "Subtraction"
    
    elif ptype == "multiplication":
        # Keep numbers reasonable
        a = random.randint(2, min(20, max_val // 5))
        b = random.randint(2, min(15, max_val // 10))
        return f"What is {a} × {b}?", str(a * b), "Multiplication"
    
    elif ptype == "division":
        # Clean division
        b = random.randint(2, 12)
        result = random.randint(2, max_val // b)
        a = b * result
        return f"What is {a} ÷ {b}?", str(result), "Division"
    
    elif ptype == "algebra":
        if cfg["algebra_simple"]:
            # x + 5 = 12, what is x?
            x = random.randint(1, max_val)
            b = random.randint(1, max_val)
            op = random.choice(["+", "-"])
            if op == "+":
                result = x + b
                return f"If x + {b} = {result}, what is x?", str(x), "Algebra"
            else:
                result = x + b
                return f"If x - {b} = {result}, what is x?\n(Think: what minus {b} equals {result}?)", str(result), "Algebra"
        else:
            # 2x + 3 = 15, what is x?
            x = random.randint(2, 20)
            coeff = random.randint(2, 5)
            const = random.randint(1, 10)
            result = coeff * x + const
            return f"If {coeff}x + {const} = {result}, what is x?", str(x), "Algebra"
    
    elif ptype == "fractions":
        # 1/2 + 1/4 = ?
        denominators = [2, 4, 3, 6, 8]
        d1 = random.choice(denominators)
        d2 = random.choice([d for d in denominators if d != d1])
        # Make sure answer is clean
        lcm = d1 * d2 // __gcd(d1, d2)
        n1 = random.randint(1, d1 - 1)
        n2 = random.randint(1, d2 - 1)
        result_num = n1 * (lcm // d1) + n2 * (lcm // d2)
        return (f"What is {n1}/{d1} + {n2}/{d2}?\n"
                f"(Give your answer as a fraction like 3/4)", 
                f"{result_num}/{lcm}", "Fractions")
    
    # Fallback
    a = random.randint(1, max_val)
    b = random.randint(1, max_val)
    return f"What is {a} + {b}?", str(a + b), "Addition"


def __gcd(a, b):
    while b:
        a, b = b, a % b
    return a


# ═══════════════════════════════════════════════════════════
#  PLAYER STATE
# ═══════════════════════════════════════════════════════════

@dataclass
class Player:
    name: str = "Hero"
    hp: int = 100
    max_hp: int = 100
    level: int = 1
    xp: int = 0
    xp_to_next: int = 50
    gems: int = 0
    potions: int = 3
    attack: int = 10
    difficulty: Difficulty = Difficulty.NORMAL
    battles_won: int = 0
    puzzles_solved: int = 0
    math_problems_solved: int = 0
    rooms_cleared: int = 0
    streak: int = 0  # consecutive correct answers
    best_streak: int = 0
    story_stage: int = 0  # 0=start, 1=entering caverns, 2=mid-caverns, 3=deep, 4=boss, 5=victory


# ═══════════════════════════════════════════════════════════
#  SAVE / LOAD
# ═══════════════════════════════════════════════════════════

SAVE_FILE = os.path.expanduser("~/.codequest_save.json")


def save_game(player: Player):
    data = {
        "name": player.name,
        "hp": player.hp,
        "max_hp": player.max_hp,
        "level": player.level,
        "xp": player.xp,
        "xp_to_next": player.xp_to_next,
        "gems": player.gems,
        "potions": player.potions,
        "attack": player.attack,
        "difficulty": player.difficulty.value,
        "battles_won": player.battles_won,
        "puzzles_solved": player.puzzles_solved,
        "math_problems_solved": player.math_problems_solved,
        "rooms_cleared": player.rooms_cleared,
        "streak": player.streak,
        "best_streak": player.best_streak,
        "story_stage": player.story_stage,
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_game() -> Player | None:
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE) as f:
            data = json.load(f)
        p = Player()
        p.name = data.get("name", "Hero")
        p.hp = data.get("hp", 100)
        p.max_hp = data.get("max_hp", 100)
        p.level = data.get("level", 1)
        p.xp = data.get("xp", 0)
        p.xp_to_next = data.get("xp_to_next", 50)
        p.gems = data.get("gems", 0)
        p.potions = data.get("potions", 3)
        p.attack = data.get("attack", 10)
        p.difficulty = Difficulty(data.get("difficulty", "normal"))
        p.battles_won = data.get("battles_won", 0)
        p.puzzles_solved = data.get("puzzles_solved", 0)
        p.math_problems_solved = data.get("math_problems_solved", 0)
        p.rooms_cleared = data.get("rooms_cleared", 0)
        p.streak = data.get("streak", 0)
        p.best_streak = data.get("best_streak", 0)
        p.story_stage = data.get("story_stage", 0)
        return p
    except Exception:
        return None


def delete_save():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)


# ═══════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════

def print_panel(text, title="", style="cyan"):
    if HAS_RICH:
        console.print(Panel(text, title=title, border_style=style, padding=1))
    else:
        if title:
            print(f"\n--- {title} ---")
        print(text)
        print("-" * 40)


def print_text(text, style="white"):
    if HAS_RICH:
        console.print(Text(text, style=style))
    else:
        print(text)


def print_banner():
    banner = """
  ██████╗ ██████╗  ██████╗  ██████╗██████╗ ███████╗██████╗
  ██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔══██╗██╔════╝██╔══██╗
  ██║  ██║██████╔╝██║   ██║██║     ██████╔╝█████╗  ██████╔╝
  ██║  ██║██╔══██╗██║   ██║██║     ██╔══██╗██╔══╝  ██╔══██╗
  ██████╔╝██║  ██║╚██████╔╝╚██████╗██║  ██║███████╗██║  ██║
  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
           The Crystal Caverns  🏔️💎⚔️
    """
    if HAS_RICH:
        console.print(Text(banner, style="bold cyan"))
    else:
        print(banner)


def show_stats(player: Player):
    if HAS_RICH:
        table = Table(show_header=False, border_style="blue", padding=(0, 2))
        table.add_column("Stat", style="bold")
        table.add_column("Value", style="green")
        table.add_row("⭐ Level", str(player.level))
        table.add_row("❤️ HP", f"{player.hp}/{player.max_hp}")
        table.add_row("✨ XP", f"{player.xp}/{player.xp_to_next}")
        table.add_row("💎 Gems", str(player.gems))
        table.add_row("🧪 Potions", str(player.potions))
        table.add_row("⚔️ Attack", str(player.attack))
        table.add_row("🏆 Battles Won", str(player.battles_won))
        table.add_row("🧩 Puzzles Solved", str(player.puzzles_solved))
        table.add_row("🔢 Math Solved", str(player.math_problems_solved))
        table.add_row("🔥 Streak", f"{player.streak} (best: {player.best_streak})")
        console.print(table)
    else:
        print(f"\nLevel: {player.level} | HP: {player.hp}/{player.max_hp} | XP: {player.xp}/{player.xp_to_next}")
        print(f"Gems: {player.gems} | Potions: {player.potions} | ATK: {player.attack}")
        print(f"Battles: {player.battles_won} | Puzzles: {player.puzzles_solved} | Math: {player.math_problems_solved}")
        print(f"Streak: {player.streak} (best: {player.best_streak})")


def show_hp_bar(player: Player, enemy=None):
    if not HAS_RICH:
        return
    bars = []
    p_hp = "█" * max(1, int(player.hp / player.max_hp * 20))
    p_hp_color = "green" if player.hp > player.max_hp * 0.5 else "yellow" if player.hp > player.max_hp * 0.25 else "red"
    bars.append(f"[{p_hp_color}]You: {p_hp}[/] {player.hp}/{player.max_hp}")
    if enemy:
        e_hp = "█" * max(1, int(enemy["hp"] / enemy["max_hp"] * 20))
        bars.append(f"[red]{enemy['name']}: {e_hp}[/] {enemy['hp']}/{enemy['max_hp']}")
    console.print("  ".join(bars))


# ═══════════════════════════════════════════════════════════
#  COMBAT — MATH BATTLES
# ═══════════════════════════════════════════════════════════

def spawn_monster(player_level: int) -> dict:
    available = [m for m in MONSTERS if m["min_level"] <= player_level + 1]
    template = random.choice(available)
    # Scale monster slightly with player level
    scale = 1 + (player_level - template["min_level"]) * 0.15
    return {
        "name": template["name"],
        "emoji": template["emoji"],
        "hp": int(template["hp"] * scale),
        "max_hp": int(template["hp"] * scale),
        "atk": int(template["atk"] * scale),
        "xp": int(template["xp"] * scale),
    }


def math_battle(player: Player, monster: dict) -> bool:
    """
    Battle loop: solve math problems to attack.
    Correct answer = hit monster. Wrong answer = monster hits you.
    First to 0 HP loses.
    Returns True if player wins.
    """
    print_panel(
        f"{monster['emoji']} A wild {monster['name']} appears!\n"
        f"HP: {monster['hp']} | ATK: {monster['atk']}\n"
        f"Solve math problems to attack!",
        title="⚔️ BATTLE!", style="red"
    )
    
    round_num = 0
    while player.hp > 0 and monster["hp"] > 0:
        round_num += 1
        show_hp_bar(player, monster)
        
        # Generate math problem
        question, answer, category = generate_math_problem(player.difficulty, player.level)
        
        print_text(f"\n📜 [{category}] Round {round_num}", style="bold yellow")
        print_text(question, style="white")
        
        # Get player answer
        try:
            user_answer = input("\nYour answer > ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        
        # Check answer
        if user_answer.lower() == answer.lower():
            # Hit!
            damage = player.attack + random.randint(0, 5)
            monster["hp"] -= damage
            player.streak += 1
            player.best_streak = max(player.best_streak, player.streak)
            player.math_problems_solved += 1
            
            # Bonus damage on streak
            if player.streak >= 3:
                bonus = player.streak * 2
                damage += bonus
                monster["hp"] -= bonus
                print_text(f"🔥 STREAK x{player.streak}! +{bonus} bonus damage!", style="bold red")
            
            print_text(f"✅ Correct! You deal {damage} damage!", style="bold green")
            
            if monster["hp"] <= 0:
                break
        else:
            # Miss! Monster attacks
            monster_damage = monster["atk"] + random.randint(0, 3)
            player.hp -= monster_damage
            player.streak = 0
            print_text(f"❌ Wrong! The answer was {answer}.", style="bold red")
            print_text(f"{monster['emoji']} {monster['name']} hits you for {monster_damage}!", style="red")
            
            if player.hp <= 0:
                break
        
        time.sleep(0.5)
    
    # Battle result
    if monster["hp"] <= 0:
        xp_gained = int(monster["xp"] * DIFFICULTY_CONFIG[player.difficulty]["xp_multiplier"])
        gem_chance = random.randint(1, 3)
        player.xp += xp_gained
        player.gems += gem_chance
        player.battles_won += 1
        
        print_panel(
            f"🎉 VICTORY!\n"
            f"Defeated {monster['emoji']} {monster['name']}\n"
            f"   +{xp_gained} XP\n"
            f"   +{gem_chance} 💎 gems\n"
            f"   Streak: {player.streak}",
            title="🏆 WIN", style="bold green"
        )
        
        # Level up check
        check_level_up(player)
        return True
    else:
        print_panel(
            f"💀 DEFEATED!\n"
            f"{monster['emoji']} {monster['name']} was too strong.\n"
            f"You retreat with {max(0, player.hp)} HP remaining.",
            title="💀 DEFEAT", style="bold red"
        )
        player.hp = max(1, player.hp)  # Don't die completely
        return False


def check_level_up(player: Player):
    while player.xp >= player.xp_to_next:
        player.xp -= player.xp_to_next
        player.level += 1
        player.max_hp += 20
        player.hp = player.max_hp  # Full heal on level up
        player.attack += 5
        player.potions += 1
        player.xp_to_next = int(player.xp_to_next * 1.5)
        
        print_panel(
            f"⭐ LEVEL UP! You are now Level {player.level}!\n"
            f"   HP: {player.max_hp} (+20)\n"
            f"   Attack: {player.attack} (+5)\n"
            f"   +1 🧪 Potion\n"
            f"   Full HP restored!",
            title="⭐ LEVEL UP", style="bold magenta"
        )


# ═══════════════════════════════════════════════════════════
#  CODING PUZZLES
# ═══════════════════════════════════════════════════════════

def coding_puzzle(player: Player, puzzle_level: int) -> bool:
    """Present a coding puzzle. Player fills in the blank."""
    # Find puzzle for this level, or generate a harder one
    puzzle = None
    for p in CODING_PUZZLES:
        if p["level"] == puzzle_level:
            puzzle = p
            break
    
    if puzzle is None:
        # Generate a dynamic puzzle for levels beyond static content
        puzzle = generate_dynamic_puzzle(puzzle_level, player.difficulty)
    
    print_panel(
        f"{puzzle['prompt']}\n\n"
        f"Fill in the blank ({{blank}}):\n"
        f"  {puzzle['code_template']}",
        title="🧩 CODING PUZZLE", style="blue"
    )
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        attempts += 1
        
        if attempts > 1:
            print_text(f"💡 Hint: {puzzle['hint']}", style="yellow")
        
        try:
            user_answer = input(f"\nYour answer (attempt {attempts}/{max_attempts}) > ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        
        # Normalize: strip whitespace, lowercase for comparison
        normalized_answer = puzzle["answer"].strip().lower()
        normalized_user = user_answer.strip().lower()
        
        # Also try evaluating as code for numeric answers
        if normalized_user == normalized_answer:
            player.puzzles_solved += 1
            xp_gained = 50 + puzzle_level * 20
            player.xp += xp_gained
            player.gems += 5
            
            print_panel(
                f"✅ Correct!\n"
                f"{puzzle['explanation']}\n"
                f"   +{xp_gained} XP\n"
                f"   +5 💎 gems",
                title="🔓 UNLOCKED", style="bold green"
            )
            check_level_up(player)
            return True
        else:
            # Try evaluating both as Python for numeric answers
            try:
                if eval(normalized_user) == eval(normalized_answer):
                    player.puzzles_solved += 1
                    xp_gained = 50 + puzzle_level * 20
                    player.xp += xp_gained
                    player.gems += 5
                    
                    print_panel(
                        f"✅ Correct!\n"
                        f"{puzzle['explanation']}\n"
                        f"   +{xp_gained} XP\n"
                        f"   +5 💎 gems",
                        title="🔓 UNLOCKED", style="bold green"
                    )
                    check_level_up(player)
                    return True
            except:
                pass
            
            print_text(f"❌ Not quite. The blank should be: {puzzle['answer']}", style="red")
    
    print_panel(
        f"The correct answer was: {puzzle['answer']}\n"
        f"{puzzle['explanation']}\n"
        f"You take 10 damage from the trap!",
        title="🔒 FAILED", style="bold red"
    )
    player.hp -= 10
    return False


def generate_dynamic_puzzle(level: int, difficulty: Difficulty) -> dict:
    """Generate a puzzle for levels beyond the static content."""
    templates = [
        {
            "prompt": f"A locked door (Level {level}):\n'Print the result of {level} multiplied by {level+1}'",
            "code_template": f"print({level} {{blank}} {level+1})",
            "answer": "*",
            "hint": "Multiply symbol",
            "explanation": f"{level} * {level+1} = {level * (level+1)}",
        },
        {
            "prompt": f"A sealed passage:\n'What function converts \"42\" into the number 42?'",
            "code_template": "{blank}(\"42\")",
            "answer": "int",
            "hint": "Short for 'integer'",
            "explanation": "int() converts a string to an integer number.",
        },
        {
            "prompt": f"An ancient lock:\n'What keyword defines a function in Python?'",
            "code_template": "{blank} my_function():\n    return True",
            "answer": "def",
            "hint": "Short for 'define'",
            "explanation": "def creates a function in Python.",
        },
        {
            "prompt": f"Runes on the wall:\n'What keyword starts a conditional in Python?'",
            "code_template": "{blank} x > 5:\n    print('big')",
            "answer": "if",
            "hint": "It checks whether something is true",
            "explanation": "if statements run code only when a condition is true.",
        },
    ]
    return random.choice(templates)


# ═══════════════════════════════════════════════════════════
#  STORY
# ═══════════════════════════════════════════════════════════

STORY_BEATS = [
    {
        "stage": 0,
        "text": (
            "You stand at the mouth of the Crystal Caverns.\n"
            "Legends say ancient knowledge is buried deep within —\n"
            "math formulas carved in stone, code etched in crystal.\n"
            "Monsters guard the treasures. Only the clever may pass.\n\n"
            "Your quest: reach the Crystal Titan at the cavern's heart\n"
            "and claim the Knowledge Crystal."
        ),
        "title": "🏔️ The Entrance",
    },
    {
        "stage": 1,
        "text": (
            "You descend into the first chamber. Stalactites glow\n"
            "with faint blue light. Slimes and bats skitter in the shadows.\n"
            "The air smells of old stone and adventure."
        ),
        "title": "🔵 The Blue Caverns",
    },
    {
        "stage": 2,
        "text": (
            "Deeper now. The crystals shift from blue to green.\n"
            "Goblins patrol these tunnels. A locked door blocks\n"
            "the path — it needs code to open."
        ),
        "title": "🟢 The Green Tunnels",
    },
    {
        "stage": 3,
        "text": (
            "The temperature drops. Ice formations glitter on the walls.\n"
            "Stronger monsters dwell here. The path forks —\n"
            "but both ways lead to danger... and knowledge."
        ),
        "title": "❄️ The Frozen Depths",
    },
    {
        "stage": 4,
        "text": (
            "You've reached the deepest chamber. A massive figure\n"
            "towers over you — the Crystal Titan. Its body is made\n"
            "of pure knowledge crystal. It speaks:\n\n"
            "'Prove your mind is worthy. Answer my questions,\n"
            "and the crystal is yours. Fail... and you join\n"
            "the crystal walls forever.'"
        ),
        "title": "💎 THE CRYSTAL TITAN",
    },
    {
        "stage": 5,
        "text": (
            "The Crystal Titan crumbles into sparkling dust.\n"
            "The Knowledge Crystal floats toward you, glowing\n"
            "with the power of math and code.\n\n"
            "You grasp it. Knowledge floods your mind.\n"
            "You are the Champion of the Crystal Caverns."
        ),
        "title": "👑 VICTORY",
    },
]


def show_story(stage: int):
    for beat in STORY_BEATS:
        if beat["stage"] == stage:
            print_panel(beat["text"], title=beat["title"], style="magenta")
            return


# ═══════════════════════════════════════════════════════════
#  ROOMS / EXPLORATION
# ═══════════════════════════════════════════════════════════

def explore_room(player: Player) -> str:
    """Generate a room event. Returns 'battle', 'puzzle', 'treasure', 'shop', 'rest', or 'boss'."""
    room_num = player.rooms_cleared + 1
    
    # Boss every 8 rooms
    if room_num % 8 == 0 and player.story_stage < 4:
        return "boss"
    
    # Story beats at specific room counts
    story_triggers = {1: 0, 3: 1, 6: 2, 10: 3, 14: 4}
    if room_num in story_triggers:
        player.story_stage = story_triggers[room_num]
        show_story(player.story_stage)
    
    # Final boss
    if player.story_stage >= 4 and room_num >= 14:
        return "final_boss"
    
    # Random room type
    roll = random.random()
    if roll < 0.45:
        return "battle"
    elif roll < 0.70:
        return "puzzle"
    elif roll < 0.82:
        return "treasure"
    elif roll < 0.92:
        return "rest"
    else:
        return "shop"


def treasure_room(player: Player):
    gems_found = random.randint(3, 10)
    player.gems += gems_found
    
    # Chance for potion
    if random.random() < 0.4:
        player.potions += 1
        print_panel(
            f"💎 You found a treasure chest!\n"
            f"   +{gems_found} gems\n"
            f"   +1 🧪 Potion",
            title="📦 TREASURE", style="bold yellow"
        )
    else:
        print_panel(
            f"💎 You found a treasure chest!\n"
            f"   +{gems_found} gems",
            title="📦 TREASURE", style="bold yellow"
        )


def rest_room(player: Player):
    heal = int(player.max_hp * 0.3)
    player.hp = min(player.max_hp, player.hp + heal)
    print_panel(
        f"🛌 You find a safe spot to rest.\n"
        f"   Restored {heal} HP\n"
        f"   HP: {player.hp}/{player.max_hp}",
        title="⛺ REST", style="green"
    )


def shop_room(player: Player):
    print_panel(
        f"🛒 A mysterious merchant appears.\n"
        f"   1. 🧪 Potion (10 gems) — Heal 50 HP\n"
        f"   2. ⚔️ Attack Boost (20 gems) — +3 ATK\n"
        f"   3. ❤️ Max HP Boost (30 gems) — +15 Max HP\n"
        f"   4. Leave",
        title="🛒 SHOP", style="blue"
    )
    
    try:
        choice = input("\nBuy what? > ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    
    if choice == "1" and player.gems >= 10:
        player.gems -= 10
        player.potions += 1
        print_text("Bought a potion!", style="green")
    elif choice == "2" and player.gems >= 20:
        player.gems -= 20
        player.attack += 3
        print_text(f"Attack increased to {player.attack}!", style="green")
    elif choice == "3" and player.gems >= 30:
        player.gems -= 30
        player.max_hp += 15
        player.hp += 15
        print_text(f"Max HP increased to {player.max_hp}!", style="green")
    elif choice == "4":
        print_text("You leave the shop.", style="white")
    else:
        print_text("Not enough gems or invalid choice.", style="red")


def use_potion(player: Player):
    if player.potions > 0 and player.hp < player.max_hp:
        player.potions -= 1
        heal = min(50, player.max_hp - player.hp)
        player.hp += heal
        print_text(f"🧪 Used a potion! Healed {heal} HP. ({player.potions} left)", style="green")
    elif player.potions == 0:
        print_text("No potions left!", style="red")
    else:
        print_text("HP is already full!", style="yellow")


# ═══════════════════════════════════════════════════════════
#  BOSS FIGHT
# ═══════════════════════════════════════════════════════════

def mini_boss(player: Player) -> bool:
    """Mini-boss: tougher monster with multiple math problems per round."""
    boss = spawn_monster(player.level + 2)
    boss["hp"] = int(boss["hp"] * 1.5)
    boss["max_hp"] = boss["hp"]
    boss["atk"] = int(boss["atk"] * 1.3)
    
    print_panel(
        f"⚠️ MINI-BOSS: {boss['emoji']} {boss['name']}\n"
        f"It's bigger and stronger than normal!\n"
        f"HP: {boss['hp']} | ATK: {boss['atk']}",
        title="⚔️ MINI-BOSS", style="bold red"
    )
    
    return math_battle(player, boss)


def final_boss(player: Player) -> bool:
    """The Crystal Titan — final boss with mixed math + coding challenges."""
    titan_hp = 300 + player.level * 50
    titan_atk = 35 + player.level * 5
    
    print_panel(
        f"💎 THE CRYSTAL TITAN\n"
        f"HP: {titan_hp} | ATK: {titan_atk}\n"
        f"Mix of math and coding challenges!",
        title="💀 FINAL BOSS", style="bold magenta"
    )
    
    titan = {"name": "Crystal Titan", "emoji": "💎", "hp": titan_hp, "max_hp": titan_hp, "atk": titan_atk}
    round_num = 0
    
    while player.hp > 0 and titan["hp"] > 0:
        round_num += 1
        show_hp_bar(player, titan)
        
        # Alternate between math and coding
        if round_num % 3 == 0:
            # Coding challenge
            puzzle = generate_dynamic_puzzle(player.level + 2, player.difficulty)
            print_panel(
                f"The Titan tests your CODE knowledge!\n"
                f"{puzzle['prompt']}\n\n"
                f"Fill in: {puzzle['code_template']}",
                title=f"🧩 Round {round_num}", style="blue"
            )
            
            try:
                user_answer = input("\nYour answer > ").strip()
            except (EOFError, KeyboardInterrupt):
                return False
            
            if user_answer.lower() == puzzle["answer"].lower():
                damage = player.attack + 15
                titan["hp"] -= damage
                player.streak += 1
                player.best_streak = max(player.best_streak, player.streak)
                print_text(f"✅ Correct! {damage} damage to the Titan!", style="bold green")
            else:
                titan_damage = titan["atk"] + random.randint(0, 5)
                player.hp -= titan_damage
                player.streak = 0
                print_text(f"❌ Wrong! Answer was {puzzle['answer']}. Titan hits you for {titan_damage}!", style="bold red")
        else:
            # Math challenge
            question, answer, category = generate_math_problem(player.difficulty, player.level + 2)
            print_text(f"\n📜 [{category}] Round {round_num}", style="bold yellow")
            print_text(question, style="white")
            
            try:
                user_answer = input("\nYour answer > ").strip()
            except (EOFError, KeyboardInterrupt):
                return False
            
            if user_answer.lower() == answer.lower():
                damage = player.attack + random.randint(0, 5)
                titan["hp"] -= damage
                player.streak += 1
                player.best_streak = max(player.best_streak, player.streak)
                player.math_problems_solved += 1
                
                if player.streak >= 3:
                    bonus = player.streak * 3
                    damage += bonus
                    titan["hp"] -= bonus
                    print_text(f"🔥 STREAK x{player.streak}! +{bonus} bonus!", style="bold red")
                
                print_text(f"✅ Correct! {damage} damage!", style="bold green")
            else:
                titan_damage = titan["atk"] + random.randint(0, 5)
                player.hp -= titan_damage
                player.streak = 0
                print_text(f"❌ Wrong! Answer was {answer}. Titan hits you for {titan_damage}!", style="bold red")
        
        time.sleep(0.5)
    
    if titan["hp"] <= 0:
        player.story_stage = 5
        show_story(5)
        xp_gained = 500
        player.xp += xp_gained
        player.gems += 50
        player.battles_won += 1
        check_level_up(player)
        
        print_panel(
            f"🏆🏆🏆 FINAL VICTORY! 🏆🏆🏆\n"
            f"You defeated the Crystal Titan!\n"
            f"   +{xp_gained} XP\n"
            f"   +50 💎 gems\n\n"
            f"Final Stats:",
            title="👑 CHAMPION", style="bold magenta"
        )
        show_stats(player)
        return True
    else:
        print_panel(
            f"The Crystal Titan was too powerful...\n"
            f"You retreat, wounded but alive.",
            title="💀 DEFEAT", style="bold red"
        )
        player.hp = max(1, player.hp)
        return False


# ═══════════════════════════════════════════════════════════
#  MAIN GAME LOOP
# ═══════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CodeQuest — The Crystal Caverns")
    parser.add_argument("--difficulty", choices=["easy", "normal", "hard"], default=None,
                        help="Set difficulty: easy (8-10), normal (10-13), hard (13-15)")
    args = parser.parse_args()
    
    print_banner()
    
    # Try to load save
    player = load_game()
    
    if player is None:
        # New game
        print_panel(
            "Welcome, brave adventurer!\n"
            "What is your name?",
            title="✨ NEW GAME", style="cyan"
        )
        try:
            name = input("> ").strip() or "Hero"
        except (EOFError, KeyboardInterrupt):
            return
        
        # Difficulty selection
        if args.difficulty:
            diff = Difficulty(args.difficulty)
        else:
            print("\nChoose your challenge:")
            print("  1. Adventurer (ages 8-10) — simpler math")
            print("  2. Hero (ages 10-13) — balanced challenge")
            print("  3. Legend (ages 13-15) — advanced math + coding")
            try:
                diff_choice = input("\nDifficulty (1/2/3) > ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            
            diff_map = {"1": Difficulty.EASY, "2": Difficulty.NORMAL, "3": Difficulty.HARD}
            diff = diff_map.get(diff_choice, Difficulty.NORMAL)
        
        player = Player(name=name, difficulty=diff)
        print_panel(
            f"Welcome, {name}!\n"
            f"Difficulty: {DIFFICULTY_CONFIG[diff]['label']}\n"
            f"HP: {player.hp} | Attack: {player.attack} | Potions: {player.potions}\n\n"
            f"Commands during exploration:\n"
            f"  [Enter] = Continue to next room\n"
            f"  s = View stats\n"
            f"  p = Use potion\n"
            f"  q = Save & quit",
            title="🎮 READY", style="bold green"
        )
    else:
        # Continue
        if args.difficulty:
            player.difficulty = Difficulty(args.difficulty)
        print_panel(
            f"Welcome back, {player.name}!\n"
            f"Level {player.level} | HP {player.hp}/{player.max_hp}\n"
            f"Battles won: {player.battles_won} | Puzzles: {player.puzzles_solved}\n"
            f"Gems: {player.gems} | Streak best: {player.best_streak}",
            title="💾 LOADED", style="cyan"
        )
    
    show_story(player.story_stage)
    time.sleep(1)
    
    # Main loop
    while True:
        # Check if game complete
        if player.story_stage >= 5:
            print_panel(
                f"You've conquered the Crystal Caverns!\n"
                f"Play again? (y/n)",
                title="👑 COMPLETE", style="bold magenta"
            )
            try:
                again = input("> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break
            
            if again == "y":
                delete_save()
                player = Player(difficulty=player.difficulty)
                show_story(0)
            else:
                break
            continue
        
        # Exploration menu
        print_text(f"\n📍 Room {player.rooms_cleared + 1} | What do you do?", style="bold cyan")
        print_text("  [Enter] Explore next room  |  s = Stats  |  p = Potion  |  q = Save & Quit", style="white")
        
        try:
            action = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            save_game(player)
            print_text("\n💾 Game saved. Goodbye!", style="cyan")
            break
        
        if action == "q":
            save_game(player)
            print_text("💾 Game saved. See you soon, adventurer!", style="cyan")
            break
        elif action == "s":
            show_stats(player)
            continue
        elif action == "p":
            use_potion(player)
            continue
        elif action == "" or action == "go" or action == "explore":
            pass  # Continue to room
        else:
            print_text("Unknown command. Press Enter to explore.", style="yellow")
            continue
        
        # Generate room
        room_type = explore_room(player)
        
        if room_type == "battle":
            monster = spawn_monster(player.level)
            won = math_battle(player, monster)
            player.rooms_cleared += 1
            
        elif room_type == "puzzle":
            puzzle_level = min(player.level, len(CODING_PUZZLES))
            coding_puzzle(player, puzzle_level)
            player.rooms_cleared += 1
            
        elif room_type == "treasure":
            treasure_room(player)
            player.rooms_cleared += 1
            
        elif room_type == "rest":
            rest_room(player)
            player.rooms_cleared += 1
            
        elif room_type == "shop":
            shop_room(player)
            player.rooms_cleared += 1
            
        elif room_type == "boss":
            won = mini_boss(player)
            player.rooms_cleared += 1
            if won:
                print_text("The path deeper into the caverns opens!", style="magenta")
                
        elif room_type == "final_boss":
            won = final_boss(player)
            player.rooms_cleared += 1
            if won:
                save_game(player)
                continue
        
        # Auto-save every 3 rooms
        if player.rooms_cleared % 3 == 0:
            save_game(player)
            print_text("💾 Auto-saved!", style="dim")
        
        # Check for death
        if player.hp <= 0:
            print_panel(
                f"💀 You have fallen in the caverns...\n"
                f"But a mysterious force revives you!\n"
                f"HP restored to 50. You lose 5 gems.",
                title="💀 REVIVED", style="bold red"
            )
            player.hp = 50
            player.gems = max(0, player.gems - 5)
            player.streak = 0


if __name__ == "__main__":
    main()
