import glob
import os
import re
import struct

def inspect_code_segments():
    rdir = "reference/macnasty/rsrc_dump"
    code0 = open(f"{rdir}/CODE_0.bin", "rb").read()
    above_a5, below_a5, jt_len, jt_off = struct.unpack(">IIII", code0[:16])
    print(f"CODE 0: above_a5={above_a5:#x} ({above_a5}), below_a5={below_a5:#x} ({below_a5}), jt_len={jt_len}, jt_off={jt_off:#x}")

    for cid in range(1, 24):
        cpath = f"{rdir}/CODE_{cid}.bin"
        data = open(cpath, "rb").read()
        print(f"\n================ CODE {cid} ({len(data)} bytes) ================")
        # Extract printable ASCII/MacRoman strings (both Pascal strings and C strings)
        for m in re.finditer(rb"[\x20-\x7e]{4,}", data):
            s = m.group(0).decode("mac_roman", errors="replace")
            off = m.start()
            # Check if preceded by a length byte matching len(s)
            plen = data[off - 1] if off > 0 else -1
            print(f"  {off:#06x} (plen={plen}): {s!r}")

if __name__ == "__main__":
    inspect_code_segments()
