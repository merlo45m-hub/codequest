"""Fix the unicode escape issue in gameover UI."""
with open('/root/workspace/codequest/server.py', 'r') as f:
    content = f.read()

# The \\u{1F480} is not valid Python unicode escape in a regular string
# Replace with actual emoji character
content = content.replace('\\u{1F480}', '\U0001F480')
content = content.replace('\\u{2022}', '\u2022')

with open('/root/workspace/codequest/server.py', 'w') as f:
    f.write(content)
print('Unicode escapes fixed')

import py_compile
py_compile.compile('/root/workspace/codequest/server.py', doraise=True)
print('Compiles OK')
