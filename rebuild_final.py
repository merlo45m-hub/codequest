"""Full rebuild: v2 base + v4 (torches, depth, stalactites, death) + v5 (spear, XP bar, bigger effects)."""
import re

# Start from v2 base
with open('/root/workspace/codequest/v2_frontend.html', 'r') as f:
    html = f.read()

print(f'Base v2: {len(html)} chars')

# === V4: Brighter torches ===
# Add torchFlicker init
html = html.replace(
    "window.addEventListener('resize',resize);resize()",
    "window.addEventListener('resize',resize);resize();\nfor(let i=0;i<6;i++)torchFlicker.push(0.7+Math.random()*0.3)"
)

# Add torch drawing to drawCavernBg (before dust particles)
old_dust = "  // Floating dust particles (color shifts with depth)"
# Add torch section
new_torches = """  // Wall torches
  const torchPositions=[[0.05,0.35],[0.95,0.35],[0.05,0.55],[0.95,0.55],[0.05,0.75],[0.95,0.75]];
  for(let i=0;i<torchPositions.length;i++){
    const tx=W*torchPositions[i][0],ty=H*torchPositions[i][1];
    ctx.fillStyle='#5a3a1a';ctx.fillRect(tx-2,ty,4,12);
    const flicker=torchFlicker[i%torchFlicker.length];
    const fh=14+flicker*12;
    ctx.fillStyle='rgba(255,100,0,0.6)';ctx.beginPath();ctx.ellipse(tx,ty-fh/2,5,fh,0,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='rgba(255,180,0,0.8)';ctx.beginPath();ctx.ellipse(tx,ty-fh/3,3,fh*0.6,0,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='rgba(255,255,200,0.9)';ctx.beginPath();ctx.ellipse(tx,ty-fh/5,1.5,fh*0.3,0,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=0.4*flicker;ctx.fillStyle='#ff4500';ctx.beginPath();ctx.arc(tx,ty-5,55,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#ff8c00';ctx.beginPath();ctx.arc(tx,ty-5,32,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=1;
    if(Math.random()<0.1)torchFlicker[i%torchFlicker.length]=0.5+Math.random()*0.5;
  }
  """
html = html.replace(old_dust, new_torches + old_dust)

print('V4 torches: OK')

# === V4: Depth-based palettes in drawCavernBg ===
# Replace the gradient with depth-aware version
old_grad = """const g=ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,'#0a0a1a');g.addColorStop(0.5,'#1a1a2e');g.addColorStop(1,'#0f0f1a');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  // Cave ceiling stalactites
  ctx.fillStyle='rgba(40,30,60,0.4)';
  for(let i=0;i<6;i++){const x=(i*W/6+bgOffset%80)-20;ctx.beginPath();ctx.moveTo(x,H*0.28);ctx.lineTo(x+15,H*0.28);ctx.lineTo(x+7,H*0.35);ctx.fill()}
  // Floor
  ctx.fillStyle='rgba(20,15,35,0.6)';ctx.fillRect(0,H*0.7,W,H*0.3);
  ctx.fillStyle='rgba(30,20,50,0.4)';
  for(let i=0;i<4;i++)ctx.fillRect(i*W/4,H*0.72+Math.sin(i)*3,W/4-2,4);"""
new_bg = """let depth=state?Math.min(7,Math.floor(state.rooms_cleared/3)):0;
  const palettes=[
    ['#0a0a2a','#1a1a4e','#0a0a1a'],
    ['#0a1a0a','#1a3a10','#0a0f0a'],
    ['#1a0a2a','#3a1050','#0f0010'],
    ['#0a1a2a','#003040','#000510'],
    ['#1a0000','#3a0000','#1f0000'],
    ['#0a001a','#200040','#100010'],
    ['#001a0a','#103a10','#000500'],
    ['#1a1000','#3a2000','#1f0500'],
  ];
  const p=palettes[depth]||palettes[7];
  const g=ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,p[0]);g.addColorStop(0.5,p[1]);g.addColorStop(1,p[2]);
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  // Stalactites (depth-based)
  let stColor,stCount;
  switch(depth){
    case 0:stColor='rgba(30,20,60,0.5)';stCount=8;break;
    case 1:stColor='rgba(20,50,20,0.5)';stCount=10;break;
    case 2:stColor='rgba(40,20,60,0.5)';stCount=6;break;
    case 3:stColor='rgba(20,40,60,0.5)';stCount=12;break;
    case 4:stColor='rgba(50,20,20,0.5)';stCount=9;break;
    case 5:stColor='rgba(40,10,60,0.5)';stCount=7;break;
    case 6:stColor='rgba(30,60,30,0.5)';stCount=11;break;
    case 7:stColor='rgba(60,40,20,0.5)';stCount=8;break;
    default:stColor='rgba(30,20,60,0.5)';stCount=6;
  }
  ctx.fillStyle=stColor;
  const period=depth%2===0?60:100;
  for(let i=0;i<stCount;i++){
    const x=(i*W/stCount+bgOffset%period)-40;
    const h=12+Math.sin(i*1.7+bgOffset*0.03)*8;
    ctx.beginPath();
    ctx.moveTo(x-7,H*0.25+h*0.1);
    ctx.lineTo(x+7,H*0.25+h*0.1);
    ctx.lineTo(x+2,H*0.25+h);
    ctx.lineTo(x-2,H*0.25+h);
    ctx.fill();
  }
  // Floor (depth-based)
  const flC=['rgba(15,10,30,0.6)','rgba(10,20,15,0.6)','rgba(20,10,30,0.6)','rgba(10,15,35,0.6)','rgba(30,10,15,0.6)','rgba(20,10,35,0.6)','rgba(10,30,15,0.6)','rgba(30,20,10,0.6)'];
  ctx.fillStyle=flC[depth%flC.length];ctx.fillRect(0,H*0.7,W,H*0.3);
  const smC=['rgba(25,20,40,0.4)','rgba(20,30,25,0.4)','rgba(30,20,40,0.4)','rgba(20,30,45,0.4)','rgba(40,20,25,0.4)','rgba(30,20,45,0.4)','rgba(20,40,25,0.4)','rgba(40,30,25,0.4)'];
  ctx.fillStyle=smC[depth%smC.length];
  for(let i=0;i<8;i++){const x=i*W/8;const h=3+Math.sin(i*1.3)*2;ctx.beginPath();ctx.moveTo(x,H*0.7);ctx.lineTo(x+8,H*0.7);ctx.lineTo(x+4,H*0.7+h);ctx.lineTo(x-4,H*0.7+h);ctx.fill()}
  // Crystals (depth-based)
  const cset=[['#4dd0e1','#ce93d8','#80cbc4','#7c4dff','#ffd54f'],['#a5d6a7','#ffab91','#80cbc4','#ce93d8','#fff59d'],['#ce93d8','#b39ddb','#9fa8da','#7986cb','#d1c4e9'],['#4fc3f7','#4dd0e1','#80deea','#b2ebf2','#e0f7fa'],['#ff8a80','#ffab91','#ffcc80','#ffe0b2','#fff3e0'],['#b39ddb','#ce93d8','#e1bee7','#f3e5f5','#f8bbd0'],['#a5d6a7','#81c784','#66bb6a','#4caf50','#388e3c'],['#ff8a80','#ffab91','#ffcc80','#ffe0b2','#ffecb3']];
  const c=colset[depth]||cset[5];
  const crDefs=depth<8?[[0.1,0.55,10,c[0]],[0.85,0.5,8,c[1]],[0.25,0.78,6,c[2]],[0.7,0.82,9,c[3]],[0.5,0.48,5,c[4]],[0.92,0.7,6,c[0]]]:[[0.1,0.6,8,c[0]],[0.85,0.55,6,c[1]],[0.2,0.75,5,c[2]],[0.7,0.8,7,c[3]],[0.5,0.5,4,c[4]]];
  for(const[cx,cy,sz,col]of crDefs){"""
html = html.replace(old_grad, new_bg)

print('V4 depth bg: OK')

# Fix crystal variable name (was 'c' but should be 'cset')
html = html.replace("const c=colset[depth]||cset[5];", "const c=cset[depth%cset.length];")

# === V4: Player death animation ===
# Add deathAnim variable
html = html.replace("let defeatLvl=0;", "let defeatLvl=0;\nlet deathAnim=0;")

# Add deathAnim update to loop
old_loop = """if(hitStop>0){hitStop-=0.03;if(hitStop<0)hitStop=0;animTime-=0.016}
  if(critFlash>0){critFlash-=0.05;if(critFlash<0)critFlash=0}
  if(bossZoom>0){bossZoom-=0.01;if(bossZoom<0)bossZoom=0}
  if(walkAnim>0){walkAnim-=0.02;if(walkAnim<0)walkAnim=0}
  if(potionAnim>0){potionAnim-=0.02}"""
new_loop = """if(hitStop>0){hitStop-=0.03;if(hitStop<0)hitStop=0;animTime-=0.016}
  if(critFlash>0){critFlash-=0.05;if(critFlash<0)critFlash=0}
  if(bossZoom>0){bossZoom-=0.01;if(bossZoom<0)bossZoom=0}
  if(walkAnim>0){walkAnim-=0.02;if(walkAnim<0)walkAnim=0}
  if(potionAnim>0){potionAnim-=0.02}
  if(deathAnim>0){deathAnim+=0.04;if(deathAnim>1)deathAnim=1}"""
html = html.replace(old_loop, new_loop)

# Better gameover
old_gover = """if(defeatLvl>=1)ctx.globalAlpha=defeatLvl/2+0.5;
    else if(defeatLvl>=0.8)ctx.globalAlpha=1-(defeatLvl*1.5-1)*0.5;
    else if(defeatLvl>=0.5){ctx.lineWidth=8;ctx.globalAlpha=1;}
    else if(defeatLvl>=0.3){ctx.lineWidth=6;}else if(defeatLvl<1){ctx.lineWidth=3;}
    ctx.save();ctx.translate(W*0.5,cy);ctx.scale(2,2);const ang=Math.PI/2+(defeatLvl-0.5)*Math.PI;
    ctx.globalAlpha=0.3+defeatLvl*0.2;ctx.rotate(ang);
    drawPlayer(0,0,1,false,false);ctx.globalAlpha=1;ctx.restore();"""
new_gover = """if(defeatLvl>=1)ctx.globalAlpha=defeatLvl/2+0.5;
    else if(defeatLvl>=0.8)ctx.globalAlpha=1-(defeatLvl*1.5-1)*0.5;
    else if(defeatLvl>=0.5){ctx.lineWidth=8;ctx.globalAlpha=1;}
    else if(defeatLvl>=0.3){ctx.lineWidth=6;}else if(defeatLvl<1){ctx.lineWidth=3;}
    ctx.save();ctx.translate(W*0.5,cy);
    if(defeatLvl>=1){ctx.scale(2,2);ctx.globalAlpha=0.5-defeatLvl*0.3;}
    else if(defeatLvl<0.5){ctx.scale(2,2);ctx.globalAlpha=0.5;}
    else{ctx.scale(2,2);const a=1-(defeatLvl-0.5)*1.5;if(a<0)a=0;ctx.globalAlpha=a;}
    const ang=Math.PI/2+(defeatLvl-0.5)*Math.PI;
    ctx.rotate(ang);
    drawPlayer(0,0,1,false,false);
    ctx.globalAlpha=1;ctx.restore();
    if(defeatLvl>0.3&&Math.random()<0.4)spawnParticles(W*0.5+Math.random()*60-30,cy+Math.random()*40-20,'#69f0ae',2);"""
html = html.replace(old_gover, new_gover)

print('V4 death: OK')

# === V4: XP bar in drawPlayer ===
old_player_body = "ctx.fillStyle='#000';ctx.fillRect(x-2*scl,yp+2.5*scl,4*scl,1.5*scl);ctx.fillStyle='#2ecc71';ctx.fillRect(x-2*scl,yp+2.5*scl,4*scl*hp,1.5*scl);"
new_player_body = """ctx.fillStyle='#000';ctx.fillRect(x-2*scl,yp+2.5*scl,4*scl,1.5*scl);ctx.fillStyle='#2ecc71';ctx.fillRect(x-2*scl,yp+2.5*scl,4*scl*hp,1.5*scl);
    if(scl>=2&&hp>0){const xpW=12*scl;ctx.fillStyle='#333';ctx.fillRect(x-2*scl,yp-3*scl,xpW,2);ctx.fillStyle='#f39c12';ctx.fillRect(x-2*scl,yp-3*scl,xpW*hp,2);}"""
html = html.replace(old_player_body, new_player_body)

print('V4 XP bar: OK')

# === V5: Bigger attack particles ===
html = html.replace("spawnParticles(W*0.72,H*0.42,'#ffd54f',12);sfxHit()", "spawnParticles(W*0.72,H*0.42,'#ffd54f',30);sfxHit()")
html = html.replace("spawnParticles(W*0.25,H*0.42,'#ff5252',15)", "spawnParticles(W*0.25,H*0.42,'#ff5252',25)")

# === V5: Spear trail ===
old_atk = "attackAnim=1;attackAnimWho='player';\n    for(let i=0;i<5;i++)attackTrail.push({x:W*0.25+i*15,y:H*0.45,life:1,color:'#4dd0e1'});"

new_atk = "attackAnim=1;attackAnimWho='player';\n    for(let i=0;i<8;i++)attackTrail.push({x:W*0.25+i*12,y:H*0.45,life:1,color:curr.streak>=3?'#ff416c':'#4dd0e1'});\n    for(let i=0;i<12;i++)spearTrails.push({x:W*0.25+(i*18),y:H*0.42+Math.sin(i)*5,life:1,color:'#4dd0e1'});"

html = html.replace(old_atk, new_atk)

# spearTrails variable
html = html.replace("let attackTrail=[];", "let attackTrail=[];\nlet spearTrails=[];")

# Slower trail decay + spear decay
old_decay = """if(attackTrail.length>0){attackTrail=attackTrail.filter(t=>t.life>0);attackTrail.forEach(t=>{t.life-=0.05})}"""
new_decay = """if(attackTrail.length>0){attackTrail=attackTrail.filter(t=>t.life>0);attackTrail.forEach(t=>{t.life-=0.035})}
  if(spearTrails.length>0){spearTrails=spearTrails.filter(t=>t.life>0);spearTrails.forEach(t=>{t.life-=0.025})}"""
html = html.replace(old_decay, new_decay)

# Add drawSpears + call it
html = html.replace("function drawGoldRain(){",
    "function drawSpears(){\n  if(spearTrails.length===0)return;\n  for(const s of spearTrails){\n    ctx.globalAlpha=s.life;ctx.fillStyle=s.color;\n    ctx.fillRect(s.x-1,s.y-12,2,20);\n  }\n  ctx.globalAlpha=1;\n}\nfunction drawGoldRain(){")
html = html.replace("drawGoldRain();drawAttackTrail();drawLevelUpText()",
    "drawGoldRain();drawAttackTrail();drawSpears();drawLevelUpText()")

# === V5: Stronger crit ===
html = html.replace("critFlash=1;hitStop=0.5;spawnParticles(W*0.72,H*0.42,'#fff',20);",
    "critFlash=1;hitStop=0.8;shakeTime=20;shakeMag=20;spawnParticles(W*0.72,H*0.42,'#fff',30);spawnParticles(W*0.72,H*0.42,'#ffd54f',20);")

print('V5 spear + crit: OK')

# Write final
with open('/root/workspace/codequest/final_frontend.html', 'w') as f:
    f.write(html)
print(f'Final frontend: {len(html)} chars')

script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
with open('/tmp/final_js.js', 'w') as f:
    f.write(script)
print('JS extracted')
