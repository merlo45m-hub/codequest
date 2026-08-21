"""Replace HTML_PAGE in server.py with the canvas-based frontend."""
import json

with open('/root/workspace/codequest/server.py', 'r') as f:
    content = f.read()

# Find STORY data
story_start = content.find('STORY = [')
if story_start == -1:
    story_start = content.find('STORY[')
    story_start = content.rfind('\n', 0, story_start) + 1
list_start = content.find('[', story_start)
bracket = 0
for i in range(list_start, len(content)):
    if content[i] == '[': bracket += 1
    elif content[i] == ']':
        bracket -= 1
        if bracket == 0:
            story_end = i + 1
            break
story_code = content[list_start:story_end]
story_data = eval(story_code)
story_json = json.dumps(story_data, ensure_ascii=False)

# Read new canvas frontend
with open('/root/workspace/codequest/canvas_frontend.html', 'r') as f:
    frontend = f.read()
frontend = frontend.replace('STORIES_JSON', story_json)

# Replace HTML_PAGE
old_tq_start = content.find("'''", content.find('HTML_PAGE') + 10) + 3
old_tq_end = content.find("'''", old_tq_start)
new_content = content[:old_tq_start] + frontend + content[old_tq_end:]

with open('/root/workspace/codequest/server.py', 'w') as f:
    f.write(new_content)

import py_compile
py_compile.compile('/root/workspace/codequest/server.py', doraise=True)
print('Compiles OK')

# Verify no surrogates
ns = {}
exec(compile(new_content, 'server.py', 'exec'), ns)
html = ns.get('HTML_PAGE', '')
try:
    html.encode('utf-8')
    print('UTF-8 encode: OK')
    print(f'HTML size: {len(html)} chars')
except UnicodeEncodeError as e:
    print(f'Surrogate error at {e.start}')
