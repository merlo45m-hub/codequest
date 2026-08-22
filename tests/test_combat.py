import importlib.util, random
spec = importlib.util.spec_from_file_location("cq", "/root/workspace/codequest/server.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("=== UNIT TESTS: calc_spell_damage ===")
cfg0 = dict(m.CONFIG); cfg0["damage"] = dict(m.CONFIG["damage"]); cfg0["damage"]["rand_min"]=0; cfg0["damage"]["rand_max"]=0
d = m.calc_spell_damage(10, 1.0, 1.0, 0, cfg0); assert d == 10, d
print("  base damage:", d, "OK")
d = m.calc_spell_damage(10, 1.0, 2.0, 0, cfg0); assert d == 20, d
print("  overload x2:", d, "OK")
d = m.calc_spell_damage(10, 1.0, 1.0, 3, cfg0); assert d == 16, d
print("  streak bonus:", d, "OK")
d = m.calc_spell_damage(1, 0.1, 1.0, 0, cfg0); assert d == 1, d
print("  min_damage floor:", d, "OK")
print("=== UNIT TESTS: resolve_special ===")
r = m.resolve_special("overload", False, True, 100); assert r["consume"] is False and r["dmg_mult"] == 1.0
print("  unarmed -> no-op OK")
r = m.resolve_special("overload", True, True, 100); assert r["consume"] and r["dmg_mult"] == 2.0 and "OVERLOAD" in r["message"]
print("  overload armed ->", r["message"], "OK")
r = m.resolve_special("bulwark", True, True, 100); assert r["heal"] == 30 and r["consume"]
print("  bulwark heal:", r["heal"], "OK")
r = m.resolve_special("great_heal", True, True, 100); assert r["heal"] == 40
print("  great_heal:", r["heal"], "OK")
r = m.resolve_special(None, True, True, 100); assert r["consume"] is False
print("  no special -> no-op OK")
print("=== BEHAVIOR: full playthrough reaches CHAMPION ===")
sid, g = m.action_start("T", "normal", "mage")
steps = 0
while g and g["mode"] != "gameover" and g["story_stage"] < 5 and steps < 3000:
    steps += 1
    if g["mode"] == "explore": g = m.action_explore(g)
    elif g["mode"] == "boss":
        if g.get("special_ready") and not g.get("special_armed"): g = m.action_special(g)
        g["current_problem"] = g["current_problem"] or m.gen_math("normal", g["level"])
        g["choices"] = g["choices"] or m.roll_spells(g["current_problem"]["cat"])
        g = m.action_answer(g, g["current_problem"]["a"], 0)
    elif g["mode"] == "battle":
        g["current_problem"] = g["current_problem"] or m.gen_math("normal", g["level"])
        g["choices"] = g["choices"] or m.roll_spells(g["current_problem"]["cat"])
        g = m.action_answer(g, g["current_problem"]["a"], 0)
    elif g["mode"] == "puzzle": g = m.action_answer(g, g["current_puzzle"]["answer"])
    elif g["mode"] == "shop": g = m.action_shop(g, "4")
    elif g["mode"] in ("rest", "treasure"): g = m.action_explore(g)
    elif g["mode"] == "fork": g = m.action_fork(g, "left")
print("  champion:", g["story_stage"] >= 5, "| steps:", steps)
assert g["story_stage"] >= 5
print("\nALL ARCH UNIT TESTS PASSED")
