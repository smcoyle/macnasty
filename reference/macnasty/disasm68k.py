import struct
import sys

MAC_TRAPS = {
    0xA850: "_InitCursor",
    0xA851: "_SetCursor",
    0xA852: "_HideCursor",
    0xA853: "_ShowCursor",
    0xA86E: "_InitGraf",
    0xA873: "_SetPort",
    0xA874: "_GetPort",
    0xA884: "_DrawString",
    0xA885: "_DrawText",
    0xA887: "_TextFont",
    0xA888: "_TextFace",
    0xA88A: "_TextSize",
    0xA893: "_MoveTo",
    0xA894: "_Move",
    0xA8A1: "_FrameRect",
    0xA8A2: "_PaintRect",
    0xA8A3: "_EraseRect",
    0xA8A4: "_InverRect",
    0xA8A5: "_FillRect",
    0xA8FE: "_InitFonts",
    0xA912: "_InitWindows",
    0xA913: "_NewWindow",
    0xA914: "_DisposeWindow",
    0xA915: "_ShowWindow",
    0xA916: "_HideWindow",
    0xA91F: "_SelectWindow",
    0xA92D: "_CloseWindow",
    0xA930: "_InitMenus",
    0xA931: "_NewMenu",
    0xA933: "_AppendMenu",
    0xA934: "_ClearMenuBar",
    0xA935: "_InsertMenu",
    0xA937: "_DrawMenuBar",
    0xA938: "_HiliteMenu",
    0xA93D: "_MenuSelect",
    0xA93E: "_MenuKey",
    0xA94B: "_PlotIcon",
    0xA954: "_NewControl",
    0xA955: "_DisposeControl",
    0xA956: "_KillControls",
    0xA957: "_ShowControl",
    0xA958: "_HideControl",
    0xA959: "_MoveControl",
    0xA960: "_GetCtlValue",
    0xA962: "_GetCRefCon",
    0xA963: "_SetCtlValue",
    0xA966: "_TestControl",
    0xA967: "_DragControl",
    0xA968: "_TrackControl",
    0xA969: "_DrawControls",
    0xA96C: "_FindControl",
    0xA970: "_GetNextEvent",
    0xA971: "_EventAvail",
    0xA972: "_GetMouse",
    0xA973: "_StillDown",
    0xA974: "_Button",
    0xA975: "_TickCount",
    0xA97B: "_InitDialogs",
    0xA97C: "_GetNewDialog",
    0xA97D: "_NewDialog",
    0xA97E: "_SelIText",
    0xA97F: "_IsDialogEvent",
    0xA980: "_DialogSelect",
    0xA982: "_CloseDialog",
    0xA983: "_DisposDialog",
    0xA985: "_Alert",
    0xA986: "_StopAlert",
    0xA987: "_NoteAlert",
    0xA988: "_CautionAlert",
    0xA98B: "_ParamText",
    0xA98D: "_GetDItem",
    0xA98E: "_SetDItem",
    0xA98F: "_SetIText",
    0xA990: "_GetIText",
    0xA991: "_ModalDialog",
    0xA994: "_CurResFile",
    0xA99B: "_SetResLoad",
    0xA9A0: "_GetResource",
    0xA9A1: "_GetNamedResource",
    0xA9A2: "_LoadResource",
    0xA9A3: "_ReleaseResource",
    0xA9B2: "_SystemEdit",
    0xA9B3: "_SystemTask",
    0xA9B4: "_SystemEvent",
    0xA9B6: "_OpenDeskAcc",
    0xA9BD: "_GetNewWindow",
    0xA9BE: "_GetNewControl",
    0xA9BF: "_GetRMenu",
    0xA9C6: "_SecondsToDate",
    0xA9C8: "_SysBeep",
    0xA9C9: "_SysError",
    0xA861: "_Random",
    0xA9F0: "_LoadSeg",
    0xA9F4: "_ExitToShell",
}

def parse_jump_table(code0: bytes):
    above_a5, below_a5, jt_len, jt_off = struct.unpack(">IIII", code0[:16])
    jt = code0[16:]
    entries = {}
    # Each jump table entry is 8 bytes:
    # Unloaded: <seg_offset: u16> 3F3C <seg_id: u16> A9F0 (_LoadSeg)
    for off in range(0, len(jt), 8):
        if off + 8 > len(jt):
            break
        seg_off, push_op, seg_id, trap = struct.unpack(">HHHH", jt[off:off+8])
        a5_disp = jt_off + off + 2
        entries[a5_disp] = (seg_id, seg_off + 4)  # +4 for CODE segment header
    return above_a5, below_a5, jt_off, entries

def s16(v):
    return v - 0x10000 if v >= 0x8000 else v

def s8(v):
    return v - 0x100 if v >= 0x80 else v

def disasm_ea(data, pc, mode, reg, size_bytes, jt_entries=None):
    if mode == 0:
        return f"D{reg}", pc
    elif mode == 1:
        return f"A{reg}", pc
    elif mode == 2:
        return f"(A{reg})", pc
    elif mode == 3:
        return f"(A{reg})+", pc
    elif mode == 4:
        return f"-(A{reg})", pc
    elif mode == 5:
        if pc + 2 > len(data):
            return "??(A?)", pc
        disp = s16(struct.unpack(">H", data[pc:pc+2])[0])
        if reg == 5 and jt_entries and disp in jt_entries:
            seg_id, seg_off = jt_entries[disp]
            return f"{disp}(A5) [CODE_{seg_id}+{seg_off:#x}]", pc + 2
        return f"{disp}(A{reg})", pc + 2
    elif mode == 6:
        if pc + 2 > len(data):
            return "??(A?,X)", pc
        ext = struct.unpack(">H", data[pc:pc+2])[0]
        da = "A" if (ext & 0x8000) else "D"
        xreg = (ext >> 12) & 7
        wl = ".L" if (ext & 0x0800) else ".W"
        disp = s8(ext & 0xFF)
        return f"{disp}(A{reg},{da}{xreg}{wl})", pc + 2
    elif mode == 7:
        if reg == 0:
            w = s16(struct.unpack(">H", data[pc:pc+2])[0])
            return f"({w:#x}).W", pc + 2
        elif reg == 1:
            l = struct.unpack(">I", data[pc:pc+4])[0]
            return f"({l:#x}).L", pc + 4
        elif reg == 2:
            disp = s16(struct.unpack(">H", data[pc:pc+2])[0])
            target = pc + disp
            # Check if target points to a Pascal string
            pstr_info = ""
            if 0 <= target < len(data):
                plen = data[target]
                if 1 <= plen <= 80 and target + 1 + plen <= len(data):
                    sub = data[target+1:target+1+plen]
                    if all(32 <= b <= 126 for b in sub):
                        pstr_info = f" ; pstr={sub.decode('mac_roman')!r}"
            return f"{disp}(PC) [{target:#x}{pstr_info}]", pc + 2
        elif reg == 3:
            ext = struct.unpack(">H", data[pc:pc+2])[0]
            da = "A" if (ext & 0x8000) else "D"
            xreg = (ext >> 12) & 7
            wl = ".L" if (ext & 0x0800) else ".W"
            disp = s8(ext & 0xFF)
            target = pc + disp
            return f"{disp}(PC,{da}{xreg}{wl}) [{target:#x}]", pc + 2
        elif reg == 4:
            if size_bytes == 1:
                v = data[pc + 1]
                return f"#{v:#x} ({s8(v)})", pc + 2
            elif size_bytes == 2:
                v = struct.unpack(">H", data[pc:pc+2])[0]
                return f"#{v:#x} ({s16(v)})", pc + 2
            elif size_bytes == 4:
                v = struct.unpack(">I", data[pc:pc+4])[0]
                return f"#{v:#x}", pc + 4
    return f"<ea {mode}:{reg}>", pc

COND_NAMES = ["T", "F", "HI", "LS", "CC", "CS", "NE", "EQ", "VC", "VS", "PL", "MI", "GE", "LT", "GT", "LE"]

def disasm_segment(data: bytes, jt_entries=None, start_pc=4, end_pc=None):
    if end_pc is None:
        end_pc = len(data)
    pc = start_pc
    lines = []
    while pc < end_pc:
        insn_pc = pc
        if pc + 2 > len(data):
            break
        op = struct.unpack(">H", data[pc:pc+2])[0]
        pc += 2

        top4 = (op >> 12) & 0xF
        if top4 == 0xA:
            tname = MAC_TRAPS.get(op, f"A_TRAP_{op:#06x}")
            lines.append(f"{insn_pc:04x}: {op:04x}        {tname}")
            continue

        # Check embedded Pascal string after RTS/JMP if top bytes look like ASCII or after N^Nu (4E5E 4E75)
        if op == 0x4E56:  # LINK A6,#disp
            disp = s16(struct.unpack(">H", data[pc:pc+2])[0])
            pc += 2
            lines.append(f"\n{insn_pc:04x}: {op:04x}        LINK    A6,#{disp}")
            continue
        elif op == 0x4E5E:
            lines.append(f"{insn_pc:04x}: {op:04x}        UNLK    A6")
            continue
        elif op == 0x4E75:
            lines.append(f"{insn_pc:04x}: {op:04x}        RTS")
            continue
        elif (op & 0xFFF8) == 0x4E50:
            lines.append(f"{insn_pc:04x}: {op:04x}        LINK    A{op&7}")
            continue
        elif (op & 0xFFC0) == 0x4E80:
            ea_str, pc = disasm_ea(data, pc, (op >> 3) & 7, op & 7, 4, jt_entries)
            lines.append(f"{insn_pc:04x}: {op:04x}        JSR     {ea_str}")
            continue
        elif (op & 0xFFC0) == 0x4EC0:
            ea_str, pc = disasm_ea(data, pc, (op >> 3) & 7, op & 7, 4, jt_entries)
            lines.append(f"{insn_pc:04x}: {op:04x}        JMP     {ea_str}")
            continue
        elif (op & 0xFFC0) == 0x4840 and ((op >> 3) & 7) != 0:
            ea_str, pc = disasm_ea(data, pc, (op >> 3) & 7, op & 7, 4, jt_entries)
            lines.append(f"{insn_pc:04x}: {op:04x}        PEA     {ea_str}")
            continue
        elif (op & 0xF1C0) == 0x41C0:
            areg = (op >> 9) & 7
            ea_str, pc = disasm_ea(data, pc, (op >> 3) & 7, op & 7, 4, jt_entries)
            lines.append(f"{insn_pc:04x}: {op:04x}        LEA     {ea_str},A{areg}")
            continue
        elif (op & 0xFF00) == 0x4200 and ((op >> 6) & 3) < 3:
            sz = (op >> 6) & 3
            s_ch = [".B", ".W", ".L"][sz]
            s_b = [1, 2, 4][sz]
            ea_str, pc = disasm_ea(data, pc, (op >> 3) & 7, op & 7, s_b, jt_entries)
            lines.append(f"{insn_pc:04x}: {op:04x}        CLR{s_ch}   {ea_str}")
            continue
        elif (op & 0xFF00) == 0x4A00 and ((op >> 6) & 3) < 3:
            sz = (op >> 6) & 3
            s_ch = [".B", ".W", ".L"][sz]
            s_b = [1, 2, 4][sz]
            ea_str, pc = disasm_ea(data, pc, (op >> 3) & 7, op & 7, s_b, jt_entries)
            lines.append(f"{insn_pc:04x}: {op:04x}        TST{s_ch}   {ea_str}")
            continue
        elif top4 in (1, 2, 3):  # MOVE.B, MOVE.L, MOVE.W
            s_ch = {1: ".B", 3: ".W", 2: ".L"}[top4]
            s_b = {1: 1, 3: 2, 2: 4}[top4]
            src_mode = (op >> 3) & 7
            src_reg = op & 7
            dst_reg = (op >> 9) & 7
            dst_mode = (op >> 6) & 7
            src_str, pc = disasm_ea(data, pc, src_mode, src_reg, s_b, jt_entries)
            dst_str, pc = disasm_ea(data, pc, dst_mode, dst_reg, s_b, jt_entries)
            mnem = "MOVEA" if dst_mode == 1 else "MOVE"
            lines.append(f"{insn_pc:04x}: {op:04x}        {mnem}{s_ch}  {src_str},{dst_str}")
            continue
        elif top4 == 7 and (op & 0x0100) == 0:  # MOVEQ
            dreg = (op >> 9) & 7
            imm = s8(op & 0xFF)
            lines.append(f"{insn_pc:04x}: {op:04x}        MOVEQ   #{imm},D{dreg}")
            continue
        elif top4 == 6:  # Bcc / BRA / BSR
            cond = (op >> 8) & 0xF
            disp8 = op & 0xFF
            if disp8 == 0:
                if pc + 2 > len(data):
                    lines.append(f"{insn_pc:04x}: {op:04x}        DC.W    {op:#06x}")
                    continue
                disp = s16(struct.unpack(">H", data[pc:pc+2])[0])
                pc += 2
            else:
                disp = s8(disp8)
            target = (insn_pc + 2) + disp
            cname = "BRA" if cond == 0 else ("BSR" if cond == 1 else f"B{COND_NAMES[cond]}")
            lines.append(f"{insn_pc:04x}: {op:04x}        {cname}     {target:#06x}")
            continue
        elif top4 == 5:  # ADDQ / SUBQ / Scc / DBcc
            if ((op >> 6) & 3) == 3:
                if ((op >> 3) & 7) == 1 and pc + 2 <= len(data):
                    cond = (op >> 8) & 0xF
                    disp = s16(struct.unpack(">H", data[pc:pc+2])[0])
                    pc += 2
                    target = (insn_pc + 2) + disp
                    lines.append(f"{insn_pc:04x}: {op:04x}        DB{COND_NAMES[cond]}   D{op&7},{target:#06x}")
                else:
                    cond = (op >> 8) & 0xF
                    ea_str, pc = disasm_ea(data, pc, (op >> 3) & 7, op & 7, 1, jt_entries)
                    lines.append(f"{insn_pc:04x}: {op:04x}        S{COND_NAMES[cond]}     {ea_str}")
            else:
                q = (op >> 9) & 7
                if q == 0:
                    q = 8
                sz = (op >> 6) & 3
                s_ch = [".B", ".W", ".L"][sz]
                s_b = [1, 2, 4][sz]
                mn = "SUBQ" if (op & 0x0100) else "ADDQ"
                ea_str, pc = disasm_ea(data, pc, (op >> 3) & 7, op & 7, s_b, jt_entries)
                lines.append(f"{insn_pc:04x}: {op:04x}        {mn}{s_ch}  #{q},{ea_str}")
            continue
        elif top4 in (0xD, 0x9, 0xB, 0xC, 0x8):  # ADD, SUB, CMP/EOR, AND/MUL, OR/DIV
            reg = (op >> 9) & 7
            opmode = (op >> 6) & 7
            mode = (op >> 3) & 7
            r = op & 7
            base_mn = {0xD: "ADD", 0x9: "SUB", 0xB: "CMP", 0xC: "AND", 0x8: "OR"}[top4]
            if opmode in (3, 7) and top4 in (0xD, 0x9, 0xB):
                s_ch = ".W" if opmode == 3 else ".L"
                s_b = 2 if opmode == 3 else 4
                ea_str, pc = disasm_ea(data, pc, mode, r, s_b, jt_entries)
                lines.append(f"{insn_pc:04x}: {op:04x}        {base_mn}A{s_ch}  {ea_str},A{reg}")
                continue
            elif opmode == 3 and top4 in (0xC, 0x8):
                mn = "MULU" if top4 == 0xC else "DIVU"
                ea_str, pc = disasm_ea(data, pc, mode, r, 2, jt_entries)
                lines.append(f"{insn_pc:04x}: {op:04x}        {mn}    {ea_str},D{reg}")
                continue
            elif opmode == 7 and top4 in (0xC, 0x8):
                mn = "MULS" if top4 == 0xC else "DIVS"
                ea_str, pc = disasm_ea(data, pc, mode, r, 2, jt_entries)
                lines.append(f"{insn_pc:04x}: {op:04x}        {mn}    {ea_str},D{reg}")
                continue
            elif (opmode & 3) < 3:
                sz = opmode & 3
                s_ch = [".B", ".W", ".L"][sz]
                s_b = [1, 2, 4][sz]
                ea_str, pc = disasm_ea(data, pc, mode, r, s_b, jt_entries)
                if opmode < 3:
                    lines.append(f"{insn_pc:04x}: {op:04x}        {base_mn}{s_ch}   {ea_str},D{reg}")
                else:
                    mn = "EOR" if top4 == 0xB else base_mn
                    lines.append(f"{insn_pc:04x}: {op:04x}        {mn}{s_ch}   D{reg},{ea_str}")
                continue
        elif top4 == 0:  # Immediate ops: ORI, ANDI, SUBI, ADDI, EORI, CMPI, BTST
            subop = (op >> 8) & 0xF
            sz = (op >> 6) & 3
            if subop in (0x0, 0x2, 0x4, 0x6, 0xA, 0xC) and sz < 3:
                mn = {0x0: "ORI", 0x2: "ANDI", 0x4: "SUBI", 0x6: "ADDI", 0xA: "EORI", 0xC: "CMPI"}[subop]
                s_ch = [".B", ".W", ".L"][sz]
                s_b = [1, 2, 4][sz]
                imm_str, pc = disasm_ea(data, pc, 7, 4, s_b, jt_entries)
                ea_str, pc = disasm_ea(data, pc, (op >> 3) & 7, op & 7, s_b, jt_entries)
                lines.append(f"{insn_pc:04x}: {op:04x}        {mn}{s_ch}  {imm_str},{ea_str}")
                continue

        lines.append(f"{insn_pc:04x}: {op:04x}        DC.W    {op:#06x}")
    return "\n".join(lines)

if __name__ == "__main__":
    rdir = "reference/macnasty/rsrc_dump"
    code0 = open(f"{rdir}/CODE_0.bin", "rb").read()
    above_a5, below_a5, jt_off, jt_entries = parse_jump_table(code0)
    seg_id = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    seg_data = open(f"{rdir}/CODE_{seg_id}.bin", "rb").read()
    print(disasm_segment(seg_data, jt_entries))
