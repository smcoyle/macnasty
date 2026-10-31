import os
import struct

def parse_mac_resource_fork(rsrc_path: str, out_dir: str):
    data = open(rsrc_path, "rb").read()
    print(f"Resource fork file: {rsrc_path}, size={len(data)} bytes")
    data_off, map_off, data_len, map_len = struct.unpack(">IIII", data[:16])
    print(f"  data_off={data_off:#x}, map_off={map_off:#x}, data_len={data_len}, map_len={map_len}")
    assert map_off + map_len <= len(data), f"Truncated resource fork! Needed {map_off + map_len}, got {len(data)}"

    rmap = data[map_off:map_off + map_len]
    type_list_off, name_list_off, num_types_minus_1 = struct.unpack(">HHH", rmap[24:30])
    num_types = (num_types_minus_1 + 1) & 0xFFFF
    print(f"  type_list_off={type_list_off:#x}, name_list_off={name_list_off:#x}, num_types={num_types}")

    os.makedirs(out_dir, exist_ok=True)
    resources = []

    for i in range(num_types):
        toff = type_list_off + 2 + i * 8
        rtype = rmap[toff:toff + 4].decode("mac_roman", errors="replace")
        rcount_minus_1, ref_list_off = struct.unpack(">HH", rmap[toff + 4:toff + 8])
        rcount = rcount_minus_1 + 1
        print(f"  Type {rtype!r}: {rcount} resource(s)")
        for j in range(rcount):
            roff = type_list_off + ref_list_off + j * 12
            rid, name_off, attrs_and_doff = struct.unpack(">hhI", rmap[roff:roff + 8])
            rattrs = (attrs_and_doff >> 24) & 0xFF
            rdoff = attrs_and_doff & 0x00FFFFFF
            if name_off != -1:
                noff = name_list_off + name_off
                nlen = rmap[noff]
                rname = rmap[noff + 1:noff + 1 + nlen].decode("mac_roman", errors="replace")
            else:
                rname = ""
            abs_doff = data_off + rdoff
            rlen = struct.unpack(">I", data[abs_doff:abs_doff + 4])[0]
            rbytes = data[abs_doff + 4:abs_doff + 4 + rlen]
            print(f"    ID={rid:6d} attrs={rattrs:#04x} len={rlen:6d} name={rname!r}")
            resources.append((rtype, rid, rname, rattrs, rbytes))
            safe_type = "".join(c if c.isalnum() or c in "_-" else f"_{ord(c):02x}" for c in rtype)
            safe_name = "".join(c if c.isalnum() or c in " ._-()" else "_" for c in rname).strip()
            fname = f"{safe_type}_{rid}_{safe_name}.bin" if safe_name else f"{safe_type}_{rid}.bin"
            with open(os.path.join(out_dir, fname), "wb") as f:
                f.write(rbytes)

    return resources

if __name__ == "__main__":
    parse_mac_resource_fork("reference/macnasty/extracted/MacNasty_.rsrc", "reference/macnasty/rsrc_dump")
    parse_mac_resource_fork("reference/macnasty/extracted/ReadMe.1st.rsrc", "reference/macnasty/readme_rsrc")
