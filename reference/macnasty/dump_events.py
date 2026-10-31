import os
import re

dis_dir = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\disasm"

for cid in [15, 16, 17, 20, 21, 22, 23]:
    with open(os.path.join(dis_dir, f"CODE_{cid:02d}.txt"), "r", encoding="utf-8") as f:
        text = f.read()
    funcs = text.split("LINK    A6,")
    print(f"================ CODE_{cid:02d} ({len(funcs)-1} funcs) ================")
    for idx, fn in enumerate(funcs[1:], 1):
        lines = fn.splitlines()
        header = lines[0] if lines else ""
        # find address of LINK A6 from end of previous chunk
        prev_lines = funcs[idx-1].splitlines()
        addr = prev_lines[-1].split(":")[0] if prev_lines else "????"
        strs = re.findall(r"pstr='([^']*)'", fn)
        if strs:
            print(f"  Func #{idx:2d} @ 0x{addr}:")
            for s in strs:
                print(f"    {repr(s)}")
