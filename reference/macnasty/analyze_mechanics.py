import struct
import os
import sys

sys.path.append(r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty")
from disasm68k import disasm_segment

rsrc_dir = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\rsrc_dump"

# Let's check which CODE segments contain strings or logic for Public Facts, Bribe, Blackmail, etc.
for cid in range(1, 24):
    p = os.path.join(rsrc_dir, f"CODE_{cid}.bin")
    if not os.path.exists(p):
        continue
    with open(p, "rb") as f:
        data = f.read()
    # Search for 0x01c2 (450) or 0x01c3 (451)
    hits_450 = [i for i in range(0, len(data)-1, 2) if struct.unpack(">H", data[i:i+2])[0] in range(450, 470)]
    print(f"CODE_{cid:2d} ({len(data):5d} bytes): {len(hits_450)} hits in 450..469")
