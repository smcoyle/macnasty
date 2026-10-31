import os
import re

dis_dir = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\disasm"

with open(os.path.join(dis_dir, "CODE_05.txt"), "r", encoding="utf-8") as f:
    c5 = f.read()

funcs = c5.split("LINK    A6,#0")
print("=== PUBLIC FACTS (CODE_05) ===")
for idx, fn in enumerate(funcs[2:46]): # skip header and copyright
    cid = 700 + idx
    strs = re.findall(r"pstr='([^']*)'", fn)
    print(f"  {cid}: {' | '.join(strs)}")
