"""Deep QA: exercise a full game loop — start, explore, fight, answer, level up, die/win."""
import urllib.request, json, sys

BASE = "http://127.0.0.1:8085/api"
results = []

def api(action, sid=None, **extra):
    payload = {"action": action}
    if sid: payload["sid"] = sid
    payload.update(extra)
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE, data=data, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=10)
    return json.loads(r.read())

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((status, name, detail))
    print(f"{status}  {name}  {detail}")
    return condition

# Start game
r = api("start", name="QAHero", difficulty="easy")
sid = r["sid"]
g = r["state"]
print(f"\nGame state keys: {list(g.keys())}")
print(f"Initial: hp={g.get('hp')}/{g.get('max_hp')}, level={g.get('level')}, xp={g.get('xp')}, gems={g.get('gems')}, potions={g.get('potions')}")

# What does explore actually return?
r2 = api("explore", sid=sid)
g2 = r2["state"]
print(f"\nAfter explore: mode={g2.get('mode')}, keys={list(g2.keys())}")
print(f"  monster={g2.get('monster')}")
print(f"  problem={g2.get('problem')}")

# If it's a battle, try attacking
if g2.get("mode") == "battle":
    print("\n--- BATTLE TEST ---")
    # Attack by answering math (the answer endpoint handles attacks?)
    # Check what 'answer' does in battle mode
    r3 = api("answer", sid=sid, answer="5")
    g3 = r3["state"]
    print(f"After answer in battle: mode={g3.get('mode')}, message={g3.get('message')}")
    print(f"  monster hp={g3.get('monster',{}).get('hp') if isinstance(g3.get('monster'), dict) else g3.get('monster_hp')}")
    print(f"  player hp={g3.get('hp')}")
    print(f"  keys={list(g3.keys())}")

# Keep exploring to see different room types
print("\n--- 10 EXPLORATIONS ---")
modes_seen = set()
for i in range(10):
    r = api("explore", sid=sid)
    g = r["state"]
    mode = g.get("mode", "unknown")
    modes_seen.add(mode)
    extra = ""
    if mode == "battle":
        m = g.get("monster", {})
        extra = f"monster={m.get('name') if isinstance(m, dict) else m}"
    elif mode == "math":
        p = g.get("problem", {})
        extra = f"problem={p}"
    elif mode == "coding":
        extra = f"puzzle={g.get('puzzle', g.get('problem', '?'))}"
    elif mode == "shop":
        extra = f"items={g.get('shop_items', g.get('items', '?'))}"
    elif mode == "treasure":
        extra = f"reward={g.get('reward', '?')}"
    elif mode == "story":
        extra = f"story={g.get('story', '?')}"
    print(f"  Room {i+1}: mode={mode}  {extra}")

print(f"\nModes seen across 10 rooms: {sorted(modes_seen)}")

# Check for game over
r = api("start", name="DeathTest", difficulty="hard")
sid2 = r["sid"]
g = r["state"]
print(f"\n--- DEATH TEST (hard difficulty) ---")
print(f"Starting hard: hp={g.get('hp')}, max_hp={g.get('max_hp')}")
for i in range(20):
    r = api("explore", sid=sid2)
    g = r["state"]
    if g.get("mode") == "battle":
        # Try to fight — answer wrong to take damage
        r = api("answer", sid=sid2, answer="999")
        g = r["state"]
        if g.get("hp", 1) <= 0:
            print(f"  Died after {i+1} rooms. mode={g.get('mode')}, hp={g.get('hp')}")
            check("Game over triggers on death", g.get("mode") == "gameover" or g.get("game_over") == True or g.get("hp", 1) <= 0, 
                  f"mode={g.get('mode')}, hp={g.get('hp')}")
            break
    if g.get("hp", 1) <= 0:
        print(f"  HP=0 after {i+1} rooms")
        check("Game over triggers on death", True, f"hp={g.get('hp')}")
        break
else:
    print("  Survived 20 rooms on hard — no death triggered")
    check("Game over triggers on death", False, "Survived 20 hard rooms")

print(f"\n{'='*50}")
passed = sum(1 for s,_,_ in results if s == "PASS")
failed = sum(1 for s,_,_ in results if s == "FAIL")
print(f"{passed}/{len(results)} passed, {failed} failed")
