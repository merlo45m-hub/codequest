"""Add death check to puzzle failure branch."""
with open('/root/workspace/codequest/server.py', 'r') as f:
    content = f.read()

old = '''            if g["puzzle_attempts"] >= 3:
                g["hp"] -= 10
                g["mode"] = "explore"'''
new = '''            if g["puzzle_attempts"] >= 3:
                g["hp"] -= 10
                if g["hp"] <= 0:
                    g["hp"] = 0
                    g["mode"] = "gameover"
                    g["message"] = "\U0001f480 The puzzle trap drains your last strength... Game Over."
                    g["message_type"] = "defeat"
                    return g
                g["mode"] = "explore"'''

if old in content:
    content = content.replace(old, new)
    with open('/root/workspace/codequest/server.py', 'w') as f:
        f.write(content)
    print('Death check added to puzzle failure')
else:
    idx = content.find('puzzle_attempts"] >= 3')
    print('Pattern not found. Context:')
    print(repr(content[idx-100:idx+250]))

import py_compile
py_compile.compile('/root/workspace/codequest/server.py', doraise=True)
print('Compiles OK')
