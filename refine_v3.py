"""Add round 3 refinements to the game frontend."""
import re

with open('/root/workspace/codequest/v2_frontend.html', 'r') as f:
    html = f.read()

# === 1. Add new state variables ===
html = html.replace(
    'let depth=0;',
    'let depth=0;\nlet walkAnim=0;\nlet potionAnim=0;\nlet critFlash=0;\nlet bossZoom=0;\nlet victoryStats=[];\nlet torchFlicker=[];\nlet screenShakeX=0;\nlet screenShakeY=0;\nlet hitStop=0;'
)

# === 2. Init torch flicker values ===
html = html.replace(
    "window.addEventListener('resize',resize);resize();",
    "window.addEventListener('resize',resize);resize();\nfor(let i=0;i<6;i++)torchFlicker.push(0.7+Math.random()*0.3);"
)

# === 3. Add torch drawing to drawCavernBg ===
# Find the end of drawCavernBg (before the closing })
# Add torches after crystals but before dust particles
old_dust = "  // Floating dust particles (color shifts with depth)"
new_torches = """  // Wall torches
  const torchPositions=[[0.05,0.35],[0.95,0.35],[0.05,0.55],[0.95,0.55],[0.05,0.75],[0.95,0.75]];
  for(let i=0;i<torchPositions.length;i++){
    const tx=W*torchPositions[i][0],ty=H*torchPositions[i][1];
    // Torch handle
    ctx.fillStyle='#5a3a1a';ctx.fillRect(tx-2,ty,4,12);
    // Flame
    const flicker=torchFlicker[i%torchFlicker.length];
    const fh=8+flicker*6;
    ctx.fillStyle='rgba(255,100,0,0.6)';ctx.beginPath();ctx.ellipse(tx,ty-fh/2,5,fh,0,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='rgba(255,180,0,0.8)';ctx.beginPath();ctx.ellipse(tx,ty-fh/3,3,fh*0.6,0,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='rgba(255,255,200,0.9)';ctx.beginPath();ctx.ellipse(tx,ty-fh/5,1.5,fh*0.3,0,0,Math.PI*2);ctx.fill();
    // Glow
    ctx.globalAlpha=0.15*flicker;ctx.fillStyle='#ff6600';ctx.beginPath();ctx.arc(tx,ty-5,25,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;
    // Update flicker
    if(Math.random()<0.1)torchFlicker[i%torchFlicker.length]=0.5+Math.random()*0.5;
  }
  // Floating dust particles (color shifts with depth)"""
html = html.replace(old_dust, new_torches)

# === 4. Add walking animation in loop for explore mode ===
old_explore_draw = "drawPlayer(W*0.5,cy,2,false,false);\n    //Treasure chest treasure rooms"
new_explore_draw = """const walkX=walkAnim>0?W*0.3+walkAnim*W*0.4:W*0.5;
    drawPlayer(walkX,cy,2,false,false);
    if(walkAnim>0){walkAnim-=0.02;if(walkAnim<0)walkAnim=0;sfxFootstep()}
    // Treasure chest treasure rooms"""
html = html.replace(old_explore_draw, new_explore_draw)

# === 5. Add potion drink animation ===
old_gameover_draw = "}else if(gameMode==='gameover'){"
new_potion = """}else if(gameMode==='explore'&&potionAnim>0){
    drawPlayer(W*0.5,cy,2,false,false);
    // Potion bottle above player
    ctx.save();ctx.translate(W*0.5,cy-40-potionAnim*20);
    ctx.fillStyle='#e74c3c';ctx.beginPath();ctx.ellipse(0,0,8,10,0,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#c0392b';ctx.fillRect(-3,-12,6,4);
    // Sparkles
    for(let j=0;j<5;j++){const sa=animTime*3+j*1.2;ctx.globalAlpha=potionAnim*0.5;ctx.fillStyle='#69f0ae';ctx.beginPath();ctx.arc(Math.cos(sa)*15,Math.sin(sa)*15,2,0,Math.PI*2);ctx.fill()}
    ctx.globalAlpha=1;ctx.restore();
    if(potionAnim>0)potionAnim-=0.02;
  }else if(gameMode==='gameover'){"""
html = html.replace(old_gameover_draw, new_potion)

# === 6. Add hit-stop and crit flash to loop ===
html = html.replace(
    'if(attackAnim>0){attackAnim-=0.05;if(attackAnim<0)attackAnim=0}',
    'if(attackAnim>0){attackAnim-=0.05;if(attackAnim<0)attackAnim=0}\n  if(hitStop>0){hitStop-=0.03;if(hitStop<0)hitStop=0;animTime-=0.016}\n  if(critFlash>0){critFlash-=0.05;if(critFlash<0)critFlash=0}\n  if(bossZoom>0){bossZoom-=0.01;if(bossZoom<0)bossZoom=0}\n  if(walkAnim>0){walkAnim-=0.02;if(walkAnim<0)walkAnim=0}\n  if(potionAnim>0){potionAnim-=0.02}'
)

# === 7. Enhance boss intro with zoom ===
old_boss_intro = """if(curr.mode==='boss'&&prev.mode!=='boss'){bossIntro=1;sfxBoss()}"""
new_boss_intro = """if(curr.mode==='boss'&&prev.mode!=='boss'){bossIntro=1;sfxBoss();bossZoom=1}"""
html = html.replace(old_boss_intro, new_boss_intro)

# === 8. Add crit hit detection ===
old_player_atk = """attackAnim=1;attackAnimWho='player';
    // Attack trail
    for(let i=0;i<5;i++)attackTrail.push({x:W*0.25+i*15,y:H*0.45,life:1,color:'#4dd0e1'});"""
new_player_atk = """attackAnim=1;attackAnimWho='player';
    // Attack trail
    for(let i=0;i<5;i++)attackTrail.push({x:W*0.25+i*15,y:H*0.45,life:1,color:'#4dd0e1'});
    // Critical hit (random or high streak)
    if(curr.streak>=3||(prev.streak||0)>=3){
      critFlash=1;hitStop=0.5;
      spawnParticles(W*0.72,H*0.42,'#fff',20);
      spawnDmg(W*0.72,H*0.38,prev.monster.hp-curr.monster.hp,'monster');
      shakeTime=15;shakeMag=15;
    }"""
html = html.replace(old_player_atk, new_player_atk)

# === 9. Add crit flash to drawFlash ===
old_flash_func = """function drawFlash(){
  if(flashAlpha>0){ctx.fillStyle=flashColor;ctx.globalAlpha=flashAlpha;ctx.fillRect(0,0,W,H);ctx.globalAlpha=1;flashAlpha-=0.04}
}"""
new_flash_func = """function drawFlash(){
  if(flashAlpha>0){ctx.fillStyle=flashColor;ctx.globalAlpha=flashAlpha;ctx.fillRect(0,0,W,H);ctx.globalAlpha=1;flashAlpha-=0.04}
  if(critFlash>0){ctx.fillStyle='#fff';ctx.globalAlpha=critFlash*0.3;ctx.fillRect(0,0,W,H);ctx.globalAlpha=1}
}"""
html = html.replace(old_flash_func, new_flash_func)

# === 10. Add potion animation trigger ===
old_heal = """if(curr.hp>prev.hp&&curr.message_type==='heal'){spawnHeal(W*0.25,H*0.38,curr.hp-prev.hp);sfxCorrect()}"""
new_heal = """if(curr.hp>prev.hp&&curr.message_type==='heal'){spawnHeal(W*0.25,H*0.38,curr.hp-prev.hp);sfxCorrect();potionAnim=1;for(let i=0;i<15;i++)spawnParticles(W*0.5,H*0.4,'#69f0ae',1)}"""
html = html.replace(old_heal, new_heal)

# === 11. Trigger walk animation on explore ===
html = html.replace(
    "if(curr.mode!=='battle'&&curr.mode!=='boss')&&prev.mode==='battle'){",
    "if(prev.mode==='battle'&&(curr.mode==='explore'||curr.mode==='shop'||curr.mode==='treasure'||curr.mode==='rest')){walkAnim=1}"
)

# === 12. Enhance boss intro with zoom effect ===
old_boss_draw = """function drawBossIntro(){
  if(bossIntro<=0)return;
  ctx.fillStyle=`rgba(0,0,0,${bossIntro*0.7})`;
  ctx.fillRect(0,0,W,H);
  if(bossIntro>0.3){
    const f=Math.min(1,(bossIntro-0.3)*2);
    ctx.globalAlpha=f;
    ctx.fillStyle='#e74c3c';ctx.font='bold 28px system-ui';ctx.textAlign='center';
    ctx.strokeStyle='#000';ctx.lineWidth=4;
    ctx.strokeText('BOSS BATTLE',W/2,H/2);
    ctx.fillText('BOSS BATTLE',W/2,H/2);
    ctx.font='bold 14px system-ui';ctx.fillStyle='#ffd54f';
    ctx.strokeText('Crystal Titan approaches...',W/2,H/2+30);
    ctx.fillText('Crystal Titan approaches...',W/2,H/2+30);
    ctx.globalAlpha=1;
  }
}"""
new_boss_draw = """function drawBossIntro(){
  if(bossIntro<=0)return;
  ctx.fillStyle=`rgba(0,0,0,${bossIntro*0.8})`;
  ctx.fillRect(0,0,W,H);
  if(bossIntro>0.2){
    const f=Math.min(1,(bossIntro-0.2)*1.5);
    const zoom=1+bossZoom*0.3;
    ctx.globalAlpha=f;
    ctx.save();ctx.translate(W/2,H/2);ctx.scale(zoom,zoom);
    ctx.fillStyle='#e74c3c';ctx.font='bold 32px system-ui';ctx.textAlign='center';
    ctx.strokeStyle='#000';ctx.lineWidth=5;
    ctx.strokeText('BOSS BATTLE',0,-10);
    ctx.fillText('BOSS BATTLE',0,-10);
    ctx.font='bold 14px system-ui';ctx.fillStyle='#ffd54f';
    ctx.strokeText('Crystal Titan approaches...',0,20);
    ctx.fillText('Crystal Titan approaches...',0,20);
    // Warning stripes
    ctx.fillStyle='rgba(255,0,0,0.3)';
    for(let i=-3;i<3;i++)ctx.fillRect(-W,i*15-5,W,8);
    ctx.restore();
    ctx.globalAlpha=1;
  }
}"""
html = html.replace(old_boss_draw, new_boss_draw)

# === 13. Add victory stats fly-in on champion ===
old_champion = "if(curr.message_type==='victory'&&curr.mode!=='boss'){flashColor='#ffd700';flashAlpha=0.3;sfxCorrect()}"
new_champion = """if(curr.message_type==='victory'&&curr.mode!=='boss'){flashColor='#ffd700';flashAlpha=0.3;sfxCorrect()}
  if(curr.story_stage>=5&&prev.story_stage<5){
    sfxVictory();
    for(let i=0;i<50;i++){goldRain.push({x:W*Math.random(),y:H*0.3,vy:1+Math.random()*3,size:2+Math.random()*4,color:'#ffd700',life:1})}
    victoryStats=['Battles: '+curr.battles_won,'Puzzles: '+curr.puzzles_solved,'Math: '+curr.math_solved,'Streak: '+curr.best_streak];
  }"""
html = html.replace(old_champion, new_champion)

# Write refined v3
with open('/root/workspace/codequest/v3_frontend.html', 'w') as f:
    f.write(html)
print('v3 frontend written:', len(html), 'chars')

# Check JS
script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
with open('/tmp/v3_js.js', 'w') as f:
    f.write(script)
