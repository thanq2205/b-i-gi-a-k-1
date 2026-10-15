"""
DOORS 3D – Trò chơi giải đố kinh dị 5 cửa, góc nhìn thứ nhất (lấy cảm hứng từ Doors trong Roblox)
Chạy:  streamlit run app.py
Đặt file nhạc "doors-roblox-ost-elevator-jam-made-with-Voicemod.mp3" cùng thư mục với app.py.
Game 3D chạy bằng Three.js, nhúng vào Streamlit qua components.html.
"""
import base64
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="DOORS 3D", layout="wide")


# ---------------------------------------------------------------------------
# DỮ LIỆU CÂU ĐỐ TRẮC NGHIỆM (sửa tại đây)
# Mỗi cửa có 3 câu. Chọn đúng -> nhận 1 chữ số. Ghép theo "order" để ra mật mã.
#   q: câu hỏi | a: đáp án ĐÚNG | w: 3 đáp án SAI | digit: chữ số | hint: gợi ý
# Vị trí A/B/C/D được xáo ngẫu nhiên mỗi lần mở câu hỏi.
# ---------------------------------------------------------------------------
DOORS = [
    {
        "name": "Sảnh đón tiếp",
        "intro": "Ánh đèn chập chờn. Hãy tìm 3 manh mối trong phòng.",
        "order": [0, 1, 2],
        "order_text": "Ghép chìa 1 → chìa 2 → chìa 3.",
        "questions": [
            {"q": "Cái gì càng lấy đi càng lớn?",
             "a": "Cái hố", "w": ["Cái bóng", "Cái cây", "Tuổi tác"],
             "digit": 4, "hint": "Bạn thường thấy nó khi đào đất."},
            {"q": "Có 3 quả táo, bạn lấy đi 2 quả. Vậy bạn đang có mấy quả táo?",
             "a": "2 quả", "w": ["1 quả", "3 quả", "5 quả"],
             "digit": 7, "hint": "Hỏi 'bạn có' chứ không hỏi 'còn lại'."},
            {"q": "Cái gì có chìa nhưng không mở được ổ khóa nào?",
             "a": "Đàn piano", "w": ["Cái tủ", "Con dao", "Quyển sách"],
             "digit": 1, "hint": "Nhạc cụ có phím đen phím trắng."},
        ],
    },
    {
        "name": "Thư viện bỏ hoang",
        "intro": "Bụi phủ kín mọi thứ. Có tiếng thì thầm: 'Hãy suy nghĩ...'",
        "order": [2, 1, 0],
        "order_text": "Ghép NGƯỢC: chìa 3 → chìa 2 → chìa 1.",
        "questions": [
            {"q": "Điền số tiếp theo: 2, 6, 12, 20, 30, ?",
             "a": "42", "w": ["36", "40", "44"],
             "digit": 3, "hint": "Hiệu giữa các số liên tiếp: 4, 6, 8, 10..."},
            {"q": "Có một từ trong từ điển luôn được 'viết sai'. Từ đó là gì?",
             "a": "Sai", "w": ["Đúng", "Chính tả", "Từ điển"],
             "digit": 8, "hint": "Chính câu hỏi đã chứa đáp án."},
            {"q": "Giải mã (mỗi chữ cái lùi 1 vị trí trong bảng chữ cái): EPPS",
             "a": "DOOR", "w": ["DOOM", "FOOT", "DEER"],
             "digit": 5, "hint": "E lùi 1 vị trí là D."},
        ],
    },
    {
        "name": "Phòng thí nghiệm",
        "intro": "Mùi hóa chất nồng nặc. Mọi thứ đều có vẻ không ổn...",
        "order": [1, 0, 2],
        "order_text": "Ghép chìa 2 → chìa 1 → chìa 3.",
        "questions": [
            {"q": "Một người đi bộ 3 km/giờ. Sau 2 giờ 30 phút đi được bao nhiêu km?",
             "a": "7,5 km", "w": ["6 km", "7 km", "8 km"],
             "digit": 9, "hint": "3 × 2,5"},
            {"q": "Điền số tiếp theo: 1, 1, 2, 3, 5, 8, ?",
             "a": "13", "w": ["11", "12", "14"],
             "digit": 6, "hint": "Mỗi số bằng tổng hai số đứng trước."},
            {"q": "Ký hiệu hóa học của vàng là gì?",
             "a": "Au", "w": ["Ag", "Fe", "Go"],
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
             "a": "Bản đồ", "w": ["Giấc mơ", "Bức ảnh", "Cuốn sách"],
             "digit": 2, "hint": "Bạn dùng nó để tìm đường."},
            {"q": "Số nhị phân 1011 bằng số thập phân nào?",
             "a": "11", "w": ["9", "10", "13"],
             "digit": 7, "hint": "8 + 0 + 2 + 1"},
            {"q": "Tôi nói mà không có miệng, nghe mà không có tai, chỉ sống nhờ không khí. Tôi là gì?",
             "a": "Tiếng vang", "w": ["Cơn gió", "Cái loa", "Bóng ma"],
             "digit": 3, "hint": "Hét vào hang núi sẽ nghe thấy tôi."},
        ],
    },
    {
        "name": "Phòng cuối cùng",
        "intro": "Cánh cửa cuối cùng, to lớn và lạnh lẽo. Chỉ còn một bước nữa...",
        "order": [2, 0, 1],
        "order_text": "Ghép chìa 3 → chìa 1 → chìa 2.",
        "questions": [
            {"q": "Tôi bay mà không có cánh, khóc mà không có mắt. Tôi là gì?",
             "a": "Đám mây", "w": ["Con chim", "Máy bay", "Cái bóng"],
             "digit": 1, "hint": "Nhìn lên trời khi sắp mưa."},
            {"q": "Trong cuộc đua, bạn vượt qua người đang đứng thứ 2. Giờ bạn thứ mấy?",
             "a": "Thứ 2", "w": ["Thứ 1", "Thứ 3", "Thứ 4"],
             "digit": 9, "hint": "Bạn thế chỗ người đó."},
            {"q": "Trong game Doors, thực thể nháy đèn rồi lao qua cực nhanh tên là gì?",
             "a": "Rush", "w": ["Seek", "Figure", "Screech"],
             "digit": 4, "hint": "Nó bắt đầu bằng chữ R."},
        ],
    },
]

MUSIC_FILE = "doors-roblox-ost-elevator-jam-made-with-Voicemod.mp3"
PLAY_MUSIC_FILE = "05._In_The_House.mp3"   # nhạc nền khi đang chơi


@st.cache_data(show_spinner=False)
def load_mp3(name: str, skip: str = "", fallback: bool = False) -> str:
    """Đọc file mp3 (cùng thư mục với app.py) và nhúng vào game dạng data-URI."""
    base = Path(__file__).resolve().parent
    p = base / name
    if not p.exists():
        if not fallback:
            return ""
        found = [f for f in sorted(base.glob("*.mp3")) if f.name != skip]
        if not found:
            return ""
        p = found[0]
    return "data:audio/mpeg;base64," + base64.b64encode(p.read_bytes()).decode()


def build_data() -> str:
    out = []
    for d in DOORS:
        out.append({
            "name": d["name"], "intro": d["intro"], "order": d["order"], "order_text": d["order_text"],
            # o[0] luôn là đáp án đúng; phía JS sẽ xáo thứ tự A/B/C/D
            "questions": [
                {"q": q["q"], "o": [q["a"]] + q["w"], "digit": q["digit"], "hint": q["hint"]}
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
  html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000;font-family:'Times New Roman','Noto Serif',Georgia,serif;color:#eee;user-select:none}
  /* Khung 16:9: #stage luôn giữ tỉ lệ 16:9 (letterbox), #ui là lớp giao diện thiết kế ở 1280x720 rồi scale theo khung */
  #stage{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);overflow:hidden;background:#000}
  #c{position:absolute;inset:0}
  #c canvas{display:block}
  #ui{position:absolute;left:0;top:0;width:1280px;height:720px;transform-origin:0 0;overflow:hidden;pointer-events:none}
  .ov,#modal,#sl,#fs,button,input{pointer-events:auto}
  #fs{position:absolute;top:8px;right:10px;z-index:30;padding:5px 10px;font-size:13px;margin:0;opacity:.75}
  #fs:hover{opacity:1}
  #nt{position:absolute;top:8px;right:76px;z-index:30;padding:5px 10px;font-size:13px;margin:0;opacity:.75;display:none}
  #nt:hover{opacity:1}
  #lockbtn{position:absolute;right:16px;bottom:16px;z-index:7;width:56px;height:56px;padding:0;margin:0;border-radius:50%;
           font-size:18px;font-weight:bold;background:rgba(0,0,0,.55);border:2px solid #9a2a2a;display:none}
  #lockbtn.on{background:rgba(120,90,10,.75);border-color:#ffd86b;box-shadow:0 0 14px #a80}
  #cross.lk{width:22px;height:22px;margin:-11px;background:transparent;border:2px solid rgba(255,255,255,.85);box-shadow:0 0 6px #000}
  #cross.lk:after{content:'';position:absolute;left:50%;top:50%;width:4px;height:4px;margin:-2px;border-radius:50%;background:#fff}
  #musichint{display:none;margin-top:14px;font-size:14px;color:#8a8070;animation:mh 1.6s infinite}
  @keyframes mh{0%,100%{opacity:.35}50%{opacity:1}}
  .row{display:flex;align-items:center;justify-content:center;gap:10px;margin:8px 0}
  .row input[type=range]{width:320px;accent-color:#b3141a}
  .sq{width:42px;padding:6px 0;font-size:20px}
  #settings .hw{text-align:center;width:600px}
  #ql{color:#ffd86b;font-size:19px;margin:4px 0}
  #qd{font-size:13px;color:#9a9080;margin:4px auto;max-width:520px}
  #opts{display:none;flex-direction:column;gap:8px;margin-bottom:8px}
  .opt{display:flex;align-items:center;gap:12px;width:100%;text-align:left;font-size:17px;padding:10px 14px;margin:0;letter-spacing:0;box-sizing:border-box}
  .opt b{display:inline-block;flex:none;min-width:28px;height:28px;line-height:28px;text-align:center;border-radius:50%;background:#7a2a2a;color:#ffd86b}
  .opt.bad{opacity:.38;text-decoration:line-through;cursor:not-allowed;background:#1c0808;border-color:#4a2a2a;box-shadow:none}
  .ov{position:absolute;inset:0;display:none;flex-direction:column;align-items:center;justify-content:center;
      background:radial-gradient(ellipse at center,rgba(30,8,8,.88),rgba(0,0,0,.97));text-align:center;padding:20px;z-index:20;overflow:auto}
  .ov h1{font-size:64px;letter-spacing:14px;margin:0 0 18px;color:#b3141a;text-shadow:0 0 18px #600,0 0 4px #000}
  .ov p{max-width:580px;line-height:1.55;color:#c9c0b0}
  button{background:#3a0d0d;color:#eee;border:1px solid #9a2a2a;padding:10px 22px;font-size:16px;
         border-radius:4px;cursor:pointer;margin:4px;font-family:inherit;letter-spacing:1px}
  button:hover{background:#6a1414;box-shadow:0 0 12px #a00}
  .mb{display:flex;flex-direction:column;align-items:center;gap:6px}
  .mb button{width:260px;font-size:19px;padding:12px 22px}
  .hw{max-width:700px;text-align:left;line-height:1.5;color:#c9c0b0;font-size:15px}
  .hw h3{margin:14px 0 4px;color:#d9b45a;font-size:17px;letter-spacing:1px}
  .hw ul{margin:0;padding-left:20px}
  .hw b{color:#fff}
  .hw kbd{background:#2a1010;border:1px solid #7a2a2a;border-radius:3px;padding:0 6px;font-family:inherit;color:#ffd86b}
  #hud{position:absolute;top:10px;left:12px;font-size:17px;text-shadow:0 0 4px #000;z-index:5;line-height:1.5}
  #ks{color:#ffd86b;font-size:20px}
  #ot{font-size:13px;color:#bbb}
  #sl{font-size:13px;color:#999;cursor:pointer;display:inline-block;margin-top:2px}
  #sl.on{color:#7dff9a}
  #help{position:absolute;bottom:8px;left:12px;font-size:12px;color:#8a8a8a;z-index:5;text-shadow:0 0 3px #000}
  #cross{position:absolute;left:50%;top:50%;width:4px;height:4px;margin:-2px;border-radius:50%;
         background:rgba(255,255,255,.45);z-index:5;pointer-events:none}
  #prompt{position:absolute;left:50%;top:58%;transform:translateX(-50%);background:rgba(0,0,0,.65);
          padding:6px 14px;border-radius:4px;font-size:18px;display:none;z-index:6;border:1px solid #9a2a2a}
  #banner{position:absolute;left:50%;top:14%;transform:translateX(-50%);text-align:center;white-space:pre-line;
          font-size:22px;text-shadow:0 0 8px #000;opacity:0;transition:opacity .5s;z-index:6;max-width:80%;pointer-events:none}
  #whisper{position:absolute;font-size:30px;font-style:italic;color:#8a0c0c;opacity:0;transition:opacity 1s;
           z-index:4;pointer-events:none;text-shadow:0 0 10px #000;letter-spacing:3px}
  #flash{position:absolute;inset:0;background:#a00;opacity:0;pointer-events:none;transition:opacity .45s;z-index:11}
  #bars{position:absolute;inset:0;pointer-events:none;z-index:9;opacity:0;transition:opacity .6s;
        background:linear-gradient(#000 0 12%,transparent 12% 88%,#000 88%)}
  #bars.on{opacity:1}
  #warn{z-index:25}
  .chk{display:flex;align-items:center;gap:10px;justify-content:center;margin:14px 0;color:#e0d6c0;font-size:16px;cursor:pointer}
  .chk input{width:20px;height:20px;accent-color:#b3141a;cursor:pointer}
  #fade{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none;transition:opacity .8s;z-index:12}
  #scare{position:absolute;inset:0;width:100%;height:100%;display:none;pointer-events:none;z-index:10;image-rendering:pixelated}
  #hide{position:absolute;inset:0;display:none;pointer-events:none;z-index:4}
  #hide.ward{background:linear-gradient(#000 0 40%,transparent 40% 58%,#000 58% 100%)}
  #hide.bed{background:linear-gradient(#000 0 42%,transparent 60%),radial-gradient(ellipse at center,transparent 45%,rgba(0,0,0,.85) 100%)}
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
  /* Bảng câu hỏi = một tờ giấy cũ */
  /* Bảng câu hỏi = tờ giấy nhàu, rách mép, chữ viết tay bằng bút chì (kiểu mấy tờ giấy trong Doors) */
  #box{position:relative;color:#16130f;border:0;padding:36px 48px 34px;width:min(760px,90%);
       text-align:center;transform:rotate(-1deg);
       font-family:'Segoe Print','Bradley Hand','Chalkboard SE','Comic Sans MS','Marker Felt',cursive;
       background:#b3a78c;background-size:100% 100%;
       clip-path:polygon(1% 3%,12% 0,27% 2.5%,44% .5%,63% 2%,82% 0,99% 2%,100% 20%,98.5% 38%,100% 57%,98% 76%,100% 98%,84% 100%,66% 98%,48% 100%,30% 98.5%,12% 100%,0 97%,1.5% 78%,0 58%,2% 38%,0 18%)}
  #mt{color:#8a0f0f;font-size:30px;margin-bottom:12px;font-weight:900;letter-spacing:2px;text-transform:uppercase;text-shadow:none}
  #mq{font-size:27px;line-height:1.4;margin-bottom:18px;color:#16130f;font-weight:900;text-transform:uppercase;letter-spacing:.5px;
      text-shadow:none;-webkit-font-smoothing:antialiased}
  #mi{width:80%;padding:9px;font-size:22px;border:0;border-bottom:3px solid #2b2722;border-radius:0;
      background:rgba(255,255,255,.14);color:#2b2722;text-align:center;outline:none;font-family:inherit;letter-spacing:4px}
  #fb{min-height:28px;margin:10px 0;color:#8a0f0f;font-size:21px;font-weight:900;text-transform:uppercase;letter-spacing:1px}
  #box button{background:rgba(40,32,20,.06);color:#16130f;border:3px solid #16130f;border-radius:3px 8px 4px 7px;
      box-shadow:none;font-family:inherit;text-transform:uppercase;text-shadow:none;font-weight:900;font-size:19px;padding:10px 22px}
  #box button:hover{background:#16130f;color:#d8ccb0;box-shadow:none;text-shadow:none}
  #box .opt{font-size:25px;font-weight:900;padding:11px 18px;gap:16px;letter-spacing:.5px}
  #box .opt b{background:transparent;color:#8a0f0f;border:3px solid #8a0f0f;text-shadow:none;font-size:22px;min-width:40px;height:40px;line-height:36px}
  #box .opt.bad{opacity:.5;text-decoration:line-through;text-decoration-thickness:3px;cursor:not-allowed;background:rgba(0,0,0,.06);border-color:#7a6e55;color:#5e5543}
  #box .opt.bad:hover{background:rgba(0,0,0,.06);color:#5e5543}
</style>
</head>
<body>
<div id="stage"><div id="c"></div><div id="ui">
<div id="vig"></div><canvas id="grain"></canvas><div id="lowhp"></div>
<div id="cross"></div>
<div id="hud"><div id="dn"></div><div id="hp"></div><div id="hn"></div><div id="ks"></div><div id="ot"></div><div id="sl"></div></div>
<div id="help">WASD / ←→: di chuyển · Kéo chuột: nhìn · Shift: Shift Lock · Giữ Space: chạy · E: tương tác · A/B/C/D: chọn đáp án · Esc: đóng</div>
<button id="fs" title="Toàn màn hình">FULL</button>
<button id="nt" title="Mở game ở tab mới (Shift Lock chuẩn như Roblox)">TAB MỚI</button>
<button id="lockbtn" title="Shift Lock (phím Shift)">SL</button>
<div id="prompt"></div>
<div id="banner"></div>
<div id="whisper"></div>
<div id="hide"></div>
<canvas id="scare" width="640" height="360"></canvas>
<div id="flash"></div>
<div id="bars"></div>
<div id="fade"></div>

<div id="modal"><div id="box">
  <div id="mt"></div><div id="mq"></div>
  <div id="opts"></div>
  <input id="mi" autocomplete="off" spellcheck="false">
  <div id="fb"></div>
  <button id="b1">Trả lời</button><button id="b2">Gợi ý</button><button id="b3">Đóng (Esc)</button>
</div></div>

<div id="menu" class="ov" style="display:flex">
  <h1>DOORS</h1>
  <div class="mb">
    <button id="start">CHƠI</button>
    <button id="how">HƯỚNG DẪN</button>
    <button id="settingsBtn">CÀI ĐẶT</button>
  </div>
  <p id="musichint">Bấm vào bất kỳ đâu để bật nhạc</p>
</div>

<div id="settings" class="ov">
  <h1 style="font-size:40px;letter-spacing:8px">CÀI ĐẶT</h1>
  <div class="hw">
    <h3>Đồ họa</h3>
    <div class="row"><button id="gLow">THẤP</button><button id="gHigh">CAO</button></div>
    <div class="row"><button id="qm" class="sq">−</button><input id="qr" type="range" min="1" max="10" step="1" value="8"><button id="qp" class="sq">+</button></div>
    <div id="ql"></div>
    <p id="qd"></p>
    <h3>Hiệu ứng</h3>
    <label class="chk" style="justify-content:flex-start"><input type="checkbox" id="rfchk2"> Giảm hiệu ứng chớp sáng (an toàn hơn cho người nhạy cảm ánh sáng)</label>
    <h3>Âm lượng nhạc</h3>
    <div class="row"><input id="vr" type="range" min="0" max="100" step="5" value="60"><span id="vv">60%</span></div>
  </div>
  <button id="sback">Quay lại</button>
</div>

<div id="howto" class="ov">
  <h1 style="font-size:40px;letter-spacing:8px">HƯỚNG DẪN</h1>
  <div class="hw">
    <h3>Điều khiển</h3>
    <ul>
      <li><kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> hoặc phím mũi tên: di chuyển / xoay</li>
      <li><b>Kéo chuột</b>: nhìn xung quanh</li>
      <li><kbd>Shift</kbd> hoặc nút SL góc phải dưới: bật / tắt <b>Shift Lock</b> giống Roblox — chuột bị khóa ở giữa màn hình, hiện tâm ngắm, xoay camera mà không cần bấm chuột. Lỡ nhả chuột (Esc) thì bấm vào màn hình để khóa lại</li>
      <li>Khi tắt Shift Lock: giữ chuột trái hoặc phải rồi kéo để nhìn</li>
      <li>Nếu chạy trong Streamlit mà không khóa được chuột (trình duyệt chặn), bấm nút <kbd>TAB MỚI</kbd> góc phải trên để mở game ở tab mới</li>
      <li><kbd>A</kbd><kbd>B</kbd><kbd>C</kbd><kbd>D</kbd> hoặc bấm chuột: chọn đáp án khi trả lời câu hỏi</li>
      <li>Giữ <kbd>Space</kbd>: chạy</li>
      <li><kbd>E</kbd>: tương tác (xem manh mối, mở cửa, trốn vào tủ / gầm giường)</li>
      <li><kbd>Esc</kbd>: đóng bảng câu hỏi</li>
    </ul>
    <h3>Mục tiêu</h3>
    <ul>
      <li>Mỗi phòng có <b>3 manh mối</b> phát sáng nhấp nháy 3 giây một lần. Trả lời <b>câu hỏi trắc nghiệm A/B/C/D</b> để lấy 3 chữ số (chìa khóa).</li>
      <li>Ghép các chữ số theo đúng thứ tự gợi ý rồi nhập mật mã vào <b>cánh cửa</b> để sang phòng tiếp theo.</li>
      <li>Có 5 cánh cửa. Chọn sai đáp án hoặc nhập sai mật mã sẽ mất 1 (có 3 ).</li>
    </ul>
    <h3>Con ma</h3>
    <ul>
      <li>Thỉnh thoảng <b>đèn sẽ chớp liên tục</b>. Đó là dấu hiệu một con ma sắp xuất hiện.</li>
      <li>Hãy <b>trốn ngay</b> vào <b>tủ quần áo</b> hoặc <b>gầm giường</b> (nhìn vào rồi bấm <kbd>E</kbd>).</li>
      <li>Khi đã trốn, đừng cử động. Ma sẽ đến lục soát rồi bỏ đi. Chỉ ra ngoài khi nó đã đi hẳn.</li>
      <li>Nếu bị ma bắt, bạn <b>chết</b> và phải <b>chơi lại từ cửa số 1</b>.</li>
      <li>Những đôi mắt đỏ trong bóng tối sẽ biến mất khi bạn nhìn thẳng vào chúng.</li>
    </ul>
    <p style="text-align:center;color:#8a8a8a;margin-top:14px"><i>Nên đeo tai nghe và tắt đèn phòng.</i></p>
  </div>
  <button id="hback">Quay lại</button>
</div>

<div id="warn" class="ov" style="display:flex">
  <h1 style="color:#d9b45a;font-size:46px;letter-spacing:8px;text-shadow:0 0 14px #6a4a10">CẢNH BÁO</h1>
  <div class="hw" style="width:620px">
    <p style="margin:0 0 6px;max-width:none">Trò chơi này là game <b>kinh dị</b> và có chứa:</p>
    <ul>
      <li><b>Âm thanh lớn, đột ngột</b> (tiếng hét, tiếng động mạnh). Hãy hạ âm lượng trước khi chơi, nhất là khi đeo tai nghe.</li>
      <li><b>Ánh sáng chớp nhanh, màn hình nhấp nháy</b>. Có thể gây khó chịu hoặc kích phát cơn co giật ở người nhạy cảm với ánh sáng / mắc chứng động kinh.</li>
      <li><b>Cảnh hù dọa bất ngờ</b> (jumpscare) và hình ảnh rùng rợn.</li>
      <li><b>Không phù hợp</b> với trẻ nhỏ, người có bệnh tim hoặc dễ hoảng sợ.</li>
    </ul>
    <p style="margin:10px 0 0;max-width:none">Nếu cảm thấy chóng mặt, buồn nôn, đau đầu hoặc khó chịu, hãy <b>dừng chơi ngay</b> và nghỉ ngơi.</p>
  </div>
  <label class="chk"><input type="checkbox" id="rfchk"> Giảm hiệu ứng chớp sáng (khuyên dùng nếu nhạy cảm với ánh sáng)</label>
  <button id="warnok" style="font-size:19px;padding:12px 30px">Tôi hiểu, tiếp tục</button>
</div>

<div id="over" class="ov"><h1>BẠN ĐÃ CHẾT</h1><p id="overmsg"></p>
  <div><button id="retry">Chơi lại từ đầu</button><button id="tomenu">Menu</button></div></div>
<div id="win" class="ov"><h1 style="color:#d9b45a">THOÁT ĐƯỢC!</h1><p>Bạn đã vượt qua cả 5 cánh cửa... lần này.</p>
  <div><button id="again">Chơi lại</button><button id="tomenu2">Menu</button></div></div>

</div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function(){
const DOORS = __DATA__;
const MUSIC_SRC = "__MUSIC__";
const PLAY_SRC = "__MUSIC2__";
const MAX_HP=3, HINTS0=5, RH=4;
const SIZES=[[18,26],[20,28],[22,30],[22,32],[24,34]];
let RW=18, RD=26;
const $=id=>document.getElementById(id);
const SRC='<!DOCTYPE html>\n'+document.documentElement.outerHTML;   // bản sao trang để mở ở tab mới
function loadNum(k,d,lo,hi){try{const v=parseInt(localStorage.getItem(k));return(v>=lo&&v<=hi)?v:d;}catch(e){return d;}}
function saveNum(k,v){try{localStorage.setItem(k,v);}catch(e){}}
let Q=loadNum('doors_q',8,1,10), HQ=Q>=6;       // mức đồ họa 1-10 (<=5: Thấp, >=6: Cao)
let STW=1280, STH=720, mouseX=0, mouseY=0, mouseIn=false, optOrder=[], wrongSet={}, lockFailShown=false, lockBlocked=false, lockEver=false;
// Cao: độ phân giải gần đầy đủ. Thấp: render độ phân giải rất nhỏ rồi phóng to kiểu pixel (low-poly retro)
const pr=()=>HQ?Math.max(.8,Math.min(window.devicePixelRatio||1,.55+Q*.15)):(0.28+Q*0.05);
let RF=loadNum('doors_rf',0,0,1)===1;   // giảm hiệu ứng chớp sáng
let hp=MAX_HP, hints=HINTS0, door=0, solved=[false,false,false], hintShown={};
let state='menu', modalOpen=false, modalMode='q', modalIdx=0, hidden=false, doorOpen=false, transitioning=false;
let yaw=0, pitch=0, dragging=false, shake=0, bob=0, bannerT=null, cur=null, curSpot=null, spots=[];
let keys={}, tt=0, stepT=0, hbT=0, evT=14, flickT=0, nextFlick=12, lampF=1, dark=0;
let shiftLock=false, expectUnlock=false, scareT=0, scareYaw=0, ghostTimer=40, scareFlashT=0;
let room=null, doorPivot=null, obstacles=[], inter=[], watchers=[], flameMat=null, fireMat=null;
const gh={phase:'idle',t:0,t0:1,x:0,z:0,alpha:0,peek:0,face:0,step:0,ux:0,uz:1};

// ---------- Renderer / Scene ----------
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(pr());
renderer.setSize(1280,720);
renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.3;
renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
$('c').appendChild(renderer.domElement);
const canvas=renderer.domElement;
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x030101);
scene.fog=new THREE.FogExp2(0x050202,0.045);
const camera=new THREE.PerspectiveCamera(72,16/9,0.1,70);
camera.rotation.order='YXZ';
scene.add(camera);
// Khung 16:9 luôn nằm gọn trong màn hình (letterbox), giao diện scale theo khung
const stage=$('stage'), ui=$('ui');
function fit(){
  const W=innerWidth,H=innerHeight; let w=W,h=Math.round(W*9/16);
  if(h>H){h=H;w=Math.round(H*16/9);}
  STW=w;STH=h; stage.style.width=w+'px'; stage.style.height=h+'px';
  ui.style.transform='scale('+(w/1280)+')';
  renderer.setSize(w,h); camera.aspect=16/9; camera.updateProjectionMatrix();
}
fit();

// Đèn pin
const spot=new THREE.SpotLight(0xfff0cc,2.1,24,Math.PI/5.2,0.5,1.1);
camera.add(spot); spot.position.set(0.2,-0.1,0); camera.add(spot.target); spot.target.position.set(0,0,-3);
spot.shadow.mapSize.set(1024,1024); spot.shadow.camera.near=0.2; spot.shadow.camera.far=24; spot.shadow.bias=-0.0006;
const ambL=new THREE.AmbientLight(0x4a3a34,0.85); scene.add(ambL);
// Các đèn cố định (tạo một lần để tránh biên dịch lại shader)
const lamp=new THREE.PointLight(0xffb066,1.1,24); scene.add(lamp);
lamp.shadow.mapSize.set(512,512); lamp.shadow.camera.near=0.3; lamp.shadow.camera.far=24; lamp.shadow.bias=-0.003;
const lampB=new THREE.PointLight(0xffb066,0.9,22); scene.add(lampB);
const doorLight=new THREE.PointLight(0xfff1c9,0,10); scene.add(doorLight);
const sconceL=[0,1].map(()=>{const l=new THREE.PointLight(0xff9a40,1.0,9);scene.add(l);return l;});
const clueL=[0,1,2].map(()=>{const l=new THREE.PointLight(0xffaa44,.9,5.5);scene.add(l);return l;});

// Bụi bay
const DUST=320, dustPos=new Float32Array(DUST*3);
const dustGeo=new THREE.BufferGeometry(); dustGeo.setAttribute('position',new THREE.BufferAttribute(dustPos,3));
const dust=new THREE.Points(dustGeo,new THREE.PointsMaterial({color:0xffddaa,size:0.035,transparent:true,opacity:.45,depthWrite:false}));
dust.frustumCulled=false; scene.add(dust);
function resetDust(){for(let i=0;i<DUST;i++){dustPos[i*3]=(Math.random()-.5)*RW;dustPos[i*3+1]=Math.random()*RH;dustPos[i*3+2]=(Math.random()-.5)*RD;}
  dustGeo.attributes.position.needsUpdate=true;}

// ---------- Texture thủ tục ----------
const CAN={};
function T(key,w,h,draw,rx,ry){
  if(!CAN[key]){const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);CAN[key]=c;}
  const t=new THREE.CanvasTexture(CAN[key]); t.wrapS=t.wrapT=THREE.RepeatWrapping; t.repeat.set(rx||1,ry||1); t.anisotropy=4;
  if(!HQ){t.magFilter=THREE.NearestFilter;t.minFilter=THREE.NearestMipmapNearestFilter;t.anisotropy=1;}   // texture vuông pixel
  return t;
}
const rnd=(a,b)=>a+Math.random()*(b-a);
function mulberry(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
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
  g.fillStyle='#3d0d10';g.fillRect(0,0,w,h);g.strokeStyle='rgba(200,150,60,.22)';g.lineWidth=2;
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
const rugTex=()=>T('rug',256,512,(g,w,h)=>{
  g.fillStyle='#3b0c10';g.fillRect(0,0,w,h);
  g.strokeStyle='#b8893a';g.lineWidth=6;g.strokeRect(10,10,w-20,h-20);g.lineWidth=2;g.strokeRect(24,24,w-48,h-48);
  g.fillStyle='rgba(184,137,58,.35)';
  for(let i=0;i<5;i++){const cy=90+i*85;g.beginPath();g.moveTo(w/2,cy-34);g.lineTo(w/2+44,cy);g.lineTo(w/2,cy+34);g.lineTo(w/2-44,cy);g.closePath();g.fill();}
  stains(g,w,h,18,.3);noiseFx(g,w,h,30);});
const clockTex=()=>T('clock',128,128,(g,w,h)=>{
  g.fillStyle='#c9b98c';g.beginPath();g.arc(64,64,60,0,7);g.fill();g.strokeStyle='#2a1a08';g.lineWidth=4;g.stroke();
  g.lineWidth=3;for(let i=0;i<12;i++){const a=i/12*6.283;g.beginPath();g.moveTo(64+Math.sin(a)*48,64-Math.cos(a)*48);g.lineTo(64+Math.sin(a)*56,64-Math.cos(a)*56);g.stroke();}
  g.lineWidth=5;g.beginPath();g.moveTo(64,64);g.lineTo(64+Math.sin(.4)*30,64-Math.cos(.4)*30);g.stroke();
  g.lineWidth=3;g.beginPath();g.moveTo(64,64);g.lineTo(64+Math.sin(4.1)*44,64-Math.cos(4.1)*44);g.stroke();noiseFx(g,w,h,18);});
const webTex=()=>T('web',128,128,(g,w,h)=>{
  g.clearRect(0,0,w,h);g.strokeStyle='rgba(220,220,220,.55)';g.lineWidth=1;
  for(let i=0;i<=6;i++){const a=i/6*Math.PI/2;g.beginPath();g.moveTo(0,0);g.lineTo(Math.cos(a)*128,Math.sin(a)*128);g.stroke();}
  for(let r=18;r<130;r+=18){g.beginPath();for(let i=0;i<=6;i++){const a=i/6*Math.PI/2,rr=r*(0.9+Math.random()*.2),x=Math.cos(a)*rr,y=Math.sin(a)*rr;if(i)g.lineTo(x,y);else g.moveTo(x,y);}g.stroke();}});
const faceTex=()=>T('face',512,640,(g,w,h)=>{
  const gr=g.createRadialGradient(w/2,h*.45,30,w/2,h*.5,w*.75);gr.addColorStop(0,'#dcd6c6');gr.addColorStop(1,'#625b50');
  g.fillStyle=gr;g.fillRect(0,0,w,h);
  g.strokeStyle='rgba(40,40,40,.55)';g.lineWidth=1.4;
  for(let i=0;i<46;i++){let x=rnd(0,w),y=rnd(0,h);g.beginPath();g.moveTo(x,y);for(let k=0;k<5;k++){x+=rnd(-26,26);y+=rnd(6,28);g.lineTo(x,y);}g.stroke();}
  [-1,1].forEach(s=>{g.save();g.translate(w/2+s*102,h*.36);g.rotate(s*.28);
    const eg=g.createRadialGradient(0,0,4,0,0,76);eg.addColorStop(0,'#000');eg.addColorStop(.7,'#050505');eg.addColorStop(1,'rgba(20,20,20,0)');
    g.fillStyle=eg;g.beginPath();g.ellipse(0,0,64,98,0,0,7);g.fill();
    g.fillStyle='#e8e8f0';g.beginPath();g.arc(0,8,5,0,7);g.fill();g.restore();
    g.strokeStyle='rgba(20,20,20,.7)';g.lineWidth=5;g.beginPath();g.moveTo(w/2+s*92,h*.36+90);g.lineTo(w/2+s*88,h*.36+200);g.stroke();});
  g.fillStyle='#101010';[-1,1].forEach(s=>{g.beginPath();g.ellipse(w/2+s*14,h*.55,6,15,s*.3,0,7);g.fill();});
  g.save();g.translate(w/2,h*.77);
  g.fillStyle='#000';g.beginPath();g.ellipse(0,0,150,128,0,0,7);g.fill();
  const ey=x=>Math.sqrt(Math.max(0,1-(x/150)*(x/150)))*128;
  g.fillStyle='#e8e2d0';
  for(let i=-6;i<=6;i++){const x=i*21,hh=26+Math.abs(Math.sin(i*2.1))*22;
    g.beginPath();g.moveTo(x-9,-ey(x-9)+3);g.lineTo(x,-ey(x)+hh);g.lineTo(x+9,-ey(x+9)+3);g.fill();
    g.beginPath();g.moveTo(x-9,ey(x-9)-3);g.lineTo(x,ey(x)-hh*.8);g.lineTo(x+9,ey(x+9)-3);g.fill();}
  g.restore();
  stains(g,w,h,10,.25);noiseFx(g,w,h,16);});

// ---------- Cơn bão bên ngoài cửa sổ (mưa, sét, sấm) ----------
const haloTex=()=>T('halo',64,64,(g,w,h)=>{
  const gr=g.createRadialGradient(32,32,0,32,32,32);
  gr.addColorStop(0,'rgba(255,255,255,1)');gr.addColorStop(.35,'rgba(255,255,255,.4)');gr.addColorStop(1,'rgba(255,255,255,0)');
  g.fillStyle=gr;g.fillRect(0,0,w,h);});
const stC=document.createElement('canvas'); stC.width=256; stC.height=192;
const stG=stC.getContext('2d');
const stTex=new THREE.CanvasTexture(stC); stTex.wrapS=THREE.RepeatWrapping;
const stormMat=new THREE.MeshBasicMaterial({map:stTex,fog:false}); stormMat.userData.keep=true;
const stormL=new THREE.PointLight(0x9db8ff,0,45); scene.add(stormL);
const drops=[]; for(let i=0;i<150;i++) drops.push({x:Math.random()*256,y:Math.random()*192,v:260+Math.random()*260,l:7+Math.random()*12});
const trees=[]; for(let i=0;i<15;i++) trees.push({x:i*18+Math.random()*8,h:28+Math.random()*34,w:12+Math.random()*10});
let flashV=0, boltT=0, nextBolt=3.5, thunderIn=-999, thunderNear=false, boltX=60, boltPts=[], stAcc=0;
const cl255=v=>Math.max(0,Math.min(255,Math.round(v)));
function drawStorm(dt){
  const g=stG,w=256,h=192,f=flashV;
  const gr=g.createLinearGradient(0,0,0,h);
  gr.addColorStop(0,'rgb('+cl255(10+f*190)+','+cl255(14+f*200)+','+cl255(26+f*225)+')');
  gr.addColorStop(1,'rgb('+cl255(22+f*170)+','+cl255(30+f*180)+','+cl255(46+f*200)+')');
  g.fillStyle=gr; g.fillRect(0,0,w,h);
  // mây đen trôi
  for(let i=0;i<6;i++){
    const x=((i*58+tt*5)%330)-35, y=14+(i%3)*15;
    g.fillStyle='rgba('+cl255(30+f*170)+','+cl255(36+f*170)+','+cl255(56+f*170)+',.6)';
    g.beginPath(); g.ellipse(x,y,55,15,0,0,7); g.fill();
  }
  // bóng cây, đồi phía xa
  const tc='rgb('+cl255(4+f*50)+','+cl255(6+f*55)+','+cl255(12+f*70)+')';
  g.fillStyle=tc; g.fillRect(0,h-14,w,14);
  trees.forEach(t=>{g.beginPath(); g.moveTo(t.x,h-12); g.lineTo(t.x+t.w/2,h-12-t.h); g.lineTo(t.x+t.w,h-12); g.fill();});
  // tia sét
  if(boltT>.7&&boltPts.length>1){
    g.lineJoin='round';
    g.strokeStyle='rgba(150,170,255,.28)'; g.lineWidth=7;
    g.beginPath(); boltPts.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])); g.stroke();
    g.strokeStyle='rgba(245,248,255,'+Math.min(1,.5+f)+')'; g.lineWidth=2.4;
    g.beginPath(); boltPts.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])); g.stroke();
    const b=boltPts[Math.floor(boltPts.length/2)];
    g.lineWidth=1.4; g.beginPath(); g.moveTo(b[0],b[1]); g.lineTo(b[0]+22,b[1]+26); g.lineTo(b[0]+14,b[1]+50); g.stroke();
  }
  // mưa
  g.strokeStyle='rgba(180,200,235,'+(.38+f*.4)+')'; g.lineWidth=1; g.beginPath();
  for(let i=0;i<drops.length;i++){
    const d=drops[i]; d.y+=d.v*dt; d.x-=d.v*dt*.18;
    if(d.y>h){d.y=-d.l;d.x=Math.random()*(w+40);} if(d.x<-10) d.x+=w+10;
    g.moveTo(d.x,d.y); g.lineTo(d.x-d.l*.18,d.y+d.l);
  }
  g.stroke();
  // lớp hơi nước mờ trên kính
  g.fillStyle='rgba(120,140,180,.07)'; g.fillRect(0,0,w,h);
}
function thunder(near){
  if(!amb) return;
  try{
    const a=ac(), t0=a.currentTime, n=Math.floor(a.sampleRate*4.2), b=a.createBuffer(1,n,a.sampleRate), x=b.getChannelData(0);
    for(let i=0;i<n;i++){const t=i/n; x[i]=(Math.random()*2-1)*Math.pow(1-t,1.25)*(.6+.4*Math.sin(t*30)+.25*Math.sin(t*71));}
    const s=a.createBufferSource(), lp=a.createBiquadFilter(), g=a.createGain(), cp=a.createDynamicsCompressor();
    lp.type='lowpass'; lp.frequency.setValueAtTime(1100,t0); lp.frequency.exponentialRampToValueAtTime(45,t0+3.8);
    g.gain.value=near?9:6.5;
    cp.threshold.value=-12; cp.knee.value=8; cp.ratio.value=14; cp.attack.value=.002; cp.release.value=.25;
    s.buffer=b; s.connect(lp); lp.connect(g); g.connect(cp); cp.connect(a.destination); s.start(t0);
    noise(.35,near?1:.7);                       // tiếng nổ chát lúc sét đánh
    if(near){ noise(.6,.8); tone(70,.7,'sawtooth',.5,30); }
    tone(near?58:44,3.2,'sine',1,18);           // tiếng ầm trầm
    tone(near?95:70,1.4,'square',.28,28);
  }catch(e){}
}
function stormUpdate(dt){
  nextBolt-=dt;
  if(nextBolt<=0){
    nextBolt=6+Math.random()*10; boltT=1; boltX=20+Math.random()*216;
    boltPts=[[boltX,0]]; let bx=boltX,by=0;
    while(by<130){bx+=(Math.random()-.5)*28; by+=10+Math.random()*14; boltPts.push([bx,by]);}
    thunderIn=.15+Math.random()*1.6; thunderNear=thunderIn<1.0;
  }
  if(boltT>0){
    boltT=Math.max(0,boltT-dt); const e=1-boltT;
    flashV=RF?.4*Math.max(0,1-e*1.3)
      :(e<.07?1:e<.13?.12:e<.24?.95:e<.34?.25:e<.46?.6:Math.max(0,.55*(1-(e-.46)/.54)));
  } else flashV=0;
  if(thunderIn>-100){thunderIn-=dt; if(thunderIn<=0){thunderIn=-999; thunder(thunderNear);}}
  stormL.intensity=flashV*3;
  stAcc+=dt;
  if(stAcc>(flashV>0?.016:.05)){drawStorm(stAcc); stAcc=0; stTex.needsUpdate=true;}
}
// Manh mối: cứ 3 giây phát sáng một lần
function pulseClues(){
  const ph=(tt%3)/3, p=ph<.05?ph/.05:Math.exp(-(ph-.05)*4.2);
  for(const o of inter){
    if(o.kind!=='clue') continue;
    if(solved[o.idx]){o.mat.emissiveIntensity=.7;o.L.intensity=.45;o.halo.material.opacity=0;}
    else{o.mat.emissiveIntensity=.12+2.6*p;o.L.intensity=.05+2.4*p;o.halo.material.opacity=.95*p;}
  }
}

// ---------- Ma (thực thể) ----------
const ghostRoot=new THREE.Group(); ghostRoot.rotation.order='YXZ'; ghostRoot.position.set(0,-80,0); scene.add(ghostRoot);
const gBody=new THREE.Group(); ghostRoot.add(gBody);
const gArms=[], gHair=[], gMats=[]; let gHeadG, gMouth, gLight;
(function(){
  const skin=new THREE.MeshStandardMaterial({color:0xb4aea0,roughness:.7,emissive:0x2c2822});
  const dk=new THREE.MeshStandardMaterial({color:0x060505,roughness:1,side:THREE.DoubleSide,emissive:0x060606});
  const prof=[[0,.74],[.2,.68],[.7,.5],[1.2,.33],[1.5,.27],[1.78,.4],[2.0,.44],[2.12,.22],[2.24,.1]];
  const lg=new THREE.LatheGeometry(prof.map(p=>new THREE.Vector2(p[1],p[0])),28), pa=lg.attributes.position;
  for(let i=0;i<pa.count;i++){const y=pa.getY(i);if(y<.32){const a=Math.atan2(pa.getZ(i),pa.getX(i));
    pa.setY(i,y+Math.abs(Math.sin(a*5)+Math.sin(a*11+1.3))*.3*(1-y/.32));}}
  lg.computeVertexNormals(); gBody.add(new THREE.Mesh(lg,dk));
  gHeadG=new THREE.Group(); gHeadG.position.set(0,2.4,0.05); gBody.add(gHeadG);
  const hs=new THREE.Mesh(new THREE.SphereGeometry(1,28,24),skin); hs.scale.set(.27,.44,.25); gHeadG.add(hs);
  const ft=faceTex();
  const fm=new THREE.MeshStandardMaterial({map:ft,emissiveMap:ft,emissive:0xffffff,emissiveIntensity:.6,roughness:.8});
  const fs=new THREE.Mesh(new THREE.SphereGeometry(1.012,28,24,Math.PI/2-.95,1.9,Math.PI*.12,Math.PI*.72),fm); fs.scale.set(.27,.44,.25); gHeadG.add(fs);
  const gm=new THREE.MeshBasicMaterial({color:0xe8e8ff});
  [-1,1].forEach(s=>{const e=new THREE.Mesh(new THREE.SphereGeometry(.024,8,6),gm);e.position.set(s*.1,.15,.232);gHeadG.add(e);});
  gMouth=new THREE.Mesh(new THREE.CircleGeometry(.1,20),new THREE.MeshBasicMaterial({color:0x000000}));
  gMouth.position.set(0,-.2,.23); gMouth.scale.set(1.1,.4,1); gHeadG.add(gMouth);
  for(let i=0;i<20;i++){const a=.9+i/19*(Math.PI*2-1.8),len=1.2+Math.random()*.9;
    const g2=new THREE.Group(); g2.position.set(Math.sin(a)*.2,.2,Math.cos(a)*.18-.02);
    const m2=new THREE.Mesh(new THREE.BoxGeometry(.014,len,.014),dk); m2.position.y=-len/2; g2.add(m2);
    g2.rotation.z=Math.sin(a)*.12; gHeadG.add(g2); gHair.push(g2);}
  [-1,1].forEach(s=>{const sh=new THREE.Group(); sh.position.set(s*.42,2.02,.03); gBody.add(sh);
    const up=new THREE.Mesh(new THREE.CylinderGeometry(.045,.035,.95,6),skin); up.position.y=-.475; sh.add(up);
    const el=new THREE.Group(); el.position.y=-.95; sh.add(el);
    const fo=new THREE.Mesh(new THREE.CylinderGeometry(.035,.028,.95,6),skin); fo.position.y=-.475; el.add(fo);
    const hand=new THREE.Group(); hand.position.y=-.95; el.add(hand);
    for(let k=0;k<5;k++){const f=new THREE.Group(); f.rotation.z=(k-2)*.26; hand.add(f);
      const fm2=new THREE.Mesh(new THREE.CylinderGeometry(.012,.004,.36,5),skin); fm2.position.y=-.18; f.add(fm2);}
    gArms.push({sh,el,s});});
  gLight=new THREE.PointLight(0xcfd8ff,0,11); gLight.position.set(0,2.2,.9); gBody.add(gLight);
  const seen=new Set();
  ghostRoot.traverse(o=>{if(o.material&&!seen.has(o.material)){seen.add(o.material);o.material.transparent=true;o.material.opacity=0;gMats.push(o.material);}});
  ghostRoot.scale.set(1.05,1.05,1.05);
})();
function parkGhost(){$('bars').className='';if(camera.fov!==72){camera.fov=72;camera.updateProjectionMatrix();}gh.phase='idle';gh.alpha=0;gh.peek=0;ghostRoot.position.set(0,-80,0);ghostRoot.rotation.x=0;gLight.intensity=0;}

// ---------- Dựng phòng ----------
const M=(c,e)=>new THREE.MeshStandardMaterial({color:c,roughness:.9,emissive:e||0x000000,side:THREE.DoubleSide});

function disposeRoom(){
  if(!room) return; scene.remove(room); const seen=new Set();
  room.traverse(o=>{ if(o.geometry) o.geometry.dispose();
    const ms=o.material?(Array.isArray(o.material)?o.material:[o.material]):[];
    ms.forEach(mt=>{ if(seen.has(mt)||(mt.userData&&mt.userData.keep))return; seen.add(mt); if(mt.map)mt.map.dispose(); if(mt.emissiveMap)mt.emissiveMap.dispose(); mt.dispose(); }); });
  room=null;
}

function buildRoom(){
  disposeRoom();
  room=new THREE.Group(); scene.add(room);
  obstacles=[]; inter=[]; watchers=[]; spots=[]; doorOpen=false; curSpot=null; fireMat=null;
  const sz=SIZES[door%SIZES.length]; RW=sz[0]; RD=sz[1];
  const hw=RW/2, hd=RD/2, m=(door%2)?-1:1, S1=-m, S2=m;
  scene.fog=new THREE.FogExp2(0x050202,0.04+door*0.004);
  renderer.shadowMap.enabled=HQ; spot.castShadow=HQ; lamp.castShadow=HQ;
  const R=mulberry(door*7919+17);
  const pick=a=>a[Math.floor(R()*a.length)];
  const ryOf=s=>s<0?Math.PI/2:-Math.PI/2;
  const lit=tx=>new THREE.MeshStandardMaterial({map:tx,roughness:.9,side:THREE.DoubleSide});
  const woodM=new THREE.MeshStandardMaterial({map:woodTex(1,1),roughness:.75});
  const woodDark=M(0x1b0f08), woodMid=M(0x3a2415), stone=M(0x3a3836);
  const brass=new THREE.MeshStandardMaterial({color:0xd4af37,metalness:.8,roughness:.3});
  const black=new THREE.MeshBasicMaterial({color:0x000000});
  const fab=c=>new THREE.MeshStandardMaterial({color:c,roughness:1});
  const plane=(w,h,mat,x,y,z,ry,rx)=>{const p=new THREE.Mesh(new THREE.PlaneGeometry(w,h),mat);
    p.position.set(x,y,z);p.rotation.set(rx||0,ry||0,0);p.receiveShadow=true;room.add(p);return p;};
  const box=(sx,sy,sz2,mat,x,y,z,parent,cast)=>{const b=new THREE.Mesh(new THREE.BoxGeometry(sx,sy,sz2),mat);
    b.position.set(x,y,z);b.castShadow=cast!==false;b.receiveShadow=true;(parent||room).add(b);return b;};
  const cyl=(r1,r2,h,seg,mat,x,y,z,parent,cast)=>{const c=new THREE.Mesh(new THREE.CylinderGeometry(r1,r2,h,seg),mat);
    c.position.set(x,y,z);c.castShadow=cast!==false;c.receiveShadow=true;(parent||room).add(c);return c;};
  const addObs=(cx,cz,sx,sz2)=>obstacles.push({x1:cx-sx/2,x2:cx+sx/2,z1:cz-sz2/2,z2:cz+sz2/2});
  const dims=(fx,fz,len,dep)=>Math.abs(fz)>.5?[len,dep]:[dep,len];
  const grp=(x,z,fx,fz)=>{const g=new THREE.Group();g.position.set(x,0,z);g.rotation.y=Math.atan2(fx,fz);room.add(g);return g;};
  const wi=door%5;

  // sàn, trần, tường
  plane(RW,RD,new THREE.MeshStandardMaterial({map:carpetTex(RW/2,RD/2),roughness:1}),0,0,0,0,-Math.PI/2);
  plane(RW,RD,lit(ceilTex(4,5)),0,RH,0,0,Math.PI/2);
  plane(RW,RH,lit(wallTex(wi,RW/2,RH/2)),0,RH/2,-hd);
  plane(RW,RH,lit(wallTex(wi,RW/2,RH/2)),0,RH/2,hd,Math.PI);
  plane(RD,RH,lit(wallTex(wi,RD/2,RH/2)),-hw,RH/2,0,Math.PI/2);
  plane(RD,RH,lit(wallTex(wi,RD/2,RH/2)),hw,RH/2,0,-Math.PI/2);
  // ốp tường gỗ
  const wains=(len,x,z,ry)=>{const gp=new THREE.Group();gp.position.set(x,0,z);gp.rotation.y=ry;room.add(gp);
    box(len,1.1,0.08,woodM,0,0.55,0,gp,false);box(len+0.04,0.07,0.13,woodDark,0,1.13,0.02,gp,false);box(len+0.04,0.16,0.12,woodDark,0,0.08,0.02,gp,false);};
  const seg=hw-1.4;
  wains(seg,-(hw+1.4)/2,-hd+0.04,0); wains(seg,(hw+1.4)/2,-hd+0.04,0); wains(RW,0,hd-0.04,Math.PI);
  wains(RD,-hw+0.04,0,Math.PI/2); wains(RD,hw-0.04,0,-Math.PI/2);
  // dầm trần
  for(let z=-hd+3;z<hd-1;z+=4.5) box(RW,0.22,0.3,woodDark,0,RH-0.11,z,null,false);
  for(let x=-hw+3;x<hw-1;x+=6) box(0.3,0.22,RD,woodDark,x,RH-0.2,0,null,false);

  // đèn chùm
  flameMat=new THREE.MeshBasicMaterial({color:0xffd9a0});
  const iron=M(0x111111);
  const chand=(x,z)=>{const c=new THREE.Group();c.position.set(x,RH,z);room.add(c);
    const chain=new THREE.Mesh(new THREE.CylinderGeometry(.015,.015,.7,6),iron);chain.position.y=-.35;c.add(chain);
    const ring=new THREE.Mesh(new THREE.TorusGeometry(.45,.025,6,18),iron);ring.rotation.x=Math.PI/2;ring.position.y=-.7;c.add(ring);
    for(let i=0;i<6;i++){const a=i/6*6.283,f=new THREE.Mesh(new THREE.SphereGeometry(.05,8,6),flameMat);f.position.set(Math.cos(a)*.45,-.62,Math.sin(a)*.45);c.add(f);}};
  chand(0,RD*0.12); chand(0,-RD*0.28);
  lamp.position.set(0,RH-0.85,RD*0.12); lampB.position.set(0,RH-0.85,-RD*0.28);

  // cửa ra
  const dz=-hd, fm=M(0x1a1008);
  box(0.3,3.3,0.25,fm,-1.1,1.65,dz+0.12,null,false); box(0.3,3.3,0.25,fm,1.1,1.65,dz+0.12,null,false); box(2.5,0.3,0.25,fm,0,3.15,dz+0.12,null,false);
  const glow=new THREE.Mesh(new THREE.PlaneGeometry(1.9,3.0),new THREE.MeshBasicMaterial({color:0xfff1c9}));
  glow.position.set(0,1.5,dz+0.03); room.add(glow);
  doorPivot=new THREE.Group(); doorPivot.position.set(-0.9,0,dz+0.14); room.add(doorPivot);
  box(1.8,2.95,0.1,new THREE.MeshStandardMaterial({map:doorTex(),roughness:.7}),0.9,1.475,0,doorPivot,false);
  [0.5,2.4].forEach(y=>box(0.12,0.22,0.14,M(0x222222),0.03,y,0,doorPivot,false));
  const knob=new THREE.Mesh(new THREE.SphereGeometry(0.07,12,10),brass); knob.position.set(1.6,1.4,0.1); doorPivot.add(knob);
  const cv=document.createElement('canvas'); cv.width=128; cv.height=64; const g=cv.getContext('2d');
  g.fillStyle='#caa24a'; g.fillRect(0,0,128,64); g.strokeStyle='#5a4010'; g.lineWidth=4; g.strokeRect(3,3,122,58);
  g.fillStyle='#2a1a08'; g.font='bold 42px serif'; g.textAlign='center'; g.textBaseline='middle'; g.fillText(String(door+1).padStart(3,'0'),64,34);
  const pm=new THREE.Mesh(new THREE.PlaneGeometry(0.6,0.3),new THREE.MeshStandardMaterial({map:new THREE.CanvasTexture(cv),metalness:.6,roughness:.4}));
  pm.position.set(0.9,2.45,0.06); doorPivot.add(pm);
  doorLight.position.set(0,1.8,dz+1.3); doorLight.intensity=0;
  inter.push({kind:'door',x:0,z:dz,r:2.7});

  // ---- đồ nội thất (các hàm dựng) ----
  const pillar=(x,z)=>{cyl(.38,.38,RH,14,M(0x4a4038),x,RH/2,z);box(1,.25,1,stone,x,.12,z);box(1,.25,1,stone,x,RH-.12,z,null,false);addObs(x,z,.8,.8);};
  const table=(x,z,sx,sz2,h)=>{box(sx,.08,sz2,woodM,x,h,z);
    [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>box(.1,h,.1,woodDark,x+p[0]*(sx/2-.1),h/2,z+p[1]*(sz2/2-.1)));addObs(x,z,sx,sz2);};
  const chair=(x,z,ry)=>{const c=new THREE.Group();c.position.set(x,0,z);c.rotation.y=ry;room.add(c);
    box(.5,.05,.5,woodDark,0,.5,0,c,false);box(.5,.7,.05,woodDark,0,.85,-.22,c,false);
    [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>box(.05,.5,.05,woodDark,p[0]*.22,.25,p[1]*.22,c,false));};
  const shelf=(x,z,fx,fz,len)=>{const gp=grp(x,z,fx,fz);box(len,2.4,.5,woodDark,0,1.2,0,gp);
    const p=new THREE.Mesh(new THREE.PlaneGeometry(len-.1,2.3),lit(bookTex()));p.position.set(0,1.2,.26);gp.add(p);
    const d=dims(fx,fz,len,.5);addObs(x,z,d[0],d[1]);};
  const clock=(x,z,fx,fz)=>{const gp=grp(x,z,fx,fz);box(.65,2.3,.42,woodDark,0,1.15,0,gp);
    box(.5,.5,.02,new THREE.MeshStandardMaterial({map:clockTex()}),0,1.75,.22,gp,false);box(.4,1.0,.02,M(0x0d0805),0,.75,.22,gp,false);
    cyl(.07,.07,.02,12,brass,0,.55,.23,gp,false).rotation.x=Math.PI/2;
    const d=dims(fx,fz,.65,.42);addObs(x,z,d[0],d[1]);};
  const fireplace=(x,z,fx,fz)=>{const gp=grp(x,z,fx,fz);
    box(.35,1.9,.8,stone,-.95,.95,0,gp);box(.35,1.9,.8,stone,.95,.95,0,gp);box(2.5,.4,.9,stone,0,1.95,0,gp);
    box(2,1.6,.5,M(0x050303),0,.8,-.2,gp,false);box(2.6,.12,1.0,woodDark,0,2.2,.05,gp,false);
    const fl=new THREE.Mesh(new THREE.PlaneGeometry(1.1,.8),new THREE.MeshBasicMaterial({color:0xff6a1a,transparent:true,opacity:.85}));
    fl.position.set(0,.55,.1);gp.add(fl);fireMat=fl.material;
    [[-.3,0.25],[.3,-.2]].forEach(p=>{const lg2=cyl(.07,.07,.9,7,woodDark,p[0],.12,.05,gp,false);lg2.rotation.z=Math.PI/2;lg2.rotation.y=p[1];});
    sconceL[0].position.set(x+fx*1.2,1.0,z+fz*1.2);
    const d=dims(fx,fz,2.5,.9);addObs(x,z,d[0],d[1]);};
  const sofa=(x,z,fx,fz,col)=>{const gp=grp(x,z,fx,fz),f=fab(col);
    box(2.4,.4,1,f,0,.3,0,gp);box(2.4,.75,.25,f,0,.78,-.4,gp);box(.25,.6,1,f,-1.08,.55,0,gp);box(.25,.6,1,f,1.08,.55,0,gp);
    box(.95,.18,.8,f,-.5,.55,.05,gp,false);box(.95,.18,.8,f,.5,.55,.05,gp,false);
    [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>box(.08,.12,.08,woodDark,p[0]*1.1,.05,p[1]*.45,gp,false));
    const d=dims(fx,fz,2.4,1);addObs(x,z,d[0],d[1]);};
  const dresser=(x,z,fx,fz)=>{const gp=grp(x,z,fx,fz);box(2.2,1.2,1,woodM,0,.6,0,gp);box(2.3,.07,1.1,woodDark,0,1.23,0,gp,false);
    for(let i=0;i<3;i++){box(.65,.4,.03,woodMid,-.72+i*.72,.8,.51,gp,false);box(.08,.04,.04,brass,-.72+i*.72,.8,.55,gp,false);}
    const d=dims(fx,fz,2.2,1);addObs(x,z,d[0],d[1]);};
  const barrel=(x,z)=>{cyl(.36,.4,.95,12,woodMid,x,.475,z);[.2,.75].forEach(y=>cyl(.41,.41,.05,12,iron,x,y,z,null,false));addObs(x,z,.8,.8);};
  const crate=(x,z,s,ry)=>{const b=box(s,s,s,woodMid,x,s/2,z);b.rotation.y=ry||0;addObs(x,z,s*1.2,s*1.2);};
  const wardrobe=(x,z,fx,fz)=>{const gp=grp(x,z,fx,fz);
    box(1.5,2.8,.95,woodM,0,1.4,0,gp);box(1.64,.14,1.08,woodDark,0,2.86,0,gp,false);box(1.6,.1,1.04,woodDark,0,.05,0,gp,false);
    box(.72,2.55,.03,woodMid,-.37,1.4,.49,gp,false);box(.72,2.55,.03,woodMid,.37,1.4,.49,gp,false);box(.03,2.55,.04,black,0,1.4,.49,gp,false);
    [-.1,.1].forEach(dx=>box(.04,.2,.04,brass,dx,1.3,.53,gp,false));
    const d=dims(fx,fz,1.5,.95);addObs(x,z,d[0],d[1]);
    const sp={kind:'hide',type:'ward',x,z,r:2.6,fx,fz,hx:x,hz:z,hy:1.5,yaw:Math.atan2(-fx,-fz),ex:x+fx*1.5,ez:z+fz*1.5,gd:2.4,bend:.85,sink:0};
    inter.push(sp);spots.push(sp);};
  const bed=(x,z,wallSide,fx,fz,col)=>{const gp=new THREE.Group();gp.position.set(x,0,z);gp.rotation.y=wallSide<0?0:Math.PI;room.add(gp);
    [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>box(.08,.5,.08,woodDark,p[0]*1.1,.25,p[1]*.7,gp,false));
    box(2.3,.12,1.5,woodDark,0,.56,0,gp);box(2.2,.22,1.4,fab(0x6b6358),0,.73,0,gp);
    box(.45,.12,.9,fab(0xcfc6b0),-.85,.9,0,gp,false);box(1.35,.07,1.46,fab(col),.35,.87,0,gp,false);
    box(.1,1.3,1.6,woodDark,-1.2,.95,0,gp);box(.08,.55,1.5,woodDark,1.15,.75,0,gp,false);
    addObs(x,z,2.3,1.5);
    const sp={kind:'hide',type:'bed',x,z,r:2.6,fx,fz,hx:x,hz:z,hy:.32,yaw:Math.atan2(-fx,-fz),ex:x+fx*1.5,ez:z+fz*1.5,gd:2.7,bend:.72,sink:1.3};
    inter.push(sp);spots.push(sp);};
  const painting=(v,x,y,z,ry,pw,ph)=>{const gp=new THREE.Group();gp.position.set(x,y,z);gp.rotation.y=ry;room.add(gp);
    box(pw+.16,ph+.16,.06,M(0x6b5320),0,0,0,gp,false);
    const t=paintTex(v),p=new THREE.Mesh(new THREE.PlaneGeometry(pw,ph),new THREE.MeshStandardMaterial({map:t,emissiveMap:t,emissive:0xffffff,emissiveIntensity:.2,roughness:.8}));
    p.position.z=.04;gp.add(p);};
  const windowAt=(x,y,z,ry,ww,hh)=>{ww=ww||2.0;hh=hh||1.8;const gp=new THREE.Group();gp.position.set(x,y,z);gp.rotation.y=ry;room.add(gp);
    const geo=new THREE.PlaneGeometry(ww,hh),uv=geo.attributes.uv,o=Math.random(),uvW=Math.min(1,(ww/hh)*(192/256));
    for(let i=0;i<uv.count;i++)uv.setX(i,o+uv.getX(i)*uvW);
    const gl=new THREE.Mesh(geo,stormMat);gl.position.z=.02;gp.add(gl);
    box(ww+.24,.1,.14,woodDark,0,hh/2+.05,.04,gp,false);box(ww+.36,.1,.24,woodDark,0,-hh/2-.05,.08,gp,false);
    box(.1,hh+.2,.14,woodDark,-ww/2-.05,0,.04,gp,false);box(.1,hh+.2,.14,woodDark,ww/2+.05,0,.04,gp,false);
    box(.05,hh,.07,woodDark,0,0,.05,gp,false);box(ww,.05,.07,woodDark,0,hh*.12,.05,gp,false);
    const cu=fab(0x3a0c0c);box(.26,hh+.3,.1,cu,-ww/2-.28,0,.09,gp,false);box(.26,hh+.3,.1,cu,ww/2+.28,0,.09,gp,false);};
  const sconceMesh=(x,z,ry)=>{const gp=new THREE.Group();gp.position.set(x,2.3,z);gp.rotation.y=ry;room.add(gp);
    box(.12,.4,.12,M(0x2a1a0a),0,0,.08,gp,false);
    const fl=new THREE.Mesh(new THREE.SphereGeometry(.07,8,6),new THREE.MeshBasicMaterial({color:0xffbb55}));fl.position.set(0,.28,.1);gp.add(fl);};
  const decal=(tx,w2,h2,x,y,z,ry,rx)=>{const p=new THREE.Mesh(new THREE.PlaneGeometry(w2,h2),
    new THREE.MeshStandardMaterial({map:tx,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2,roughness:.4}));
    p.position.set(x,y,z);p.rotation.set(rx||0,ry||0,0);p.receiveShadow=true;room.add(p);};
  const clue=(idx,x,y,z,sx,sy,sz2,lz)=>{
    const mat=new THREE.MeshStandardMaterial({color:0xffcc55,emissive:0xffaa22,emissiveIntensity:1.4});
    box(sx,sy,sz2,mat,x,y,z,null,false);
    const L=clueL[idx];L.color.set(0xffaa44);L.position.set(x,y+0.4,z+lz);
    const halo=new THREE.Sprite(new THREE.SpriteMaterial({map:haloTex(),color:0xffcc66,transparent:true,opacity:0,blending:THREE.AdditiveBlending,depthWrite:false,fog:false}));
    halo.position.set(x,y+.05,z+lz*.4);halo.scale.set(1.6,1.6,1);room.add(halo);
    inter.push({kind:'clue',idx,x,z,r:2.6,mat,L,halo});};

  // ---- bày trí: mỗi phòng một bố cục riêng ----
  sconceL.forEach(l=>l.color.set(0xff9a40));
  sconceL[0].position.set(-hw+1.2,2.4,-hd+5); sconceL[1].position.set(hw-1.2,2.6,hd-6);
  stormL.position.set(0,RH-.7,0);
  const wx=(s,o)=>s*(hw-o);
  const candle=(x,z,h)=>{cyl(.04,.04,.22,8,M(0xddd5c0),x,h+.11,z,null,false);
    const f1=new THREE.Mesh(new THREE.SphereGeometry(.045,8,6),new THREE.MeshBasicMaterial({color:0xffc060}));f1.position.set(x,h+.27,z);room.add(f1);};
  const paintClue=(idx,cx)=>{box(1.7,1.4,.06,M(0x6b5320),cx,2.0,hd-.06,null,false);
    clue(idx,cx,2.0,hd-.1,1.5,1.2,.04,-.7);plane(1.3,1.0,lit(paintTex(3)),cx,2.0,hd-.16,Math.PI);};
  // thảm: mỗi phòng một kích thước
  const rs=[[7,12],[4.5,18],[2.4,26],[3.6,22],[6,24]][door%5];
  const rug=new THREE.Mesh(new THREE.PlaneGeometry(rs[0],rs[1]),new THREE.MeshStandardMaterial({map:rugTex(),roughness:1}));
  rug.rotation.x=-Math.PI/2; rug.position.set(0,.012,0); rug.receiveShadow=true; room.add(rug);

  switch(door%5){

  // ===== PHÒNG 1: SẢNH ĐÓN TIẾP — đại sảnh có bàn ăn dài ở giữa, lò sưởi, cột đá =====
  case 0:{
    [-1,1].forEach(sx=>[-1,1].forEach(sz2=>pillar(sx*(hw-4),sz2*RD*0.2)));
    table(0,-RD*0.04,2.2,4,.8);
    [-1.2,0,1.2].forEach(d=>{chair(-1.6,-RD*0.04+d,Math.PI/2);chair(1.6,-RD*0.04+d,-Math.PI/2);});
    [-1,1].forEach(d=>candle(0,-RD*0.04+d*1.2,.8));
    clock(wx(-1,.4),-RD*0.40,1,0);
    const tx0=wx(-1,1.7),tz0=-RD*0.25;
    table(tx0,tz0,1.3,2.4,.8);chair(tx0,tz0+1.7,-Math.PI/2);
    clue(0,tx0,.88,tz0+.3,.5,.08,.35,0);candle(tx0,tz0-.8,.8);
    sconceMesh(wx(-1,.1),-RD*0.15,ryOf(-1));
    wardrobe(wx(-1,.55),-RD*0.05,1,0);
    shelf(wx(-1,.3),RD*0.15,1,0,3);
    bed(wx(-1,1.4),RD*0.36,-1,0,-1,pick([0x5a1a1a,0x1a3a5a,0x3a5a2a]));
    fireplace(wx(1,.45),-RD*0.40,-1,0);
    shelf(wx(1,.3),-RD*0.20,-1,0,3);
    dresser(wx(1,.8),RD*0.05,-1,0);
    clue(1,wx(1,.8),1.28,RD*0.05,.5,.05,.4,0);
    bed(wx(1,1.4),RD*0.26,1,0,-1,pick([0x4a1a4a,0x5a3a1a,0x1a4a4a]));
    sofa(wx(1,.9),RD*0.37,-1,0,pick([0x5a1212,0x1a3a2a,0x2a2a4a]));
    wardrobe(wx(1,.55),RD*0.47,-1,0);
    wardrobe(4.5,hd-.55,0,-1);
    paintClue(2,-4.5);
    box(1.0,1,1,woodMid,-7.6,.5,hd-.8); addObs(-7.6,hd-.8,1.0,1.0);
    barrel(-(hw-.7),-hd+.8); barrel(-(hw-1.5),-hd+.7); crate(hw-.8,-hd+.8,.9,.4); crate(hw-1.8,-hd+.7,.7,.9);
    painting(0,wx(-1,.05),2.5,RD*0.36,ryOf(-1),1,1.25);
    painting(1,wx(1,.05),3.1,-RD*0.20,ryOf(1),1,1.25);
    painting(2,wx(1,.05),2.3,RD*0.26,ryOf(1),1,1.25);
    painting(0,wx(1,.05),2.3,RD*0.37,ryOf(1),1,1.25);
    painting(2,3.6,2.2,-hd+.05,0,1,1.25);
    painting(0,-2.5,2.2,hd-.05,Math.PI,1,1.25);
    windowAt(wx(-1,.06),2.4,-RD*0.25,ryOf(-1));
    windowAt(wx(1,.06),2.4,4.2,ryOf(1));
    windowAt(-6.5,2.4,-hd+.06,0); windowAt(6.5,2.4,-hd+.06,0);
    windowAt(1.5,2.4,hd-.06,Math.PI);
    sconceMesh(wx(1,.1),RD*0.05,ryOf(1));
    sconceL[1].position.set(wx(-1,.9),2.6,-RD*0.15);
    break;}

  // ===== PHÒNG 2: THƯ VIỆN BỎ HOANG — kệ sách chạy dọc tường, các bàn đọc sách =====
  case 1:{
    sconceL[0].position.set(-hw+1.5,2.4,-1); sconceL[1].position.set(hw-1.5,2.6,6);
    [-9,-5.8,-2.6].forEach(z=>shelf(wx(-1,.3),z,1,0,3));
    [-10.4,-7.2].forEach(z=>shelf(wx(1,.3),z,-1,0,3));
    shelf(wx(1,.3),4.5,-1,0,3);
    shelf(-3.8,-hd+.3,0,1,3); shelf(3.8,-hd+.3,0,1,3);
    table(-3.6,-3,2.6,1.3,.8); chair(-3.6,-4.1,0); chair(-3.6,-1.9,Math.PI);
    clue(0,-3.0,.88,-3,.5,.08,.35,0); candle(-4.6,-3,.8);
    table(3.6,2.5,2.6,1.3,.8); chair(3.6,1.4,0); chair(3.6,3.6,Math.PI);
    clue(1,3.6,.88,2.5,.5,.08,.35,0); candle(4.6,2.5,.8);
    table(-3.6,8,2.6,1.3,.8); chair(-3.6,6.9,0); chair(-3.6,9.1,Math.PI); candle(-3.6,8,.8);
    wardrobe(wx(-1,.55),8.5,1,0);
    bed(wx(-1,1.4),11.5,-1,0,-1,pick([0x3a2a4a,0x1a3a3a,0x4a2a1a]));
    clock(wx(1,.4),8,-1,0);
    wardrobe(wx(1,.55),11.5,-1,0);
    dresser(-4.5,hd-.8,0,-1); clue(2,-4.5,1.28,hd-.8,.5,.05,.4,0);
    wardrobe(5.5,hd-.55,0,-1);
    crate(wx(-1,.8),-hd+.8,.8,.3); crate(wx(1,.9),-hd+.8,.7,.8);
    painting(1,wx(-1,.05),3.1,-5.8,ryOf(-1),1,1.25);
    painting(2,wx(1,.05),3.1,-7.2,ryOf(1),1,1.25);
    painting(0,-4.5,2.3,hd-.05,Math.PI,1,1.25);
    windowAt(wx(-1,.06),2.4,1.5,ryOf(-1)); windowAt(wx(-1,.06),2.4,5.5,ryOf(-1));
    windowAt(wx(1,.06),2.4,-3.5,ryOf(1)); windowAt(wx(1,.06),2.4,.5,ryOf(1));
    windowAt(-7.5,2.4,-hd+.06,0); windowAt(7.5,2.4,-hd+.06,0);
    windowAt(1.5,2.4,hd-.06,Math.PI); windowAt(8.5,2.4,hd-.06,Math.PI);
    sconceMesh(wx(-1,.1),3.5,ryOf(-1)); sconceMesh(wx(1,.1),-1.5,ryOf(1));
    break;}

  // ===== PHÒNG 3: PHÒNG THÍ NGHIỆM — hai dãy bàn thí nghiệm dài, bình chứa phát sáng xanh =====
  case 2:{
    sconceL[1].color.set(0x66ffaa);
    sconceL[0].position.set(-hw+1.5,2.2,-4); sconceL[1].position.set(hw-1.5,2.2,6);
    const gm2=c=>new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:.9});
    const flask=(x,y,z,c)=>cyl(.07,.1,.24,8,gm2(c),x,y+.12,z,null,false);
    table(-4,-4,1.5,7,.95); table(4,-4,1.5,7,.95);
    const fc=[0x66ff99,0x66aaff,0xff6688,0xffe066,0x99ff66,0xcc88ff];
    for(let i=0;i<6;i++){flask(-4.5,.99,-6.8+i*1.2,fc[i]);flask(3.5,.99,-6.8+i*1.2,fc[(i+2)%6]);}
    clue(0,-4,1.03,-3.5,.5,.08,.35,0);
    clue(1,4,1.03,-5,.5,.08,.35,0);
    const tank=(x,z)=>{cyl(.62,.62,.12,16,woodDark,x,.06,z);cyl(.62,.62,.12,16,woodDark,x,2.5,z,null,false);
      cyl(.52,.52,2.4,16,gm2(0x33ff88),x,1.3,z,null,false);addObs(x,z,1.3,1.3);};
    tank(wx(-1,1.4),-hd+1.4); tank(wx(1,1.4),-hd+1.4); tank(wx(-1,1.4),-hd+3);
    barrel(-8,-11); barrel(-7.2,-11.6);
    dresser(wx(-1,.8),3,1,0); clue(2,wx(-1,.8),1.28,3,.5,.05,.4,0);
    shelf(wx(-1,.3),-9,1,0,3); shelf(wx(1,.3),-10,-1,0,3);
    shelf(-4.5,-hd+.3,0,1,3); shelf(4.5,-hd+.3,0,1,3);
    wardrobe(wx(1,.55),-1.5,-1,0); wardrobe(wx(1,.55),5.5,-1,0);
    bed(wx(-1,1.4),8,-1,0,-1,0x2a4a5a);
    wardrobe(wx(-1,.55),12,1,0);
    wardrobe(5,hd-.55,0,-1);
    windowAt(wx(1,.06),2.4,-6,ryOf(1)); windowAt(wx(1,.06),2.4,2,ryOf(1)); windowAt(wx(1,.06),2.4,9,ryOf(1));
    windowAt(wx(-1,.06),2.4,-4.5,ryOf(-1)); windowAt(wx(-1,.06),2.4,-1,ryOf(-1));
    windowAt(-7.5,2.4,-hd+.06,0); windowAt(7.5,2.4,-hd+.06,0);
    windowAt(-4.5,2.4,hd-.06,Math.PI); windowAt(9,2.4,hd-.06,Math.PI);
    sconceMesh(wx(-1,.1),-6.5,ryOf(-1)); sconceMesh(wx(1,.1),-4,ryOf(1));
    break;}

  // ===== PHÒNG 4: HẦM TỐI — hầm rượu: hàng cột, thùng gỗ, cửa sổ thông gió nhỏ trên cao =====
  case 3:{
    sconceL[0].position.set(-6,2.4,-7); sconceL[1].position.set(6,2.4,5);
    [-10,-3.5,3,9.5].forEach(z=>[-4.5,4.5].forEach(x=>pillar(x,z)));
    wardrobe(wx(-1,.55),-6,1,0);
    bed(wx(-1,1.4),.5,-1,0,-1,0x3a2a1a);
    table(-9.6,6.5,1.2,1.2,.9); clue(2,-9.6,.98,6.5,.5,.08,.35,0); candle(-9.2,6,.94);
    shelf(wx(-1,.3),-11.5,1,0,3); shelf(wx(1,.3),-12,-1,0,3);
    wardrobe(wx(1,.55),9,-1,0);
    crate(8.5,-6.5,.9,.2); clue(0,8.5,.95,-6.5,.5,.08,.35,0);
    table(-8,-9,1.4,1.4,.9); clue(1,-8,.98,-9,.5,.08,.35,0);
    [[-9.8,-14.6],[-8.8,-14.8],[9.8,-14.4],[8.8,-14.7],[-9.6,13.6],[-8.5,14.4],[9.6,14.2],[-7.5,10.5],[7.8,1.5],[7.2,-2.5]].forEach(p=>barrel(p[0],p[1]));
    crate(-8,12.3,.9,.5); crate(8.5,12,.9,.2); crate(7.6,-9.5,.8,.7); crate(-7.5,3.5,.8,.1);
    [-11,-4,3,10].forEach(z=>{windowAt(wx(-1,.06),3.3,z,ryOf(-1),2,.6);windowAt(wx(1,.06),3.3,z,ryOf(1),2,.6);});
    windowAt(-6.5,3.2,-hd+.06,0,2,.6); windowAt(6.5,3.2,-hd+.06,0,2,.6);
    sconceMesh(wx(-1,.1),-3,ryOf(-1)); sconceMesh(wx(1,.1),4,ryOf(1));
    painting(1,3.6,2.2,-hd+.05,0,1,1.25);
    break;}

  // ===== PHÒNG 5: PHÒNG CUỐI CÙNG — đại điện lộng lẫy, hai hàng cột, tượng đá, cửa sổ cao sát trần =====
  case 4:{
    [-11,-4,3,10].forEach(z=>[-5.5,5.5].forEach(x=>pillar(x,z)));
    const statue=(x,z)=>{box(1,.6,1,stone,x,.3,z);cyl(.28,.4,1.9,10,M(0x2a2a2e),x,1.55,z);
      const h2=new THREE.Mesh(new THREE.SphereGeometry(.24,12,10),M(0x2a2a2e));h2.position.set(x,2.65,z);h2.castShadow=true;room.add(h2);addObs(x,z,1,1);};
    statue(-3.6,-hd+1.3); statue(3.6,-hd+1.3);
    wardrobe(wx(-1,.55),-8,1,0);
    table(wx(-1,1.6),0,1.2,2.4,.8); clue(0,wx(-1,1.6),.88,0,.5,.08,.35,0); candle(wx(-1,1.6),-.9,.8);
    bed(wx(-1,1.4),6,-1,0,-1,0x4a1a1a);
    sofa(wx(-1,.9),12.5,1,0,0x3a1a2a);
    fireplace(wx(1,.45),-hd+2.4,-1,0);
    dresser(wx(1,.8),-1,-1,0); clue(1,wx(1,.8),1.28,-1,.5,.05,.4,0);
    wardrobe(wx(1,.55),6,-1,0);
    bed(wx(1,1.4),13,1,0,-1,0x1a3a4a);
    wardrobe(6,hd-.55,0,-1); paintClue(2,-3);
    [-12,-4,3,9].forEach(z=>windowAt(wx(-1,.06),2.1,z,ryOf(-1),2.4,2.6));
    [-9,-4,3,9].forEach(z=>windowAt(wx(1,.06),2.1,z,ryOf(1),2.4,2.6));
    windowAt(-8.5,2.1,-hd+.06,0,2.4,2.6); windowAt(8.5,2.1,-hd+.06,0,2.4,2.6);
    windowAt(-8,2.1,hd-.06,Math.PI,2.4,2.6); windowAt(9.5,2.1,hd-.06,Math.PI,2.4,2.6);
    sconceMesh(wx(-1,.1),-6,ryOf(-1)); sconceMesh(wx(1,.1),-6.5,ryOf(1));
    break;}
  }
  sconceMesh(-1.9,-hd+.1,0); sconceMesh(1.9,-hd+.1,0);

  // mạng nhện
  [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>{const w2=new THREE.Mesh(new THREE.PlaneGeometry(1.5,1.5),
    new THREE.MeshBasicMaterial({map:webTex(),transparent:true,depthWrite:false,side:THREE.DoubleSide}));
    w2.position.set(p[0]*(hw-.6),RH-.8,p[1]*(hd-.6));w2.rotation.y=Math.atan2(-p[0],-p[1]);room.add(w2);});

  // vết máu, dấu tay, chữ viết bằng máu, giấy rơi
  for(let i=0;i<4;i++) decal(bloodTex(),rnd(1.2,2.2),rnd(1.2,2.2),rnd(-hw+3,hw-3),.014+i*.001,rnd(-hd+4,hd-4),0,-Math.PI/2);
  decal(handTex(),.9,.9,-5.3,1.4,-hd+.02,0);
  decal(handTex(),.9,.9,5.3,1.4,-hd+.02,0);
  decal(msgTex(MSG[door%5]),3.0,.6,0,3.65,-hd+.02,0);
  const paperM=new THREE.MeshStandardMaterial({color:0xcfc6a8,roughness:1});
  for(let i=0;i<14;i++){const p=new THREE.Mesh(new THREE.PlaneGeometry(.28,.38),paperM);
    p.rotation.set(-Math.PI/2,0,rnd(0,6.3));p.position.set(rnd(-hw+2,hw-2),.02+i*.0005,rnd(-hd+3,hd-3));room.add(p);}
  // ghế đổ
  const tc=new THREE.Group();tc.position.set(-2*m,0.2,RD*0.22);tc.rotation.set(0.1,rnd(0,3),1.45);room.add(tc);
  box(.5,.05,.5,woodDark,0,0,0,tc,false);box(.5,.6,.05,woodDark,0,.3,-.22,tc,false);

  // đôi mắt trong bóng tối
  const eyeMat=new THREE.MeshBasicMaterial({color:0xff2020});
  const spotsE=[[-hw+.6,3.5,-hd+3],[hw-.6,3.5,-hd+3],[-hw+.6,3.6,hd-3],[hw-.6,3.6,hd-3],[0,3.7,-hd+.6],[-hw+.6,3.3,0],[hw-.6,3.3,-2],[0,3.7,hd-.6]];
  const nW=Math.min(2+door,spotsE.length);
  for(let i=0;i<nW;i++){const s=spotsE[(i*3+door)%spotsE.length];const gp=new THREE.Group();gp.position.set(s[0],s[1],s[2]);
    [-0.2,0.2].forEach(dx=>{const e=new THREE.Mesh(new THREE.SphereGeometry(.07,8,6),eyeMat);e.scale.set(1.4,.8,.5);e.position.x=dx;gp.add(e);});
    room.add(gp);watchers.push({g:gp,t:rnd(0,20),off:rnd(0,6)});}
  resetDust();
}
function refreshClues(){
  inter.forEach(o=>{ if(o.kind==='clue' && solved[o.idx]){
    o.mat.color.set(0x55ff88); o.mat.emissive.set(0x22aa55); o.L.color.set(0x55ff88); }});
}

// ---------- Âm thanh ----------
let AC, droneG; const ac=()=>AC||(AC=new (window.AudioContext||window.webkitAudioContext)());
function tone(f,d,type,v,f2){try{const a=ac(),o=a.createOscillator(),g=a.createGain();o.type=type||'sine';
  o.frequency.setValueAtTime(f,a.currentTime);if(f2)o.frequency.exponentialRampToValueAtTime(f2,a.currentTime+d);
  g.gain.setValueAtTime(v||.15,a.currentTime);g.gain.exponentialRampToValueAtTime(.001,a.currentTime+d);
  o.connect(g).connect(a.destination);o.start();o.stop(a.currentTime+d);}catch(e){}}
function noise(d,v){try{const a=ac(),n=Math.floor(a.sampleRate*d),b=a.createBuffer(1,n,a.sampleRate),x=b.getChannelData(0);
  for(let i=0;i<n;i++)x[i]=(Math.random()*2-1)*(1-i/n);const s=a.createBufferSource(),g=a.createGain();
  g.gain.value=v;s.buffer=b;s.connect(g).connect(a.destination);s.start();}catch(e){}}
const sGood=()=>{tone(660,.15,'sine',.15);setTimeout(()=>tone(990,.3,'sine',.15),120);};
const sBad=()=>{tone(160,.4,'sawtooth',.2,60);noise(.3,.25);};
function scream(){
  try{const a=ac(),t0=a.currentTime;
    const mk=(type,f0,f1,vol,dur)=>{const o=a.createOscillator(),g=a.createGain();o.type=type;
      o.frequency.setValueAtTime(f0,t0);o.frequency.exponentialRampToValueAtTime(f1,t0+.35);
      const lfo=a.createOscillator(),lg=a.createGain();lfo.frequency.value=11;lg.gain.value=f1*.08;lfo.connect(lg);lg.connect(o.frequency);lfo.start(t0);lfo.stop(t0+dur);
      g.gain.setValueAtTime(.0001,t0);g.gain.exponentialRampToValueAtTime(vol,t0+.04);g.gain.setValueAtTime(vol,t0+dur*.6);g.gain.exponentialRampToValueAtTime(.001,t0+dur);
      const ws=a.createWaveShaper(),c=new Float32Array(256);for(let i=0;i<256;i++){c[i]=Math.tanh((i/128-1)*4);}ws.curve=c;
      o.connect(ws);ws.connect(g);g.connect(a.destination);o.start(t0);o.stop(t0+dur);};
    mk('sawtooth',300,1250,.35,2.3); mk('square',450,1800,.16,2.1); mk('sawtooth',90,240,.3,2.0);
    noise(1.8,.5); tone(40,1.2,'sine',.6,25);
  }catch(e){}
}
let amb=false;
function ambience(){
  try{const a=ac(); if(a.resume)a.resume(); if(amb)return; amb=true;
    const mk=(f,type,vol)=>{const o=a.createOscillator(),g=a.createGain(),lp=a.createBiquadFilter();o.type=type;o.frequency.value=f;
      lp.type='lowpass';lp.frequency.value=170;g.gain.value=vol;o.connect(lp);lp.connect(g);g.connect(a.destination);o.start();return g;};
    const g1=mk(46,'sawtooth',.05); mk(49.3,'sawtooth',.04);
    const lfo=a.createOscillator(),lg=a.createGain();lfo.frequency.value=.13;lg.gain.value=.03;lfo.connect(lg);lg.connect(g1.gain);lfo.start();
    const n=a.sampleRate*3,b=a.createBuffer(1,n,a.sampleRate),x=b.getChannelData(0);for(let i=0;i<n;i++)x[i]=Math.random()*2-1;
    const s=a.createBufferSource();s.buffer=b;s.loop=true;const bp=a.createBiquadFilter();bp.type='bandpass';bp.frequency.value=400;bp.Q.value=.6;
    const wg=a.createGain();wg.gain.value=.022;s.connect(bp);bp.connect(wg);wg.connect(a.destination);s.start();
    const od=a.createOscillator(),dl=a.createBiquadFilter();droneG=a.createGain();droneG.gain.value=0;od.type='sawtooth';od.frequency.value=62;
    dl.type='lowpass';dl.frequency.value=260;od.connect(dl);dl.connect(droneG);droneG.connect(a.destination);od.start();
  }catch(e){}
}
const WH=['đừng quay lại...','nó đang nhìn bạn','phía sau bạn','đừng nhìn vào bóng tối','chạy đi...','bạn không một mình','nó biết bạn ở đây'];
function whisper(txt){const w=$('whisper');w.textContent=txt||WH[Math.floor(Math.random()*WH.length)];
  w.style.left=(8+Math.random()*60)+'%';w.style.top=(15+Math.random()*60)+'%';w.style.opacity=.8;setTimeout(()=>w.style.opacity=0,2400);noise(1.2,.05);}

// ---------- Tiện ích UI ----------
function banner(t,ms){const b=$('banner');b.textContent=t;b.style.opacity=1;clearTimeout(bannerT);
  bannerT=setTimeout(()=>b.style.opacity=0,ms||2500);}
function updateHud(){
  if(door>=DOORS.length) return;
  const D=DOORS[door];
  $('dn').textContent='Cửa '+(door+1)+'/5';
  $('hp').innerHTML='MẠNG '+'<span style="color:#d01a1a">&#9829;</span>'.repeat(Math.max(hp,0))+'<span style="color:#4a4a4a">&#9829;</span>'.repeat(MAX_HP-Math.max(hp,0));
  $('hn').textContent='Gợi ý: '+hints;
  $('ks').textContent='Chìa khóa: '+D.questions.map((q,i)=>solved[i]?q.digit:'_').join(' · ');
  $('ot').textContent=solved.every(Boolean)?D.order_text:'';
  $('sl').textContent='Shift Lock: '+(shiftLock?'BẬT':'TẮT');
  $('sl').className=shiftLock?'on':'';
  $('lockbtn').className=shiftLock?'on':''; $('lockbtn').textContent='SL';
  $('lockbtn').style.display=state==='play'?'block':'none';
  $('lowhp').className=(hp===1&&state==='play')?'pulse':'';
}
// Shift Lock kiểu Roblox: chuột bị khóa ở GIỮA màn hình (con trỏ ẩn, hiện tâm ngắm), xoay camera không cần bấm chuột.
// Bấm Shift (hoặc nút ) để bật/tắt. Nếu trình duyệt chặn khóa chuột trong khung nhúng -> dùng nút TAB MỚI mở game ở tab mới.
const inFrame=(function(){try{return window.top!==window;}catch(e){return true;}})();
const isLocked=()=>document.pointerLockElement===canvas;
function lockFail(){
  if(!lockEver) lockBlocked=true;        // chưa từng khóa được -> khung nhúng bị chặn
  setCursor();
}
function lockPtr(){try{const p=canvas.requestPointerLock();if(p&&p.catch)p.catch(lockFail);}catch(e){lockFail();}}
function unlockPtr(){expectUnlock=true;try{document.exitPointerLock();}catch(e){}setTimeout(()=>{expectUnlock=false;},250);}
function setCursor(){
  const want=shiftLock&&state==='play'&&!modalOpen;
  canvas.style.cursor=want?'none':'default';       // Shift Lock: luôn ẩn con trỏ
  $('cross').className=(shiftLock&&state==='play')?'lk':'';
}
function syncLock(){
  const want=shiftLock&&state==='play'&&!modalOpen;
  if(want&&!isLocked()) lockPtr();
  else if(!want&&isLocked()) unlockPtr();
  setCursor();
  if(state!=='menu') updateHud();
}
function toggleSL(){
  shiftLock=!shiftLock; lockFailShown=false; syncLock(); updateHud();
  banner(shiftLock?'Shift Lock: BẬT — chuột khóa ở giữa màn hình':'Shift Lock: TẮT — giữ chuột trái/phải và kéo để nhìn',1800);
}
document.addEventListener('pointerlockchange',()=>{
  if(isLocked()){lockEver=true;lockBlocked=false;}
  else if(shiftLock&&!expectUnlock&&state==='play'&&!modalOpen){   // lỡ nhả chuột (Esc): giữ Shift Lock BẬT như Roblox
    banner('Chuột đã nhả. Bấm vào màn hình để khóa lại (Shift để tắt Shift Lock).',2600);}
  setCursor();
});
document.addEventListener('pointerlockerror',lockFail);
$('sl').onclick=()=>{if(state==='play'&&!modalOpen)toggleSL();};

// grain
(function(){const gc=$('grain');gc.width=160;gc.height=90;const x=gc.getContext('2d');
  setInterval(()=>{const id=x.createImageData(160,90),d=id.data;for(let i=0;i<d.length;i+=4){const v=Math.random()*255;d[i]=d[i+1]=d[i+2]=v;d[i+3]=70;}x.putImageData(id,0,0);},70);})();

function damage(msg){
  hp--; shake=0.3; sBad();
  const f=$('flash'); f.style.background='#a00'; f.style.opacity=.75; setTimeout(()=>f.style.opacity=0,350);
  banner(msg+'  -1 mạng',2500); updateHud();
  if(hp<=0) gameOver('Bạn gục ngã ở cửa số '+(door+1)+'...\nBạn phải bắt đầu lại từ cửa số 1.');
}
function gameOver(msg){
  state='over'; closeModal(true); syncLock(); updateHud(); parkGhost();
  camera.fov=72; camera.updateProjectionMatrix(); $('scare').style.display='none'; $('flash').style.opacity=0;
  $('overmsg').style.whiteSpace='pre-line'; $('overmsg').textContent=msg;
  $('over').style.display='flex';
}

// ---------- Modal ----------
// Texture giấy nhàu cho bảng câu hỏi (nếp gấp, mảng sáng/tối, vết ố, hạt)
(function(){
  const w=640,h=560,c=document.createElement('canvas');c.width=w;c.height=h;const g=c.getContext('2d');
  const gr=g.createLinearGradient(0,0,w,h);gr.addColorStop(0,'#c6bba1');gr.addColorStop(.5,'#b5a98e');gr.addColorStop(1,'#a69a7d');
  g.fillStyle=gr;g.fillRect(0,0,w,h);
  for(let i=0;i<90;i++){const x=rnd(0,w),y=rnd(0,h);
    g.fillStyle=Math.random()<.5?'rgba(255,250,235,'+rnd(.03,.12)+')':'rgba(40,30,15,'+rnd(.03,.12)+')';
    g.beginPath();g.moveTo(x,y);for(let k=0;k<4;k++)g.lineTo(x+rnd(-100,100),y+rnd(-100,100));g.closePath();g.fill();}
  for(let i=0;i<26;i++){let x=rnd(0,w),y=rnd(0,h),a=rnd(0,6.3);const pts=[[x,y]];
    for(let k=0;k<5;k++){a+=rnd(-.6,.6);x+=Math.cos(a)*rnd(30,70);y+=Math.sin(a)*rnd(30,70);pts.push([x,y]);}
    [[0,0,'rgba(35,25,10,.30)'],[1.5,1.5,'rgba(255,250,235,.28)']].forEach(s=>{
      g.save();g.translate(s[0],s[1]);g.strokeStyle=s[2];g.lineWidth=1.3;g.beginPath();
      pts.forEach((p,k)=>k?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.stroke();g.restore();});}
  stains(g,w,h,10,.13); noiseFx(g,w,h,22);
  const vg=g.createRadialGradient(w/2,h/2,h*.25,w/2,h/2,w*.75);vg.addColorStop(0,'rgba(0,0,0,0)');vg.addColorStop(1,'rgba(50,35,10,.4)');
  g.fillStyle=vg;g.fillRect(0,0,w,h);
  $('box').style.backgroundImage='url('+c.toDataURL('image/jpeg',.88)+')';
})();
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function openModal(){modalOpen=true;syncLock();$('modal').style.display='flex';$('fb').textContent='';
  if(modalMode==='code') setTimeout(()=>$('mi').focus(),30);}
function closeModal(silent){modalOpen=false;$('modal').style.display='none';$('mi').value='';keys={};
  if(!silent) syncLock();}
function openQ(i){
  const q=DOORS[door].questions[i]; modalMode='q'; modalIdx=i;
  $('mt').textContent='Manh mối '+(i+1); $('mq').textContent=q.q; $('b2').style.display='inline-block';
  $('mi').style.display='none'; $('b1').style.display='none';
  optOrder=shuffle([0,1,2,3]); wrongSet={};            // q.o[0] là đáp án đúng
  const box=$('opts'); box.innerHTML=''; box.style.display='flex';
  optOrder.forEach((oi,k)=>{
    const b=document.createElement('button'); b.className='opt';
    const l=document.createElement('b'); l.textContent='ABCD'[k];
    const t=document.createElement('span'); t.textContent=q.o[oi];
    b.appendChild(l); b.appendChild(t); b.onclick=()=>choose(k); box.appendChild(b);
  });
  openModal(); if(hintShown[door+'-'+i]) $('fb').textContent=''+q.hint;
}
function choose(k){
  if(!modalOpen||modalMode!=='q'||wrongSet[k]) return;
  const q=DOORS[door].questions[modalIdx];
  if(optOrder[k]===0){
    solved[modalIdx]=true; sGood(); closeModal(); refreshClues(); updateHud();
    banner('Đúng! Chìa khóa '+(modalIdx+1)+' = '+q.digit+(solved.every(Boolean)?'\nĐã đủ chìa! Hãy ra mở cửa.':''),3000);
  } else {
    wrongSet[k]=true; $('opts').children[k].classList.add('bad'); $('fb').textContent='Sai rồi!';
    damage('Một thực thể tấn công bạn!');
  }
}
function openCode(){
  const D=DOORS[door]; modalMode='code';
  $('mt').textContent='Ổ khóa'; $('mq').textContent='Nhập mật mã '+D.questions.length+' chữ số. '+D.order_text;
  $('b2').style.display='none'; $('opts').style.display='none'; $('mi').style.display=''; $('b1').style.display=''; openModal();
}
function submit(){
  if(modalMode!=='code') return;
  const v=$('mi').value; if(!v.trim()) return;
  const D=DOORS[door];
  const code=D.order.map(i=>D.questions[i].digit).join('');
  if(v.trim()===code){ closeModal(); doorOpen=true; sGood(); tone(70,1.2,'sawtooth',.12,40); banner('Cửa đã mở! Hãy bước vào ánh sáng...',3000); }
  else { $('fb').textContent='Mật mã sai!'; $('mi').value=''; damage('Ổ khóa phóng điện vào bạn!'); }
}
$('b1').onclick=submit; $('b3').onclick=()=>closeModal();
$('b2').onclick=()=>{
  const k=door+'-'+modalIdx, q=DOORS[door].questions[modalIdx];
  if(hintShown[k]){$('fb').textContent=''+q.hint;return;}
  if(hints<=0){$('fb').textContent='Hết lượt gợi ý!';return;}
  hints--; hintShown[k]=true; $('fb').textContent=''+q.hint; updateHud();
};
$('mi').addEventListener('keydown',e=>{if(e.key==='Enter')submit();});

// ---------- Luồng game ----------
function startRoom(){
  solved=[false,false,false]; buildRoom(); hidden=false; spot.intensity=2.1; $('hide').style.display='none';
  camera.position.set(0,1.6,RD/2-2); yaw=0; pitch=0; lampF=1; dark=0; parkGhost();
  ghostTimer=(door===0?38:28)+Math.random()*24; updateHud();
  banner('CỬA '+(door+1)+': '+DOORS[door].name+'\n'+DOORS[door].intro,4500);
}
function showOnly(id){['menu','howto','settings','over','win'].forEach(i=>$(i).style.display=(i===id?'flex':'none'));}
function resetGame(){musicStop();hp=MAX_HP;hints=HINTS0;door=0;hintShown={};state='play';ambience();playMusicStart();
  camera.fov=72;camera.updateProjectionMatrix();$('scare').style.display='none';
  showOnly(''); startRoom(); syncLock();}
function toMenu(){playMusicStop();state='menu';closeModal(true);syncLock();parkGhost();showOnly('menu');buildRoom();camera.position.set(0,1.6,RD/2-2);yaw=0;pitch=0;musicStart();}
$('start').onclick=resetGame; $('retry').onclick=resetGame; $('again').onclick=resetGame;
function setRF(v){RF=!!v; saveNum('doors_rf',RF?1:0); $('rfchk').checked=RF; $('rfchk2').checked=RF;}
$('rfchk').onchange=()=>setRF($('rfchk').checked); $('rfchk2').onchange=()=>setRF($('rfchk2').checked); setRF(RF);
$('warnok').onclick=()=>{$('warn').style.display='none';};
$('tomenu').onclick=toMenu; $('tomenu2').onclick=toMenu;
$('how').onclick=()=>showOnly('howto'); $('hback').onclick=()=>showOnly('menu');
// ----- Cài đặt đồ họa (kiểu Roblox: thanh trượt 1-10; 1-5 = Thấp, 6-10 = Cao) -----
function updateSettingsUI(){
  $('qr').value=Q;
  $('ql').textContent='Mức đồ họa: '+Q+' / 10 — '+(Q>=6?'CAO':'THẤP');
  $('qd').textContent=Q>=6
    ?'Cao: bóng đổ động, độ phân giải đầy đủ, nhiễu hạt phim và bụi bay. Đẹp hơn nhưng cần máy khỏe.'
    :'Thấp: kiểu pixel low-poly retro — hình ảnh vuông pixel, texture thô, tắt bóng đổ, nhiễu hạt và bụi. Rất mượt trên máy yếu.';
  $('gLow').style.boxShadow=Q<=5?'0 0 10px #a00':'none'; $('gHigh').style.boxShadow=Q>=6?'0 0 10px #a00':'none';
}
function applyQuality(noBuild){
  HQ=Q>=6;
  renderer.setPixelRatio(pr()); renderer.setSize(STW,STH);
  canvas.style.imageRendering=HQ?'auto':'pixelated';
  renderer.toneMappingExposure=HQ?1.3:1.55;
  [[spot,Q>=9?1024:512],[lamp,Q>=9?512:256]].forEach(a=>{
    if(a[0].shadow.map){a[0].shadow.map.dispose();a[0].shadow.map=null;} a[0].shadow.mapSize.set(a[1],a[1]);});
  $('grain').style.display=HQ?'block':'none'; dust.visible=HQ;
  gMats.forEach(m=>{m.needsUpdate=true;});
  saveNum('doors_q',Q); updateSettingsUI();
  if(!noBuild) buildRoom();
}
$('settingsBtn').onclick=()=>{showOnly('settings');updateSettingsUI();};
$('sback').onclick=()=>showOnly('menu');
$('qr').oninput=()=>{Q=+$('qr').value;updateSettingsUI();};
$('qr').onchange=()=>{Q=+$('qr').value;applyQuality();};
$('qm').onclick=()=>{Q=Math.max(1,Q-1);applyQuality();};
$('qp').onclick=()=>{Q=Math.min(10,Q+1);applyQuality();};
$('gLow').onclick=()=>{Q=3;applyQuality();};
$('gHigh').onclick=()=>{Q=10;applyQuality();};

// ----- Nhạc menu -----
const bgm=new Audio(); bgm.loop=true; bgm.preload='auto'; if(MUSIC_SRC) bgm.src=MUSIC_SRC;
let musicVol=loadNum('doors_vol',60,0,100)/100, fadeI=null;
$('vr').value=Math.round(musicVol*100); $('vv').textContent=Math.round(musicVol*100)+'%';
function fadeTo(v,done){
  clearInterval(fadeI);
  fadeI=setInterval(()=>{const d=v-bgm.volume;
    if(Math.abs(d)<.03){bgm.volume=v;clearInterval(fadeI);if(done)done();}
    else bgm.volume=Math.max(0,Math.min(1,bgm.volume+Math.sign(d)*.03));},40);
}
function musicStart(){
  if(!MUSIC_SRC||state!=='menu') return;
  if(bgm.paused) bgm.volume=0;
  const p=bgm.play();
  const ok=()=>{$('musichint').style.display='none'; if(state==='menu') fadeTo(musicVol); else bgm.pause();};
  const blocked=()=>{$('musichint').style.display='block';};     // trình duyệt chặn tự phát -> chờ người chơi bấm
  if(p&&p.then) p.then(ok).catch(blocked); else ok();
}
function musicStop(){ $('musichint').style.display='none'; fadeTo(0,()=>bgm.pause()); }
// Nhạc nền khi đang chơi (nhỏ lại khi ma xuất hiện)
const pbgm=new Audio(); pbgm.loop=true; pbgm.preload='auto'; if(PLAY_SRC) pbgm.src=PLAY_SRC;
let pduck=1;
function playMusicStart(){ if(!PLAY_SRC||!pbgm.paused) return; pbgm.volume=Math.min(1,musicVol*.8); const p=pbgm.play(); if(p&&p.catch)p.catch(()=>{}); }
function playMusicStop(){ pbgm.pause(); try{pbgm.currentTime=0;}catch(e){} }
$('vr').oninput=()=>{musicVol=+$('vr').value/100;$('vv').textContent=$('vr').value+'%';saveNum('doors_vol',$('vr').value);
  if(!bgm.paused){clearInterval(fadeI);bgm.volume=musicVol;}};
['pointerdown','keydown'].forEach(ev=>addEventListener(ev,()=>{if(state==='menu'&&bgm.paused)musicStart();},true));
function nextRoom(){
  transitioning=true; $('fade').style.opacity=1;
  setTimeout(()=>{
    door++;
    if(door>=DOORS.length){playMusicStop();state='win';syncLock();updateHud();parkGhost();showOnly('win');}
    else startRoom();
    $('fade').style.opacity=0; transitioning=false;
  },900);
}
function toggleHide(sp){
  if(!hidden){
    if(gh.phase!=='idle'&&Math.hypot(gh.x-camera.position.x,gh.z-camera.position.z)<3&&gh.phase==='hunt'){banner('Quá muộn! Ma ở quá gần!',1500);return;}
    hidden=true; curSpot=sp; camera.position.set(sp.hx,sp.hy,sp.hz); yaw=sp.yaw; pitch=0; spot.intensity=0;
    $('hide').className=sp.type; $('hide').style.display='block'; noise(.25,.08); tone(90,.2,'square',.05,70);
  } else {
    if(gh.phase!=='idle'){banner('Ma vẫn còn ở đây... đừng ra!',1600);return;}
    hidden=false; let ex=curSpot.ex,ez=curSpot.ez,k=0;
    while(hit(ex,ez)&&k<4){ex+=curSpot.fx*.5;ez+=curSpot.fz*.5;k++;}
    camera.position.set(ex,1.6,ez); spot.intensity=2.1; $('hide').style.display='none'; curSpot=null; noise(.2,.06);
  }
}
function act(){
  if(hidden){toggleHide();return;}
  if(!cur) return;
  if(cur.kind==='hide') toggleHide(cur);
  else if(gh.phase!=='idle'){banner('Không phải lúc này! Hãy trốn đi!',1500);}
  else if(cur.kind==='clue'){ if(!solved[cur.idx]) openQ(cur.idx); }
  else if(cur.kind==='door'){
    if(doorOpen) return;
    if(solved.every(Boolean)) openCode();
    else banner('Cửa bị khóa. Cần đủ 3 chìa khóa ('+solved.filter(Boolean).length+'/3).',2200);
  }
}

// ---------- Ma: logic ----------
function startGhost(){
  gh.phase='warn'; gh.t=5.2; gh.alpha=0;
  if(modalOpen) closeModal(true), syncLock();
  banner('ĐÈN CHỚP… CÓ THỨ GÌ ĐÓ ĐANG TỚI!\nTRỐN NGAY: tủ hoặc gầm giường (E)',4600);
  tone(90,1.6,'sawtooth',.12,45);
}
function ghostSpawn(){
  const c=[[0,-RD/2+2.5],[0,RD/2-2.5],[-RW/2+2.5,0],[RW/2-2.5,0]];
  let best=c[0],bd=-1; c.forEach(p=>{const d=Math.hypot(p[0]-camera.position.x,p[1]-camera.position.z);if(d>bd){bd=d;best=p;}});
  // Cảnh xuất hiện: ma hiện ra TRƯỚC MẶT người chơi (cách ~15m, trong tầm nhìn), đứng yên nhìn chằm chằm rồi mới đuổi
  const fx=-Math.sin(yaw), fz=-Math.cos(yaw);
  let sx=Math.max(-RW/2+1.5,Math.min(RW/2-1.5,camera.position.x+fx*15));
  let sz=Math.max(-RD/2+1.5,Math.min(RD/2-1.5,camera.position.z+fz*15));
  if(Math.hypot(sx-camera.position.x,sz-camera.position.z)<9){sx=best[0];sz=best[1];}
  gh.x=sx; gh.z=sz; gh.phase='reveal'; gh.t0=gh.t=4.6; gh.step=0; gh.alpha=0; gh.shr=false;
  gh.face=Math.atan2(camera.position.x-gh.x,camera.position.z-gh.z);
  noise(1.4,.3); tone(70,1.6,'sawtooth',.2,160);
  $('bars').className='on'; $('banner').style.opacity=0;      // đoạn phim ngắn: hiện hai thanh đen điện ảnh
}
function moveGhost(tx,tz,sp,dt){
  const dx=tx-gh.x,dz=tz-gh.z,d=Math.hypot(dx,dz)||1,s=Math.min(d,sp*dt);
  gh.x+=dx/d*s; gh.z+=dz/d*s; if(d>.05) gh.face=Math.atan2(dx,dz); return d;
}
function caught(){
  if(state!=='play') return;
  state='scare'; gh.phase='scare'; scareT=0; closeModal(true); syncLock();
  const dx=gh.x-camera.position.x, dz=gh.z-camera.position.z, d=Math.hypot(dx,dz)||1;
  gh.ux=dx/d; gh.uz=dz/d; scareYaw=Math.atan2(-gh.ux,-gh.uz); gh.alpha=1;
  $('scare').style.display='block'; $('banner').style.opacity=0; $('prompt').style.display='none';
  scream(); shake=.5;
}
function updGhost(dt){
  const P=gh.phase;
  if(P==='idle'){
    ghostTimer-=dt;
    if(ghostTimer<=0&&!transitioning&&state==='play') startGhost();
    return;
  }
  if(P==='warn'){ gh.t-=dt; if(gh.t<=0) ghostSpawn(); return; }
  if(P==='reveal'){
    // ĐOẠN PHIM: 0-1.2s ma chập chờn hiện hình · 1.2-3.3s từ từ tiến lại gần · 3.3s+ camera zoom, ma gào, chớp trắng · hết -> đuổi
    gh.t-=dt; const e=gh.t0-gh.t, px2=camera.position.x, pz2=camera.position.z;
    gh.alpha=e<1.2?Math.min(1,e/1.2)*(Math.random()<.35?.3:1):1;
    gh.face=Math.atan2(px2-gh.x,pz2-gh.z);
    if(e>1.2&&Math.hypot(gh.x-px2,gh.z-pz2)>10) moveGhost(px2,pz2,1.1,dt);
    shake=Math.max(shake,e>3.3?.12:.02);
    if(Math.random()<dt*2) noise(.25,.1);
    const fv=e>3.3?72-16*Math.min(1,(e-3.3)/.9):72;
    if(Math.abs(camera.fov-fv)>.05){camera.fov=fv;camera.updateProjectionMatrix();}
    if(e>3.3&&!gh.shr){gh.shr=true; tone(900,.9,'sawtooth',.22,260); tone(120,1,'square',.2,50); noise(.9,.45);
      if(!RF){const f=$('flash'); f.style.transition='none'; f.style.background='#fff'; f.style.opacity=.7;
        setTimeout(()=>{f.style.transition='opacity .45s'; f.style.opacity=0; f.style.background='#a00';},60);}}
    if(gh.t<=0){gh.phase='hunt'; gh.t=0; gh.step=0; camera.fov=72; camera.updateProjectionMatrix(); $('bars').className='';
      noise(1.2,.35); tone(60,1.4,'sawtooth',.22,200); whisper('chạy đi...');
      banner('NÓ ĐANG ĐUỔI THEO BẠN!\nTRỐN NGAY (tủ / gầm giường — E)',3200);}
    return;
  }
  if(P==='hunt'||P==='search') gh.alpha=Math.min(1,gh.alpha+dt*1.4);
  const px=camera.position.x, pz=camera.position.z;
  if(P==='hunt'){
    if(!hidden){
      const d=moveGhost(px,pz,3.6,dt);
      if(d<1.15){caught();return;}
    } else {
      const sp=curSpot, d=moveGhost(sp.x+sp.fx*sp.gd,sp.z+sp.fz*sp.gd,3.6,dt);
      if(d<0.12){gh.phase='search'; gh.t0=gh.t=6+Math.random()*1.5; gh.peek=0; whisper('tôi biết bạn ở đây...');}
    }
    gh.step-=dt; if(gh.step<=0){gh.step=.55; const dd=Math.hypot(gh.x-px,gh.z-pz); tone(45,.25,'sine',Math.min(.5,1/(dd*.3+1)),30); noise(.08,Math.min(.2,.6/(dd+1)));}
  } else if(P==='search'){
    gh.t-=dt; const sp=curSpot;
    gh.x=sp.x+sp.fx*sp.gd; gh.z=sp.z+sp.fz*sp.gd; gh.face=Math.atan2(-sp.fx,-sp.fz);
    const tp=gh.t0*.55, goal=gh.t<tp?1-gh.t/tp:0;
    gh.peek+=(goal-gh.peek)*Math.min(1,dt*3);
    if(Math.random()<dt*1.2) noise(.3,.05);
    if(gh.t<=0){gh.phase='leave'; gh.t=3; tone(60,1.8,'sawtooth',.14,35);}
  } else if(P==='leave'){
    gh.t-=dt; gh.peek=Math.max(0,gh.peek-dt*1.2); const sp=curSpot;
    if(sp) moveGhost(gh.x+sp.fx*6,gh.z+sp.fz*6,2.2,dt);
    gh.alpha=Math.max(0,Math.min(1,gh.t/1.6));
    if(gh.t<=0){parkGhost(); ghostTimer=45+Math.random()*35; banner('Ma đã đi rồi... Bạn có thể ra ngoài.',2800);}
  }
}
function animGhost(dt){
  const act2=gh.phase!=='idle';
  if(!act2){return;}
  const t=tt;
  const hunting=(gh.phase==='hunt'||gh.phase==='scare');
  gMats.forEach(m=>m.opacity=gh.alpha);
  gLight.intensity=gh.alpha*2.4*(0.6+0.4*Math.random());
  if(gh.phase!=='scare'){
    const sp=curSpot;
    const sink=(gh.phase==='search'||gh.phase==='leave')&&sp?sp.sink*gh.peek:0;
    const bend=(gh.phase==='search'||gh.phase==='leave')&&sp?sp.bend*gh.peek:(gh.phase==='reveal'?.65*Math.max(0,gh.t/gh.t0):0);
    ghostRoot.position.set(gh.x,-sink+Math.sin(t*2)*.04,gh.z);
    let da=gh.face-ghostRoot.rotation.y; da=Math.atan2(Math.sin(da),Math.cos(da));
    ghostRoot.rotation.y+=da*Math.min(1,dt*8);
    ghostRoot.rotation.x=bend;
  }
  const tgt=hunting?-1.35:(gh.phase==='reveal'?-.8:-.2);
  gArms.forEach((a,i)=>{a.sh.rotation.x+=((tgt+Math.sin(t*3+i)*.1)-a.sh.rotation.x)*Math.min(1,dt*6);a.el.rotation.x=-.25+Math.sin(t*5+i*2)*.08;});
  gHeadG.rotation.set(Math.sin(t*2.1)*.12,Math.sin(t*1.3)*.2,Math.sin(t*7)*.07+(Math.random()<dt*3?(Math.random()-.5)*.8:0));
  const lunge=gh.phase==='reveal'&&gh.t0-gh.t>3.3;
  if(gh.phase==='scare'||lunge){gHeadG.rotation.z+=(Math.random()-.5)*.5;gHeadG.rotation.y+=(Math.random()-.5)*.4;}
  gHair.forEach((h,i)=>{h.rotation.x=Math.sin(t*2+i)*.12;});
  gMouth.scale.y=(gh.phase==='scare'||lunge)?1.1+Math.abs(Math.sin(t*40))*.5:.35+Math.sin(t*3)*.1+(gh.phase==='search'?gh.peek*.5:0);
}
const sc=$('scare'), scx=sc.getContext('2d');
function drawScare(t){
  const w=sc.width,h=sc.height; scx.clearRect(0,0,w,h);
  if(t<.12||t>2.2||(!RF&&Math.random()<.18)||!CAN.face) return;
  const k=1+Math.min(t,.6)*.9+Math.sin(t*50)*.04, fh=h*1.35*k, fw=fh*512/640;
  scx.fillStyle='rgba(0,0,0,.55)'; scx.fillRect(0,0,w,h);
  scx.save(); scx.translate(w/2+(Math.random()-.5)*w*.04,h*.52+(Math.random()-.5)*h*.04); scx.rotate((Math.random()-.5)*.08);
  scx.drawImage(CAN.face,-fw/2,-fh/2,fw,fh); scx.restore();
  scx.fillStyle='rgba(140,150,175,'+(.08+Math.random()*.16)+')'; scx.fillRect(0,0,w,h);
  scx.fillStyle='rgba(0,0,0,.25)'; for(let y=0;y<h;y+=4) scx.fillRect(0,y,w,1);
}
function updScare(dt){
  scareT+=dt;
  let da=scareYaw-yaw; da=Math.atan2(Math.sin(da),Math.cos(da)); yaw+=da*(1-Math.exp(-dt*16));
  pitch+=(0.18-pitch)*(1-Math.exp(-dt*10));
  const e=Math.min(1,scareT/.25), fd=3.0-1.0*(1-Math.pow(1-e,3));
  ghostRoot.position.set(camera.position.x+gh.ux*fd+(Math.random()-.5)*.05,(Math.random()-.5)*.05,camera.position.z+gh.uz*fd+(Math.random()-.5)*.05);
  ghostRoot.rotation.y=Math.atan2(-gh.ux,-gh.uz); ghostRoot.rotation.x=.8*Math.min(1,scareT/.2);
  camera.fov=72+Math.min(scareT,1.2)*18; camera.updateProjectionMatrix();
  shake=Math.max(shake,.3);
  scareFlashT-=dt; if(scareFlashT<=0){scareFlashT=.06;const f=$('flash');
    if(RF){f.style.transition='opacity .3s';f.style.background='#667';f.style.opacity=.22;}
    else{f.style.transition='none';f.style.background=Math.random()<.4?'#fff':'#8890a0';f.style.opacity=Math.random()<.6?(.3+Math.random()*.6):0;}}
  drawScare(scareT);
  if(scareT>2.6){ const f=$('flash'); f.style.transition='opacity .45s'; gameOver('Con ma đã bắt được bạn...\nBạn phải bắt đầu lại từ cửa số 1.'); }
}

// ---------- Điều khiển ----------
addEventListener('keydown',e=>{
  if(modalOpen){
    if(e.code==='Escape') closeModal();
    else if(modalMode==='q'&&!e.repeat&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&(e.key||'').length===1){
      const k='ABCD'.indexOf(e.key.toUpperCase()); if(k>=0) choose(k);
    }
    return;
  }
  if((e.code==='ShiftLeft'||e.code==='ShiftRight')&&!e.repeat){ if(state==='play'&&!transitioning) toggleSL(); return; }
  keys[e.code]=true;
  if(e.code==='KeyE'&&state==='play'&&!transitioning) act();
  if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space'].includes(e.code)) e.preventDefault();
});
addEventListener('keyup',e=>{keys[e.code]=false;});
canvas.addEventListener('mousedown',()=>{
  dragging=!shiftLock;                      // Roblox: không Shift Lock thì giữ chuột (trái/phải) để xoay
  if(shiftLock&&state==='play'&&!modalOpen&&!isLocked()) lockPtr();
});
canvas.addEventListener('contextmenu',e=>e.preventDefault());
addEventListener('mouseup',()=>dragging=false);
document.documentElement.addEventListener('mouseleave',()=>{mouseIn=false;});
addEventListener('mousemove',e=>{
  const r=stage.getBoundingClientRect();
  mouseX=(e.clientX-r.left)/r.width*2-1; mouseY=(e.clientY-r.top)/r.height*2-1;
  mouseIn=Math.abs(mouseX)<=1&&Math.abs(mouseY)<=1;
  if(state!=='play'||modalOpen||gh.phase==='reveal') return;   // đoạn phim: không xoay được camera
  // Vuốt sang phải -> quay phải, sang trái -> quay trái (cả khi khóa chuột thật lẫn khi bị trình duyệt chặn)
  if(isLocked()||dragging||shiftLock){
    yaw-=e.movementX*0.0025; pitch=Math.max(-1.3,Math.min(1.3,pitch-e.movementY*0.0025));
  }
});
addEventListener('resize',fit);
document.addEventListener('fullscreenchange',fit);
$('lockbtn').onclick=()=>{if(state==='play'&&!modalOpen&&!transitioning)toggleSL();};
$('nt').style.display=inFrame?'block':'none';
$('nt').onclick=()=>{try{
  const w=window.open(URL.createObjectURL(new Blob([SRC],{type:'text/html'})),'_blank');
  if(!w) banner('Trình duyệt chặn cửa sổ mới — hãy cho phép popup rồi bấm lại.',3000);
}catch(e){banner('Không mở được tab mới.',2500);}};
$('fs').onclick=()=>{try{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen();}catch(e){}};

function hit(x,z){for(const b of obstacles){if(x>b.x1-0.35&&x<b.x2+0.35&&z>b.z1-0.35&&z<b.z2+0.35)return true;}return false;}

function update(dt){
  tt+=dt;
  stormUpdate(dt); pulseClues();
  if(PLAY_SRC&&!pbgm.paused){pduck+=((gh.phase!=='idle'&&state==='play'?.3:1)-pduck)*Math.min(1,dt*2);pbgm.volume=Math.max(0,Math.min(1,musicVol*.8*pduck));}
  for(let i=0;i<DUST;i++){dustPos[i*3+1]+=Math.sin(tt*.6+i)*0.0009+0.0006;dustPos[i*3]+=Math.cos(tt*.4+i*1.7)*0.0007;
    if(dustPos[i*3+1]>RH)dustPos[i*3+1]=0;}
  dustGeo.attributes.position.needsUpdate=true;
  sconceL.forEach((l,i)=>l.intensity=(0.85+0.25*Math.sin(tt*13+i*2.1)*Math.sin(tt*5.3+i))*lampF);
  if(fireMat) fireMat.opacity=.7+.2*Math.sin(tt*17)*Math.sin(tt*7.3);
  animGhost(dt);
  if(state==='scare'){ updScare(dt); return; }
  if(state!=='play') return;
  if(!modalOpen){ if(keys.ArrowLeft) yaw+=1.8*dt; if(keys.ArrowRight) yaw-=1.8*dt; }
  // Shift Lock dự phòng (không khóa được chuột): xoay camera theo vị trí chuột so với tâm khung
  // (khi không khóa được chuột, con trỏ ẩn nhưng vẫn chạm mép màn hình -> chạm mép thì tiếp tục xoay về phía đó)
  if(!modalOpen&&shiftLock&&!isLocked()&&mouseIn&&!dragging){
    const eb=.94, f=v=>Math.abs(v)>eb?Math.sign(v)*(Math.abs(v)-eb)/(1-eb):0;
    yaw-=f(mouseX)*2.6*dt; pitch=Math.max(-1.3,Math.min(1.3,pitch-f(mouseY)*1.6*dt));
  }
  let moving=false;
  if(!modalOpen&&!hidden&&!transitioning&&gh.phase!=='reveal'){
    let f=0,s=0;
    if(keys.KeyW||keys.ArrowUp)f++; if(keys.KeyS||keys.ArrowDown)f--; if(keys.KeyD)s++; if(keys.KeyA)s--;
    if(f||s){
      moving=true; const run=keys.Space, sp=(run?5.2:3.2)*dt, l=Math.hypot(f,s);
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
  if(hidden&&curSpot){ yaw=Math.max(curSpot.yaw-.75,Math.min(curSpot.yaw+.75,yaw)); pitch=Math.max(-.35,Math.min(.4,pitch)); }
  if(gh.phase==='reveal'&&!hidden){      // đoạn phim: camera tự quay về phía ma, người chơi không điều khiển được
    let da=Math.atan2(-(gh.x-camera.position.x),-(gh.z-camera.position.z))-yaw; da=Math.atan2(Math.sin(da),Math.cos(da));
    yaw+=da*(1-Math.exp(-dt*5)); pitch+=(0.05-pitch)*(1-Math.exp(-dt*4));
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
  if(hidden){ txt=gh.phase==='idle'?'[E] Ra khỏi chỗ trốn':'Đừng cử động...'; }
  else if(!modalOpen&&!transitioning){
    const px=camera.position.x,pz=camera.position.z; let best=99;
    for(const o of inter){
      if(o.kind==='clue'&&solved[o.idx]) continue;
      if(o.kind==='door'&&doorOpen) continue;
      const dx=o.x-px,dzz=o.z-pz,d=Math.hypot(dx,dzz);
      if(d<o.r&&(dx*fxv+dzz*fzv)/(d||1)>0.35&&d<best){best=d;cur=o;}
    }
    if(cur) txt=cur.kind==='hide'?(cur.type==='bed'?'[E] Chui xuống gầm giường':'[E] Trốn vào tủ'):cur.kind==='door'?(solved.every(Boolean)?'[E] Nhập mật mã':'[E] Cửa (bị khóa)'):'[E] Xem manh mối';
  }
  if(gh.phase==='reveal'&&!hidden) txt='';
  const p=$('prompt'); p.style.display=txt?'block':'none'; p.textContent=txt;

  // sự kiện ngẫu nhiên + nhịp tim
  const ghostOn=gh.phase!=='idle';
  if(!modalOpen&&!transitioning&&!ghostOn){
    nextFlick-=dt; if(nextFlick<=0){flickT=.5;nextFlick=10+Math.random()*15;tone(120,.5,'sawtooth',.05,60);}
    evT-=dt; if(evT<=0){evT=12+Math.random()*14;tone(rnd(110,240),.8,'sawtooth',.04,rnd(60,100)); if(Math.random()<.6)whisper();}
  }
  hbT-=dt;
  if(hbT<=0){
    if(ghostOn&&gh.phase!=='leave'){const dd=Math.hypot(gh.x-camera.position.x,gh.z-camera.position.z);
      const iv=gh.phase==='warn'?.8:(gh.phase==='search'?.42:.38+.5*Math.min(1,Math.max(0,(dd-2)/12)));
      tone(55,.12,'sine',.4,40);setTimeout(()=>tone(48,.12,'sine',.32,36),150);hbT=iv;shake=Math.max(shake,.012);}
    else if(hp===1){tone(55,.12,'sine',.35,40);setTimeout(()=>tone(48,.12,'sine',.3,36),170);hbT=.85;}
    else hbT=.3;
  }
  if(droneG&&AC){const dd=ghostOn?Math.hypot(gh.x-camera.position.x,gh.z-camera.position.z):99;
    droneG.gain.setTargetAtTime(ghostOn?(.05+.12*Math.max(0,1-dd/18)):0,AC.currentTime,.3);}

  // ánh sáng: tối dần khi ma xuất hiện
  const dtarget=gh.phase==='warn'?.5:(ghostOn?.9:0); dark+=(dtarget-dark)*Math.min(1,dt*3);
  lampF=1; if(flickT>0){flickT-=dt;lampF=Math.random()<.5?.08:1;}
  if(gh.phase==='warn') lampF=(Math.sin(tt*40)>.1&&Math.random()<.55)?1:.04;
  else if(ghostOn) lampF=Math.random()<.1?.6:.05+Math.random()*.08;
  if(RF) lampF=gh.phase==='warn'?.35+.25*Math.sin(tt*2.5):(ghostOn?.12:(flickT>0?.5:1));   // chế độ giảm chớp: đèn mờ/sáng chậm, không nhấp nháy
  ambL.intensity=.85*(1-dark*.7)+flashV*1.2;
  lamp.intensity=1.1*lampF; lampB.intensity=.9*lampF;
  if(flameMat){const v=Math.max(.15,lampF);flameMat.color.setRGB(v,.85*v,.63*v);}
  if(!hidden) spot.intensity=2.1*(0.93+0.07*Math.sin(tt*23))*(lampF<.5?0.5:1);

  updGhost(dt);
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
applyQuality(true);
buildRoom(); camera.position.set(0,1.6,RD/2-2);
musicStart();
requestAnimationFrame(loop);
})();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# STREAMLIT
# ---------------------------------------------------------------------------
# Khung game luôn 16:9 theo chiều rộng trang
st.markdown(
    """
<style>
.block-container{padding:3.2rem 1rem 0 1rem !important;max-width:100% !important;}
iframe[title="streamlit.components.v1.html"]{
    width:100% !important;height:auto !important;aspect-ratio:16/9;
    max-height:calc(100vh - 4rem);border:0;background:#000;}
</style>
""",
    unsafe_allow_html=True,
)

_html = (GAME_HTML.replace("__DATA__", build_data())
         .replace("__MUSIC__", load_mp3(MUSIC_FILE, PLAY_MUSIC_FILE, True))
         .replace("__MUSIC2__", load_mp3(PLAY_MUSIC_FILE)))
if not load_mp3(MUSIC_FILE, PLAY_MUSIC_FILE, True):
    st.warning(f"Không tìm thấy file nhạc '{MUSIC_FILE}'. Hãy đặt nó cùng thư mục với app.py để có nhạc ở menu.")
if not load_mp3(PLAY_MUSIC_FILE):
    st.warning(f"Không tìm thấy file nhạc '{PLAY_MUSIC_FILE}'. Hãy đặt nó cùng thư mục với app.py để có nhạc nền khi chơi.")
components.html(_html, height=720, scrolling=False)
st.caption("Shift Lock kiểu Roblox cần trình duyệt cho khóa chuột. Nếu không khóa được trong khung này, "
           "bấm nút TAB MỚI trong game hoặc tải bản HTML bên dưới và mở bằng trình duyệt.")
st.download_button("Tải game (.html) để chơi độc lập", _html, file_name="doors3d.html", mime="text/html")
