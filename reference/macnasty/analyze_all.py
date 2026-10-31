import struct
import os
import json

rsrc_dir = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\rsrc_dump"

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

for d_id in [6000, 6001, 6002, 6003, 6010, 7000, 7001, 7002, 7003, 7004, 7005, 7006, 7007, 7008]:
    items = parse_ditl(d_id)
    print(f"=== DITL {d_id} ({len(items)} items) ===")
    for it in items:
        print(f"  #{it['index']:2d} rect={it['rect']} kind={it['kind']} val={repr(it['val'])}")
