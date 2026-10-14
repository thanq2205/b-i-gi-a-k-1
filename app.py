"""
🚪 DOORS – Trò chơi giải đố 5 cửa (lấy cảm hứng từ Doors trong Roblox)
Chạy:  streamlit run app.py
"""
import random
import re
import unicodedata

import streamlit as st

st.set_page_config(page_title="DOORS – 5 Cửa", page_icon="🚪", layout="centered")

MAX_HP = 3
MAX_HINTS = 5

# ---------------------------------------------------------------------------
# DỮ LIỆU GAME
# Mỗi cửa có 3 câu hỏi. Trả lời đúng -> nhận 1 chữ số của chìa khóa.
# Ghép các chữ số theo "order" để ra mật mã mở cửa.
# ---------------------------------------------------------------------------
DOORS = [
    {
        "name": "Sảnh đón tiếp",
        "intro": "Ánh đèn chập chờn. Cánh cửa số 1 đóng chặt, trên tường có ba tấm bảng ghi câu đố.",
        "order": [0, 1, 2],
        "order_text": "Ghép chìa 1 → chìa 2 → chìa 3.",
        "questions": [
            {"q": "Cái gì càng lấy đi càng lớn?", "a": ["cai ho", "ho", "cai lo", "lo"],
             "digit": 4, "hint": "Bạn thường thấy nó khi đào đất."},
            {"q": "Có 3 quả táo, bạn lấy đi 2 quả. Vậy bạn đang có mấy quả táo?", "a": ["2", "hai"],
             "digit": 7, "hint": "Hỏi 'bạn có' chứ không hỏi 'còn lại'."},
            {"q": "Cái gì có chìa nhưng không mở được ổ khóa nào?", "a": ["dan piano", "piano", "ban phim", "dan organ", "dan"],
             "digit": 1, "hint": "Nhạc cụ có phím đen phím trắng."},
        ],
    },
    {
        "name": "Thư viện bỏ hoang",
        "intro": "Bụi phủ kín các kệ sách. Một giọng thì thầm: 'Hãy im lặng... và suy nghĩ.'",
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
        "intro": "Mùi hóa chất nồng nặc. Màn hình cũ nhấp nháy ba câu hỏi.",
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
        "intro": "Đèn pin của bạn gần hết pin. Có thứ gì đó đang di chuyển trong bóng tối...",
        "order": [1, 2, 0],
        "order_text": "Ghép chìa 2 → chìa 3 → chìa 1.",
        "questions": [
            {"q": "Mình có thành phố nhưng không có nhà, có núi nhưng không có cây, có sông nhưng không có nước. Mình là gì?",
             "a": ["ban do", "map", "cai ban do"], "digit": 2, "hint": "Bạn dùng nó để tìm đường."},
            {"q": "Số nhị phân 1011 bằng số thập phân nào?", "a": ["11"],
             "digit": 7, "hint": "8 + 0 + 2 + 1"},
            {"q": "Tôi nói mà không có miệng, nghe mà không có tai, chỉ sống nhờ không khí. Tôi là gì?",
             "a": ["tieng vang", "vang", "echo", "tieng doi"], "digit": 3, "hint": "Hét vào hang núi sẽ nghe thấy tôi."},
        ],
    },
    {
        "name": "Phòng cuối cùng",
        "intro": "Cánh cửa cuối cùng, to lớn và lạnh lẽo. Chỉ còn một bước nữa thôi...",
        "order": [2, 0, 1],
        "order_text": "Ghép chìa 3 → chìa 1 → chìa 2.",
        "questions": [
            {"q": "Tôi bay mà không có cánh, khóc mà không có mắt. Tôi là gì?",
             "a": ["may", "dam may", "may den", "dam may den"], "digit": 1, "hint": "Nhìn lên trời khi sắp mưa."},
            {"q": "Trong cuộc đua, bạn vượt qua người đang đứng thứ 2. Giờ bạn thứ mấy?", "a": ["2", "hai", "thu 2", "thu hai"],
             "digit": 9, "hint": "Bạn thế chỗ người đó."},
            {"q": "Trong game Doors, thực thể nháy đèn rồi lao qua cực nhanh, có tên là gì? (tiếng Anh, 1 từ)",
             "a": ["rush"], "digit": 4, "hint": "Nó bắt đầu bằng chữ R."},
        ],
    },
]

ENTITY_MESSAGES = [
    "💡 Đèn nháy liên tục... RUSH lao qua người bạn!",
    "👁️ AMBUSH xuất hiện từ bóng tối!",
    "😱 SCREECH hét lên ngay sau lưng bạn!",
    "🌀 Một thực thể vô hình quật bạn ngã!",
    "🚪 Cánh cửa rung lên dữ dội và hất bạn ra sau!",
]


# ---------------------------------------------------------------------------
# HÀM TIỆN ÍCH
# ---------------------------------------------------------------------------
def normalize(text: str) -> str:
    """Bỏ dấu, viết thường, chuẩn hóa khoảng trắng và dấu phẩy thập phân."""
    text = text.strip().lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace(",", ".")
    text = re.sub(r"[^a-z0-9. ]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def new_game():
    st.session_state.screen = "playing"
    st.session_state.door = 0
    st.session_state.hp = MAX_HP
    st.session_state.hints = MAX_HINTS
    st.session_state.solved = set()
    st.session_state.hints_shown = set()
    st.session_state.flash = []


def init():
    if "screen" not in st.session_state:
        st.session_state.screen = "start"
        st.session_state.door = 0
        st.session_state.hp = MAX_HP
        st.session_state.hints = MAX_HINTS
        st.session_state.solved = set()
        st.session_state.hints_shown = set()
        st.session_state.flash = []


def flash(kind: str, text: str):
    st.session_state.flash.append((kind, text))


def hurt():
    """Mất 1 máu, kích hoạt thực thể. Trả về True nếu hết máu."""
    st.session_state.hp -= 1
    flash("error", random.choice(ENTITY_MESSAGES) + " **-1 ❤️**")
    if st.session_state.hp <= 0:
        st.session_state.screen = "gameover"
        return True
    return False


def render_flash():
    for kind, text in st.session_state.flash:
        getattr(st, kind)(text)
    st.session_state.flash = []


def sidebar():
    s = st.session_state
    with st.sidebar:
        st.header("🕯️ Trạng thái")
        st.write("Máu: " + "❤️" * max(s.hp, 0) + "🖤" * (MAX_HP - max(s.hp, 0)))
        st.write(f"💡 Gợi ý còn lại: **{s.hints}**")
        st.write(f"🚪 Cửa: **{min(s.door + 1, 5)}/5**")
        st.divider()
        st.caption("Trả lời sai sẽ bị thực thể tấn công. Hết máu là thua!")
        if st.button("🔄 Chơi lại từ đầu"):
            new_game()
            st.rerun()


# ---------------------------------------------------------------------------
# MÀN HÌNH
# ---------------------------------------------------------------------------
def screen_start():
    st.title("🚪 DOORS")
    st.subheader("Thoát khỏi 5 cánh cửa")
    st.markdown(
        """
Bạn bị kẹt trong một khách sạn bí ẩn. Mỗi cửa có **3 câu đố**.
Trả lời đúng để nhận từng **chìa khóa (một chữ số)**, ghép lại thành **mật mã** mở cửa tiếp theo.

- ❤️ Bạn có **3 máu**. Trả lời sai hoặc nhập sai mật mã sẽ mất 1 máu.
- 💡 Bạn có **5 lượt gợi ý** cho cả trò chơi.
- ✍️ Không cần gõ dấu tiếng Việt.

Bạn có thoát được cửa số 5 không?
"""
    )
    if st.button("▶️ Bắt đầu", type="primary"):
        new_game()
        st.rerun()


def screen_gameover():
    st.title("💀 BẠN ĐÃ CHẾT")
    st.error(f"Bạn gục ngã ở cửa số {st.session_state.door + 1}...")
    if st.button("🔄 Thử lại", type="primary"):
        new_game()
        st.rerun()


def screen_win():
    st.title("🎉 BẠN ĐÃ THOÁT!")
    st.balloons()
    st.success(f"Bạn đã vượt qua cả 5 cánh cửa với {st.session_state.hp} ❤️ còn lại!")
    if st.button("🔄 Chơi lại", type="primary"):
        new_game()
        st.rerun()


def screen_playing():
    s = st.session_state
    d = s.door
    door = DOORS[d]
    qs = door["questions"]

    st.title(f"🚪 CỬA {d + 1}: {door['name']}")
    st.progress(d / len(DOORS))
    st.caption(door["intro"])
    render_flash()

    st.markdown("### 🗝️ Các câu đố")
    for i, q in enumerate(qs):
        key = (d, i)
        if key in s.solved:
            st.success(f"✅ Câu {i + 1}: {q['q']}  →  **Chìa khóa {i + 1} = {q['digit']}**")
            continue

        with st.form(f"form_{d}_{i}", clear_on_submit=True):
            ans = st.text_input(f"Câu {i + 1}: {q['q']}", key=f"in_{d}_{i}")
            c1, c2, _ = st.columns([1, 1, 3])
            submit = c1.form_submit_button("Trả lời", type="primary")
            hint = c2.form_submit_button("💡 Gợi ý")

        if key in s.hints_shown:
            st.info(f"💡 Gợi ý câu {i + 1}: {q['hint']}")

        if hint:
            if key in s.hints_shown:
                flash("info", "Bạn đã xem gợi ý câu này rồi.")
            elif s.hints <= 0:
                flash("warning", "Hết lượt gợi ý!")
            else:
                s.hints -= 1
                s.hints_shown.add(key)
            st.rerun()

        if submit:
            if not ans.strip():
                flash("warning", "Hãy nhập câu trả lời.")
            elif normalize(ans) in [normalize(x) for x in q["a"]]:
                s.solved.add(key)
                flash("success", f"🔑 Đúng rồi! Bạn nhận được chìa khóa {i + 1}.")
            else:
                hurt()
            st.rerun()

    # --- Nhập mật mã khi đã có đủ chìa ---
    if all((d, i) in s.solved for i in range(len(qs))):
        st.divider()
        st.markdown("### 🔐 Ổ khóa")
        st.write(f"Bạn đã có đủ chìa khóa. **{door['order_text']}**")
        with st.form(f"code_{d}", clear_on_submit=True):
            code = st.text_input("Nhập mật mã:", max_chars=len(qs))
            go = st.form_submit_button("🚪 Mở cửa", type="primary")
        if go:
            correct = "".join(str(qs[i]["digit"]) for i in door["order"])
            if code.strip() == correct:
                if d == len(DOORS) - 1:
                    s.screen = "win"
                else:
                    s.door += 1
                    flash("success", f"🔓 Cửa {d + 1} đã mở! Bạn bước sang cửa {d + 2}...")
            else:
                hurt()
            st.rerun()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
init()
if st.session_state.screen != "start":
    sidebar()

{
    "start": screen_start,
    "playing": screen_playing,
    "gameover": screen_gameover,
    "win": screen_win,
}[st.session_state.screen]()
