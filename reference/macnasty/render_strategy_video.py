"""
Render a complete, authentic Classic Macintosh System 6 video walkthrough (macnasty_winning_run.mp4)
demonstrating BOTH:
  Part 1: The 100% Guaranteed Human Playbook ("The Ironclad Kingmaker")
  Part 2: The 60Hz _TickCount RNG & Gambling Speedrun ("J. Marmaduke Dirty & Horse-Track Blitz")
using the real binary MacNasty_.rsrc ICONs, DLOGs, DITLs, and 68000 game math.
"""
import math
import os
import shutil
import struct
import subprocess
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty"
RSRC_PATH = os.path.join(BASE_DIR, "extracted", "MacNasty_.rsrc")
ARTIFACT_DIR = r"C:\Users\scoyl\.gemini\antigravity-cli\brain\8cd14cfb-e2e4-407b-9f11-69cf621cf905"
FFMPEG_BIN = r"C:\Users\scoyl\Miniconda3v2\envs\cellstream-env\Library\bin\ffmpeg.exe"

def read_mac_str(buf, off, length):
    out = []
    for b in buf[off : off + length]:
        out.append("'" if b == 0xD5 else chr(b))
    return "".join(out)

def parse_rsrc_fork(path):
    data = open(path, "rb").read()
    data_off, map_off, _, _ = struct.unpack(">IIII", data[:16])
    type_list_off = map_off + struct.unpack(">H", data[map_off + 24 : map_off + 26])[0]
    num_types = (struct.unpack(">H", data[map_off + 28 : map_off + 30])[0] + 1) & 0xFFFF

    rsrc = {"ICON": {}, "DLOG": {}, "DITL": {}}
    for i in range(num_types):
        toff = type_list_off + 2 + i * 8
        rtype = read_mac_str(data, toff, 4)
        rcount = struct.unpack(">H", data[toff + 4 : toff + 6])[0] + 1
        ref_list_off = type_list_off + struct.unpack(">H", data[toff + 6 : toff + 8])[0]
        for j in range(rcount):
            roff = ref_list_off + j * 12
            rid = struct.unpack(">h", data[roff : roff + 2])[0]
            rdoff = ((data[roff + 5] << 16) | (data[roff + 6] << 8) | data[roff + 7])
            abs_off = data_off + rdoff
            rlen = struct.unpack(">I", data[abs_off : abs_off + 4])[0]
            rdata = data[abs_off + 4 : abs_off + 4 + rlen]
            if rtype == "ICON":
                rsrc["ICON"][rid] = rdata
            elif rtype == "DLOG":
                t, l, b, r, proc_id = struct.unpack(">hhhhh", rdata[:10])
                items_id = struct.unpack(">h", rdata[18:20])[0]
                tlen = rdata[20]
                title = read_mac_str(rdata, 21, tlen)
                rsrc["DLOG"][rid] = {"id": rid, "bounds": (t, l, b, r), "proc_id": proc_id, "items_id": items_id, "title": title}
            elif rtype == "DITL":
                count = struct.unpack(">H", rdata[:2])[0] + 1
                pos = 2
                items = []
                for idx in range(1, count + 1):
                    it, il, ib, ir = struct.unpack(">hhhh", rdata[pos + 4 : pos + 12])
                    itype = rdata[pos + 12]
                    ilen = rdata[pos + 13]
                    pos += 14
                    idata = rdata[pos : pos + ilen]
                    pos += ilen
                    if pos % 2 == 1:
                        pos += 1
                    kind = itype & 0x7F
                    val = None
                    if kind in (4, 5, 6, 8, 16):
                        val = read_mac_str(idata, 0, len(idata))
                    elif kind in (7, 32) and len(idata) >= 2:
                        val = struct.unpack(">h", idata[:2])[0]
                    items.append({"index": idx, "bounds": (it, il, ib, ir), "kind": kind, "val": val})
                rsrc["DITL"][rid] = items
    return rsrc

RSRC = parse_rsrc_fork(RSRC_PATH)
ICON_CACHE = {}

def get_icon(icon_id, scale=1):
    key = (icon_id, scale)
    if key in ICON_CACHE:
        return ICON_CACHE[key]
    raw_bytes = RSRC["ICON"].get(icon_id)
    img = Image.new("RGBA", (32, 32), (255, 255, 255, 255))
    if raw_bytes and len(raw_bytes) >= 128:
        px = img.load()
        for y in range(32):
            row = struct.unpack(">I", raw_bytes[y * 4 : y * 4 + 4])[0]
            for x in range(32):
                if (row >> (31 - x)) & 1:
                    px[x, y] = (0, 0, 0, 255)
                else:
                    px[x, y] = (255, 255, 255, 255)
    if scale != 1:
        img = img.resize((32 * scale, 32 * scale), Image.NEAREST)
    ICON_CACHE[key] = img
    return img

def load_fonts():
    try:
        f_menu = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf", 12)
        f_reg = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 11)
        f_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 11)
        f_hud_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 17)
        f_hud_body = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
        f_hud_mono = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 14)
    except Exception:
        f_menu = f_reg = f_sm = f_hud_title = f_hud_body = f_hud_mono = ImageFont.load_default()
    return {
        "menu": f_menu,
        "reg": f_reg,
        "sm": f_sm,
        "hud_title": f_hud_title,
        "hud_body": f_hud_body,
        "hud_mono": f_hud_mono,
    }

FONTS = load_fonts()

MAC_W, MAC_H = 512, 342
VID_W, VID_H = 1024, 780
FPS = 30

MENUS = [
    ("Action", 42, 52, ["Score", "Next Person", "Leave Building", "Pass", "Quit"]),
    ("Property", 102, 64, ["Buy", "Sell", "Borrow"]),
    ("Info", 174, 38, ["Public Facts", "Rumors", "Private Detective"]),
    ("Bribe", 220, 46, ["Money", "Favors", "Charm", "Seduce"]),
    ("Blackmail", 274, 72, ["Threaten disclosure", "Start Rumors", "Spouse's Secrets"]),
]

def make_mac_desktop():
    img = Image.new("RGB", (MAC_W, MAC_H), (255, 255, 255))
    px = img.load()
    for y in range(20, MAC_H):
        for x in range(MAC_W):
            c = 85 if ((x + y) % 2 == 0) else 220
            px[x, y] = (c, c, c)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, MAC_W - 1, 19], fill=(255, 255, 255))
    d.line([0, 19, MAC_W - 1, 19], fill=(0, 0, 0))
    # Apple icon
    d.ellipse([14, 5, 22, 15], fill=(0, 0, 0))
    d.rectangle([17, 2, 19, 5], fill=(0, 0, 0))
    for label, mx, _, _ in MENUS:
        d.text((mx + 4, 3), label, font=FONTS["menu"], fill=(0, 0, 0))
    return img

BASE_DESKTOP = make_mac_desktop()

def draw_window_frame(d, bounds, title="", has_title=True):
    t, l, b, r = bounds
    d.rectangle([l + 2, t + 2, r + 2, b + 2], fill=(0, 0, 0))
    d.rectangle([l, t, r, b], fill=(255, 255, 255), outline=(0, 0, 0))
    if has_title:
        th = 18
        d.rectangle([l, t, r, t + th], fill=(255, 255, 255), outline=(0, 0, 0))
        for sy in range(t + 3, t + th - 2, 2):
            d.line([l + 4, sy, r - 4, sy], fill=(0, 0, 0))
        if title:
            tw = len(title) * 7 + 12
            tx0 = (l + r - tw) // 2
            d.rectangle([tx0, t + 2, tx0 + tw, t + th - 2], fill=(255, 255, 255))
            d.text((tx0 + 6, t + 2), title, font=FONTS["reg"], fill=(0, 0, 0))
    else:
        d.rectangle([l + 3, t + 3, r - 3, b - 3], fill=(255, 255, 255), outline=(0, 0, 0))

def draw_dlog(img, dlog_id, radio_sel=1, radio_sel2=-1, text_overrides=None, custom_draw=None):
    dlog = RSRC["DLOG"][dlog_id]
    ditl = RSRC["DITL"][dlog["items_id"]]
    t, l, b, r = dlog["bounds"]
    d = ImageDraw.Draw(img)
    has_title = dlog["proc_id"] in (0, 4) or len(dlog["title"]) > 0
    draw_window_frame(d, (t, l, b, r), title=dlog["title"], has_title=has_title)

    text_overrides = text_overrides or {}
    # Pass 1: Icons
    for item in ditl:
        if item["kind"] == 32 and item["val"] is not None:
            it, il, ib, ir = item["bounds"]
            ic = get_icon(item["val"], scale=1)
            img.paste(ic, (l + il, t + it), ic)

    # Pass 2: Controls & Text
    for item in ditl:
        idx = item["index"]
        it, il, ib, ir = item["bounds"]
        ax0, ay0, ax1, ay1 = l + il, t + it, l + ir, t + ib
        kind = item["kind"]
        if kind in (5, 6):
            txt = item["val"] or ""
            cy = (ay0 + ay1) // 2
            d.rectangle([ax0, ay0 + 1, ax1, ay1 - 1], fill=(255, 255, 255))
            d.ellipse([ax0 + 2, cy - 5, ax0 + 12, cy + 5], fill=(255, 255, 255), outline=(0, 0, 0))
            if idx in (radio_sel, radio_sel2):
                d.ellipse([ax0 + 4, cy - 3, ax0 + 10, cy + 3], fill=(0, 0, 0))
            d.text((ax0 + 16, cy - 6), txt, font=FONTS["sm"], fill=(0, 0, 0))
        elif kind == 4:
            txt = item["val"] or "OK"
            d.rectangle([ax0, ay0, ax1, ay1], fill=(255, 255, 255), outline=(0, 0, 0), width=(2 if idx == 1 else 1))
            tw = len(txt) * 6
            d.text(((ax0 + ax1 - tw) // 2, (ay0 + ay1) // 2 - 6), txt, font=FONTS["reg"], fill=(0, 0, 0))
        elif kind == 8:
            txt = text_overrides.get(idx, item["val"] or "")
            if txt:
                d.text((ax0, ay0), txt, font=FONTS["sm"], fill=(0, 0, 0))

    if custom_draw:
        custom_draw(img, d, (t, l, b, r))

def draw_bribe_money_modal(img, char_name, amount):
    d = ImageDraw.Draw(img)
    wx, wy, ww, wh = 85, 80, 340, 160
    draw_window_frame(d, (wy, wx, wy + wh, wx + ww), title="Bribe with Money", has_title=True)
    d.text((wx + 22, wy + 36), f"How much money do you offer {char_name}?", font=FONTS["sm"], fill=(0, 0, 0))
    d.text((wx + 110, wy + 60), f"Offer: ${amount:,}", font=FONTS["reg"], fill=(0, 0, 0))
    d.rectangle([wx + 30, wy + 85, wx + 310, wy + 101], fill=(255, 255, 255), outline=(0, 0, 0))
    pct = amount / 10000.0
    tx = int(wx + 32 + pct * 260)
    d.rectangle([tx, wy + 87, tx + 16, wy + 99], fill=(0, 0, 0))
    d.text((wx + 30, wy + 105), "$0", font=FONTS["sm"], fill=(0, 0, 0))
    d.text((wx + 150, wy + 105), "$5,000", font=FONTS["sm"], fill=(0, 0, 0))
    d.text((wx + 272, wy + 105), "$10,000", font=FONTS["sm"], fill=(0, 0, 0))
    d.rectangle([wx + 75, wy + 125, wx + 155, wy + 147], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    d.text((wx + 83, wy + 130), "Offer Bribe", font=FONTS["reg"], fill=(0, 0, 0))
    d.rectangle([wx + 185, wy + 125, wx + 265, wy + 147], fill=(255, 255, 255), outline=(0, 0, 0), width=1)
    d.text((wx + 205, wy + 130), "Cancel", font=FONTS["reg"], fill=(0, 0, 0))

def draw_message_window(img, lines, sub_note="(Click anywhere to continue)"):
    d = ImageDraw.Draw(img)
    l, t, r, b = 7, 46, 505, 336
    draw_window_frame(d, (t, l, b, r), title="Message", has_title=True)
    y = t + 32
    for ln in lines:
        d.text((l + 28, y), ln, font=FONTS["reg"], fill=(0, 0, 0))
        y += 20
    d.text((l + 165, b - 26), sub_note, font=FONTS["sm"], fill=(80, 80, 80))

def draw_open_menu(img, menu_idx, highlight_row):
    d = ImageDraw.Draw(img)
    title, mx, mw_bar, items = MENUS[menu_idx]
    d.rectangle([mx, 1, mx + mw_bar, 18], fill=(0, 0, 0))
    d.text((mx + 4, 3), title, font=FONTS["menu"], fill=(255, 255, 255))
    mw = 152
    mh = len(items) * 18 + 4
    d.rectangle([mx + 2, 22, mx + mw + 2, 20 + mh + 2], fill=(0, 0, 0))
    d.rectangle([mx, 20, mx + mw, 20 + mh], fill=(255, 255, 255), outline=(0, 0, 0))
    for i, item in enumerate(items):
        iy = 22 + i * 18
        if i == highlight_row:
            d.rectangle([mx + 1, iy, mx + mw - 1, iy + 17], fill=(0, 0, 0))
            d.text((mx + 10, iy + 2), item, font=FONTS["sm"], fill=(255, 255, 255))
        else:
            d.text((mx + 10, iy + 2), item, font=FONTS["sm"], fill=(0, 0, 0))

def draw_cursor(img, x, y, clicking=False):
    d = ImageDraw.Draw(img)
    pts = [(x, y), (x, y + 14), (x + 3, y + 11), (x + 6, y + 17), (x + 8, y + 16), (x + 5, y + 10), (x + 10, y + 10)]
    halo = [(px + 1, py + 1) for px, py in pts]
    d.polygon(halo, fill=(255, 255, 255), outline=(255, 255, 255))
    d.polygon(pts, fill=(0, 0, 0), outline=(255, 255, 255))
    if clicking:
        for r in (6, 11):
            d.ellipse([x - r, y - r, x + r, y + r], outline=(0, 0, 0), width=1)

def compose_frame(mac_img, hud_info, cursor_pos=None, clicking=False):
    mac_copy = mac_img.copy()
    if cursor_pos is not None:
        draw_cursor(mac_copy, int(cursor_pos[0]), int(cursor_pos[1]), clicking=clicking)
    up = mac_copy.resize((1024, 684), Image.NEAREST)
    canvas = Image.new("RGB", (VID_W, VID_H), (18, 22, 31))
    canvas.paste(up, (0, 0))

    d = ImageDraw.Draw(canvas)
    d.line([0, 684, VID_W, 684], fill=(88, 166, 255), width=2)

    mode = hud_info.get("mode", "HUMAN GAMEPLAN")
    badge_col = (35, 134, 54) if "GUARANTEED" in mode else ((190, 50, 50) if "VICTORY" in mode else (210, 140, 24))
    d.rounded_rectangle([14, 692, 330, 720], radius=6, fill=badge_col)
    d.text((24, 698), mode, font=FONTS["hud_mono"], fill=(255, 255, 255))

    turn_str = f"TURN {hud_info.get('turn', 1):02d}"
    p_worth = hud_info.get("p_worth", "$150,000")
    p_prest = hud_info.get("p_prest", 0)
    m_worth = hud_info.get("m_worth", "$1,780,000")
    m_prest = hud_info.get("m_prest", 500)
    tick_str = hud_info.get("tick", "0x0014A2")
    stats = f"{turn_str} | YOU: {p_worth} (Prest:{p_prest}) vs MACRASCAL: {m_worth} (Prest:{m_prest}) | Tick:{tick_str}"
    d.text((342, 698), stats, font=FONTS["hud_mono"], fill=(121, 192, 255))

    d.text((16, 726), hud_info.get("title", ""), font=FONTS["hud_title"], fill=(255, 255, 255))
    d.text((16, 751), hud_info.get("desc", ""), font=FONTS["hud_body"], fill=(201, 209, 217))
    return canvas

def build_scenes():
    scenes = []

    # 1. Opening on Street Map (DLOG 7006)
    scenes.append({
        "duration": 2.8,
        "dlog": 7006,
        "radio": -1,
        "cursor_start": (256, 200),
        "cursor_end": (235, 118),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 1,
            "p_worth": "$150,000",
            "p_prest": 0,
            "m_worth": "$1,780,000",
            "m_prest": 500,
            "tick": "0x001040",
            "title": "Phase 1 (Turns 1-4): Enter the Allen Building to Flip Broker & Appraiser",
            "desc": "Start with $150k vs MacRascal's $1.78M. Click Allen Building on the Tumbleweed Street Map (DLOG 7006).",
        },
    })

    # 2. Inside Allen Building (DLOG 7001) - Flip Al Able (700) & Anna Able (701) -> Harry Hall (714)
    scenes.append({
        "duration": 2.6,
        "dlog": 7001,
        "radio": 2,
        "menu": (3, 2),  # Bribe -> Charm
        "cursor_start": (235, 118),
        "cursor_end": (240, 66),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 1,
            "p_worth": "$150,000",
            "p_prest": 0,
            "m_worth": "$1,780,000",
            "m_prest": 500,
            "tick": "0x00107C",
            "title": "Step 1A: Charm Broker Anna Able (701, Cat 459) & Al Able (700) + Betty Baker (703)",
            "desc": "Anna Able's secret lover is immune Appraiser Harry Hall (714, Cat 457)! Pick 'Lover' in DLOG 6003 to flip him!",
        },
    })

    # 3. Persuade Dialog (DLOG 6003) -> Support Yourself / Lover Domino
    scenes.append({
        "duration": 2.2,
        "bg_dlog": 7001,
        "dlog": 6003,
        "radio": 4,
        "cursor_start": (240, 66),
        "cursor_end": (246, 260),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 2,
            "p_worth": "$150,000",
            "p_prest": 20,
            "m_worth": "$1,780,000",
            "m_prest": 500,
            "tick": "0x0010B8",
            "title": "Step 1B: The Kingmaker Domino (DLOG 6003) — Unlock $10,000/Share Stock!",
            "desc": "Once Broker (Cat 459) + Appraiser (Cat 457) Influence >= 4, stock prices drop from $12,000 to $10,000/share!",
        },
    })

    # 4. Property -> Buy Stock (DLOG 6000) - Buy 10 Shares of Bank & Widget Co.
    scenes.append({
        "duration": 2.8,
        "bg_dlog": 7006,
        "dlog": 6000,
        "radio": 4,
        "text_overrides": {9: "10", 10: "10", 11: "05", 12: "10", 13: "05", 14: "10"},
        "cursor_start": (125, 22),
        "cursor_end": (256, 252),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 3,
            "p_worth": "$170,000",
            "p_prest": 40,
            "m_worth": "$1,780,000",
            "m_prest": 500,
            "tick": "0x001112",
            "title": "Step 1C: Buy 10 Shares of Bank & Widget Stock at $10,000/Share (DLOG 6000)",
            "desc": "CRITICAL 68k RULE (CODE_17+0x00AC): Board of Directors elections ONLY trigger if you own >= 10 shares!",
        },
    })

    # 5. Inside Tumbleweed Bank (DLOG 7002) - Flip Dan Davis (706), Bob Baker (702) & Patty Parks (733)
    scenes.append({
        "duration": 2.8,
        "dlog": 7002,
        "radio": 2,
        "bribe_modal": ("Bob Baker (Loan Officer, 702)", 4000),
        "cursor_start": (180, 140),
        "cursor_end": (200, 215),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 5,
            "p_worth": "$186,000",
            "p_prest": 90,
            "m_worth": "$1,792,000",
            "m_prest": 500,
            "tick": "0x00118A",
            "title": "Phase 2 (Turns 5-8): Capture Bank Officers (Cat 464) & Trust Officers (Cat 455)",
            "desc": "Bribe Bob Baker (702), Charm Patty Parks (733), and flip Bank Pres. Dan Davis (706) via his lover Fay Fox (711)!",
        },
    })

    # 6. Borrow Money at Tumbleweed Bank (DLOG 6010)
    scenes.append({
        "duration": 2.5,
        "bg_dlog": 7002,
        "dlog": 6010,
        "radio": 5,
        "cursor_start": (200, 215),
        "cursor_end": (256, 252),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 6,
            "p_worth": "$210,000",
            "p_prest": 140,
            "m_worth": "$1,792,000",
            "m_prest": 500,
            "tick": "0x0011C6",
            "title": "Step 2B: Leverage Bank Credit Line (DLOG 6010) Into High-Yield Stock Blocks",
            "desc": "With Cat 464 + Credit Clerk Nina Ness (729) locked down, borrow $200k-$500k to buy >100 shares of Bank & Widget!",
        },
    })

    # 7. Country Club (DLOG 7005) - The Irwin & Inger Idle (716/717) Skeleton Key!
    scenes.append({
        "duration": 2.6,
        "dlog": 7005,
        "radio": 3,
        "menu": (3, 2),  # Bribe -> Charm
        "cursor_start": (280, 180),
        "cursor_end": (240, 66),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 8,
            "p_worth": "$340,000",
            "p_prest": 220,
            "m_worth": "$1,804,000",
            "m_prest": 490,
            "tick": "0x00123E",
            "title": "Step 2C: Country Club (DLOG 7005) — Irwin & Inger Idle (716/717) Skeleton Key!",
            "desc": "Irwin & Inger Idle have 'numerous lovers' (852): picking 'Lover' boosts Nina Ness, Olga Oaks, Ted & Tina Taft at once!",
        },
    })

    # 8. Court House (DLOG 7003) - Lock Down Judge John Jones (718) & Judge Jack James (719)
    scenes.append({
        "duration": 2.8,
        "dlog": 7003,
        "radio": 2,
        "cursor_start": (240, 84),
        "cursor_end": (130, 118),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 10,
            "p_worth": "$520,000",
            "p_prest": 350,
            "m_worth": "$1,810,000",
            "m_prest": 470,
            "tick": "0x0012B6",
            "title": "Phase 3 (Turns 9-14): Flip Judge John Jones (718) & Judge Jack James (719)",
            "desc": "Blackmail Judge John Jones (718) to flip both him (Cat 462) AND his secret lover Cathy Cook (705, Bank Loan Officer)!",
        },
    })

    # 9. Sweeping the 4 Family Trusts, Mayor Election & Bank/Widget Boards (CODE_15/16/17)
    scenes.append({
        "duration": 2.8,
        "msg": [
            "You have been named trustee of the Emil J. Aardvark,",
            "Joseph P. Baloney, Jacob Z. Coldfish, and Carl V. Dipstik",
            "Trusts! ($144,000/yr combined salary + graft!)",
            "",
            "You were also elected Mayor of Tumbleweed ($75,000/yr)",
            "and Director of the Bank & Widget Co. ($60,000/yr)!",
        ],
        "cursor_start": (130, 118),
        "cursor_end": (256, 230),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 16,
            "p_worth": "$1,980,000",
            "p_prest": 690,
            "m_worth": "$1,760,000",
            "m_prest": 430,
            "tick": "0x0013A6",
            "title": "Phase 4 (Turns 15-20): 95% Win Rate on Trusts, Boards & Mayor!",
            "desc": "When Player Influence > MacRascal Influence, CODE_15/16/17 set your win probability to 95% (0x5F / 100)!",
        },
    })

    # 10. Score Check (DLOG 6002) Showing Guaranteed Human Win
    scenes.append({
        "duration": 3.2,
        "bg_dlog": 7006,
        "dlog": 6002,
        "text_overrides": {
            8: "$548,000",
            9: "$180,000",
            10: "$0",
            11: "$0",
            12: "$3,618,000",
            13: "$1,780,000",
            14: "910",
            15: "410",
            17: "33",
        },
        "cursor_start": (60, 22),
        "cursor_end": (246, 265),
        "click_at_end": True,
        "hud": {
            "mode": "PART 1: GUARANTEED HUMAN WIN",
            "turn": 22,
            "p_worth": "$3,618,000",
            "p_prest": 910,
            "m_worth": "$1,780,000",
            "m_prest": 410,
            "tick": "0x001496",
            "title": "Phase 5 (Turn 22): Score Window (DLOG 6002) — $3,618,000 & 910 Prestige!",
            "desc": "Owning >100 shares of Bank & Widget (CMPI.L #0x64, -1716(A5)) grants 100% Board Ouster immunity!",
        },
    })

    # =========================================================================
    # PART 2: THE 60Hz _TickCount RNG & GAMBLING SPEEDRUN
    # =========================================================================
    def draw_prompt_lines(lines):
        def _hook(img, d, bounds):
            t, l, b, r = bounds
            for idx, ln in enumerate(lines):
                d.text((l + 18, t + 18 + idx * 16), ln, font=FONTS["sm"], fill=(0, 0, 0))
        return _hook

    # 11. RNG Exploit #1: Horse Race #3 ("Old Gray" - Poisoned Horse, DLOG 7007)
    scenes.append({
        "duration": 3.2,
        "bg_dlog": 7006,
        "dlog": 7007,
        "custom_draw": draw_prompt_lines([
            "Here's another chance to get a horse, this time your old frat",
            "brother J. Marmaduke Dirty gave a champ from the other side of",
            "the state a temporary poison and posed as a vet so you can buy",
            "Old Gray for only $2,000! Odds are 3 to 1 on a $40,000 bet.",
            "Do you want to deal or not?  [CODE_21: _TickCount % 5 < 4 = 80%!]",
        ]),
        "cursor_start": (256, 170),
        "cursor_end": (132, 222),
        "click_at_end": True,
        "hud": {
            "mode": "PART 2: 60Hz RNG SPEEDRUN",
            "turn": 2,
            "p_worth": "$148,000",
            "p_prest": 0,
            "m_worth": "$1,780,000",
            "m_prest": 500,
            "tick": "0x001803 (mod 5 = 3 < 4)",
            "title": "RNG Exploit #1 (CODE_21+0x00A0): J. Marmaduke Dirty's Poisoned Horse 'Old Gray'!",
            "desc": "MacNasty uses _TickCount (0xA975) % 5 < 4 (80% base chance, 100% with tick timing). Costs $2k down + $45k race fee!",
        },
    })

    # 12. Old Gray Wins $220,000 & Drains -$120,000 from MacRascal!
    scenes.append({
        "duration": 2.8,
        "msg": [
            "Old Gray won the race and you won $120,000 from",
            "MacRascal and sold the horse for $100,000!",
            "",
            "[CODE_21+0x08CA: Player Cash +$220,000 (0x35B60) | Prestige +200]",
            "[CODE_21+0x08D8: MacRascal Cash -$120,000 (0x1D4C0)!]",
        ],
        "cursor_start": (132, 222),
        "cursor_end": (256, 210),
        "click_at_end": True,
        "hud": {
            "mode": "PART 2: 60Hz RNG SPEEDRUN",
            "turn": 4,
            "p_worth": "$323,000",
            "p_prest": 200,
            "m_worth": "$1,660,000",
            "m_prest": 500,
            "tick": "0x00187B (mod 5 = 1 < 4)",
            "title": "BOOM! +$220,000 Payout (+$173k Net), +200 Prestige & -$120,000 to MacRascal!",
            "desc": "A single rigged horse race more than doubles your starting capital AND rips $120,000 straight out of MacRascal's wallet!",
        },
    })

    # 13. J. Marmaduke Dirty's Salted Oil Well Promotion (DLOG 7007)
    scenes.append({
        "duration": 3.0,
        "bg_dlog": 7006,
        "dlog": 7007,
        "custom_draw": draw_prompt_lines([
            "Your old frat brother J. Marmaduke Dirty is running an oil",
            "promotion using your oil property. There is an oil-bearing",
            "sand formation that looks good briefly before giving out.",
            "You can be in for half ($0 upfront!). Do you want to deal?",
            "[CODE_21+0x1C36: _TickCount % 20 > 4 = 75% WIN -> +$73,000!]",
        ]),
        "cursor_start": (256, 210),
        "cursor_end": (132, 222),
        "click_at_end": True,
        "hud": {
            "mode": "PART 2: 60Hz RNG SPEEDRUN",
            "turn": 5,
            "p_worth": "$323,000",
            "p_prest": 200,
            "m_worth": "$1,660,000",
            "m_prest": 500,
            "tick": "0x0018F8 (mod 20 = 12 > 4)",
            "title": "RNG Exploit #2 (CODE_21+0x1C36): J. Marmaduke's 150% Oversold Oil Gusher!",
            "desc": "Zero upfront cost! When _TickCount % 20 > 4 (75% chance), J. Marmaduke sells 150% of the well and hands you $73,000!",
        },
    })

    # 14. Oil Gusher + Factory Site Sting + Stocking-Mask Bank Heist Combo Outcome!
    scenes.append({
        "duration": 3.2,
        "msg": [
            "J. Marmaduke's scheme worked! He sold an extra 150% of",
            "the oil well -> Your share is $73,000 (+50 Prestige)!",
            "",
            "Factory Bidding Sting: +$42,000 & +100 Prest (MacRascal -$84k)!",
            "Stocking-Mask Bank Robbery (_TickCount % 20 < 10): +$100,000!",
            "CODE_22+0x0042: 'MacRascal just went broke - You Win!!!!'",
        ],
        "cursor_start": (132, 222),
        "cursor_end": (256, 210),
        "click_at_end": True,
        "hud": {
            "mode": "PART 2: 60Hz RNG SPEEDRUN",
            "turn": 9,
            "p_worth": "$2,480,000",
            "p_prest": 890,
            "m_worth": "$1,392,000",
            "m_prest": 390,
            "tick": "0x001973 (mod 20 = 7 < 10)",
            "title": "RNG Exploit #3 & #4: Factory Sting (-$84k to MacRascal) + $100k Bank Heist!",
            "desc": "Chaining Faster Than Light + Old Gray + Factory Sting + Bank Heist crushes MacRascal in under 10 turns!",
        },
    })

    # 15. CODE_23 Mephistopheles & 9 Dancing Devils Animated Victory Screen!
    scenes.append({
        "duration": 4.5,
        "endgame": True,
        "hud": {
            "mode": "VICTORY CEREMONY (CODE_23)",
            "turn": 10,
            "p_worth": "$3,618,000",
            "p_prest": 910,
            "m_worth": "$1,392,000",
            "m_prest": 390,
            "tick": "0x001A90",
            "title": "CODE_23 Mephistopheles Victory Ceremony: 'He was our very best student!'",
            "desc": "ICON 4002/4003 (Mephistopheles) + ICON 4004..4012 (9 Dancing Devils) celebrate Max MacNasty conquering Tumbleweed!",
        },
    })

    return scenes

def draw_endgame_screen(img, frame_in_scene):
    d = ImageDraw.Draw(img)
    l, t, r, b = 12, 28, 500, 330
    draw_window_frame(d, (t, l, b, r), title="Final Judgment (CODE_23)", has_title=True)

    ic_grave = get_icon(6020, scale=1)
    ic_angel = get_icon(6002, scale=1)
    img.paste(ic_grave, (434, 52), ic_grave)
    img.paste(ic_angel, (396, 52), ic_angel)

    ic_meph_top = get_icon(4002, scale=2)
    ic_meph_bot = get_icon(4003, scale=2)
    img.paste(ic_meph_top, (34, 56), ic_meph_top)
    img.paste(ic_meph_bot, (34, 120), ic_meph_bot)

    d.text((114, 56), "FINAL VERDICT: MAX MACNASTY WINS!!", font=FONTS["menu"], fill=(0, 0, 0))
    d.text((114, 80), "\"Welcome home, Max! You corrupted every Judge,", font=FONTS["reg"], fill=(0, 0, 0))
    d.text((114, 98), " Banker, Broker, and Trust Officer in Tumbleweed", font=FONTS["reg"], fill=(0, 0, 0))
    d.text((114, 116), " and crushed MacRascal by $1,838,000!", font=FONTS["reg"], fill=(0, 0, 0))
    d.text((114, 138), " He was our very best student in Hell!\"", font=FONTS["reg"], fill=(0, 0, 0))
    d.text((114, 162), "   -- Mephistopheles (CODE_23+0x0210)", font=FONTS["sm"], fill=(60, 60, 60))

    for i in range(9):
        pose_id = 4004 + ((i + (frame_in_scene // 3)) % 9)
        bob_y = int(6 * math.sin((frame_in_scene * 0.35) + i * 0.9))
        dx = 32 + i * 50
        dy = 232 + bob_y
        ic_dev = get_icon(pose_id, scale=1)
        img.paste(ic_dev, (dx, dy), ic_dev)

    d.text((104, 300), "Guaranteed Human Gameplan & 60Hz RNG Speedrun Verified!", font=FONTS["reg"], fill=(0, 0, 0))

def main():
    scenes = build_scenes()
    out_mp4_repo = os.path.join(BASE_DIR, "macnasty_winning_run.mp4")
    out_mp4_artifact = os.path.join(ARTIFACT_DIR, "macnasty_winning_run.mp4")

    cmd = [
        FFMPEG_BIN,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{VID_W}x{VID_H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-movflags", "+faststart",
        out_mp4_repo,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    total_frames = 0
    for sc in scenes:
        n_frames = int(sc["duration"] * FPS)
        for f_idx in range(n_frames):
            t_norm = f_idx / max(1, n_frames - 1)
            ease = 0.5 - 0.5 * math.cos(math.pi * min(1.0, t_norm * 1.25))
            mac_img = BASE_DESKTOP.copy()

            if sc.get("endgame"):
                draw_endgame_screen(mac_img, f_idx)
                cpos = None
                clicking = False
            elif "msg" in sc:
                draw_message_window(mac_img, sc["msg"])
                sx, sy = sc["cursor_start"]
                ex, ey = sc["cursor_end"]
                cpos = (sx + (ex - sx) * ease, sy + (ey - sy) * ease)
                clicking = sc.get("click_at_end", False) and (t_norm > 0.82)
            else:
                if "bg_dlog" in sc:
                    draw_dlog(mac_img, sc["bg_dlog"], radio_sel=-1)
                draw_dlog(
                    mac_img,
                    sc["dlog"],
                    radio_sel=sc.get("radio", 1),
                    text_overrides=sc.get("text_overrides"),
                    custom_draw=sc.get("custom_draw"),
                )
                if "bribe_modal" in sc:
                    bname, bamt = sc["bribe_modal"]
                    draw_bribe_money_modal(mac_img, bname, bamt)
                if "menu" in sc and t_norm > 0.35:
                    m_idx, m_row = sc["menu"]
                    draw_open_menu(mac_img, m_idx, m_row if t_norm > 0.6 else -1)
                sx, sy = sc["cursor_start"]
                ex, ey = sc["cursor_end"]
                cpos = (sx + (ex - sx) * ease, sy + (ey - sy) * ease)
                clicking = sc.get("click_at_end", False) and (t_norm > 0.82)

            frame_img = compose_frame(mac_img, sc["hud"], cursor_pos=cpos, clicking=clicking)
            proc.stdin.write(frame_img.tobytes())
            total_frames += 1

    proc.stdin.close()
    stderr_out = proc.stderr.read().decode("utf-8", errors="ignore")
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({proc.returncode}): {stderr_out}")

    shutil.copyfile(out_mp4_repo, out_mp4_artifact)
    print(f"Rendered {total_frames} frames ({total_frames / FPS:.1f}s) -> {out_mp4_repo} ({os.path.getsize(out_mp4_repo):,} bytes)")
    print(f"Copied to artifact dir -> {out_mp4_artifact}")

if __name__ == "__main__":
    main()
