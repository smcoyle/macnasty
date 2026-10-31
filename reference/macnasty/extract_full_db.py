import struct
import os

rsrc_dir = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\rsrc_dump"

with open(os.path.join(rsrc_dir, "CODE_3.bin"), "rb") as f:
    code3 = f.read()

a5_mem = {}
cur_a2 = None
pos = 0x0450
end = 0x0DDE
while pos < end:
    op = struct.unpack(">H", code3[pos:pos+2])[0]
    if op == 0x45ED: # LEA d16(A5), A2
        cur_a2 = struct.unpack(">h", code3[pos+2:pos+4])[0]
        pos += 4
    elif op == 0x34BC and cur_a2 is not None: # MOVE.W #imm, (A2)
        val = struct.unpack(">H", code3[pos+2:pos+4])[0]
        a5_mem[(cur_a2 + 0, 'w')] = val
        pos += 4
    elif op == 0x4252 and cur_a2 is not None: # CLR.W (A2)
        a5_mem[(cur_a2 + 0, 'w')] = 0
        pos += 2
    elif op == 0x357C and cur_a2 is not None: # MOVE.W #imm, d16(A2)
        val, off = struct.unpack(">Hh", code3[pos+2:pos+6])
        a5_mem[(cur_a2 + off, 'w')] = val
        pos += 6
    elif op == 0x426A and cur_a2 is not None: # CLR.W d16(A2)
        off = struct.unpack(">h", code3[pos+2:pos+4])[0]
        a5_mem[(cur_a2 + off, 'w')] = 0
        pos += 4
    elif op == 0x157C and cur_a2 is not None: # MOVE.B #imm, d16(A2)
        val, off = struct.unpack(">Hh", code3[pos+2:pos+6])
        a5_mem[(cur_a2 + off, 'b')] = val & 0xFF
        pos += 6
    elif op == 0x422A and cur_a2 is not None: # CLR.B d16(A2)
        off = struct.unpack(">h", code3[pos+2:pos+4])[0]
        a5_mem[(cur_a2 + off, 'b')] = 0
        pos += 4
    else:
        pos += 2

# Scan all CODE segments for 0C40 <imm16> 6600 <disp16> 487A <pdisp16>
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

print("\n=== ALL 44 CHARACTERS ===")
for cid in sorted(char_base_disp.keys()):
    base = char_base_disp[cid]
    name = id_to_str.get(cid, f"Char_{cid}")
    job_id = a5_mem.get((base + 0, 'w'), 0)
    sec_flag = a5_mem.get((base + 2, 'b'), 0)
    sec_id = a5_mem.get((base + 4, 'w'), 0)
    f6 = a5_mem.get((base + 6, 'b'), 0)
    f7 = a5_mem.get((base + 7, 'b'), 0)
    f8 = a5_mem.get((base + 8, 'b'), 0)
    lover_id = a5_mem.get((base + 10, 'w'), 0)
    rumor_id = a5_mem.get((base + 12, 'w'), 0)
    rep_id = a5_mem.get((base + 14, 'w'), 0)
    f16 = a5_mem.get((base + 16, 'b'), 0)
    f17 = a5_mem.get((base + 17, 'b'), 0)
    print(f"{cid} ({base:5d}): {name:16s} | Job={job_id:3d} | SecFlag={sec_flag} Sec={sec_id:3d}({id_to_str.get(sec_id,'')}) Lover={lover_id:3d}({id_to_str.get(lover_id,'')}) | Rumor={rumor_id:3d}({id_to_str.get(rumor_id,'')}) | Rep={rep_id:3d}({id_to_str.get(rep_id,'')}) | flags=({f6},{f7},{f8},{f16},{f17})")
