"""Refine the game frontend with: low-HP vignette, level-up burst text, monster death animation,
depth-based backgrounds, attack lunge with trail, streak fire effect, treasure gold rain,
improved room transition wipes, floating ambient particles per depth."""

import json, re

with open('/root/workspace/codequest/current_frontend.html', 'r') as f:
    html = f.read()

# === 1. Add new CSS for level-up burst and streak fire ===
old_css_end = '</style>'
new_css = """</style>
<!-- end css -->"""
# Actually let's just insert before </style>

# === 2. Add new JS variables and functions ===

# Add new state variables after the existing ones
old_vars = "let bgOffset=0;"
new_vars = """let bgOffset=0;
let monsterDeath=0;
let lowHpPulse=0;
let levelUpText='';
let levelUpTextLife=0;
let streakFire=[];
let goldRain=[];
let attackTrail=[];
let depth=0;"""
html = html.replace(old_vars, new_vars)

# === 3. Replace drawCavernBg with depth-based backgrounds ===
old_bg_start = html.find('function drawCavernBg(){')
old_bg_end = html.find('function drawChest(x,y){')
new_bg = '''function drawCavernBg(){
  depth=state?Math.min(5,Math.floor(state.rooms_cleared/3)):0;
  const palettes=[
    ['#0a0a1a','#1a1a2e','#0f0f1a'],
    ['#0a0a1a','#1a1020','#0a0f0a'],
    ['#0a0010','#1a0a20','#0f0010'],
    ['#000a10','#001020','#000510'],
    ['#100000','#200010','#0f0000'],
    ['#0a000a','#200020','#100010'],
  ];
  const p=palettes[depth]||palettes[5];
  const g=ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,p[0]);g.addColorStop(0.5,p[1]);g.addColorStop(1,p[2]);
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  // Stalactites (color shifts with depth)
  const stColor=depth<2?'rgba(40,30,60,0.4)':depth<4?'rgba(60,20,40,0.4)':'rgba(40,10,50,0.4)';
  ctx.fillStyle=stColor;
  for(let i=0;i<6;i++){const x=(i*W/6+bgOffset%80)-20;ctx.beginPath();ctx.moveTo(x,H*0.28);ctx.lineTo(x+15,H*0.28);ctx.lineTo(x+7,H*0.35);ctx.fill()}
  // Floor
  ctx.fillStyle='rgba(15,10,30,0.6)';ctx.fillRect(0,H*0.7,W,H*0.3);
  ctx.fillStyle='rgba(25,15,45,0.4)';
  for(let i=0;i<4;i++)ctx.fillRect(i*W/4,H*0.72+Math.sin(i)*3,W/4-2,4);
  // Crystals (color shifts with depth)
  const crystalColors=[['#4dd0e1','#ce93d8','#80cbc4','#7c4dff','#ffd54f'],
    ['#a5d6a7','#ffab91','#80cbc4','#ce93d8','#fff59d'],
    ['#ce93d8','#b39ddb','#9fa8da','#7986cb','#d1c4e9'],
    ['#4fc3f7','#4dd0e1','#80deea','#b2ebf2','#e0f7fa'],
    ['#ff8a80','#ffab91','#ffcc80','#ffe0b2','#fff3e0'],
    ['#b39ddb','#ce93d8','#e1bee7','#f3e5f5','#f8bbd0']];
  const cset=crystalColors[depth]||crystalColors[5];
  const crystals=[[0.1,0.6,8,cset[0]],[0.85,0.55,6,cset[1]],[0.2,0.75,5,cset[2]],[0.7,0.8,7,cset[3]],[0.5,0.5,4,cset[4]]];
  for(const[cx,cy,sz,col]of crystals){
    const x=W*cx,y=H*cy;const glow=0.3+Math.sin(animTime+cx*10)*0.15;
    ctx.globalAlpha=glow;ctx.fillStyle=col;ctx.beginPath();ctx.moveTo(x,y-sz);ctx.lineTo(x-sz/2,y);ctx.lineTo(x+sz/2,y);ctx.closePath();ctx.fill();
    ctx.globalAlpha=glow*0.3;ctx.beginPath();ctx.arc(x,y-sz/2,sz*1.5,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=1;
  }
  // Floating dust particles (color shifts with depth)
  const dustColor=depth<3?'rgba(180,180,255,1)':'rgba(220,180,255,1)';
  for(let i=0;i<25;i++){
    const px=(i*37+animTime*15)%(W+20)-10;
    const py=(i*53+animTime*8)%H;
    const pa=0.15+Math.sin(animTime+i)*0.1;
    ctx.globalAlpha=pa;ctx.fillStyle=dustColor;ctx.beginPath();ctx.arc(px,py,1.2,0,Math.PI*2);ctx.fill();
  }
  ctx.globalAlpha=1;
  // Low HP vignette
  if(state&&state.hp>0){
    const hpPct=state.hp/state.max_hp;
    if(hpPct<0.3){
      lowHpPulse=Math.sin(animTime*3)*0.15+0.2;
      const vg=ctx.createRadialGradient(W/2,H/2,W*0.2,W/2,H/2,W*0.6);
      vg.addColorStop(0,'rgba(255,0,0,0)');
      vg.addColorStop(1,`rgba(255,0,0,${lowHpPulse})`);
      ctx.fillStyle=vg;ctx.fillRect(0,0,W,H);
    }
  }
}

'''

html = html.replace(html[old_bg_start:old_bg_end], new_bg)

# === 4. Add monster death animation and level-up burst to loop ===
old_loop_block = """if(attackAnim>0){attackAnim-=0.05;if(attackAnim<0)attackAnim=0}
  bgOffset+=0.5;"""
new_loop_block = """if(attackAnim>0){attackAnim-=0.05;if(attackAnim<0)attackAnim=0}
  if(monsterDeath>0){monsterDeath-=0.02;if(monsterDeath<0)monsterDeath=0}
  if(levelUpTextLife>0){levelUpTextLife-=0.015;if(levelUpTextLife<0)levelUpTextLife=0}
  if(streakFire.length>0){streakFire=streakFire.filter(f=>f.life>0);streakFire.forEach(f=>{f.y-=1;f.life-=0.02;f.x+=Math.sin(animTime*10)*2})}
  if(goldRain.length>0){goldRain=goldRain.filter(g=>g.life>0);goldRain.forEach(g=>{g.y+=g.vy;g.vy+=0.2;g.life-=0.02})}
  if(attackTrail.length>0){attackTrail=attackTrail.filter(t=>t.life>0);attackTrail.forEach(t=>{t.life-=0.05})}
  bgOffset+=0.5;"""
html = html.replace(old_loop_block, new_loop_block)

# === 5. Add level-up burst and streak fire drawing before drawParticles in loop ===
old_draw_part = 'drawParticles();drawDmgNums();drawFlash();drawBossIntro();drawRoomTransition()'
new_draw_part = '''drawStreakFire();drawGoldRain();drawAttackTrail();drawLevelUpText();
  drawParticles();drawDmgNums();drawFlash();drawBossIntro();drawRoomTransition()'''
html = html.replace(old_draw_part, new_draw_part)

# === 6. Add new drawing functions before drawParticles ===
old_part_func = 'function drawParticles(){'
new_funcs = '''function drawStreakFire(){
  if(streakFire.length===0)return;
  for(const f of streakFire){
    ctx.globalAlpha=f.life*0.7;ctx.fillStyle=f.color;
    ctx.beginPath();ctx.arc(f.x,f.y,f.size*(1+Math.sin(animTime*15)*0.3),0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=f.life;ctx.fillStyle='rgba(255,200,0,'+f.life*0.3+')';
    ctx.beginPath();ctx.arc(f.x,f.y,f.size*2,0,Math.PI*2);ctx.fill();
  }
  ctx.globalAlpha=1;
}
function drawGoldRain(){
  for(const g of goldRain){
    ctx.globalAlpha=g.life;ctx.fillStyle=g.color;
    ctx.beginPath();ctx.arc(g.x,g.y,g.size,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=g.life*0.5;ctx.beginPath();ctx.arc(g.x,g.y,g.size*1.5,0,Math.PI*2);ctx.fill();
  }
  ctx.globalAlpha=1;
}
function drawAttackTrail(){
  for(const t of attackTrail){
    ctx.globalAlpha=t.life*0.4;ctx.fillStyle=t.color;
    ctx.fillRect(t.x-2,t.y-15,4,30);
  }
  ctx.globalAlpha=1;
}
function drawLevelUpText(){
  if(levelUpTextLife<=0)return;
  const lt=levelUpTextLife;
  ctx.globalAlpha=lt;
  ctx.font='bold 32px system-ui';ctx.textAlign='center';
  const scl=1+(1-lt)*0.5;
  ctx.save();ctx.translate(W/2,H*0.3);ctx.scale(scl,scl);
  ctx.strokeStyle='#000';ctx.lineWidth=5;
  ctx.strokeText(levelUpText,0,0);
  ctx.fillStyle='#ce93d8';ctx.fillText(levelUpText,0,0);
  ctx.restore();
  ctx.globalAlpha=1;
}
function drawParticles(){'''
html = html.replace(old_part_func, new_funcs)

# === 7. Enhance onStateChange with new effects ===
old_levelup = "if(curr.level>(prev?.level||1)){\n    flashColor='#9b59b6';flashAlpha=0.5;spawnParticles(W*0.5,H*0.5,'#ce93d8',30)\n  }"
new_levelup = """if(curr.level>(prev?.level||1)){
    flashColor='#9b59b6';flashAlpha=0.5;spawnParticles(W*0.5,H*0.5,'#ce93d8',30);sfxLevelUp();
    levelUpText='LEVEL '+curr.level+'!';levelUpTextLife=1;
    goldRain.push(); // trigger
    for(let i=0;i<20;i++){goldRain.push({x:W/2+(Math.random()-0.5)*60,y:H*0.4,vy:-2-Math.random()*4,size:2+Math.random()*3,color:'#ffd700',life:1})}
  }"""
html = html.replace(old_levelup, new_levelup)

# === 8. Add streak fire on high streak ===
old_treasure = "if(curr.message_type==='treasure')"
new_streak_check = """// Streak fire
  if(curr.streak>=(prev?.streak||0)+1&&curr.streak>=3){
    for(let i=0;i<8;i++){streakFire.push({x:W*0.25+(Math.random()-0.5)*30,y:H*0.3+Math.random()*20,size:3+Math.random()*3,life:1,color:curr.streak>=5?'#ff416c':'#ff9800'})}
  }
  // Gold rain on treasure
  if(curr.message_type==='treasure')"
html = html.replace(old_treasure, new_streak_check)

# === 9. Add gold rain to treasure ===
old_treasure_fx = "if(curr.message_type==='treasure'){flashColor='#ffd700';flashAlpha=0.3;spawnParticles(W*0.5,H*0.4,'#ffd54f',20);sfxTreasure();chestOpen=true;chestAnim=0}"
new_treasure_fx = "if(curr.message_type==='treasure'){flashColor='#ffd700';flashAlpha=0.3;spawnParticles(W*0.5,H*0.4,'#ffd54f',20);sfxTreasure();chestOpen=true;chestAnim=0;for(let i=0;i<25;i++){goldRain.push({x:W/2+(Math.random()-0.5)*80,y:H*0.35,vy:-1-Math.random()*5,size:2+Math.random()*4,color:'#ffd700',life:1})}}"
html = html.replace(old_treasure_fx, new_treasure_fx)

# === 10. Add monster death animation ===
old_monster_dmg = "if(prev.monster&&curr.monster&&curr.monster.hp<prev.monster.hp){\n    spawnDmg(W*0.72,H*0.38,prev.monster.hp-curr.monster.hp,'monster');\n    spawnParticles(W*0.72,H*0.42,'#ffd54f',12);sfxHit();\n    attackAnim=1;attackAnimWho='player';\n  }"
new_monster_dmg = """if(prev.monster&&curr.monster&&curr.monster.hp<prev.monster.hp){
    spawnDmg(W*0.72,H*0.38,prev.monster.hp-curr.monster.hp,'monster');
    spawnParticles(W*0.72,H*0.42,'#ffd54f',12);sfxHit();
    attackAnim=1;attackAnimWho='player';
    // Attack trail
    for(let i=0;i<5;i++)attackTrail.push({x:W*0.25+i*15,y:H*0.45,life:1,color:'#4dd0e1'});
  }
  // Monster death
  if(prev.monster&&(!curr.monster||curr.mode!=='battle'&&curr.mode!=='boss')&&prev.mode==='battle'){
    monsterDeath=1;
    spawnParticles(W*0.72,H*0.42,'#ff5252',20);
    spawnParticles(W*0.72,H*0.42,'#ffd54f',15);
    for(let i=0;i<15;i++)goldRain.push({x:W*0.72+(Math.random()-0.5)*40,y:H*0.4,vy:-1-Math.random()*4,size:2+Math.random()*3,color:'#ffd700',life:1});
  }"""
html = html.replace(old_monster_dmg, new_monster_dmg)

# === 11. Fade out monster on death in drawBattleScene ===
old_monster_draw = "drawMonster(mx,my,1.8,mType,mHit,mAttacking);"
new_monster_draw = """if(monsterDeath>0){
      ctx.globalAlpha=monsterDeath;ctx.translate(0,monsterDeath*20);
      drawMonster(mx,my,1.8,mType,mHit,mAttacking);
      ctx.globalAlpha=1;
    }else{
      drawMonster(mx,my,1.8,mType,mHit,mAttacking);
    }"""
html = html.replace(old_monster_draw, new_monster_draw)

# === 12. Better room transition (slide + fade) ===
old_room_trans = """function drawRoomTransition(){
  if(roomTrans<=0)return;
  ctx.fillStyle=`rgba(0,0,0,${roomTrans})`;
  ctx.fillRect(0,0,W,H);
}"""
new_room_trans = """function drawRoomTransition(){
  if(roomTrans<=0)return;
  const t=roomTrans;
  ctx.fillStyle=`rgba(0,0,0,${t*0.8})`;
  ctx.fillRect(0,0,W,H);
  // Slide bars
  ctx.fillStyle='rgba(100,100,200,0.3)';
  for(let i=0;i<5;i++){
    const x=(1-t)*W*(i/5-0.5)*2;
    ctx.fillRect(x,H*i/5,W*0.1,H/5);
  }
  // Room number
  if(t>0.3&&state){
    ctx.globalAlpha=t;ctx.font='bold 20px system-ui';ctx.textAlign='center';
    ctx.fillStyle='#4dd0e1';ctx.strokeStyle='#000';ctx.lineWidth=3;
    ctx.strokeText('Room '+(state.rooms_cleared+1),W/2,H/2);
    ctx.fillText('Room '+(state.rooms_cleared+1),W/2,H/2);
    ctx.globalAlpha=1;
  }
}"""
html = html.replace(old_room_trans, new_room_trans)

# Write the refined frontend
with open('/root/workspace/codequest/refined_frontend.html', 'w') as f:
    f.write(html)
print('Refined frontend written:', len(html), 'chars')

# Verify JS syntax
script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
with open('/tmp/refined_js.js', 'w') as f:
    f.write(script)
"