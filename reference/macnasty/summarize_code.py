import os
import re

dis_dir = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\disasm"

for cid in range(1, 24):
    p = os.path.join(dis_dir, f"CODE_{cid:02d}.txt")
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    pstrs = re.findall(r"pstr='([^']*)'", text)
    # deduplicate preserving order
    seen = set()
    uniq = []
    for s in pstrs:
        if s not in seen and s != "Copyright 1987 by George Lott":
            seen.add(s)
            uniq.append(s)
    print(f"=== CODE_{cid:02d} ({len(uniq)} unique strings) ===")
    for s in uniq[:15]:
        print(f"  - {repr(s)}")
    if len(uniq) > 15:
        print(f"  ... ({len(uniq) - 15} more)")
