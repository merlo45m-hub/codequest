"""Replace the HTML_PAGE in server.py with the new visual frontend."""
import json

with open('/root/workspace/codequest/server.py', 'r') as f:
    content = f.read()

# Find STORY data and generate JSON
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

# Read new frontend
with open('/root/workspace/codequest/game_frontend.html', 'r') as f:
    frontend = f.read()
frontend = frontend.replace('STORIES_JSON_PLACEHOLDER', story_json)

# Find old HTML_PAGE boundaries
old_start = content.find("HTML_PAGE = '''")
if old_start == -1:
    old_start = content.find("HTML_PAGE'''")
    old_start = content.rfind('\n', 0, old_start) + 1

old_tq_start = content.find("'''", old_start + 10) + 3
old_tq_end = content.find("'''", old_tq_start)

# Replace
new_content = content[:old_tq_start] + frontend + content[old_tq_end:]

with open('/root/workspace/codequest/server.py', 'w') as f:
    f.write(new_content)

print(f'Old HTML: {old_tq_end - old_tq_start} chars')
print(f'New HTML: {len(frontend)} chars')
print(f'New file: {len(new_content)} chars')

import py_compile
py_compile.compile('/root/workspace/codequest/server.py', doraise=True)
print('Compiles OK')
