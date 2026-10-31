import glob
import os
import struct

def dump_pascal_str(b: bytes, off: int):
    ln = b[off]
    return b[off + 1:off + 1 + ln].decode("mac_roman", errors="replace"), off + 1 + ln

def inspect_all():
    rdir = "reference/macnasty/rsrc_dump"

    # 1. MNTY 0 & vers 2
    mnty = open(f"{rdir}/MNTY_0.bin", "rb").read()
    print("=== MNTY 0 ===")
    print(repr(mnty), dump_pascal_str(mnty, 0)[0])

    vers = open(f"{rdir}/vers_2_Hello There.bin", "rb").read()
    print("\n=== vers 2 ===")
    print(repr(vers))
    s1, next_off = dump_pascal_str(vers, 6)
    s2, _ = dump_pascal_str(vers, next_off)
    print(f"  short: {s1!r}, long: {s2!r}")

    # 2. STR# 1001
    str_list = open(f"{rdir}/STR_23_1001.bin", "rb").read()
    num_strs = struct.unpack(">H", str_list[:2])[0]
    print(f"\n=== STR# 1001 ({num_strs} strings) ===")
    off = 2
    for i in range(num_strs):
        s, off = dump_pascal_str(str_list, off)
        print(f"  [{i+1}] {s!r}")

    # 3. WIND 1
    wind = open(f"{rdir}/WIND_1.bin", "rb").read()
    top, left, bot, right, proc_id, vis, go_away, ref_con = struct.unpack(">hhhhhbxBxI", wind[:18])
    wtitle, _ = dump_pascal_str(wind, 18)
    print(f"\n=== WIND 1 ===")
    print(f"  rect=({left},{top})-({right},{bot}) size={right-left}x{bot-top} proc={proc_id} vis={vis} title={wtitle!r}")

    # 4. CNTL
    print("\n=== CNTLs ===")
    for cid in [130, 131, 156]:
        c = open(f"{rdir}/CNTL_{cid}.bin", "rb").read()
        top, left, bot, right, val, vis, mx, mn, proc_id, ref_con = struct.unpack(">hhhhhBxhhhI", c[:22])
        ctitle, _ = dump_pascal_str(c, 22)
        print(f"  CNTL {cid}: rect=({left},{top})-({right},{bot}) val={val} min={mn} max={mx} proc={proc_id} title={ctitle!r}")

    # 5. MENUs
    print("\n=== MENUs ===")
    for mid in [1, 2, 3, 4, 5]:
        m = open(f"{rdir}/MENU_{mid}.bin", "rb").read()
        menu_id, width, height, res_id, enable_flags = struct.unpack(">hhhhxxI", m[:14])
        mtitle, off = dump_pascal_str(m, 14)
        print(f"  MENU {mid} (id={menu_id} title={mtitle!r}):")
        while off < len(m) and m[off] != 0:
            item_str, off = dump_pascal_str(m, off)
            icon_num, key_eq, mark_char, style = m[off:off+4]
            off += 4
            k_str = chr(key_eq) if key_eq else ""
            print(f"    - {item_str!r} (icon={icon_num}, cmd={k_str!r}, mark={mark_char}, style={style})")

    # 6. DLOGs and DITLs
    print("\n=== DLOGs & DITLs ===")
    dlog_ids = [6000, 6001, 6002, 6003, 6010, 7000, 7001, 7002, 7003, 7004, 7005, 7006, 7007, 7008]
    for did in dlog_ids:
        d = open(f"{rdir}/DLOG_{did}.bin", "rb").read()
        top, left, bot, right, proc_id, vis, go_away, ref_con, items_id = struct.unpack(">hhhhhbxbxIh", d[:20])
        dtitle, _ = dump_pascal_str(d, 20)
        print(f"\n  DLOG {did}: rect=({left},{top})-({right},{bot}) size={right-left}x{bot-top} proc={proc_id} ditl={items_id} title={dtitle!r}")
        ditl = open(f"{rdir}/DITL_{items_id}.bin", "rb").read()
        num_items_minus_1 = struct.unpack(">h", ditl[:2])[0]
        num_items = num_items_minus_1 + 1
        off = 2
        for idx in range(num_items):
            # 4 bytes handle/placeholder, 8 bytes rect, 1 byte itemType, 1 byte dataLen
            itop, ileft, ibot, iright, itype, dlen = struct.unpack(">xxxxhhhhBB", ditl[off:off+14])
            idata = ditl[off+14:off+14+dlen]
            off += 14 + dlen
            if off & 1:
                off += 1
            enabled = (itype & 0x80) == 0
            kind = itype & 0x7F
            if kind in (4, 5, 6, 8, 16):  # Button, CheckBox, Radio, StaticText, EditText
                txt = idata.decode("mac_roman", errors="replace")
                print(f"    Item {idx+1}: kind={kind} en={enabled} rect=({ileft},{itop})-({iright},{ibot}) text={txt!r}")
            elif kind in (7, 32, 64):  # Ctrl, Icon, Pict
                res_id = struct.unpack(">h", idata[:2])[0] if len(idata) >= 2 else None
                print(f"    Item {idx+1}: kind={kind} en={enabled} rect=({ileft},{itop})-({iright},{ibot}) res_id={res_id}")
            else:
                print(f"    Item {idx+1}: kind={kind} en={enabled} rect=({ileft},{itop})-({iright},{ibot}) raw={idata!r}")

    # 7. ReadMe.1st
    print("\n=== ReadMe.1st.data ===")
    readme = open("reference/macnasty/extracted/ReadMe.1st.data", "rb").read()
    print(readme.decode("mac_roman", errors="replace"))

if __name__ == "__main__":
    inspect_all()
