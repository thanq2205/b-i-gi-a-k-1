"""
🚪 DOORS 3D – Trò chơi giải đố 5 cửa, góc nhìn thứ nhất (lấy cảm hứng từ Doors trong Roblox)
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
      background:rgba(0,0,0,.85);text-align:center;padding:20px;z-index:20}
  .ov h1{font-size:52px;letter-spacing:8px;margin:0 0 10px;color:#e8c070}
  .ov p{max-width:560px;line-height:1.5;color:#ccc}
  button{background:#7a4a22;color:#fff;border:1px solid #e8c070;padding:10px 22px;font-size:16px;
         border-radius:6px;cursor:pointer;margin:4px;font-family:inherit}
  button:hover{background:#97602e}
  #hud{position:absolute;top:10px;left:12px;font-size:18px;text-shadow:0 0 4px #000;z-index:5;line-height:1.5}
  #ks{color:#ffd86b;font-size:20px}
  #ot{font-size:13px;color:#bbb}
  #help{position:absolute;bottom:8px;left:12px;font-size:12px;color:#aaa;z-index:5;text-shadow:0 0 3px #000}
  #cross{position:absolute;left:50%;top:50%;width:6px;height:6px;margin:-3px;border-radius:50%;
         background:rgba(255,255,255,.55);z-index:5;pointer-events:none}
  #prompt{position:absolute;left:50%;top:58%;transform:translateX(-50%);background:rgba(0,0,0,.6);
          padding:6px 14px;border-radius:6px;font-size:18px;display:none;z-index:6;border:1px solid #e8c070}
  #banner{position:absolute;left:50%;top:14%;transform:translateX(-50%);text-align:center;white-space:pre-line;
          font-size:22px;text-shadow:0 0 6px #000;opacity:0;transition:opacity .5s;z-index:6;max-width:80%;pointer-events:none}
  #flash{position:absolute;inset:0;background:#a00;opacity:0;pointer-events:none;transition:opacity .45s;z-index:7}
  #fade{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none;transition:opacity .8s;z-index:8}
  #hide{position:absolute;inset:0;display:none;pointer-events:none;z-index:4;
        background:linear-gradient(#000 0 40%,transparent 40% 58%,#000 58% 100%)}
  #modal{position:absolute;inset:0;display:none;align-items:center;justify-content:center;
         background:rgba(0,0,0,.6);z-index:15}
  #box{background:#1c130b;border:2px solid #e8c070;border-radius:10px;padding:22px;width:min(520px,86%);text-align:center}
  #mt{color:#e8c070;font-size:22px;margin-bottom:10px}
  #mq{font-size:18px;line-height:1.5;margin-bottom:12px}
  #mi{width:80%;padding:9px;font-size:18px;border-radius:5px;border:1px solid #888;background:#2b1f14;color:#fff;
      text-align:center;outline:none}
  #fb{min-height:24px;margin:10px 0;color:#ffd86b}
</style>
</head>
<body>
<div id="c"></div>
<div id="cross"></div>
<div id="hud"><div id="dn"></div><div id="hp"></div><div id="hn"></div><div id="ks"></div><div id="ot"></div></div>
<div id="help">WASD: di chuyển · Chuột: nhìn (kéo chuột nếu không khóa được) · E: tương tác · Shift: chạy · Esc: nhả chuột</div>
<div id="prompt"></div>
<div id="banner"></div>
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
  <p>Bạn bị kẹt trong một khách sạn bí ẩn. Mỗi phòng có <b>3 manh mối</b> phát sáng (sách, giấy trên tủ, bức tranh).
  Giải đố để lấy <b>chìa khóa</b>, ghép thành mật mã mở cửa.<br><br>
  ⚡ Khi đèn nhấp nháy, <b>RUSH</b> sắp lao qua phòng: hãy <b>trốn vào tủ</b> hoặc né sang bên!<br>
  Có 3 ❤️. Sai đáp án hoặc bị Rush đâm sẽ mất 1 ❤️.</p>
  <button id="start">▶ BẮT ĐẦU</button>
</div>
<div id="over" class="ov"><h1 style="color:#c33">BẠN ĐÃ CHẾT</h1><p id="overmsg"></p><button id="retry">🔄 Thử lại</button></div>
<div id="win" class="ov"><h1>🎉 THOÁT ĐƯỢC!</h1><p>Bạn đã vượt qua cả 5 cánh cửa!</p><button id="again">🔄 Chơi lại</button></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function(){
const DOORS = __DATA__;
const MAX_HP=3, HINTS0=5, RW=12, RD=16, RH=4;
const $=id=>document.getElementById(id);
let hp=MAX_HP, hints=HINTS0, door=0, solved=[false,false,false], hintShown={};
let state='menu', modalOpen=false, modalMode='q', modalIdx=0, hidden=false, doorOpen=false, transitioning=false;
let yaw=0, pitch=0, dragging=false, shake=0, bob=0, rush=null, rushTimer=25, bannerT=null, cur=null, wardI=null;
let keys={};

// ---------- Three.js ----------
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setSize(innerWidth,innerHeight);
$('c').appendChild(renderer.domElement);
const canvas=renderer.domElement;
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x050403);
scene.fog=new THREE.Fog(0x050403,3,18);
const camera=new THREE.PerspectiveCamera(72,innerWidth/innerHeight,0.1,60);
camera.rotation.order='YXZ';
scene.add(camera);
const spot=new THREE.SpotLight(0xfff0c8,1.7,20,Math.PI/5.5,0.45,1.2);
camera.add(spot); spot.position.set(0.2,-0.1,0); camera.add(spot.target); spot.target.position.set(0,0,-3);
scene.add(new THREE.AmbientLight(0x3a2a20,0.7));
const lamp=new THREE.PointLight(0xffb066,0.9,16); lamp.position.set(0,3.4,0); scene.add(lamp);

let room=null, doorPivot=null, obstacles=[], inter=[];

// Rush
const rushMesh=new THREE.Group();
(function(){
  const b=new THREE.Mesh(new THREE.SphereGeometry(1,16,12),new THREE.MeshBasicMaterial({color:0x000000}));
  b.scale.set(2.4,1.6,1.2); rushMesh.add(b);
  const em=new THREE.MeshBasicMaterial({color:0xffffff});
  [-0.7,0.7].forEach(x=>{const e=new THREE.Mesh(new THREE.SphereGeometry(0.22,10,8),em);e.position.set(x,0.3,1.1);rushMesh.add(e);});
  const l=new THREE.PointLight(0xff3322,1.5,7); l.position.set(0,0,2); rushMesh.add(l);
  rushMesh.position.y=1.4; rushMesh.visible=false; scene.add(rushMesh);
})();

const M=(c,e)=>new THREE.MeshStandardMaterial({color:c,roughness:.9,emissive:e||0x000000,side:THREE.DoubleSide});
const WALLC=[0x6b4a35,0x4a5a4a,0x4a5568,0x5a3a4a,0x3a3a3a];

function buildRoom(){
  if(room) scene.remove(room);
  room=new THREE.Group(); scene.add(room);
  obstacles=[]; inter=[]; doorOpen=false; wardI=null;
  const m=(door%2)?-1:1, wm=M(WALLC[door%5]);
  const plane=(w,h,mat,x,y,z,ry,rx)=>{const p=new THREE.Mesh(new THREE.PlaneGeometry(w,h),mat);
    p.position.set(x,y,z);p.rotation.y=ry||0;p.rotation.x=rx||0;room.add(p);return p;};
  const box=(sx,sy,sz,mat,x,y,z,parent)=>{const b=new THREE.Mesh(new THREE.BoxGeometry(sx,sy,sz),mat);
    b.position.set(x,y,z);(parent||room).add(b);return b;};
  const solid=(cx,cz,sx,sz,sy,color)=>{box(sx,sy,sz,M(color),cx,sy/2,cz);
    obstacles.push({x1:cx-sx/2,x2:cx+sx/2,z1:cz-sz/2,z2:cz+sz/2});};

  plane(RW,RD,M(0x4a1818),0,0,0,0,-Math.PI/2);
  plane(RW,RD,M(0x24190f),0,RH,0,0,Math.PI/2);
  plane(RW,RH,wm,0,RH/2,-RD/2);
  plane(RW,RH,wm,0,RH/2,RD/2,Math.PI);
  plane(RD,RH,wm,-RW/2,RH/2,0,Math.PI/2);
  plane(RD,RH,wm,RW/2,RH/2,0,-Math.PI/2);
  const bb=M(0x1a110a);
  box(RW,0.25,0.1,bb,0,0.12,-RD/2+0.05); box(RW,0.25,0.1,bb,0,0.12,RD/2-0.05);
  box(0.1,0.25,RD,bb,-RW/2+0.05,0.12,0); box(0.1,0.25,RD,bb,RW/2-0.05,0.12,0);
  // đèn trần (trang trí)
  box(0.6,0.1,0.6,new THREE.MeshBasicMaterial({color:0xffd9a0}),0,RH-0.05,0);

  // cửa
  const dz=-RD/2;
  const fm=M(0x1a1008);
  box(0.3,3.3,0.25,fm,-1.1,1.65,dz+0.12); box(0.3,3.3,0.25,fm,1.1,1.65,dz+0.12); box(2.5,0.3,0.25,fm,0,3.15,dz+0.12);
  const glow=new THREE.Mesh(new THREE.PlaneGeometry(1.9,3.0),new THREE.MeshBasicMaterial({color:0xfff1c9}));
  glow.position.set(0,1.5,dz+0.03); room.add(glow);
  doorPivot=new THREE.Group(); doorPivot.position.set(-0.9,0,dz+0.14); room.add(doorPivot);
  box(1.8,2.95,0.1,M(0x7a4a22),0.9,1.475,0,doorPivot);
  const knob=new THREE.Mesh(new THREE.SphereGeometry(0.07,10,8),M(0xd4af37,0x442200)); knob.position.set(1.55,1.4,0.1); doorPivot.add(knob);
  const cv=document.createElement('canvas'); cv.width=128; cv.height=64; const g=cv.getContext('2d');
  g.fillStyle='#caa24a'; g.fillRect(0,0,128,64); g.fillStyle='#2a1a08'; g.font='bold 44px serif';
  g.textAlign='center'; g.textBaseline='middle'; g.fillText(String(door+1).padStart(3,'0'),64,34);
  const pm=new THREE.Mesh(new THREE.PlaneGeometry(0.6,0.3),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(cv),color:0xaa9977}));
  pm.position.set(0.9,2.45,0.06); doorPivot.add(pm);
  inter.push({kind:'door',x:0,z:dz,r:2.7});

  // manh mối phát sáng
  const clue=(idx,x,y,z,sx,sy,sz)=>{
    const mat=new THREE.MeshStandardMaterial({color:0xffcc55,emissive:0xffaa22,emissiveIntensity:1.3});
    box(sx,sy,sz,mat,x,y,z);
    const L=new THREE.PointLight(0xffaa44,0.7,4.5); L.position.set(x,y+0.4,z+(z<-7?0.6:0)); room.add(L);
    inter.push({kind:'clue',idx,x,z,r:2.5,mat,L});
  };
  solid(-4.6*m,-2.5,1.3,2.5,0.8,0x3a2515);  clue(0,-4.6*m,0.86,-2.5,0.5,0.08,0.35);
  solid(4.9*m,0.5,1.1,2.2,1.2,0x2d2016);    clue(1,4.9*m,1.26,0.5,0.6,0.05,0.4);
  box(1.6,1.2,0.06,M(0x2a1a10),-3.2*m,2.0,-RD/2+0.06);
  clue(2,-3.2*m,2.0,-RD/2+0.12,1.3,1.0,0.05);

  // tủ quần áo để trốn
  solid(5*m,6.4,1.5,1.2,2.8,0x3b2a1c);
  box(0.04,2.4,0.02,M(0x000000),5*m,1.4,6.4-0.61);
  const w={kind:'hide',x:5*m,z:6.4,r:2.5}; inter.push(w); wardI=w;
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
}
function lock(){try{const p=canvas.requestPointerLock();if(p&&p.catch)p.catch(()=>{});}catch(e){}}
function unlock(){try{document.exitPointerLock();}catch(e){}}

function damage(msg){
  hp--; shake=0.3; sBad();
  const f=$('flash'); f.style.opacity=.7; setTimeout(()=>f.style.opacity=0,350);
  banner(msg+'  -1 ❤️',2500); updateHud();
  if(hp<=0) gameOver();
}
function gameOver(){
  state='over'; closeModal(true); unlock();
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
    if(v.trim()===code){ closeModal(); doorOpen=true; sGood(); banner('🔓 Cửa đã mở! Hãy bước vào ánh sáng...',3000); }
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
  solved=[false,false,false]; buildRoom(); hidden=false; spot.visible=true; $('hide').style.display='none';
  camera.position.set(0,1.6,RD/2-2); yaw=0; pitch=0; rush=null; rushMesh.visible=false; lamp.intensity=.9;
  rushTimer=18+Math.random()*10; updateHud();
  banner('CỬA '+(door+1)+': '+DOORS[door].name+'\n'+DOORS[door].intro,4500);
}
function resetGame(){hp=MAX_HP;hints=HINTS0;door=0;hintShown={};state='play';
  ['menu','over','win'].forEach(i=>$(i).style.display='none'); startRoom(); lock();}
$('start').onclick=resetGame; $('retry').onclick=resetGame; $('again').onclick=resetGame;
function nextRoom(){
  transitioning=true; $('fade').style.opacity=1;
  setTimeout(()=>{
    door++;
    if(door>=DOORS.length){state='win';unlock();$('win').style.display='flex';}
    else startRoom();
    $('fade').style.opacity=0; transitioning=false;
  },900);
}
function toggleHide(){
  if(!hidden){hidden=true;camera.position.set(wardI.x,1.5,wardI.z);yaw=0;pitch=0;spot.visible=false;$('hide').style.display='block';}
  else{hidden=false;camera.position.set(wardI.x,1.6,wardI.z-1.3);spot.visible=true;$('hide').style.display='none';}
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
  if(state!=='play') return;
  if(!modalOpen){ if(keys.ArrowLeft) yaw+=1.8*dt; if(keys.ArrowRight) yaw-=1.8*dt; }
  let moving=false;
  if(!modalOpen&&!hidden&&!transitioning){
    let f=0,s=0;
    if(keys.KeyW||keys.ArrowUp)f++; if(keys.KeyS||keys.ArrowDown)f--; if(keys.KeyD)s++; if(keys.KeyA)s--;
    if(f||s){
      moving=true; const sp=(keys.ShiftLeft||keys.ShiftRight?5.2:3.2)*dt, l=Math.hypot(f,s);
      const fx=-Math.sin(yaw),fz=-Math.cos(yaw),rx=Math.cos(yaw),rz=-Math.sin(yaw);
      const dx=(fx*f+rx*s)/l*sp, dzz=(fz*f+rz*s)/l*sp;
      if(!hit(camera.position.x+dx,camera.position.z)) camera.position.x+=dx;
      if(!hit(camera.position.x,camera.position.z+dzz)) camera.position.z+=dzz;
      bob+=dt*9;
    }
    const zmin=doorOpen?-RD/2-1.5:-RD/2+0.7;
    camera.position.x=Math.max(-RW/2+0.5,Math.min(RW/2-0.5,camera.position.x));
    camera.position.z=Math.max(zmin,Math.min(RD/2-0.5,camera.position.z));
    if(doorOpen&&camera.position.z<-RD/2+0.6) camera.position.x=Math.max(-0.75,Math.min(0.75,camera.position.x));
    if(doorOpen&&camera.position.z<-RD/2-0.3&&!transitioning) nextRoom();
  }
  if(!hidden) camera.position.y=1.6+(moving?Math.sin(bob)*0.035:0);
  if(doorOpen&&doorPivot.rotation.y<1.9) doorPivot.rotation.y=Math.min(1.9,doorPivot.rotation.y+dt*1.5);

  // tìm vật có thể tương tác
  cur=null; let txt='';
  if(hidden){ txt='[E] Thoát khỏi tủ'; }
  else if(!modalOpen&&!transitioning){
    const px=camera.position.x,pz=camera.position.z,fx=-Math.sin(yaw),fz=-Math.cos(yaw); let best=99;
    for(const o of inter){
      if(o.kind==='clue'&&solved[o.idx]) continue;
      if(o.kind==='door'&&doorOpen) continue;
      const dx=o.x-px,dzz=o.z-pz,d=Math.hypot(dx,dzz);
      if(d<o.r&&(dx*fx+dzz*fz)/(d||1)>0.35&&d<best){best=d;cur=o;}
    }
    if(cur) txt=cur.kind==='hide'?'[E] Trốn vào tủ':cur.kind==='door'?(solved.every(Boolean)?'[E] Nhập mật mã':'[E] Cửa (bị khóa)'):'[E] Xem manh mối';
  }
  const p=$('prompt'); p.style.display=txt?'block':'none'; p.textContent=txt;

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
        lamp.intensity=Math.random()<.5?0.05:1.0;
        if(rush.t<=0){rush.phase='run';rush.z=-9;rushMesh.visible=true;rushMesh.position.x=rush.x;noise(1.6,.4);}
      } else {
        const z0=rush.z; rush.z+=15*dt; rushMesh.position.z=rush.z; lamp.intensity=Math.random()<.3?.2:.9;
        const pz=camera.position.z;
        if(z0<pz&&rush.z>=pz){
          if(hidden) banner('😮‍💨 Bạn đã trốn thành công!',2000);
          else if(Math.abs(camera.position.x-rush.x)<2.2) damage('RUSH đã đâm vào bạn!');
        }
        if(rush.z>RD/2+4){rush=null;rushMesh.visible=false;lamp.intensity=.9;rushTimer=25+Math.random()*20;}
      }
    }
  }
}

let last=performance.now();
function loop(now){
  requestAnimationFrame(loop);
  const dt=Math.min(0.05,(now-last)/1000); last=now;
  update(dt);
  camera.rotation.set(pitch,yaw,0);
  if(shake>0){camera.rotation.z=(Math.random()-.5)*shake;shake=Math.max(0,shake-dt*.6);}
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
           "hãy **kéo chuột** để xoay camera (hoặc dùng phím ← →).")

components.html(GAME_HTML.replace("__DATA__", build_data()), height=760, scrolling=False)
