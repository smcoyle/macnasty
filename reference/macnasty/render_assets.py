import os
import struct
import glob
from PIL import Image, ImageDraw, ImageFont

rsrc_dir = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\rsrc_dump"
out_dirs = [
    r"C:\Users\scoyl\.gemini\antigravity-cli\brain\8cd14cfb-e2e4-407b-9f11-69cf621cf905",
    r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty"
]

def load_icon_bitmap(data, offset=0):
    """Convert 128-byte 32x32 1-bit Classic Mac ICON into a PIL Image (mode 'RGBA')."""
    img = Image.new("RGBA", (32, 32), (255, 255, 255, 255))
    pixels = img.load()
    for y in range(32):
        row_bytes = data[offset + y*4 : offset + (y+1)*4]
        if len(row_bytes) < 4:
            break
        val = struct.unpack(">I", row_bytes)[0]
        for x in range(32):
            bit = (val >> (31 - x)) & 1
            if bit:
                pixels[x, y] = (0, 0, 0, 255)
            else:
                pixels[x, y] = (255, 255, 255, 255)
    return img

def load_icon(icon_id):
    path = os.path.join(rsrc_dir, f"ICON_{icon_id}.bin")
    with open(path, "rb") as f:
        data = f.read()
    return load_icon_bitmap(data, 0)

def parse_dlog(dlog_id):
    path = os.path.join(rsrc_dir, f"DLOG_{dlog_id}.bin")
    with open(path, "rb") as f:
        data = f.read()
    t, l, b, r, proc_id, visible, _pad1, go_away, _pad2, ref_con, items_id, title_len = struct.unpack(
        ">hhhhhBBBBihB", data[:21]
    )
    title = data[21:21+title_len].decode("mac_roman", errors="replace")
    return {
        "id": dlog_id,
        "rect": (l, t, r, b),
        "width": r - l,
        "height": b - t,
        "proc_id": proc_id,
        "items_id": items_id,
        "title": title,
    }

def parse_ditl(ditl_id):
    path = os.path.join(rsrc_dir, f"DITL_{ditl_id}.bin")
    with open(path, "rb") as f:
        data = f.read()
    count = struct.unpack(">H", data[0:2])[0] + 1
    pos = 2
    items = []
    for i in range(1, count + 1):
        t, l, b, r, itype, ilen = struct.unpack(">4xhhhhBB", data[pos:pos+14])
        pos += 14
        idata = data[pos:pos+ilen]
        pos += ilen
        if pos % 2 == 1:
            pos += 1
        kind = itype & 0x7F
        enabled = (itype & 0x80) == 0
        val = None
        if kind in (4, 5, 6, 8, 16):
            val = idata.decode("mac_roman", errors="replace")
        elif kind == 32 and len(idata) >= 2:
            val = struct.unpack(">h", idata[0:2])[0]
        elif kind == 7 and len(idata) >= 2:
            val = struct.unpack(">h", idata[0:2])[0]
        items.append({
            "index": i,
            "rect": (l, t, r, b),
            "kind": kind,
            "enabled": enabled,
            "val": val
        })
    return items

# 1. Render macnasty_icons_sheet.png
icon_files = glob.glob(os.path.join(rsrc_dir, "ICON_*.bin"))
icon_ids = sorted([int(os.path.basename(p).split("_")[1].split(".")[0]) for p in icon_files])

categories = [
    ("Application Icon & Mask (ICN# 128)", ["ICN_DATA", "ICN_MASK"]),
    ("Female Bodies (3000 - 3008)", [i for i in icon_ids if 3000 <= i <= 3008]),
    ("Female Heads (3010 - 3024)", [i for i in icon_ids if 3010 <= i <= 3024]),
    ("Special Portrait Tiles (3098 - 3099)", [i for i in icon_ids if 3098 <= i <= 3099]),
    ("Endgame: Mephistopheles & Hell Animation (4000 - 4012)", [i for i in icon_ids if 4000 <= i <= 4012]),
    ("Male Bodies (6000 - 6002)", [i for i in icon_ids if 6000 <= i <= 6002]),
    ("Male Heads (6010 - 6029)", [i for i in icon_ids if 6010 <= i <= 6029]),
    ("Tumbleweed Street Map Tiles (7000 - 7040) & Exit Door (8001)", [i for i in icon_ids if i >= 7000]),
]

scale = 2
cell_w = 88
cell_h = 92
cols = 11
sheet_w = cols * cell_w + 40
# Calculate height
total_rows = 0
for title, ids in categories:
    rows = (len(ids) + cols - 1) // cols
    total_rows += rows

sheet_h = 60 + len(categories) * 32 + total_rows * cell_h + 20
sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 245, 240))
draw = ImageDraw.Draw(sheet)

# Title
draw.rectangle([0, 0, sheet_w, 44], fill=(30, 30, 35))
draw.text((20, 14), "MacNasty (1987, George Lott) - Complete Resource Fork ICON & ICN# Asset Sheet (103 Bitmaps)", fill=(255, 255, 255))

with open(os.path.join(rsrc_dir, "ICN_23_128.bin"), "rb") as f:
    icn128_data = f.read()

y_cursor = 56
for cat_title, ids in categories:
    draw.rectangle([16, y_cursor, sheet_w - 16, y_cursor + 24], fill=(215, 220, 230), outline=(160, 165, 175))
    draw.text((24, y_cursor + 6), cat_title, fill=(20, 20, 30))
    y_cursor += 30
    for idx, item_id in enumerate(ids):
        r = idx // cols
        c = idx % cols
        cx = 20 + c * cell_w
        cy = y_cursor + r * cell_h
        draw.rectangle([cx, cy, cx + cell_w - 8, cy + cell_h - 6], fill=(255, 255, 255), outline=(190, 190, 190))
        if item_id == "ICN_DATA":
            im = load_icon_bitmap(icn128_data, 0)
            label = "ICN# 128"
        elif item_id == "ICN_MASK":
            im = load_icon_bitmap(icn128_data, 128)
            label = "Mask 128"
        else:
            im = load_icon(item_id)
            label = f"ICON {item_id}"
        im_scaled = im.resize((32 * scale, 32 * scale), Image.NEAREST)
        ix = cx + (cell_w - 8 - 32 * scale) // 2
        iy = cy + 4
        sheet.paste(im_scaled, (ix, iy))
        draw.rectangle([ix - 1, iy - 1, ix + 32 * scale, iy + 32 * scale], outline=(120, 120, 120))
        draw.text((cx + 8, iy + 32 * scale + 4), label, fill=(40, 40, 40))
    rows = (len(ids) + cols - 1) // cols
    y_cursor += rows * cell_h + 4

for od in out_dirs:
    sheet.save(os.path.join(od, "macnasty_icons_sheet.png"))

# 2. Render Dialog Windows helper
def render_dialog_window(dlog_id, scale=2):
    dlog = parse_dlog(dlog_id)
    ditl = parse_ditl(dlog["items_id"])
    w = dlog["width"]
    h = dlog["height"]
    title_h = 20
    canvas = Image.new("RGB", (w + 4, h + title_h + 4), (220, 220, 220))
    cdraw = ImageDraw.Draw(canvas)
    # Outer Mac window frame with drop shadow
    cdraw.rectangle([2, 2, w + 3, h + title_h + 3], fill=(0, 0, 0))
    cdraw.rectangle([0, 0, w + 1, h + title_h + 1], fill=(255, 255, 255), outline=(0, 0, 0))
    # Title bar with Classic Mac pinstripes
    cdraw.rectangle([0, 0, w + 1, title_h], fill=(255, 255, 255), outline=(0, 0, 0))
    for py in range(3, title_h - 2, 2):
        cdraw.line([4, py, w - 3, py], fill=(0, 0, 0))
    title_text = f"{dlog['title']} (DLOG {dlog_id})"
    tw = len(title_text) * 6 + 12
    tx = max(8, (w - tw) // 2)
    cdraw.rectangle([tx, 2, tx + tw, title_h - 2], fill=(255, 255, 255))
    cdraw.text((tx + 6, 4), title_text, fill=(0, 0, 0))

    ox = 1
    oy = title_h + 1
    # First draw all ICON items (kind == 32), then controls/text on top
    for it in ditl:
        l, t, r, b = it["rect"]
        if it["kind"] == 32 and it["val"] is not None:
            try:
                ic = load_icon(it["val"])
                canvas.paste(ic.convert("RGB"), (ox + l, oy + t))
            except Exception:
                pass
    for it in ditl:
        l, t, r, b = it["rect"]
        kind = it["kind"]
        val = it["val"]
        if kind in (5, 6): # Check box (5) or Radio button (6)
            # Draw white backing box for readability
            cdraw.rectangle([ox + l, oy + t + 1, ox + r, oy + b - 1], fill=(255, 255, 255))
            cy = oy + (t + b) // 2
            cx = ox + l + 6
            cdraw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(255, 255, 255), outline=(0, 0, 0))
            if it["index"] == 1 and dlog_id != 7006:
                cdraw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(0, 0, 0))
            cdraw.text((ox + l + 14, oy + t + 2), str(val or ""), fill=(0, 0, 0))
        elif kind == 4: # Push button
            cdraw.rounded_rectangle([ox + l, oy + t, ox + r, oy + b], radius=4, fill=(255, 255, 255), outline=(0, 0, 0))
            cdraw.text((ox + l + 8, oy + t + 3), str(val or ""), fill=(0, 0, 0))
        elif kind == 8: # Static text
            cdraw.text((ox + l, oy + t), str(val or ""), fill=(0, 0, 0))
    return canvas.resize(((w + 4) * scale, (h + title_h + 4) * scale), Image.NEAREST)

# Save macnasty_town_map.png (DLOG 7006 at 2x scale)
town_map_img = render_dialog_window(7006, scale=2)
for od in out_dirs:
    town_map_img.save(os.path.join(od, "macnasty_town_map.png"))

# Save macnasty_locations_sheet.png (DLOG 7000..7005 in a 2x3 grid at 1.5x or 2x scale)
loc_ids = [7000, 7001, 7002, 7003, 7004, 7005]
loc_imgs = [render_dialog_window(lid, scale=2) for lid in loc_ids]
lw, lh = loc_imgs[0].size
grid_w = lw * 2 + 48
grid_h = lh * 3 + 100
loc_sheet = Image.new("RGB", (grid_w, grid_h), (240, 240, 235))
ldraw = ImageDraw.Draw(loc_sheet)
ldraw.rectangle([0, 0, grid_w, 44], fill=(30, 30, 35))
ldraw.text((20, 14), "MacNasty (1987) - All 6 Tumbleweed Building Interiors (DLOG 7000 - 7005)", fill=(255, 255, 255))
for idx, im in enumerate(loc_imgs):
    r = idx // 2
    c = idx % 2
    x = 16 + c * (lw + 16)
    y = 60 + r * (lh + 16)
    loc_sheet.paste(im, (x, y))

for od in out_dirs:
    loc_sheet.save(os.path.join(od, "macnasty_locations_sheet.png"))

# 3. Map every character (700..743) to their building, radio button, Head ICON, and Body ICON
# From CODE_14 radio button handlers:
building_radio_map = {
    7000: ("Widget Mfg.", {1: 742, 2: 741, 3: 734, 4: 708, 5: 724}),
    7001: ("Allen Bldg.", {1: 700, 2: 701, 3: 709, 4: 712, 5: 714, 6: 703, 7: 704, 8: 735, 9: 724}),
    7002: ("Tumbleweed Bank", {1: 724, 2: 702, 3: 705, 4: 706, 5: 733, 6: 736, 7: 721, 8: 723, 9: 729}),
    7003: ("Court House", {1: 724, 2: 711, 3: 740, 4: 715, 5: 722, 6: 718, 7: 732, 8: 730, 9: 737}),
    7004: ("Butler Bldg.", {1: 724, 2: 710, 3: 728, 4: 731, 5: 726, 6: 738, 7: 720}),
    7005: ("Country Club", {1: 724, 2: 713, 3: 716, 4: 717, 5: 725, 6: 727, 7: 707, 8: 719, 9: 739, 10: 743}),
}

char_visual_info = {}
for dlog_id, (bname, rmap) in building_radio_map.items():
    ditl = parse_ditl(dlog_id)
    icons_in_ditl = [it for it in ditl if it["kind"] == 32 and it["val"] != 8001]
    for r_idx, cid in rmap.items():
        if cid in char_visual_info and cid == 724:
            continue
        r_item = ditl[r_idx - 1]
        rl, rt, rr, rb = r_item["rect"]
        # Find body icon immediately above radio button (0 <= rt - ib <= 16) and horizontally overlapping
        best_body = None
        best_dist = 9999
        for ic_it in icons_in_ditl:
            il, it_top, ir, ib = ic_it["rect"]
            if -2 <= (rt - ib) <= 16:
                dist = abs(((il + ir) / 2.0) - ((rl + rr) / 2.0))
                if dist < best_dist:
                    best_dist = dist
                    best_body = ic_it
        body_icon = best_body["val"] if best_body else 6000
        # Find head icon directly above best_body (same left coordinate, ib == body_t)
        head_icon = 6010
        if best_body:
            bl, bt, br, bb = best_body["rect"]
            for ic_it in icons_in_ditl:
                il, it_top, ir, ib = ic_it["rect"]
                if abs(il - bl) <= 4 and abs(ib - bt) <= 4:
                    head_icon = ic_it["val"]
                    break
        char_visual_info[cid] = {
            "dlog_id": dlog_id,
            "building": bname,
            "radio_index": r_idx,
            "radio_label": r_item["val"],
            "head_icon": head_icon,
            "body_icon": body_icon,
        }

# Also extract A5 database for all 44 characters
with open(os.path.join(rsrc_dir, "CODE_3.bin"), "rb") as f:
    code3 = f.read()
a5_mem = {}
cur_a2 = None
pos = 0x0450
while pos < 0x0DDE:
    op = struct.unpack(">H", code3[pos:pos+2])[0]
    if op == 0x45ED:
        cur_a2 = struct.unpack(">h", code3[pos+2:pos+4])[0]
        pos += 4
    elif op == 0x34BC and cur_a2 is not None:
        val = struct.unpack(">H", code3[pos+2:pos+4])[0]
        a5_mem[(cur_a2 + 0, 'w')] = val
        pos += 4
    elif op == 0x4252 and cur_a2 is not None:
        a5_mem[(cur_a2 + 0, 'w')] = 0
        pos += 2
    elif op == 0x357C and cur_a2 is not None:
        val, off = struct.unpack(">Hh", code3[pos+2:pos+6])
        a5_mem[(cur_a2 + off, 'w')] = val
        pos += 6
    elif op == 0x426A and cur_a2 is not None:
        off = struct.unpack(">h", code3[pos+2:pos+4])[0]
        a5_mem[(cur_a2 + off, 'w')] = 0
        pos += 4
    elif op == 0x157C and cur_a2 is not None:
        val, off = struct.unpack(">Hh", code3[pos+2:pos+6])
        a5_mem[(cur_a2 + off, 'b')] = val & 0xFF
        pos += 6
    elif op == 0x422A and cur_a2 is not None:
        off = struct.unpack(">h", code3[pos+2:pos+4])[0]
        a5_mem[(cur_a2 + off, 'b')] = 0
        pos += 4
    else:
        pos += 2

id_to_str = {}
for cid_num in range(1, 24):
    p = os.path.join(rsrc_dir, f"CODE_{cid_num}.bin")
    if not os.path.exists(p):
        continue
    with open(p, "rb") as f:
        cdata = f.read()
    for i in range(len(cdata) - 12):
        w0, imm, w2 = struct.unpack(">HHH", cdata[i:i+6])
        if w0 == 0x0C40 and w2 == 0x6600:
            w4, pdisp = struct.unpack(">Hh", cdata[i+8:i+12])
            if w4 == 0x487A:
                saddr = (i + 10) + pdisp
                if 0 <= saddr < len(cdata):
                    slen = cdata[saddr]
                    s = cdata[saddr+1:saddr+1+slen].decode("mac_roman", errors="replace")
                    if imm not in id_to_str or imm >= 700:
                        id_to_str[imm] = s

with open(os.path.join(rsrc_dir, "CODE_4.bin"), "rb") as f:
    code4 = f.read()
char_base_disp = {}
for i in range(0x0C50, 0x1090):
    w0, imm, w2 = struct.unpack(">HHH", code4[i:i+6])
    if w0 == 0x0C40 and 700 <= imm <= 743 and w2 == 0x6600:
        w6, base_disp = struct.unpack(">Hh", code4[i+12:i+16])
        if w6 == 0x486D:
            char_base_disp[imm] = base_disp

# Render macnasty_characters_sheet.png (44 characters in a 4x11 grid)
c_cols = 4
c_rows = 11
card_w = 310
card_h = 148
csheet_w = c_cols * card_w + 32
csheet_h = 60 + c_rows * card_h + 20
csheet = Image.new("RGB", (csheet_w, csheet_h), (242, 242, 236))
cdraw = ImageDraw.Draw(csheet)
cdraw.rectangle([0, 0, csheet_w, 44], fill=(30, 30, 35))
cdraw.text((20, 14), "MacNasty (1987) - Complete Cast of 44 Characters (22 Married Couples, Composite Portraits & Secrets)", fill=(255, 255, 255))

for idx, cid in enumerate(range(700, 744)):
    r = idx // c_cols
    c = idx % c_cols
    x = 16 + c * card_w
    y = 56 + r * card_h
    base = char_base_disp[cid]
    name = id_to_str.get(cid, f"Char {cid}")
    spouse_cid = cid + 1 if cid % 2 == 0 else cid - 1
    spouse_name = id_to_str.get(spouse_cid, "")
    vinfo = char_visual_info.get(cid, {"building": "All Buildings", "head_icon": 6014, "body_icon": 6002})
    sec_id = a5_mem.get((base + 4, 'w'), 0)
    lover_id = a5_mem.get((base + 10, 'w'), 0)
    f8 = a5_mem.get((base + 8, 'b'), 0)
    rep_id = a5_mem.get((base + 14, 'w'), 0)
    rumor_id = a5_mem.get((base + 12, 'w'), 0)

    # Highlight card border if involved in an affair
    has_affair = (lover_id != 0) or (sec_id == 852) or (f8 == 1)
    bg_color = (255, 248, 246) if has_affair else (255, 255, 255)
    border_color = (190, 60, 60) if has_affair else (180, 180, 185)
    cdraw.rectangle([x, y, x + card_w - 10, y + card_h - 8], fill=bg_color, outline=border_color, width=2 if has_affair else 1)

    # Composite Head + Body portrait (2x scale = 64x128)
    head_im = load_icon(vinfo["head_icon"]).resize((64, 64), Image.NEAREST)
    body_im = load_icon(vinfo["body_icon"]).resize((64, 64), Image.NEAREST)
    px = x + 8
    py = y + 6
    csheet.paste(head_im, (px, py))
    csheet.paste(body_im, (px, py + 64))
    cdraw.rectangle([px - 1, py - 1, px + 64, py + 128], outline=(100, 100, 100))

    tx = px + 72
    ty = y + 8
    cdraw.text((tx, ty), f"[{cid}] {name}", fill=(15, 15, 20))
    cdraw.text((tx, ty + 18), f"Loc: {vinfo['building']} (H:{vinfo['head_icon']}/B:{vinfo['body_icon']})", fill=(70, 70, 80))
    cdraw.text((tx, ty + 34), f"Spouse: {spouse_name} [{spouse_cid}]", fill=(70, 70, 80))
    rep_str = id_to_str.get(rep_id, "None") if rep_id != 0 else "None"
    if len(rep_str) > 32:
        rep_str = rep_str[:32] + "..."
    cdraw.text((tx, ty + 50), f"Rep: {rep_str}", fill=(50, 80, 50))
    rum_str = id_to_str.get(rumor_id, "None") if rumor_id != 0 else "None"
    if len(rum_str) > 32:
        rum_str = rum_str[:32] + "..."
    cdraw.text((tx, ty + 66), f"Rumor: {rum_str}", fill=(80, 70, 40))

    if lover_id != 0:
        lover_name = id_to_str.get(lover_id, str(lover_id))
        sec_text = f"LOVER: {lover_name} [{lover_id}]"
        sec_col = (180, 20, 20)
    elif sec_id != 0:
        s_str = id_to_str.get(sec_id, str(sec_id))
        if len(s_str) > 30:
            s_str = s_str[:30] + "..."
        sec_text = f"Secret: {s_str}"
        sec_col = (150, 30, 30) if sec_id == 852 else (40, 40, 140)
    else:
        sec_text = "Secret: None"
        sec_col = (100, 100, 100)
    cdraw.text((tx, ty + 84), sec_text, fill=sec_col)

    flags_list = []
    if a5_mem.get((base + 6, 'b'), 0): flags_list.append("Money")
    if a5_mem.get((base + 7, 'b'), 0): flags_list.append("Favor")
    if a5_mem.get((base + 16, 'b'), 0): flags_list.append("Charm")
    if a5_mem.get((base + 2, 'b'), 0): flags_list.append("Blkml")
    if a5_mem.get((base + 17, 'b'), 0): flags_list.append("SpouseSec")
    cdraw.text((tx, ty + 102), "Weakness: " + (", ".join(flags_list) if flags_list else "None"), fill=(60, 60, 60))

for od in out_dirs:
    csheet.save(os.path.join(od, "macnasty_characters_sheet.png"))

print("Rendered all 4 asset sheets successfully!")
for cid in sorted(char_visual_info.keys()):
    vi = char_visual_info[cid]
    print(f"Char {cid} ({id_to_str.get(cid,'')}): {vi['building']} (DLOG {vi['dlog_id']} #{vi['radio_index']}) Head={vi['head_icon']} Body={vi['body_icon']}")
