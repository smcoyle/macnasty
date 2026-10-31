import os
import sys

sys.path.append(r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty")
from disasm68k import disasm_segment, parse_jump_table

rsrc_dir = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\rsrc_dump"
out_dir = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\disasm"
os.makedirs(out_dir, exist_ok=True)

with open(os.path.join(rsrc_dir, "CODE_0.bin"), "rb") as f:
    code0 = f.read()
above_a5, below_a5, jt_off, jt_entries = parse_jump_table(code0)

for cid in range(1, 24):
    p = os.path.join(rsrc_dir, f"CODE_{cid}.bin")
    if not os.path.exists(p):
        continue
    with open(p, "rb") as f:
        data = f.read()
    text = disasm_segment(data, jt_entries)
    out_path = os.path.join(out_dir, f"CODE_{cid:02d}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(f"Disassembled CODE_{cid:02d} -> {text.count(chr(10))+1} lines")
