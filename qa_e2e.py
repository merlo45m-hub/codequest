"""End-to-end QA: exercise every game action through the API."""
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

# 1. START GAME
try:
    r = api("start", name="TestHero", difficulty="easy")
    sid = r.get("sid")
    g = r.get("state", {})
    check("Game starts with session ID", bool(sid), f"sid={sid}")
    check("Player has HP", g.get("hp", 0) > 0, f"hp={g.get('hp')}")
    check("Player has level", g.get("level", 0) >= 1, f"level={g.get('level')}")
    check("Player has gold", g.get("gold", 0) >= 0, f"gold={g.get('gold')}")
    check("Game has rooms/progression", "room" in str(g) or "rooms" in str(g), "")
except Exception as e:
    check("Game starts", False, str(e))
    sys.exit(1)

# 2. EXPLORE (should trigger math or monster or treasure)
try:
    r = api("explore", sid=sid)
    g = r.get("state", {})
    check("Explore returns state", bool(g), "")
    check("Explore sets a mode (math/battle/shop/treasure)", 
          g.get("mode") in ("math", "battle", "shop", "treasure", "coding", "story") or "problem" in g or "monster" in g,
          f"mode={g.get('mode', '?')}, keys={list(g.keys())[:8]}")
except Exception as e:
    check("Explore works", False, str(e))

# 3. ANSWER MATH (try answering whatever problem explore gave)
try:
    # If there's a math problem, try to answer it
    r = api("answer", sid=sid, answer="42")
    g = r.get("state", {})
    check("Answer endpoint accepts input", "error" not in r, f"error={r.get('error','none')}")
except Exception as e:
    check("Answer endpoint works", False, str(e))

# 4. POTION
try:
    r = api("potion", sid=sid)
    g = r.get("state", {})
    check("Potion endpoint responds", "error" not in r or r.get("error") == "No potions", 
          f"hp={g.get('hp')}, potions={g.get('potions')}")
except Exception as e:
    check("Potion works", False, str(e))

# 5. SHOP
try:
    r = api("shop", sid=sid, choice="1")
    g = r.get("state", {})
    check("Shop endpoint responds", "error" not in r, f"gold={g.get('gold')}")
except Exception as e:
    check("Shop works", False, str(e))

# 6. INVALID ACTION
try:
    r = api("frobnicate", sid=sid)
    check("Invalid action returns error", r.get("error") == "Invalid action", f"error={r.get('error')}")
except Exception as e:
    check("Invalid action handled", False, str(e))

# 7. NONEXISTENT SESSION
try:
    r = api("explore", sid="fake-session-id")
    check("Bad session handled gracefully", "error" in r or r.get("state") is None, 
          f"keys={list(r.keys())}")
except Exception as e:
    check("Bad session handled", False, str(e))

# Summary
print(f"\n{'='*50}")
passed = sum(1 for s,_,_ in results if s == "PASS")
failed = sum(1 for s,_,_ in results if s == "FAIL")
print(f"{passed}/{len(results)} passed, {failed} failed")
if failed:
    print("FAILED CHECKS:")
    for s, name, detail in results:
        if s == "FAIL":
            print(f"  - {name}: {detail}")
