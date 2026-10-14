"""
🚪 DOORS 3D – Trò chơi giải đố kinh dị 5 cửa, góc nhìn thứ nhất (lấy cảm hứng từ Doors trong Roblox)
Chạy:  streamlit run app.py
Game 3D chạy bằng Three.js, nhúng vào Streamlit qua components.html.
"""
import json
import re
import unicodedata

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="DOORS 3D", page_icon="🚪", layout="wide")


# ---------------------------------------------------------------------------
# DỮ LIỆU CÂU ĐỐ (sửa tại đây)
# Mỗi cửa có 3 câu. Đúng -> nhận 1 chữ số. Ghép theo "order" để ra mật mã.
#   q: câu hỏi | a: các đáp án chấp nhận (không cần dấu) | digit: chữ số | hint: gợi ý
# ---------------------------------------------------------------------------
DOORS = [
    {
        "name": "Sảnh đón tiếp",
        "intro": "Ánh đèn chập chờn. Hãy tìm 3 manh mối trong phòng.",
        "order": [0, 1, 2],
        "order_text": "Ghép chìa 1 → chìa 2 → chìa 3.",
        "questions": [
            {"q": "Cái gì càng lấy đi càng lớn?", "a": ["cai ho", "ho", "cai lo", "lo"],
             "digit": 4, "hint": "Bạn thường thấy nó khi đào đất."},
            {"q": "Có 3 quả táo, bạn lấy đi 2 quả. Vậy bạn đang có mấy quả táo?", "a": ["2", "hai"],
             "digit": 7, "hint": "Hỏi 'bạn có' chứ không hỏi 'còn lại'."},
            {"q": "Cái gì có chìa nhưng không mở được ổ khóa nào?",
             "a": ["dan piano", "piano", "ban phim", "dan organ", "dan"],
             "digit": 1, "hint": "Nhạc cụ có phím đen phím trắng."},
        ],
    },
    {
        "name": "Thư viện bỏ hoang",
        "intro": "Bụi phủ kín mọi thứ. Có tiếng thì thầm: 'Hãy suy nghĩ...'",
        "order": [2, 1, 0],
        "order_text": "Ghép NGƯỢC: chìa 3 → chìa 2 → chìa 1.",
        "questions": [
            {"q": "Điền số tiếp theo: 2, 6, 12, 20, 30, ?", "a": ["42"],
             "digit": 3, "hint": "Hiệu giữa các số liên tiếp: 4, 6, 8, 10..."},
            {"q": "Có một từ trong từ điển luôn được 'viết sai'. Từ đó là gì?", "a": ["sai"],
             "digit": 8, "hint": "Chính câu hỏi đã chứa đáp án."},
            {"q": "Giải mã (mỗi chữ cái lùi 1 vị trí trong bảng chữ cái): EPPS", "a": ["door"],
             "digit": 5, "hint": "E lùi 1 vị trí là D."},
        ],
    },
    {
        "name": "Phòng thí nghiệm",
        "intro": "Mùi hóa chất nồng nặc. Mọi thứ đều có vẻ không ổn...",
        "order": [1, 0, 2],
        "order_text": "Ghép chìa 2 → chìa 1 → chìa 3.",
        "questions": [
            {"q": "Một người đi bộ 3 km/giờ. Sau 2 giờ 30 phút đi được bao nhiêu km?", "a": ["7.5"],
             "digit": 9, "hint": "3 × 2,5"},
            {"q": "Điền số tiếp theo: 1, 1, 2, 3, 5, 8, ?", "a": ["13"],
             "digit": 6, "hint": "Mỗi số bằng tổng hai số đứng trước."},
            {"q": "Ký hiệu hóa học của vàng là gì?", "a": ["au"],
             "digit": 0, "hint": "Từ tiếng Latin 'Aurum'."},
        ],
    },
    {
        "name": "Hầm tối",
        "intro": "Có thứ gì đó đang di chuyển trong bóng tối...",
        "order": [1, 2, 0],
        "order_text": "Ghép chìa 2 → chìa 3 → chìa 1.",
        "questions": [
            {"q": "Mình có thành phố nhưng không có nhà, có núi nhưng không có cây, có sông nhưng không có nước. Mình là gì?",
             "a": ["ban do", "map", "cai ban do"], "digit": 2, "hint": "Bạn dùng nó để tìm đường."},
            {"q": "Số nhị phân 1011 bằng số thập phân nào?", "a": ["11"],
             "digit": 7, "hint": "8 + 0 + 2 + 1"},
            {"q": "Tôi nói mà không có miệng, nghe mà không có tai, chỉ sống nhờ không khí. Tôi là gì?",
             "a": ["tieng vang", "vang", "echo", "tieng doi"], "digit": 3,
             "hint": "Hét vào hang núi sẽ nghe thấy tôi."},
        ],
    },
    {
        "name": "Phòng cuối cùng",
        "intro": "Cánh cửa cuối cùng, to lớn và lạnh lẽo. Chỉ còn một bước nữa...",
        "order": [2, 0, 1],
        "order_text": "Ghép chìa 3 → chìa 1 → chìa 2.",
        "questions": [
            {"q": "Tôi bay mà không có cánh, khóc mà không có mắt. Tôi là gì?",
             "a": ["may", "dam may", "may den", "dam may den"], "digit": 1, "hint": "Nhìn lên trời khi sắp mưa."},
            {"q": "Trong cuộc đua, bạn vượt qua người đang đứng thứ 2. Giờ bạn thứ mấy?",
             "a": ["2", "hai", "thu 2", "thu hai"], "digit": 9, "hint": "Bạn thế chỗ người đó."},
            {"q": "Trong game Doors, thực thể nháy đèn rồi lao qua cực nhanh tên là gì? (tiếng Anh, 1 từ)",
             "a": ["rush"], "digit": 4, "hint": "Nó bắt đầu bằng chữ R."},
        ],
    },
]


def normalize(text: str) -> str:
    """Bỏ dấu, viết thường (khớp với hàm norm() bên JS)."""
    text = text.strip().lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace(",", ".")
    text = re.sub(r"[^a-z0-9. ]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def build_data() -> str:
    out = []
    for d in DOORS:
        out.append({
            "name": d["name"], "intro": d["intro"], "order": d["order"], "order_text": d["order_text"],
            "questions": [
                {"q": q["q"], "a": [normalize(x) for x in q["a"]], "digit": q["digit"], "hint": q["hint"]}
                for q in d["questions"]
            ],
        })
    return json.dumps(out, ensure_ascii=False)


# ---------------------------------------------------------------------------
# GAME 3D (HTML + Three.js)
# ---------------------------------------------------------------------------
GAME_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#000;font-family:Georgia,serif;color:#eee;user-select:none}
  #c{position:absolute;inset:0}
  .ov{position:absolute;inset:0;display:none;flex-direction:column;align-items:center;justify-content:center;
      background:radial-gradient(ellipse at center,rgba(30,8,8,.88),rgba(0,0,0,.97));text-align:center;padding:20px;z-index:20}
  .ov h1{font-size:64px;letter-spacing:14px;margin:0 0 10px;color:#b3141a;text-shadow:0 0 18px #600,0 0 4px #000}
  .ov p{max-width:580px;line-height:1.55;color:#c9c0b0}
  button{background:#3a0d0d;color:#eee;border:1px solid #9a2a2a;padding:10px 22px;font-size:16px;
         border-radius:4px;cursor:pointer;margin:4px;font-family:inherit;letter-spacing:1px}
  button:hover{background:#6a1414;box-shadow:0 0 12px #a00}
  #hud{position:absolute;top:10px;left:12px;font-size:17px;text-shadow:0 0 4px #000;z-index:5;line-height:1.5}
  #ks{color:#ffd86b;font-size:20px}
  #ot{font-size:13px;color:#bbb}
  #help{position:absolute;bottom:8px;left:12px;font-size:12px;color:#8a8a8a;z-index:5;text-shadow:0 0 3px #000}
  #cross{position:absolute;left:50%;top:50%;width:4px;height:4px;margin:-2px;border-radius:50%;
         background:rgba(255,255,255,.45);z-index:5;pointer-events:none}
  #prompt{position:absolute;left:50%;top:58%;transform:translateX(-50%);background:rgba(0,0,0,.65);
          padding:6px 14px;border-radius:4px;font-size:18px;display:none;z-index:6;border:1px solid #9a2a2a}
  #banner{position:absolute;left:50%;top:14%;transform:translateX(-50%);text-align:center;white-space:pre-line;
          font-size:22px;text-shadow:0 0 8px #000;opacity:0;transition:opacity .5s;z-index:6;max-width:80%;pointer-events:none}
  #whisper{position:absolute;font-size:30px;font-style:italic;color:#8a0c0c;opacity:0;transition:opacity 1s;
           z-index:4;pointer-events:none;text-shadow:0 0 10px #000;letter-spacing:3px}
  #flash{position:absolute;inset:0;background:#a00;opacity:0;pointer-events:none;transition:opacity .45s;z-index:7}
  #fade{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none;transition:opacity .8s;z-index:8}
  #hide{position:absolute;inset:0;display:none;pointer-events:none;z-index:4;
        background:linear-gradient(#000 0 40%,transparent 40% 58%,#000 58% 100%)}
  #vig{position:absolute;inset:0;pointer-events:none;z-index:3;
       background:radial-gradient(ellipse at center,transparent 38%,rgba(0,0,0,.55) 75%,rgba(0,0,0,.95) 100%)}
  #grain{position:absolute;inset:0;width:100%;height:100%;image-rendering:pixelated;opacity:.2;
         mix-blend-mode:overlay;pointer-events:none;z-index:3}
  #lowhp{position:absolute;inset:0;pointer-events:none;z-index:3;opacity:0;
         background:radial-gradient(ellipse at center,transparent 35%,rgba(150,0,0,.75) 100%)}
  #lowhp.pulse{animation:pl 1.1s infinite}
  @keyframes pl{0%,100%{opacity:.25}50%{opacity:1}}
  #modal{position:absolute;inset:0;display:none;align-items:center;justify-content:center;
         background:rgba(0,0,0,.65);z-index:15}
  #box{background:#150d08;border:2px solid #7a2a2a;border-radius:8px;padding:22px;width:min(520px,86%);
       text-align:center;box-shadow:0 0 40px #300}
  #mt{color:#c9a050;font-size:22px;margin-bottom:10px}
  #mq{font-size:18px;line-height:1.5;margin-bottom:12px}
  #mi{width:80%;padding:9px;font-size:18px;border-radius:4px;border:1px solid #666;background:#241810;color:#fff;
      text-align:center;outline:none}
  #fb{min-height:24px;margin:10px 0;color:#ffd86b}
</style>
</head>
<body>
<div id="c"></div>
<div id="vig"></div><canvas id="grain"></canvas><div id="lowhp"></div>
<div id="cross"></div>
<div id="hud"><div id="dn"></div><div id="hp"></div><div id="hn"></div><div id="ks"></div><div id="ot"></div></div>
<div id="help">WASD: di chuyển · Chuột: nhìn (kéo chuột nếu không khóa được) · E: tương tác · Shift: chạy · Esc: nhả chuột</div>
<div id="prompt"></div>
<div id="banner"></div>
<div id="whisper"></div>
<div id="hide"></div>
<div id="flash"></div>
<div id="fade"></div>

<div id="modal"><div id="box">
  <div id="mt"></div><div id="mq"></div>
  <input id="mi" autocomplete="off" spellcheck="false">
  <div id="fb"></div>
  <button id="b1">Trả lời</button><button id="b2">💡 Gợi ý</button><button id="b3">Đóng (Esc)</button>
</div></div>

<div id="menu" class="ov" style="display:flex">
  <h1>DOORS</h1>
  <p>Bạn bị kẹt trong một khách sạn bị bỏ hoang. Mỗi phòng có <b>3 manh mối</b> phát sáng.
  Giải đố để lấy <b>chìa khóa</b>, ghép thành mật mã mở cửa.<br><br>
  ⚡ Khi đèn nhấp nháy, <b>RUSH</b> sắp lao qua phòng: hãy <b>trốn vào tủ</b> hoặc né sang bên!<br>
  👁️ Những đôi mắt trong bóng tối sẽ biến mất khi bạn nhìn thẳng vào chúng.<br>
  Có 3 ❤️. Sai đáp án hoặc bị Rush đâm sẽ mất 1 ❤️.<br><br>
  <i>Nên đeo tai nghe và tắt đèn phòng.</i></p>
  <div><button id="start">▶ BẮT ĐẦU</button><button id="qual">⚙️ Chất lượng: Cao</button></div>
</div>
<div id="over" class="ov"><h1>BẠN ĐÃ CHẾT</h1><p id="overmsg"></p><button id="retry">🔄 Thử lại</button></div>
<div id="win" class="ov"><h1 style="color:#d9b45a">THOÁT ĐƯỢC!</h1><p>Bạn đã vượt qua cả 5 cánh cửa... lần này.</p><button id="again">🔄 Chơi lại</button></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function(){
const DOORS = __DATA__;
const MAX_HP=3, HINTS0=5, RW=12, RD=16, RH=4;
const $=id=>document.getElementById(id);
let HQ=true;
let hp=MAX_HP, hints=HINTS0, door=0, solved=[false,false,false], hintShown={};
let state='menu', modalOpen=false, modalMode='q', modalIdx=0, hidden=false, doorOpen=false, transitioning=false;
let yaw=0, pitch=0, dragging=false, shake=0, bob=0, rush=null, rushTimer=25, bannerT=null, cur=null, wardI=null;
let keys={}, tt=0, stepT=0, hbT=0, evT=14, flickT=0, nextFlick=12, lampF=1;

// ---------- Renderer / Scene ----------
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
renderer.setSize(innerWidth,innerHeight);
renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.3;
renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
$('c').appendChild(renderer.domElement);
const canvas=renderer.domElement;
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x030101);
scene.fog=new THREE.FogExp2(0x050202,0.075);
const camera=new THREE.PerspectiveCamera(72,innerWidth/innerHeight,0.1,60);
camera.rotation.order='YXZ';
scene.add(camera);

// Đèn pin
const spot=new THREE.SpotLight(0xfff0cc,2.1,22,Math.PI/5.2,0.5,1.1);
camera.add(spot); spot.position.set(0.2,-0.1,0); camera.add(spot.target); spot.target.position.set(0,0,-3);
spot.shadow.mapSize.set(1024,1024); spot.shadow.camera.near=0.2; spot.shadow.camera.far=22; spot.shadow.bias=-0.0006;
scene.add(new THREE.AmbientLight(0x4a3a34,0.85));
// Đèn chùm + các đèn cố định (tạo một lần để tránh biên dịch lại shader)
const lamp=new THREE.PointLight(0xffb066,1.0,20); scene.add(lamp);
lamp.shadow.mapSize.set(512,512); lamp.shadow.camera.near=0.3; lamp.shadow.camera.far=22; lamp.shadow.bias=-0.003;
const doorLight=new THREE.PointLight(0xfff1c9,0,10); scene.add(doorLight);
const sconceL=[0,1].map(()=>{const l=new THREE.PointLight(0xff9a40,1.0,8);scene.add(l);return l;});
const clueL=[0,1,2].map(()=>{const l=new THREE.PointLight(0xffaa44,.9,5.5);scene.add(l);return l;});

let room=null, doorPivot=null, obstacles=[], inter=[], watchers=[], flameMat=null;

// Bụi bay
const DUST=220, dustPos=new Float32Array(DUST*3);
const dustGeo=new THREE.BufferGeometry(); dustGeo.setAttribute('position',new THREE.BufferAttribute(dustPos,3));
const dust=new THREE.Points(dustGeo,new THREE.PointsMaterial({color:0xffddaa,size:0.035,transparent:true,opacity:.45,depthWrite:false}));
dust.frustumCulled=false; scene.add(dust);
function resetDust(){for(let i=0;i<DUST;i++){dustPos[i*3]=(Math.random()-.5)*RW;dustPos[i*3+1]=Math.random()*RH;dustPos[i*3+2]=(Math.random()-.5)*RD;}
  dustGeo.attributes.position.needsUpdate=true;}

// Rush (thực thể)
const rushMesh=new THREE.Group();
(function(){
  const bg=new THREE.IcosahedronGeometry(1,2), pa=bg.attributes.position;
  for(let i=0;i<pa.count;i++){const x=pa.getX(i),y=pa.getY(i),z=pa.getZ(i),k=1+0.2*Math.sin(x*7.3+y*5.1+z*3.7);pa.setXYZ(i,x*k,y*k,z*k);}
  const b=new THREE.Mesh(bg,new THREE.MeshBasicMaterial({color:0x000000})); b.scale.set(2.2,1.7,1.3); rushMesh.add(b);
  const em=new THREE.MeshBasicMaterial({color:0xffffff});
  [-0.8,0.8].forEach(x=>{const e=new THREE.Mesh(new THREE.SphereGeometry(0.3,12,10),em);e.scale.set(1,1.4,.5);e.position.set(x,0.45,1.15);rushMesh.add(e);});
  const grin=new THREE.Mesh(new THREE.TorusGeometry(0.9,0.05,6,28,Math.PI),em); grin.rotation.z=Math.PI; grin.position.set(0,-0.15,1.2); grin.scale.x=1.1; rushMesh.add(grin);
  const l=new THREE.PointLight(0xff2200,2,9); l.position.set(0,0,2.2); rushMesh.add(l);
  rushMesh.position.set(0,-50,0); scene.add(rushMesh);
})();

// ---------- Texture thủ tục ----------
const CAN={};
function T(key,w,h,draw,rx,ry){
  if(!CAN[key]){const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);CAN[key]=c;}
  const t=new THREE.CanvasTexture(CAN[key]); t.wrapS=t.wrapT=THREE.RepeatWrapping; t.repeat.set(rx||1,ry||1); t.anisotropy=4; return t;
}
const rnd=(a,b)=>a+Math.random()*(b-a);
function noiseFx(g,w,h,a){const id=g.getImageData(0,0,w,h),d=id.data;for(let i=0;i<d.length;i+=4){const n=(Math.random()-.5)*a;d[i]+=n;d[i+1]+=n;d[i+2]+=n;}g.putImageData(id,0,0);}
function stains(g,w,h,n,a){for(let i=0;i<n;i++){const x=rnd(0,w),y=rnd(0,h),r=rnd(6,46),gr=g.createRadialGradient(x,y,0,x,y,r);
  gr.addColorStop(0,'rgba(0,0,0,'+a+')');gr.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=gr;g.fillRect(x-r,y-r,r*2,r*2);}}
const WALLC=['#6b4a35','#4a5a4a','#4a5568','#5a3a4a','#3d3d3d'];
const wallTex=(i,rx,ry)=>T('wall'+i,256,256,(g,w,h)=>{
  g.fillStyle=WALLC[i];g.fillRect(0,0,w,h);
  for(let x=0;x<w;x+=32){g.fillStyle='rgba(255,255,255,.05)';g.fillRect(x,0,16,h);}
  g.strokeStyle='rgba(0,0,0,.28)';g.lineWidth=2;
  for(let y=0;y<h;y+=64)for(let x=0;x<w;x+=64){const cx=x+32,cy=y+32;
    g.beginPath();g.moveTo(cx,cy-18);g.lineTo(cx+12,cy);g.lineTo(cx,cy+18);g.lineTo(cx-12,cy);g.closePath();g.stroke();
    g.beginPath();g.arc(cx,cy,3,0,6.3);g.stroke();}
  stains(g,w,h,26,.16);noiseFx(g,w,h,22);},rx,ry);
const carpetTex=(rx,ry)=>T('carpet',256,256,(g,w,h)=>{
  g.fillStyle='#4a0f12';g.fillRect(0,0,w,h);g.strokeStyle='rgba(200,150,60,.28)';g.lineWidth=2;
  for(let i=-h;i<w+h;i+=32){g.beginPath();g.moveTo(i,0);g.lineTo(i+h,h);g.stroke();g.beginPath();g.moveTo(i+h,0);g.lineTo(i,h);g.stroke();}
  g.fillStyle='rgba(0,0,0,.25)';for(let y=16;y<h;y+=32)for(let x=16;x<w;x+=32){g.fillRect(x-3,y-3,6,6);}
  stains(g,w,h,22,.22);noiseFx(g,w,h,34);},rx,ry);
const woodTex=(rx,ry)=>T('wood',128,128,(g,w,h)=>{
  g.fillStyle='#2e1b10';g.fillRect(0,0,w,h);
  for(let x=0;x<w;x+=16){g.fillStyle='rgba(0,0,0,.35)';g.fillRect(x,0,2,h);}
  for(let i=0;i<60;i++){g.strokeStyle='rgba(0,0,0,'+rnd(.05,.2)+')';g.beginPath();const x=rnd(0,w);g.moveTo(x,0);g.bezierCurveTo(x+6,h/3,x-6,h*2/3,x+rnd(-3,3),h);g.stroke();}
  noiseFx(g,w,h,26);},rx,ry);
const ceilTex=(rx,ry)=>T('ceil',256,256,(g,w,h)=>{g.fillStyle='#2b1f16';g.fillRect(0,0,w,h);stains(g,w,h,30,.4);noiseFx(g,w,h,24);},rx,ry);
const doorTex=()=>T('door',256,512,(g,w,h)=>{
  g.fillStyle='#6f4322';g.fillRect(0,0,w,h);
  for(let x=0;x<w;x+=32){g.fillStyle='rgba(0,0,0,.18)';g.fillRect(x,0,2,h);}
  [[24,24],[134,24],[24,270],[134,270]].forEach(p=>{const pw=98,ph=p[1]<200?230:210;
    g.fillStyle='rgba(0,0,0,.35)';g.fillRect(p[0],p[1],pw,ph);g.fillStyle='#7c4c28';g.fillRect(p[0]+6,p[1]+6,pw-12,ph-12);
    g.strokeStyle='rgba(0,0,0,.4)';g.strokeRect(p[0]+14,p[1]+14,pw-28,ph-28);});
  stains(g,w,h,10,.25);noiseFx(g,w,h,28);});
const bookTex=()=>T('books',256,128,(g,w,h)=>{
  g.fillStyle='#1b110a';g.fillRect(0,0,w,h);
  for(let r=0;r<4;r++){let x=4;const y=r*32;while(x<w-8){const bw=rnd(6,14),bh=rnd(18,28);
    g.fillStyle='hsl('+Math.floor(rnd(0,40))+','+Math.floor(rnd(20,50))+'%,'+Math.floor(rnd(14,30))+'%)';g.fillRect(x,y+30-bh,bw,bh);x+=bw+1;}
    g.fillStyle='#000';g.fillRect(0,y+30,w,3);}
  noiseFx(g,w,h,22);});
const paintTex=v=>T('paint'+v,256,320,(g,w,h)=>{
  const gr=g.createLinearGradient(0,0,0,h);gr.addColorStop(0,['#1d2a2a','#2a1d2a','#2a2a1d','#241a1a'][v%4]);gr.addColorStop(1,'#050505');
  g.fillStyle=gr;g.fillRect(0,0,w,h);
  g.fillStyle='#0b0b0b';g.beginPath();g.ellipse(w/2,h+10,95,120,0,0,7);g.fill();
  const ox=(v%3-1)*6;
  g.fillStyle='#b8a98a';g.beginPath();g.ellipse(w/2+ox,125,52,68,0,0,7);g.fill();
  g.fillStyle='#000';[-20,20].forEach(dx=>{g.beginPath();g.ellipse(w/2+dx+ox,112,11,15+(v%3)*2,0,0,7);g.fill();});
  g.fillStyle='#ff2a2a';[-20,20].forEach(dx=>{g.beginPath();g.arc(w/2+dx+ox,114,2.4,0,7);g.fill();});
  g.strokeStyle='#000';g.lineWidth=3;g.beginPath();g.moveTo(w/2-28+ox,158);g.quadraticCurveTo(w/2+ox,180+(v%3)*8,w/2+28+ox,158);g.stroke();
  g.strokeStyle='rgba(0,0,0,.5)';g.lineWidth=1;for(let i=0;i<8;i++){g.beginPath();g.moveTo(rnd(0,w),rnd(0,h));g.lineTo(rnd(0,w),rnd(0,h));g.stroke();}
  stains(g,w,h,14,.35);noiseFx(g,w,h,26);});
const bloodTex=()=>T('blood',128,128,(g,w,h)=>{
  for(let i=0;i<26;i++){const x=64+rnd(-40,40),y=64+rnd(-40,40),r=rnd(2,16),gr=g.createRadialGradient(x,y,0,x,y,r);
    gr.addColorStop(0,'rgba(110,5,5,.95)');gr.addColorStop(1,'rgba(90,0,0,0)');g.fillStyle=gr;g.beginPath();g.arc(x,y,r,0,7);g.fill();}});
const handTex=()=>T('hand',128,128,(g,w,h)=>{
  g.fillStyle='rgba(115,8,8,.92)';g.strokeStyle='rgba(115,8,8,.92)';g.lineCap='round';
  g.beginPath();g.ellipse(64,88,28,32,0,0,7);g.fill();g.lineWidth=11;
  for(let i=0;i<5;i++){const a=-2.45+i*.37;g.beginPath();g.moveTo(64+Math.cos(a)*16,88+Math.sin(a)*16);g.lineTo(64+Math.cos(a)*(i==2?58:52),88+Math.sin(a)*(i==2?58:52));g.stroke();}
  g.lineWidth=3;for(let i=0;i<5;i++){const x=rnd(40,88);g.beginPath();g.moveTo(x,110);g.lineTo(x,110+rnd(6,18));g.stroke();}});
const MSG=['ĐỪNG NHÌN','TRỐN ĐI','NÓ Ở ĐÂY','ĐỪNG CHẠY','KHÔNG CÓ LỐI RA'];
const msgTex=t=>T('msg'+t,512,128,(g,w,h)=>{
  g.font='bold 60px serif';g.textAlign='center';g.fillStyle='#7d0a0a';g.shadowColor='#400';g.shadowBlur=8;g.fillText(t,w/2,66);
  g.shadowBlur=0;for(let i=0;i<22;i++){g.fillRect(rnd(60,w-60),68,rnd(2,4),rnd(8,46));}});

// ---------- Dựng phòng ----------
const M=(c,e)=>new THREE.MeshStandardMaterial({color:c,roughness:.9,emissive:e||0x000000,side:THREE.DoubleSide});

function buildRoom(){
  if(room) scene.remove(room);
  room=new THREE.Group(); scene.add(room);
  obstacles=[]; inter=[]; watchers=[]; doorOpen=false; wardI=null;
  const m=(door%2)?-1:1;
  scene.fog=new THREE.FogExp2(0x050202,0.07+door*0.008);
  renderer.shadowMap.enabled=HQ; spot.castShadow=HQ; lamp.castShadow=HQ;
  const wallRY=(m===1)?Math.PI/2:-Math.PI/2;       // tường bên "trái" (phía -m)
  const plane=(w,h,mat,x,y,z,ry,rx)=>{const p=new THREE.Mesh(new THREE.PlaneGeometry(w,h),mat);
    p.position.set(x,y,z);p.rotation.set(rx||0,ry||0,0);p.receiveShadow=true;room.add(p);return p;};
  const box=(sx,sy,sz,mat,x,y,z,parent,cast)=>{const b=new THREE.Mesh(new THREE.BoxGeometry(sx,sy,sz),mat);
    b.position.set(x,y,z);b.castShadow=cast!==false;b.receiveShadow=true;(parent||room).add(b);return b;};
  const solid=(cx,cz,sx,sz,sy,mat)=>{box(sx,sy,sz,mat,cx,sy/2,cz);obstacles.push({x1:cx-sx/2,x2:cx+sx/2,z1:cz-sz/2,z2:cz+sz/2});};
  const lit=(tx)=>new THREE.MeshStandardMaterial({map:tx,roughness:.9,side:THREE.DoubleSide});
  const wood=(rx,ry)=>new THREE.MeshStandardMaterial({map:woodTex(rx,ry),roughness:.75});
  const woodDark=M(0x1b0f08);
  const wi=door%5;

  // sàn, trần, tường
  plane(RW,RD,new THREE.MeshStandardMaterial({map:carpetTex(RW/2,RD/2),roughness:1}),0,0,0,0,-Math.PI/2);
  plane(RW,RD,lit(ceilTex(3,4)),0,RH,0,0,Math.PI/2);
  plane(RW,RH,lit(wallTex(wi,RW/2,RH/2)),0,RH/2,-RD/2);
  plane(RW,RH,lit(wallTex(wi,RW/2,RH/2)),0,RH/2,RD/2,Math.PI);
  plane(RD,RH,lit(wallTex(wi,RD/2,RH/2)),-RW/2,RH/2,0,Math.PI/2);
  plane(RD,RH,lit(wallTex(wi,RD/2,RH/2)),RW/2,RH/2,0,-Math.PI/2);
  // ốp tường gỗ
  const wains=(len,x,z,ry)=>{const gp=new THREE.Group();gp.position.set(x,0,z);gp.rotation.y=ry;room.add(gp);
    box(len,1.1,0.08,wood(len/2,1),0,0.55,0,gp);box(len+0.04,0.07,0.13,woodDark,0,1.13,0.02,gp);box(len+0.04,0.16,0.12,woodDark,0,0.08,0.02,gp);};
  wains(5,-3.5,-RD/2+0.04,0); wains(5,3.5,-RD/2+0.04,0); wains(RW,0,RD/2-0.04,Math.PI);
  wains(RD,-RW/2+0.04,0,Math.PI/2); wains(RD,RW/2-0.04,0,-Math.PI/2);

  // đèn chùm
  const iron=M(0x111111), chand=new THREE.Group(); chand.position.set(0,RH,0); room.add(chand);
  const chain=new THREE.Mesh(new THREE.CylinderGeometry(.015,.015,.7,6),iron); chain.position.y=-.35; chand.add(chain);
  const ring=new THREE.Mesh(new THREE.TorusGeometry(.45,.025,6,18),iron); ring.rotation.x=Math.PI/2; ring.position.y=-.7; chand.add(ring);
  flameMat=new THREE.MeshBasicMaterial({color:0xffd9a0});
  for(let i=0;i<6;i++){const a=i/6*6.283,f=new THREE.Mesh(new THREE.SphereGeometry(.05,8,6),flameMat);f.position.set(Math.cos(a)*.45,-.62,Math.sin(a)*.45);chand.add(f);}
  lamp.position.set(0,RH-0.85,0);

  // cửa
  const dz=-RD/2;
  const fm=M(0x1a1008);
  box(0.3,3.3,0.25,fm,-1.1,1.65,dz+0.12,null,false); box(0.3,3.3,0.25,fm,1.1,1.65,dz+0.12,null,false); box(2.5,0.3,0.25,fm,0,3.15,dz+0.12,null,false);
  const glow=new THREE.Mesh(new THREE.PlaneGeometry(1.9,3.0),new THREE.MeshBasicMaterial({color:0xfff1c9}));
  glow.position.set(0,1.5,dz+0.03); room.add(glow);
  doorPivot=new THREE.Group(); doorPivot.position.set(-0.9,0,dz+0.14); room.add(doorPivot);
  box(1.8,2.95,0.1,new THREE.MeshStandardMaterial({map:doorTex(),roughness:.7}),0.9,1.475,0,doorPivot,false);
  [0.5,2.4].forEach(y=>box(0.12,0.22,0.14,M(0x222222),0.03,y,0,doorPivot,false));
  const knob=new THREE.Mesh(new THREE.SphereGeometry(0.07,12,10),new THREE.MeshStandardMaterial({color:0xd4af37,metalness:.8,roughness:.3})); knob.position.set(1.6,1.4,0.1); doorPivot.add(knob);
  const cv=document.createElement('canvas'); cv.width=128; cv.height=64; const g=cv.getContext('2d');
  g.fillStyle='#caa24a'; g.fillRect(0,0,128,64); g.strokeStyle='#5a4010'; g.lineWidth=4; g.strokeRect(3,3,122,58);
  g.fillStyle='#2a1a08'; g.font='bold 42px serif'; g.textAlign='center'; g.textBaseline='middle'; g.fillText(String(door+1).padStart(3,'0'),64,34);
  const pm=new THREE.Mesh(new THREE.PlaneGeometry(0.6,0.3),new THREE.MeshStandardMaterial({map:new THREE.CanvasTexture(cv),metalness:.6,roughness:.4}));
  pm.position.set(0.9,2.45,0.06); doorPivot.add(pm);
  doorLight.position.set(0,1.8,dz+1.3); doorLight.intensity=0;
  inter.push({kind:'door',x:0,z:dz,r:2.7});

  // manh mối
  const clue=(idx,x,y,z,sx,sy,sz)=>{
    const mat=new THREE.MeshStandardMaterial({color:0xffcc55,emissive:0xffaa22,emissiveIntensity:1.4});
    box(sx,sy,sz,mat,x,y,z,null,false);
    const L=clueL[idx]; L.color.set(0xffaa44); L.position.set(x,y+0.4,z+(z<-7?0.7:0));
    inter.push({kind:'clue',idx,x,z,r:2.5,mat,L});
  };
  const tableMat=wood(2,1);
  solid(-4.6*m,-2.5,1.3,2.5,0.8,tableMat);
  clue(0,-4.6*m,0.86,-2.5,0.5,0.08,0.35);
  const candle=new THREE.Mesh(new THREE.CylinderGeometry(.04,.04,.22,8),M(0xddd5c0)); candle.position.set(-4.6*m,0.91,-3.2); room.add(candle);
  const cf=new THREE.Mesh(new THREE.SphereGeometry(.045,8,6),new THREE.MeshBasicMaterial({color:0xffc060})); cf.position.set(-4.6*m,1.07,-3.2); room.add(cf);
  solid(4.9*m,0.5,1.1,2.2,1.2,wood(1,1));
  clue(1,4.9*m,1.26,0.5,0.6,0.05,0.4);
  // tủ sách
  solid(-5.6*m,3.8,0.5,3,2.4,woodDark);
  plane(2.9,2.3,lit(bookTex()),-5.6*m+0.26*m,1.2,3.8,wallRY);
  // tranh manh mối
  box(1.7,1.4,0.06,M(0x6b5320),-3.2*m,2.0,-RD/2+0.06,null,false);
  clue(2,-3.2*m,2.0,-RD/2+0.1,1.5,1.2,0.04);
  plane(1.3,1.0,lit(paintTex(3)),-3.2*m,2.0,-RD/2+0.16,0);
  // tủ quần áo
  solid(5*m,6.4,1.5,1.2,2.8,wood(1,2));
  box(0.04,2.4,0.02,M(0x000000),5*m,1.4,6.4-0.61,null,false);
  [-0.12,0.12].forEach(dx=>box(0.04,0.2,0.04,M(0xd4af37),5*m+dx,1.3,6.4-0.63,null,false));
  const w={kind:'hide',x:5*m,z:6.4,r:2.5}; inter.push(w); wardI=w;

  // tranh trang trí (mắt đỏ)
  const painting=(v,x,y,z,ry,pw,ph)=>{const gp=new THREE.Group();gp.position.set(x,y,z);gp.rotation.y=ry;room.add(gp);
    box(pw+.16,ph+.16,.06,M(0x6b5320),0,0,0,gp,false);
    const t=paintTex(v);const p=new THREE.Mesh(new THREE.PlaneGeometry(pw,ph),new THREE.MeshStandardMaterial({map:t,emissiveMap:t,emissive:0xffffff,emissiveIntensity:.2,roughness:.8}));
    p.position.z=.04;gp.add(p);};
  painting((door)%3,-(RW/2-0.05)*m,2.1,0.8,wallRY,1.0,1.25);
  painting((door+1)%3,3.6*m,2.2,-RD/2+0.05,0,1.0,1.25);
  painting((door+2)%3,-2*m,2.2,RD/2-0.05,Math.PI,1.0,1.25);

  // đèn tường
  const sconce=(x,z,ry,L)=>{const gp=new THREE.Group();gp.position.set(x,2.3,z);gp.rotation.y=ry;room.add(gp);
    box(0.12,0.4,0.12,M(0x2a1a0a),0,0,0.08,gp,false);
    const fl=new THREE.Mesh(new THREE.SphereGeometry(.07,8,6),new THREE.MeshBasicMaterial({color:0xffbb55}));fl.position.set(0,.28,.1);gp.add(fl);
    L.position.set(x+(ry>0?0.8:-0.8),2.6,z);};
  sconce(-(RW/2-0.1)*m,-5.2,wallRY,sconceL[0]);
  sconce((RW/2-0.1)*m,3.4,-wallRY,sconceL[1]);

  // vết máu, dấu tay, chữ viết bằng máu
  const decal=(tx,w2,h2,x,y,z,ry,rx)=>{const p=new THREE.Mesh(new THREE.PlaneGeometry(w2,h2),
    new THREE.MeshStandardMaterial({map:tx,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2,roughness:.4}));
    p.position.set(x,y,z);p.rotation.set(rx||0,ry||0,0);p.receiveShadow=true;room.add(p);};
  decal(bloodTex(),1.9,1.9,rnd(-3,3),0.012,rnd(-4,3),0,-Math.PI/2);
  decal(bloodTex(),1.4,1.4,rnd(-3,3),0.013,rnd(-1,5),0,-Math.PI/2);
  decal(handTex(),0.9,0.9,-3.6,1.5,RD/2-0.02,Math.PI);
  decal(handTex(),0.9,0.9,5.3*m,1.4,-RD/2+0.02,0);
  decal(msgTex(MSG[door%5]),3.4,0.85,(RW/2-0.03)*m,2.4,-5.3,-wallRY);
  // ghế đổ
  const chair=new THREE.Group();chair.position.set(-2*m,0.2,3.2);chair.rotation.set(0.1,rnd(0,3),1.45);room.add(chair);
  box(0.5,0.05,0.5,woodDark,0,0,0,chair); box(0.5,0.6,0.05,woodDark,0,0.3,-0.22,chair);

  // đôi mắt trong bóng tối
  const eyeMat=new THREE.MeshBasicMaterial({color:0xff2020});
  const spots=[[-5.4,3.5,-7.4],[5.4,3.5,-7.4],[-5.4,3.6,7.4],[5.4,3.6,7.4],[0,3.7,-7.6],[-5.7,3.3,0],[5.7,3.3,-1]];
  const nW=Math.min(2+door,spots.length);
  for(let i=0;i<nW;i++){const s=spots[(i*3+door)%spots.length];const gp=new THREE.Group();gp.position.set(s[0],s[1],s[2]);
    gp.rotation.y=Math.atan2(-s[0],-s[2]);
    [-0.2,0.2].forEach(dx=>{const e=new THREE.Mesh(new THREE.SphereGeometry(.07,8,6),eyeMat);e.scale.set(1.4,.8,.5);e.position.x=dx;gp.add(e);});
    room.add(gp);watchers.push({g:gp,t:rnd(0,20),off:rnd(0,6)});}
  resetDust();
}
function refreshClues(){
  inter.forEach(o=>{ if(o.kind==='clue' && solved[o.idx]){
    o.mat.color.set(0x55ff88); o.mat.emissive.set(0x22aa55); o.L.color.set(0x55ff88); }});
}

// ---------- Âm thanh ----------
let AC; const ac=()=>AC||(AC=new (window.AudioContext||window.webkitAudioContext)());
function tone(f,d,type,v,f2){try{const a=ac(),o=a.createOscillator(),g=a.createGain();o.type=type||'sine';
  o.frequency.setValueAtTime(f,a.currentTime);if(f2)o.frequency.exponentialRampToValueAtTime(f2,a.currentTime+d);
  g.gain.setValueAtTime(v||.15,a.currentTime);g.gain.exponentialRampToValueAtTime(.001,a.currentTime+d);
  o.connect(g).connect(a.destination);o.start();o.stop(a.currentTime+d);}catch(e){}}
function noise(d,v){try{const a=ac(),n=Math.floor(a.sampleRate*d),b=a.createBuffer(1,n,a.sampleRate),x=b.getChannelData(0);
  for(let i=0;i<n;i++)x[i]=(Math.random()*2-1)*(1-i/n);const s=a.createBufferSource(),g=a.createGain();
  g.gain.value=v;s.buffer=b;s.connect(g).connect(a.destination);s.start();}catch(e){}}
const sGood=()=>{tone(660,.15,'sine',.15);setTimeout(()=>tone(990,.3,'sine',.15),120);};
const sBad=()=>{tone(160,.4,'sawtooth',.2,60);noise(.3,.25);};
let amb=false;
function ambience(){
  try{const a=ac(); if(a.resume)a.resume(); if(amb)return; amb=true;
    const mk=(f,type,vol)=>{const o=a.createOscillator(),g=a.createGain(),lp=a.createBiquadFilter();o.type=type;o.frequency.value=f;
      lp.type='lowpass';lp.frequency.value=170;g.gain.value=vol;o.connect(lp).connect(g).connect(a.destination);o.start();return g;};
    const g1=mk(46,'sawtooth',.05); mk(49.3,'sawtooth',.04);
    const lfo=a.createOscillator(),lg=a.createGain();lfo.frequency.value=.13;lg.gain.value=.03;lfo.connect(lg).connect(g1.gain);lfo.start();
    const n=a.sampleRate*3,b=a.createBuffer(1,n,a.sampleRate),x=b.getChannelData(0);for(let i=0;i<n;i++)x[i]=Math.random()*2-1;
    const s=a.createBufferSource();s.buffer=b;s.loop=true;const bp=a.createBiquadFilter();bp.type='bandpass';bp.frequency.value=400;bp.Q.value=.6;
    const wg=a.createGain();wg.gain.value=.022;s.connect(bp).connect(wg).connect(a.destination);s.start();
  }catch(e){}
}
const WH=['đừng quay lại...','nó đang nhìn bạn','phía sau bạn','đừng nhìn vào bóng tối','chạy đi...','bạn không một mình','nó biết bạn ở đây'];
function whisper(){const w=$('whisper');w.textContent=WH[Math.floor(Math.random()*WH.length)];
  w.style.left=(8+Math.random()*60)+'%';w.style.top=(15+Math.random()*60)+'%';w.style.opacity=.8;setTimeout(()=>w.style.opacity=0,2400);noise(1.2,.05);}

// ---------- Tiện ích UI ----------
function norm(s){return s.trim().toLowerCase().replace(/đ/g,'d').normalize('NFD').replace(/[\u0300-\u036f]/g,'')
  .replace(/,/g,'.').replace(/[^a-z0-9. ]/g,'').replace(/\s+/g,' ').trim();}
function banner(t,ms){const b=$('banner');b.textContent=t;b.style.opacity=1;clearTimeout(bannerT);
  bannerT=setTimeout(()=>b.style.opacity=0,ms||2500);}
function updateHud(){
  if(door>=DOORS.length) return;
  const D=DOORS[door];
  $('dn').textContent='🚪 Cửa '+(door+1)+'/5';
  $('hp').textContent='❤️'.repeat(Math.max(hp,0))+'🖤'.repeat(MAX_HP-Math.max(hp,0));
  $('hn').textContent='💡 Gợi ý: '+hints;
  $('ks').textContent='🔑 '+D.questions.map((q,i)=>solved[i]?q.digit:'_').join(' · ');
  $('ot').textContent=solved.every(Boolean)?D.order_text:'';
  $('lowhp').className=(hp===1&&state==='play')?'pulse':'';
}
function lock(){try{const p=canvas.requestPointerLock();if(p&&p.catch)p.catch(()=>{});}catch(e){}}
function unlock(){try{document.exitPointerLock();}catch(e){}}

// grain
(function(){const gc=$('grain');gc.width=160;gc.height=90;const x=gc.getContext('2d');
  setInterval(()=>{const id=x.createImageData(160,90),d=id.data;for(let i=0;i<d.length;i+=4){const v=Math.random()*255;d[i]=d[i+1]=d[i+2]=v;d[i+3]=70;}x.putImageData(id,0,0);},70);})();

function damage(msg){
  hp--; shake=0.3; sBad();
  const f=$('flash'); f.style.opacity=.75; setTimeout(()=>f.style.opacity=0,350);
  banner(msg+'  -1 ❤️',2500); updateHud();
  if(hp<=0) gameOver();
}
function gameOver(){
  state='over'; closeModal(true); unlock(); updateHud();
  $('overmsg').textContent='Bạn gục ngã ở cửa số '+(door+1)+'...';
  $('over').style.display='flex';
}

// ---------- Modal ----------
function openModal(){modalOpen=true;unlock();$('modal').style.display='flex';$('fb').textContent='';
  setTimeout(()=>$('mi').focus(),30);}
function closeModal(silent){modalOpen=false;$('modal').style.display='none';$('mi').value='';keys={};
  if(!silent&&state==='play')lock();}
function openQ(i){
  const q=DOORS[door].questions[i]; modalMode='q'; modalIdx=i;
  $('mt').textContent='📜 Manh mối '+(i+1); $('mq').textContent=q.q; $('b2').style.display='inline-block';
  openModal(); if(hintShown[door+'-'+i]) $('fb').textContent='💡 '+q.hint;
}
function openCode(){
  const D=DOORS[door]; modalMode='code';
  $('mt').textContent='🔐 Ổ khóa'; $('mq').textContent='Nhập mật mã '+D.questions.length+' chữ số. '+D.order_text;
  $('b2').style.display='none'; openModal();
}
function submit(){
  const v=$('mi').value; if(!v.trim()) return;
  const D=DOORS[door];
  if(modalMode==='q'){
    const q=D.questions[modalIdx];
    if(q.a.includes(norm(v))){
      solved[modalIdx]=true; sGood(); closeModal(); refreshClues(); updateHud();
      banner('🔑 Đúng! Chìa khóa '+(modalIdx+1)+' = '+q.digit+(solved.every(Boolean)?'\nĐã đủ chìa! Hãy ra mở cửa.':''),3000);
    } else { $('fb').textContent='❌ Sai rồi!'; $('mi').value=''; damage('Một thực thể tấn công bạn!'); }
  } else {
    const code=D.order.map(i=>D.questions[i].digit).join('');
    if(v.trim()===code){ closeModal(); doorOpen=true; sGood(); tone(70,1.2,'sawtooth',.12,40); banner('🔓 Cửa đã mở! Hãy bước vào ánh sáng...',3000); }
    else { $('fb').textContent='❌ Mật mã sai!'; $('mi').value=''; damage('Ổ khóa phóng điện vào bạn!'); }
  }
}
$('b1').onclick=submit; $('b3').onclick=()=>closeModal();
$('b2').onclick=()=>{
  const k=door+'-'+modalIdx, q=DOORS[door].questions[modalIdx];
  if(hintShown[k]){$('fb').textContent='💡 '+q.hint;return;}
  if(hints<=0){$('fb').textContent='Hết lượt gợi ý!';return;}
  hints--; hintShown[k]=true; $('fb').textContent='💡 '+q.hint; updateHud();
};
$('mi').addEventListener('keydown',e=>{if(e.key==='Enter')submit();});

// ---------- Luồng game ----------
function startRoom(){
  solved=[false,false,false]; buildRoom(); hidden=false; spot.intensity=2.1; $('hide').style.display='none';
  camera.position.set(0,1.6,RD/2-2); yaw=0; pitch=0; rush=null; rushMesh.position.set(0,-50,0); lampF=1;
  rushTimer=18+Math.random()*10; updateHud();
  banner('CỬA '+(door+1)+': '+DOORS[door].name+'\n'+DOORS[door].intro,4500);
}
function resetGame(){hp=MAX_HP;hints=HINTS0;door=0;hintShown={};state='play';ambience();
  ['menu','over','win'].forEach(i=>$(i).style.display='none'); startRoom(); lock();}
$('start').onclick=resetGame; $('retry').onclick=resetGame; $('again').onclick=resetGame;
$('qual').onclick=()=>{HQ=!HQ;$('qual').textContent='⚙️ Chất lượng: '+(HQ?'Cao':'Thấp');
  renderer.setPixelRatio(HQ?Math.min(window.devicePixelRatio||1,2):1);renderer.setSize(innerWidth,innerHeight);buildRoom();};
function nextRoom(){
  transitioning=true; $('fade').style.opacity=1;
  setTimeout(()=>{
    door++;
    if(door>=DOORS.length){state='win';unlock();updateHud();$('win').style.display='flex';}
    else startRoom();
    $('fade').style.opacity=0; transitioning=false;
  },900);
}
function toggleHide(){
  if(!hidden){hidden=true;camera.position.set(wardI.x,1.5,wardI.z);yaw=0;pitch=0;spot.intensity=0;$('hide').style.display='block';}
  else{hidden=false;camera.position.set(wardI.x,1.6,wardI.z-1.3);spot.intensity=2.1;$('hide').style.display='none';}
}
function act(){
  if(hidden){toggleHide();return;}
  if(!cur) return;
  if(cur.kind==='hide') toggleHide();
  else if(cur.kind==='clue'){ if(!solved[cur.idx]) openQ(cur.idx); }
  else if(cur.kind==='door'){
    if(doorOpen) return;
    if(solved.every(Boolean)) openCode();
    else banner('🔒 Cửa bị khóa. Cần đủ 3 chìa khóa ('+solved.filter(Boolean).length+'/3).',2200);
  }
}

// ---------- Điều khiển ----------
addEventListener('keydown',e=>{
  if(modalOpen){ if(e.code==='Escape') closeModal(); return; }
  keys[e.code]=true;
  if(e.code==='KeyE'&&state==='play'&&!transitioning) act();
  if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space'].includes(e.code)) e.preventDefault();
});
addEventListener('keyup',e=>{keys[e.code]=false;});
canvas.addEventListener('mousedown',()=>{dragging=true; if(state==='play'&&!modalOpen) lock();});
addEventListener('mouseup',()=>dragging=false);
addEventListener('mousemove',e=>{
  if(state!=='play'||modalOpen) return;
  if(document.pointerLockElement===canvas||dragging){
    yaw-=e.movementX*0.0025; pitch=Math.max(-1.3,Math.min(1.3,pitch-e.movementY*0.0025));
  }
});
addEventListener('resize',()=>{renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();});

function hit(x,z){for(const b of obstacles){if(x>b.x1-0.35&&x<b.x2+0.35&&z>b.z1-0.35&&z<b.z2+0.35)return true;}return false;}

function update(dt){
  tt+=dt;
  // bụi + mắt luôn chạy để cảnh sống động
  for(let i=0;i<DUST;i++){dustPos[i*3+1]+=Math.sin(tt*.6+i)*0.0009+0.0006;dustPos[i*3]+=Math.cos(tt*.4+i*1.7)*0.0007;
    if(dustPos[i*3+1]>RH)dustPos[i*3+1]=0;}
  dustGeo.attributes.position.needsUpdate=true;
  // nhấp nháy ngọn lửa
  sconceL.forEach((l,i)=>l.intensity=(0.85+0.25*Math.sin(tt*13+i*2.1)*Math.sin(tt*5.3+i))*lampF);
  if(state!=='play') return;
  if(!modalOpen){ if(keys.ArrowLeft) yaw+=1.8*dt; if(keys.ArrowRight) yaw-=1.8*dt; }
  let moving=false;
  if(!modalOpen&&!hidden&&!transitioning){
    let f=0,s=0;
    if(keys.KeyW||keys.ArrowUp)f++; if(keys.KeyS||keys.ArrowDown)f--; if(keys.KeyD)s++; if(keys.KeyA)s--;
    if(f||s){
      moving=true; const run=keys.ShiftLeft||keys.ShiftRight, sp=(run?5.2:3.2)*dt, l=Math.hypot(f,s);
      const fx=-Math.sin(yaw),fz=-Math.cos(yaw),rx=Math.cos(yaw),rz=-Math.sin(yaw);
      const dx=(fx*f+rx*s)/l*sp, dzz=(fz*f+rz*s)/l*sp;
      if(!hit(camera.position.x+dx,camera.position.z)) camera.position.x+=dx;
      if(!hit(camera.position.x,camera.position.z+dzz)) camera.position.z+=dzz;
      bob+=dt*(run?12:9);
      stepT-=dt; if(stepT<=0){noise(.07,.08);tone(70,.09,'sine',.1,40);stepT=run?.32:.5;}
    }
    const zmin=doorOpen?-RD/2-1.5:-RD/2+0.7;
    camera.position.x=Math.max(-RW/2+0.5,Math.min(RW/2-0.5,camera.position.x));
    camera.position.z=Math.max(zmin,Math.min(RD/2-0.5,camera.position.z));
    if(doorOpen&&camera.position.z<-RD/2+0.6) camera.position.x=Math.max(-0.75,Math.min(0.75,camera.position.x));
    if(doorOpen&&camera.position.z<-RD/2-0.3&&!transitioning) nextRoom();
  }
  if(!hidden) camera.position.y=1.6+(moving?Math.sin(bob)*0.04:0);
  if(doorOpen){ if(doorPivot.rotation.y<1.9) doorPivot.rotation.y=Math.min(1.9,doorPivot.rotation.y+dt*1.5);
    doorLight.intensity=Math.min(1.8,doorLight.intensity+dt*1.5); }

  // mắt trong bóng tối: chỉ hiện khi bạn không nhìn vào
  const fxv=-Math.sin(yaw), fzv=-Math.cos(yaw);
  watchers.forEach(w=>{
    const dx=w.g.position.x-camera.position.x, dzv=w.g.position.z-camera.position.z, d=Math.hypot(dx,dzv)||1;
    const dot=(dx*fxv+dzv*fzv)/d, on=Math.sin(tt*.5+w.off)>-0.3;
    w.g.visible=on&&dot<0.45&&!hidden;
    w.g.children.forEach(e=>e.scale.y=(Math.sin(tt*2+w.off)>0.97)?0.05:0.8);
  });

  // tương tác
  cur=null; let txt='';
  if(hidden){ txt='[E] Thoát khỏi tủ'; }
  else if(!modalOpen&&!transitioning){
    const px=camera.position.x,pz=camera.position.z; let best=99;
    for(const o of inter){
      if(o.kind==='clue'&&solved[o.idx]) continue;
      if(o.kind==='door'&&doorOpen) continue;
      const dx=o.x-px,dzz=o.z-pz,d=Math.hypot(dx,dzz);
      if(d<o.r&&(dx*fxv+dzz*fzv)/(d||1)>0.35&&d<best){best=d;cur=o;}
    }
    if(cur) txt=cur.kind==='hide'?'[E] Trốn vào tủ':cur.kind==='door'?(solved.every(Boolean)?'[E] Nhập mật mã':'[E] Cửa (bị khóa)'):'[E] Xem manh mối';
  }
  const p=$('prompt'); p.style.display=txt?'block':'none'; p.textContent=txt;

  // sự kiện ngẫu nhiên + nhịp tim
  if(!modalOpen&&!transitioning){
    nextFlick-=dt; if(nextFlick<=0){flickT=.5;nextFlick=10+Math.random()*15;tone(120,.5,'sawtooth',.05,60);}
    evT-=dt; if(evT<=0){evT=12+Math.random()*14;tone(rnd(110,240),.8,'sawtooth',.04,rnd(60,100)); if(Math.random()<.6)whisper();}
    hbT-=dt; if(hp===1&&hbT<=0){tone(55,.12,'sine',.35,40);setTimeout(()=>tone(48,.12,'sine',.3,36),170);hbT=.85;}
  }
  lampF=1;
  if(flickT>0){flickT-=dt;lampF=Math.random()<.5?.08:1;}

  // Rush
  if(!modalOpen&&!transitioning){
    rushTimer-=dt;
    if(!rush&&rushTimer<=0){
      rush={phase:'warn',t:3,x:(Math.random()-.5)*8,z:-9};
      banner('⚡ Đèn nhấp nháy... RUSH sắp tới!\nTrốn vào tủ (E) hoặc né sang bên!',3000); tone(90,1.5,'sawtooth',.1,50);
    }
    if(rush){
      rush.t-=dt;
      if(rush.phase==='warn'){
        lampF=Math.random()<.5?0.05:1;
        if(rush.t<=0){rush.phase='run';rush.z=-9;rushMesh.position.set(rush.x,1.4,-9);noise(1.8,.45);tone(60,1.4,'sawtooth',.18,200);}
      } else {
        const z0=rush.z; rush.z+=15*dt; rushMesh.position.z=rush.z; lampF=Math.random()<.3?.2:1;
        const pz=camera.position.z; if(Math.abs(rush.z-pz)<9) shake=Math.max(shake,0.05);
        if(z0<pz&&rush.z>=pz){
          if(hidden) banner('😮‍💨 Bạn đã trốn thành công!',2000);
          else if(Math.abs(camera.position.x-rush.x)<2.2) damage('RUSH đã đâm vào bạn!');
        }
        if(rush.z>RD/2+4){rush=null;rushMesh.position.set(0,-50,0);rushTimer=25+Math.random()*20;}
      }
    }
  }
  lamp.intensity=1.0*lampF;
  if(flameMat){const v=Math.max(.15,lampF);flameMat.color.setRGB(v,.85*v,.63*v);}
  if(!hidden) spot.intensity=2.1*(0.93+0.07*Math.sin(tt*23))*(lampF<.5?0.5:1);
}

let last=performance.now();
function loop(now){
  requestAnimationFrame(loop);
  const dt=Math.min(0.05,(now-last)/1000); last=now;
  update(dt);
  camera.rotation.set(pitch,yaw,Math.sin(tt*.7)*0.004);
  if(shake>0){camera.rotation.z+=(Math.random()-.5)*shake;camera.rotation.x+=(Math.random()-.5)*shake*.4;shake=Math.max(0,shake-dt*.6);}
  renderer.render(scene,camera);
}
buildRoom(); camera.position.set(0,1.6,RD/2-2);
requestAnimationFrame(loop);
})();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# STREAMLIT
# ---------------------------------------------------------------------------
st.markdown("### 🚪 DOORS 3D – Thoát khỏi 5 cánh cửa")
st.caption("Bấm **BẮT ĐẦU** rồi click vào màn hình để khóa chuột. Nếu trình duyệt không khóa được chuột, "
           "hãy **kéo chuột** để xoay camera (hoặc dùng phím ← →). Máy yếu thì chọn **Chất lượng: Thấp**.")

components.html(GAME_HTML.replace("__DATA__", build_data()), height=760, scrolling=False)
