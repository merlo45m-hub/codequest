"""Test that death now triggers game over, and test a full winning playthrough."""
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

# === TEST 1: Death triggers game over ===
print("=== DEATH TEST ===")
r = api("start", name="DeathHero", difficulty="hard")
sid = r["sid"]
g = r["state"]
print(f"Start: hp={g['hp']}, mode={g.get('mode')}")

died = False
for i in range(30):
    r = api("explore", sid=sid)
    g = r["state"]
    mode = g.get("mode")
    
    if mode in ("battle", "boss"):
        # Answer wrong to take damage
        r = api("answer", sid=sid, answer="0")
        g = r["state"]
        if g.get("mode") == "gameover":
            print(f"  GAME OVER at room {i+1}! hp={g.get('hp')}")
            died = True
            check("Death triggers game over", True, f"mode=gameover at room {i+1}")
            break
    elif mode == "puzzle":
        for _ in range(4):
            r = api("answer", sid=sid, answer="0")
            g = r["state"]
            if g.get("mode") != "puzzle":
                break
        if g.get("mode") == "gameover":
            print(f"  GAME OVER at room {i+1}! hp={g.get('hp')}")
            died = True
            check("Death triggers game over", True, f"mode=gameover at room {i+1}")
            break

if not died:
    check("Death triggers game over", False, "Survived 30 rooms on hard")

# === TEST 2: Winning playthrough (easy, answer everything right) ===
print("\n=== WINNING PLAYTHROUGH ===")
r = api("start", name="WinHero", difficulty="easy")
sid2 = r["sid"]
g = r["state"]
print(f"Start: hp={g['hp']}, level={g['level']}, gems={g.get('gems',0)}")

rooms_cleared = 0
for i in range(50):
    r = api("explore", sid=sid2)
    g = r["state"]
    mode = g.get("mode")
    
    if mode == "battle" or mode == "boss":
        prob = g.get("current_problem", {})
        # The answer field
        ans = prob.get("a", prob.get("answer", "1"))
        # Try eval for math problems
        try:
            if isinstance(ans, str) and ans.isdigit() == False:
                ans = str(eval(ans))
        except:
            pass
        r = api("answer", sid=sid2, answer=str(ans))
        g = r["state"]
        # Might need multiple hits to kill monster
        while g.get("mode") in ("battle", "boss"):
            prob = g.get("current_problem", {})
            ans = prob.get("a", prob.get("answer", "1"))
            try:
                if isinstance(ans, str) and ans.isdigit() == False:
                    ans = str(eval(ans))
            except:
                pass
            r = api("answer", sid=sid2, answer=str(ans))
            g = r["state"]
            if g.get("mode") == "gameover":
                break
        rooms_cleared = g.get("rooms_cleared", rooms_cleared)
        
    elif mode == "puzzle":
        p = g.get("current_puzzle", {})
        ans = p.get("answer", "1")
        r = api("answer", sid=sid2, answer=str(ans))
        g = r["state"]
        rooms_cleared = g.get("rooms_cleared", rooms_cleared)
        
    elif mode == "shop":
        # Just leave
        r = api("shop", sid=sid2, choice="4")
        g = r["state"]
        
    elif mode == "gameover":
        print(f"  Game over at room {i+1}")
        break
        
    if g.get("level", 1) >= 5:
        print(f"  Reached level 5 at room {i+1}!")
        check("Can level up to 5", True, f"level={g['level']} at room {i+1}")
        break

    if i % 10 == 0:
        print(f"  Room {i+1}: mode={mode} hp={g.get('hp')} level={g.get('level')} xp={g.get('xp')} gems={g.get('gems',0)} cleared={rooms_cleared}")

print(f"Final: level={g.get('level')}, rooms_cleared={rooms_cleared}, battles_won={g.get('battles_won',0)}")
check("Game progresses (rooms cleared > 5)", rooms_cleared > 5, f"rooms_cleared={rooms_cleared}")
check("Player levels up", g.get("level", 1) > 1, f"level={g.get('level')}")
check("Battles won recorded", g.get("battles_won", 0) > 0, f"battles_won={g.get('battles_won',0)}")

# === SUMMARY ===
print(f"\n{'='*50}")
passed = sum(1 for s,_,_ in results if s == "PASS")
failed = sum(1 for s,_,_ in results if s == "FAIL")
print(f"{passed}/{len(results)} passed, {failed} failed")
