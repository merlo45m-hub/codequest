"""v5: bigger attack effects, spear throw, XP bar, cleaner structure."""
import re

with open('/root/workspace/codequest/v5_src.html', 'r') as f:
    html = f.read()

# 1. XP bar near player body
html = html.replace(
    "ctx.fillStyle='#1e3a5f';ctx.beginPath();ctx.moveTo(x-4*scl,yp+4*scl);ctx.lineTo(x+4*scl,yp+4*scl);ctx.lineTo(x+2*scl,yp+11*scl);ctx.lineTo(x-2*scl,yp+11*scl);ctx.fill();",
    "ctx.fillStyle='#1e3a5f';ctx.beginPath();ctx.moveTo(x-4*scl,yp+4*scl);ctx.lineTo(x+4*scl,yp+4*scl);ctx.lineTo(x+2*scl,yp+11*scl);ctx.lineTo(x-2*scl,yp+11*scl);ctx.fill();\n    if(scl>=2&&hp>0){const xpW=12*scl;ctx.fillStyle='#333';ctx.fillRect(x-2*scl,yp-3*scl,xpW,2);ctx.fillStyle='#f39c12';ctx.fillRect(x-2*scl,yp-3*scl,xpW*hp,2);}"
)

# 2. Bigger particles
html = html.replace("spawnParticles(W*0.72,H*0.42,'#ffd54f',12);sfxHit()", "spawnParticles(W*0.72,H*0.42,'#ffd54f',30);sfxHit()")
html = html.replace("spawnParticles(W*0.25,H*0.42,'#ff5252',15)", "spawnParticles(W*0.25,H*0.42,'#ff5252',25)")

# 3. Spear trail + bigger old trail
old_atk = "attackAnim=1;attackAnimWho='player';\n    for(let i=0;i<5;i++)attackTrail.push({x:W*0.25+i*15,y:H*0.45,life:1,color:'#4dd0e1'});"
new_atk = "attackAnim=1;attackAnimWho='player';\n    for(let i=0;i<8;i++)attackTrail.push({x:W*0.25+i*12,y:H*0.45,life:1,color:curr.streak>=3?'#ff416c':'#4dd0e1'});\n    for(let i=0;i<12;i++)spearTrails.push({x:W*0.25+(i*18),y:H*0.42+Math.sin(i)*5,life:1,color:'#4dd0e1'});"
html = html.replace(old_atk, new_atk)

# 4. Slower decay
html = html.replace("attackTrail.forEach(t=>{t.life-=0.05})", "attackTrail.forEach(t=>{t.life-=0.035})")

# 5. spearTrails variable
html = html.replace("let attackTrail=[];", "let attackTrail=[];\nlet spearTrails=[];")

# Add spear decay after attackTrail decay
old_decay = """if(attackTrail.length>0){attackTrail=attackTrail.filter(t=>t.life>0);attackTrail.forEach(t=>{t.life-=0.035})}"""
new_decay = """if(attackTrail.length>0){attackTrail=attackTrail.filter(t=>t.life>0);attackTrail.forEach(t=>{t.life-=0.035})}
  if(spearTrails.length>0){spearTrails=spearTrails.filter(t=>t.life>0);spearTrails.forEach(t=>{t.life-=0.025})}"""
html = html.replace(old_decay, new_decay)

# Add drawSpears
old_gold = "function drawGoldRain(){"
new_spears_func = "function drawSpears(){\n  if(spearTrails.length===0)return;\n  for(const s of spearTrails){\n    ctx.globalAlpha=s.life;ctx.fillStyle=s.color;\n    ctx.fillRect(s.x-1,s.y-12,2,20);\n  }\n  ctx.globalAlpha=1;\n}\nfunction drawGoldRain(){"
html = html.replace(old_gold, new_spears_func)

# Add drawSpears call
html = html.replace("drawGoldRain();drawAttackTrail();drawLevelUpText()", "drawGoldRain();drawAttackTrail();drawSpears();drawLevelUpText()")

# 6. Stronger crit
html = html.replace("critFlash=1;hitStop=0.5;spawnParticles(W*0.72,H*0.42,'#fff',20);", "critFlash=1;hitStop=0.8;shakeTime=20;shakeMag=20;spawnParticles(W*0.72,H*0.42,'#fff',30);spawnParticles(W*0.72,H*0.42,'#ffd54f',20);")

with open('/root/workspace/codequest/v5_frontend.html', 'w') as f:
    f.write(html)
print('v5 written:', len(html), 'chars')

script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
with open('/tmp/v5_js.js', 'w') as f:
    f.write(script)
