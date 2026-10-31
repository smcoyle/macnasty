import json

with open(r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\chars_db.json", encoding="utf-8") as f:
    db = json.load(f)

with open(r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\rust_chars_table.inc", "w", encoding="utf-8") as f:
    f.write("pub const CHARS_DB: [CharRecord; 44] = [\n")
    for cid in range(700, 744):
        c = db[str(cid)]
        pl = c["public_lines"]
        l0 = pl[0] if len(pl) > 0 else ""
        l1 = pl[1] if len(pl) > 1 else ""
        l2 = pl[2] if len(pl) > 2 else ""
        f.write(
            f"    CharRecord {{ id: {cid}, name: {json.dumps(c['name'])}, spouse_id: {c['spouse_id']}, "
            f"cat: {c['cat']}, vuln_blackmail: {str(bool(c['vuln_blackmail'])).lower()}, "
            f"secret_id: {c['secret_id']}, secret_str: {json.dumps(c['secret_str'])}, "
            f"vuln_money: {str(bool(c['vuln_money'])).lower()}, vuln_favors: {str(bool(c['vuln_favors'])).lower()}, "
            f"has_affair: {str(bool(c['has_affair'])).lower()}, lover_id: {c['lover_id']}, "
            f"lover_name: {json.dumps(c['lover_name'])}, rumor_id: {c['rumor_id']}, "
            f"rumor_str: {json.dumps(c['rumor_str'])}, rep_id: {c['rep_id']}, "
            f"rep_str: {json.dumps(c['rep_str'])}, vuln_charm: {str(bool(c['vuln_charm'])).lower()}, "
            f"vuln_spouse_sec: {str(bool(c['vuln_spouse_sec'])).lower()}, "
            f"pub_lines: [{json.dumps(l0)}, {json.dumps(l1)}, {json.dumps(l2)}] }},\n"
        )
    f.write("];\n")

print("Generated rust_chars_table.inc successfully.")
