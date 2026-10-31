import os
import struct

def read_hfs_volume(img_path: str):
    raw = open(img_path, "rb").read()
    hfs = raw[84:84 + 819200]
    mdb = hfs[1024:1536]
    sig, cr_date, ls_mod, atrb, nm_fls, vbm_st, alloc_ptr, nm_al_blks, al_blk_siz, clp_siz, al_bl_st, nxt_cnid, free_bks = struct.unpack(
        ">2sIIHHHHHIIHHI", mdb[:36]
    )
    vol_name_len = mdb[36]
    vol_name = mdb[37:37 + vol_name_len].decode("mac_roman", errors="replace")
    print(f"HFS Volume: {vol_name!r}, sig={sig}, al_blk_siz={al_blk_siz}, al_bl_st={al_bl_st}, nm_al_blks={nm_al_blks}")

    # Extents overflow and Catalog file extents in MDB:
    # Offset 128 (0x80): drXTFlSize (4), drXTExtRec (12 bytes: 3 * (start_ablk: u16, num_ablks: u16))
    # Offset 144 (0x90): drCTFlSize (4), drCTExtRec (12 bytes: 3 * (start_ablk: u16, num_ablks: u16))
    xt_size = struct.unpack(">I", mdb[130:134])[0]
    xt_ext = struct.unpack(">HHHHHH", mdb[134:146])
    ct_size = struct.unpack(">I", mdb[146:150])[0]
    ct_ext = struct.unpack(">HHHHHH", mdb[150:162])
    print(f"Catalog size={ct_size}, extents={ct_ext}")

    def read_extents(ext_tuple, logical_size):
        out = bytearray()
        for i in range(0, 6, 2):
            st, cnt = ext_tuple[i], ext_tuple[i + 1]
            if cnt == 0:
                break
            byte_off = al_bl_st * 512 + st * al_blk_siz
            byte_len = cnt * al_blk_siz
            out.extend(hfs[byte_off:byte_off + byte_len])
        return bytes(out[:logical_size])

    cat_data = read_extents(ct_ext, ct_size)
    num_nodes = len(cat_data) // 512
    print(f"Catalog nodes: {num_nodes}")

    files = []
    folders = {}

    for node_idx in range(num_nodes):
        node = cat_data[node_idx * 512:(node_idx + 1) * 512]
        f_link, b_link, kind, height, num_recs, _ = struct.unpack(">IIbbHH", node[:14])
        if kind != -1:  # -1 (0xFF) is leaf node in HFS B-tree
            continue
        for rec_idx in range(num_recs):
            rec_off = struct.unpack(">H", node[512 - (rec_idx + 1) * 2:512 - rec_idx * 2])[0]
            key_len = node[rec_off]
            if key_len == 0:
                continue
            par_id = struct.unpack(">I", node[rec_off + 2:rec_off + 6])[0]
            cname_len = node[rec_off + 6]
            cname = node[rec_off + 7:rec_off + 7 + cname_len].decode("mac_roman", errors="replace")
            # Data starts after key_len + 1, aligned to even byte offset
            val_off = rec_off + 1 + key_len
            if val_off & 1:
                val_off += 1
            rec_type = node[val_off]
            if rec_type == 1:  # Folder record
                folder_id = struct.unpack(">I", node[val_off + 6:val_off + 10])[0]
                folders[folder_id] = (par_id, cname)
                print(f"  [DIR] id={folder_id} par={par_id} name={cname!r}")
            elif rec_type == 2:  # File record
                f_type = node[val_off + 4:val_off + 8].decode("mac_roman", errors="replace")
                f_creator = node[val_off + 8:val_off + 12].decode("mac_roman", errors="replace")
                file_id = struct.unpack(">I", node[val_off + 20:val_off + 24])[0]
                data_lsize, data_psize = struct.unpack(">II", node[val_off + 26:val_off + 34])
                rsrc_lsize, rsrc_psize = struct.unpack(">II", node[val_off + 36:val_off + 44])
                data_ext = struct.unpack(">HHHHHH", node[val_off + 74:val_off + 86])
                rsrc_ext = struct.unpack(">HHHHHH", node[val_off + 86:val_off + 98])
                print(
                    f"  [FILE] id={file_id} par={par_id} name={cname!r} type={f_type!r}/{f_creator!r} "
                    f"data={data_lsize}B rsrc={rsrc_lsize}B"
                )
                data_bytes = read_extents(data_ext, data_lsize)
                rsrc_bytes = read_extents(rsrc_ext, rsrc_lsize)
                files.append((par_id, cname, f_type, f_creator, data_bytes, rsrc_bytes))

    os.makedirs("reference/macnasty/extracted", exist_ok=True)
    for par_id, cname, f_type, f_creator, data_bytes, rsrc_bytes in files:
        safe_name = "".join(c if c.isalnum() or c in " ._-()" else "_" for c in cname).strip()
        if data_bytes:
            with open(f"reference/macnasty/extracted/{safe_name}.data", "wb") as f:
                f.write(data_bytes)
        if rsrc_bytes:
            with open(f"reference/macnasty/extracted/{safe_name}.rsrc", "wb") as f:
                f.write(rsrc_bytes)

if __name__ == "__main__":
    read_hfs_volume("reference/macnasty/SoftShoppe5691.img")
