import urllib.request, urllib.error, json, re

base = "http://127.0.0.1:8085"
results = []

# 1. Main page loads
html = urllib.request.urlopen(base + "/", timeout=10).read().decode()
results.append(("Main page loads", len(html) > 1000, f"{len(html)} bytes"))

# 2. Core UI elements present in served HTML
for name, pat in [
    ("Has canvas/game container", r'<canvas|game-container|id="game"'),
    ("Has JavaScript", r'<script'),
    ("Has interactivity", r'<button|onclick|addEventListener'),
]:
    results.append((name, bool(re.search(pat, html, re.I)), ""))

# 3. Probe API endpoints declared in server.py
src = open('/root/workspace/codequest/server.py').read()
endpoints = sorted(set(re.findall(r'["\'](/api/[a-z_/]+)["\']', src)))
print("API endpoints in server.py:", endpoints)

for ep in endpoints:
    try:
        r = urllib.request.urlopen(base + ep, timeout=5)
        body = r.read()[:200]
        results.append((f"GET {ep}", r.status == 200, f"HTTP {r.status}"))
    except urllib.error.HTTPError as e:
        results.append((f"GET {ep}", e.code in (400, 405), f"HTTP {e.code} (POST-only ok)"))
    except Exception as e:
        results.append((f"GET {ep}", False, str(e)))

print()
fails = 0
for name, ok, note in results:
    if not ok:
        fails += 1
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {note}")
print(f"\n{len(results)-fails}/{len(results)} checks passed")
