import re, urllib.request

html = urllib.request.urlopen("http://127.0.0.1:8085/", timeout=10).read().decode()

scripts = re.findall(r'<script[^>]*src="([^"]+)"', html)
print("External scripts:", scripts)

inline = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
total_js = sum(len(s) for s in inline)
print(f"Inline JS blocks: {len(inline)}, total {total_js} chars")

for s in scripts:
    try:
        body = urllib.request.urlopen("http://127.0.0.1:8085" + s, timeout=5).read().decode()
        print(f"  {s}: {len(body)} chars")
        total_js += len(body)
    except Exception as e:
        print(f"  {s}: FAILED {e}")

buttons = re.findall(r'<button[^>]*>([^<]+)</button>', html)
print("Buttons:", buttons[:15])

for marker in ['math', 'battle', 'quest', 'level', 'score', 'puzzle', 'code']:
    print(f"  '{marker}': {html.lower().count(marker)} occurrences")
