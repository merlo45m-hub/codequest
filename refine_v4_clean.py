"""Round 4: brighter torches, more dramatic depth backgrounds, real player death animation."""
import re

with open('/root/workspace/codequest/v4_frontend.html', 'r') as f:
    html = f.read()

# === 1. Brighter torch glow ===
html = html.replace(
    "ctx.globalAlpha=0.15*flicker;ctx.fillStyle='#ff6600';ctx.beginPath();ctx.arc(tx,ty-5,25,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;",
    "ctx.globalAlpha=0.4*flicker;ctx.fillStyle='#ff4500';ctx.beginPath();ctx.arc(tx,ty-5,55,0,Math.PI*2);ctx.fill();ctx.fillStyle='#ff8c00';ctx.beginPath();ctx.arc(tx,ty-5,32,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;"
)
# Bigger flames
html = html.replace(
    "const fh=8+flicker*6;",
    "const fh=14+flicker*12;"
)

# === 2. More dramatic depth backgrounds ===
old_palettes = """const palettes=[
    ['#0a0a1a','#1a1a2e','#0f0f1a'],
    ['#0a0a1a','#1a1020','#0a0f0a'],
    ['#0a0010','#1a0a20','#0f0010'],
    ['#000a10','#001020','#000510'],
    ['#100000','#200010','#0f0000'],
    ['#0a000a','#200020','#100010'],
  ];"""
new_palettes = """const palettes=[
    ['#0a0a2a','#1a1a4e','#0a0a1a'],
    ['#0a1a0a','#1a3a10','#0a0f0a'],
    ['#1a0a2a','#3a1050','#0f0010'],
    ['#0a1a2a','#003040','#000510'],
    ['#1a0000','#3a0000','#1f0000'],
    ['#0a001a','#200040','#100010'],
    ['#001a0a','#103a10','#000500'],
    ['#1a1000','#3a2000','#1f0500'],
  ];"""
html = html.replace(old_palettes, new_palettes)

# Stalactites
old_stal = """let stColor=depth<2?'rgba(40,30,60,0.4)':depth<4?'rgba(60,20,40,0.4)':'rgba(40,10,50,0.4)';ctx.fillStyle=stColor;for(let i=0;i<6;i++){const x=(i*W/6+bgOffset%80)-20;ctx.beginPath();ctx.moveTo(x,H*0.28);ctx.lineTo(x+15,H*0.28);ctx.lineTo(x+7,H*0.35);ctx.fill()}"""
new_stal = """let stColor,stCount;
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
  }"""
html = html.replace(old_stal, new_stal)

# Floor + stalagmites
old_floor = """ctx.fillStyle='rgba(15,10,30,0.6)';ctx.fillRect(0,H*0.7,W,H*0.3);
  ctx.fillStyle='rgba(25,15,45,0.4)';for(let i=0;i<4;i++)ctx.fillRect(i*W/4,H*0.72+Math.sin(i)*3,W/4-2,4);"""
new_floor = """let flC=['rgba(15,10,30,0.6)','rgba(10,20,15,0.6)','rgba(20,10,30,0.6)','rgba(10,15,35,0.6)','rgba(30,10,15,0.6)','rgba(20,10,35,0.6)','rgba(10,30,15,0.6)','rgba(30,20,10,0.6)'];
  ctx.fillStyle=flC[depth%flC.length];ctx.fillRect(0,H*0.7,W,H*0.3);
  let smC=['rgba(25,20,40,0.4)','rgba(20,30,25,0.4)','rgba(30,20,40,0.4)','rgba(20,30,45,0.4)','rgba(40,20,25,0.4)','rgba(30,20,45,0.4)','rgba(20,40,25,0.4)','rgba(40,30,25,0.4)'];
  ctx.fillStyle=smC[depth%smC.length];
  for(let i=0;i<8;i++){const x=i*W/8;const h=3+Math.sin(i*1.3)*2;ctx.beginPath();ctx.moveTo(x,H*0.7);ctx.lineTo(x+8,H*0.7);ctx.lineTo(x+4,H*0.7+h);ctx.lineTo(x-4,H*0.7+h);ctx.fill()}"""
html = html.replace(old_floor, new_floor)

# Crystals
old_crys = """const crystals=[[0.1,0.6,8,cset[0]],[0.85,0.55,6,cset[1]],[0.2,0.75,5,cset[2]],[0.7,0.8,7,cset[3]],[0.5,0.5,4,cset[4]]];"""
new_crys = """let crDefs;
  switch(depth){
    case 0:crDefs=[[0.1,0.55,10,cset[0]],[0.85,0.5,8,cset[1]],[0.25,0.78,6,cset[2]],[0.7,0.82,9,cset[3]],[0.5,0.48,5,cset[4]],[0.92,0.7,6,cset[0]]];break;
    case 1:crDefs=[[0.12,0.58,10,cset[1]],[0.82,0.55,8,cset[2]],[0.2,0.75,6,cset[3]],[0.72,0.8,9,cset[0]],[0.45,0.5,5,cset[1]],[0.9,0.72,7,cset[2]]];break;
    case 2:crDefs=[[0.08,0.55,10,cset[4]],[0.88,0.5,8,cset[0]],[0.3,0.78,7,cset[1]],[0.68,0.82,9,cset[2]],[0.52,0.46,6,cset[3]],[0.95,0.7,7,cset[4]]];break;
    case 3:crDefs=[[0.15,0.55,10,cset[0]],[0.8,0.52,8,cset[1]],[0.25,0.76,7,cset[2]],[0.7,0.82,9,cset[3]],[0.48,0.48,5,cset[4]],[0.93,0.7,7,cset[0]]];break;
    case 4:crDefs=[[0.1,0.55,10,cset[0]],[0.85,0.5,8,cset[1]],[0.22,0.78,7,cset[2]],[0.72,0.8,9,cset[3]],[0.48,0.48,5,cset[4]],[0.91,0.7,7,cset[0]]];break;
    case 5:crDefs=[[0.12,0.55,10,cset[1]],[0.82,0.52,8,cset[2]],[0.25,0.76,7,cset[3]],[0.7,0.82,9,cset[4]],[0.5,0.48,6,cset[0]],[0.92,0.7,7,cset[1]]];break;
    case 6:crDefs=[[0.08,0.55,10,cset[2]],[0.88,0.5,8,cset[3]],[0.28,0.78,7,cset[4]],[0.67,0.8,9,cset[0]],[0.47,0.46,5,cset[1]],[0.94,0.7,7,cset[2]]];break;
    case 7:crDefs=[[0.13,0.55,10,cset[3]],[0.83,0.52,8,cset[4]],[0.25,0.76,7,cset[0]],[0.71,0.82,9,cset[1]],[0.49,0.48,5,cset[2]],[0.93,0.7,7,cset[3]]];break;
    default:crDefs=[[0.1,0.55,8,cset[0]],[0.85,0.55,6,cset[1]],[0.2,0.75,5,cset[2]],[0.7,0.8,7,cset[3]],[0.5,0.5,4,cset[4]]];
  }"""
html = html.replace(old_crys, new_crys)

old_crys_draw = """for(const[cx,cy,sz,col]of crystals){"""
new_crys_draw = """for(const[cx,cy,sz,col]of crDefs){"""
html = html.replace(old_crys_draw, new_crys_draw)

# === 3. Player death animation ===
# Add deathAnim variable
html = html.replace(
    'let defeatLvl=0;',
    'let defeatLvl=0;\nlet deathAnim=0;'
)

# Add deathAnim update to loop
old_loop = """if(hitStop>0){hitStop-=0.03;if(hitStop<0)hitStop=0;animTime-=0.016}
  if(critFlash>0){critFlash-=0.05;if(critFlash<0)critFlash=0}
  if(bossZoom>0){bossZoom-=0.01;if(bossZoom<0)bossZoom=0}
  if(walkAnim>0){walkAnim-=0.02;if(walkAnim<0)walkAnim=0}
  if(potionAnim>0){potionAnim-=0.02}"""
new_loop = """let deathAnim=0;
  if(hitStop>0){hitStop-=0.03;if(hitStop<0)hitStop=0;animTime-=0.016}
  if(critFlash>0){critFlash-=0.05;if(critFlash<0)critFlash=0}
  if(bossZoom>0){bossZoom-=0.01;if(bossZoom<0)bossZoom=0}
  if(walkAnim>0){walkAnim-=0.02;if(walkAnim<0)walkAnim=0}
  if(potionAnim>0){potionAnim-=0.02}
  if(deathAnim>0){deathAnim+=0.04;if(deathAnim>1)deathAnim=1}"""
html = html.replace(old_loop, new_loop)

# Better gameover: player rotates and fades with death particles
old_gover = """if(defeatLvl>=1)ctx.globalAlpha=defeatLvl/2+0.5;
    else if(defeatLvl>=0.8)ctx.globalAlpha=1-(defeatLvl*1.5-1)*0.5;
    else if(defeatLvl>=0.5){ctx.lineWidth=8;ctx.globalAlpha=1;}
    else if(defeatLvl>=0.3){ctx.lineWidth=6;}else if(defeatLvl<1){ctx.lineWidth=3;}
    ctx.save();ctx.translate(W*0.5,cy);ctx.scale(2,2);const ang=Math.PI/2+(defeatLvl-0.5)*Math.PI;
    ctx.globalAlpha=0.3+defeatLvl*0.2;ctx.rotate(ang);
    drawPlayer(0,0,1,false,false);ctx.globalAlpha=1;ctx.restore();
  }else if(gameMode==='explore'&&potionAnim>0){
    drawPlayer(W*0.5,cy,2,false,false);"""
new_gover = """if(defeatLvl>=1)ctx.globalAlpha=defeatLvl/2+0.5;
    else if(defeatLvl>=0.8)ctx.globalAlpha=1-(defeatLvl*1.5-1)*0.5;
    else if(defeatLvl>=0.5){ctx.lineWidth=8;ctx.globalAlpha=1;}
    else if(defeatLvl>=0.3){ctx.lineWidth=6;}else if(defeatLvl<1){ctx.lineWidth=3;}
    ctx.save();ctx.translate(W*0.5,cy);
    if(defeatLvl>=1){ctx.scale(2,2);ctx.globalAlpha=0.5-defeatLvl*0.3;}
    else if(defeatLvl<0.5){ctx.scale(2,2);ctx.globalAlpha=0.5;}
    else {ctx.scale(2,2);const a=1-(defeatLvl-0.5)*1.5;if(a<0)a=0;ctx.globalAlpha=a;}
    const ang=Math.PI/2+(defeatLvl-0.5)*Math.PI;
    ctx.rotate(ang);
    drawPlayer(0,0,1,false,false);
    ctx.globalAlpha=1;ctx.restore();
    // Death particles
    if(defeatLvl>0.3&&Math.random()<0.4){
      spawnParticles(W*0.5+Math.random()*60-30,cy+Math.random()*40-20,'#69f0ae',2)
    }
  }else if(gameMode==='explore'&&potionAnim>0){
    drawPlayer(W*0.5,cy,2,false,false);"""
html = html.replace(old_gover, new_gover)

with open('/root/workspace/codequest/v4_frontend.html', 'w') as f:
    f.write(html)
print('v4 frontend written:', len(html), 'chars')

script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
with open('/tmp/v4_js.js', 'w') as f:
    f.write(script)
