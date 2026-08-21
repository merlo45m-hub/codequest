"""Add gameover rendering to the frontend JS and fix remaining issues."""
with open('/root/workspace/codequest/server.py', 'r') as f:
    content = f.read()

# Find the puzzle render block end and add gameover handling before c.innerHTML = html
# The pattern: after the puzzle block '}' and before 'c.innerHTML = html;'
old = """  }

  c.innerHTML = html;
}"""
new = """  }

  else if (state.mode === 'gameover') {
    html += `<div class="panel" style="text-align:center">
      <div class="story-title">\\u{1F480} Game Over</div>
      <p>${state.name} fell in the Crystal Caverns...</p>
      <p>Level ${state.level} \\u2022 Battles Won: ${state.battles_won} \\u2022 Puzzles: ${state.puzzles_solved}</p>
      <p>Best Streak: ${state.best_streak}</p>
      <button class="btn btn-primary" onclick="SID=null;state=null;render()">Play Again</button>
    </div>`;
  }

  c.innerHTML = html;
}"""

if old in content:
    content = content.replace(old, new, 1)
    with open('/root/workspace/codequest/server.py', 'w') as f:
        f.write(content)
    print('gameover UI added to frontend')
else:
    print('Pattern not found - debugging...')
    # Find the actual text around c.innerHTML
    idx = content.find('c.innerHTML')
    if idx != -1:
        print('Found c.innerHTML at:', idx)
        print('Context:', repr(content[idx-100:idx+50]))

import py_compile
py_compile.compile('/root/workspace/codequest/server.py', doraise=True)
print('Compiles OK')
