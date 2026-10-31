import struct
import zlib

RANDOMIZATION_TABLE = [
    0xee,  0x56,  0xf8,  0xc3,  0x9d,  0x9f,  0xae,  0x2c,
    0xad,  0xcd,  0x24,  0x9d,  0xa6, 0x101,  0x18,  0xb9,
    0xa1,  0x82,  0x75,  0xe9,  0x9f,  0x55,  0x66,  0x6a,
    0x86,  0x71,  0xdc,  0x84,  0x56,  0x96,  0x56,  0xa1,
    0x84,  0x78,  0xb7,  0x32,  0x6a,   0x3,  0xe3,   0x2,
    0x11, 0x101,   0x8,  0x44,  0x83, 0x100,  0x43,  0xe3,
    0x1c,  0xf0,  0x86,  0x6a,  0x6b,   0xf,   0x3,  0x2d,
    0x86,  0x17,  0x7b,  0x10,  0xf6,  0x80,  0x78,  0x7a,
    0xa1,  0xe1,  0xef,  0x8c,  0xf6,  0x87,  0x4b,  0xa7,
    0xe2,  0x77,  0xfa,  0xb8,  0x81,  0xee,  0x77,  0xc0,
    0x9d,  0x29,  0x20,  0x27,  0x71,  0x12,  0xe0,  0x6b,
    0xd1,  0x7c,   0xa,  0x89,  0x7d,  0x87,  0xc4, 0x101,
    0xc1,  0x31,  0xaf,  0x38,   0x3,  0x68,  0x1b,  0x76,
    0x79,  0x3f,  0xdb,  0xc7,  0x1b,  0x36,  0x7b,  0xe2,
    0x63,  0x81,  0xee,   0xc,  0x63,  0x8b,  0x78,  0x38,
    0x97,  0x9b,  0xd7,  0x8f,  0xdd,  0xf2,  0xa3,  0x77,
    0x8c,  0xc3,  0x39,  0x20,  0xb3,  0x12,  0x11,   0xe,
    0x17,  0x42,  0x80,  0x2c,  0xc4,  0x92,  0x59,  0xc8,
    0xdb,  0x40,  0x76,  0x64,  0xb4,  0x55,  0x1a,  0x9e,
    0xfe,  0x5f,   0x6,  0x3c,  0x41,  0xef,  0xd4,  0xaa,
    0x98,  0x29,  0xcd,  0x1f,   0x2,  0xa8,  0x87,  0xd2,
    0xa0,  0x93,  0x98,  0xef,   0xc,  0x43,  0xed,  0x9d,
    0xc2,  0xeb,  0x81,  0xe9,  0x64,  0x23,  0x68,  0x1e,
    0x25,  0x57,  0xde,  0x9a,  0xcf,  0x7f,  0xe5,  0xba,
    0x41,  0xea,  0xea,  0x36,  0x1a,  0x28,  0x79,  0x20,
    0x5e,  0x18,  0x4e,  0x7c,  0x8e,  0x58,  0x7a,  0xef,
    0x91,   0x2,  0x93,  0xbb,  0x56,  0xa1,  0x49,  0x1b,
    0x79,  0x92,  0xf3,  0x58,  0x4f,  0x52,  0x9c,   0x2,
    0x77,  0xaf,  0x2a,  0x8f,  0x49,  0xd0,  0x99,  0x4d,
    0x98, 0x101,  0x60,  0x93, 0x100,  0x75,  0x31,  0xce,
    0x49,  0x20,  0x56,  0x57,  0xe2,  0xf5,  0x26,  0x2b,
    0x8a,  0xbf,  0xde,  0xd0,  0x83,  0x34,  0xf4,  0x17
]

class BitReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.bitbuf = 0
        self.bits = 0

    def next_bit(self) -> int:
        if self.bits == 0:
            if self.pos < len(self.data):
                self.bitbuf = self.data[self.pos]
                self.pos += 1
            else:
                self.bitbuf = 0
            self.bits = 8
        self.bits -= 1
        return (self.bitbuf >> self.bits) & 1

    def next_bits(self, n: int) -> int:
        v = 0
        for _ in range(n):
            v = (v << 1) | self.next_bit()
        return v

class ArithmeticModel:
    def __init__(self, first_sym: int, last_sym: int, increment: int, freq_limit: int):
        self.increment = increment
        self.freq_limit = freq_limit
        self.num_symbols = last_sym - first_sym + 1
        self.symbols = list(range(first_sym, last_sym + 1))
        self.reset()

    def reset(self):
        self.total_freq = self.increment * self.num_symbols
        self.freqs = [self.increment] * self.num_symbols

    def increase_freq(self, idx: int):
        self.freqs[idx] += self.increment
        self.total_freq += self.increment
        if self.total_freq > self.freq_limit:
            total = 0
            for i in range(self.num_symbols):
                f = (self.freqs[i] + 1) >> 1
                self.freqs[i] = f
                total += f
            self.total_freq = total

class ArithmeticDecoder:
    NUM_BITS = 26
    ONE = 1 << (NUM_BITS - 1)
    HALF = 1 << (NUM_BITS - 2)

    def __init__(self, reader: BitReader):
        self.reader = reader
        self.range = self.ONE
        self.code = reader.next_bits(self.NUM_BITS)

    def next_symbol(self, model: ArithmeticModel) -> int:
        renorm = self.range // model.total_freq
        freq = self.code // renorm
        cum = 0
        n = 0
        limit = model.num_symbols - 1
        freqs = model.freqs
        while n < limit:
            if cum + freqs[n] > freq:
                break
            cum += freqs[n]
            n += 1
        sym_size = freqs[n]
        low_incr = renorm * cum
        self.code -= low_incr
        if cum + sym_size == model.total_freq:
            self.range -= low_incr
        else:
            self.range = sym_size * renorm
        while self.range <= self.HALF:
            self.range <<= 1
            self.code = (self.code << 1) | self.reader.next_bit()
        model.increase_freq(n)
        return model.symbols[n]

    def next_bit_string(self, model: ArithmeticModel, bits: int) -> int:
        res = 0
        for i in range(bits):
            if self.next_symbol(model):
                res |= 1 << i
        return res

def decode_arsenic(comp_data: bytes, expected_len: int) -> bytes:
    reader = BitReader(comp_data)
    dec = ArithmeticDecoder(reader)
    initial_model = ArithmeticModel(0, 1, 1, 256)
    selector_model = ArithmeticModel(0, 10, 8, 1024)
    mtf_models = [
        ArithmeticModel(2, 3, 8, 1024),
        ArithmeticModel(4, 7, 4, 1024),
        ArithmeticModel(8, 15, 4, 1024),
        ArithmeticModel(16, 31, 4, 1024),
        ArithmeticModel(32, 63, 2, 1024),
        ArithmeticModel(64, 127, 2, 1024),
        ArithmeticModel(128, 255, 1, 1024),
    ]

    m0 = dec.next_bit_string(initial_model, 8)
    m1 = dec.next_bit_string(initial_model, 8)
    assert m0 == ord('A') and m1 == ord('s'), f"Bad Arsenic magic: {m0:#x} {m1:#x}"

    block_bits = dec.next_bit_string(initial_model, 4) + 9
    block_size = 1 << block_bits
    end_of_blocks = dec.next_symbol(initial_model)

    out = bytearray()
    comp_crc = 0

    while not end_of_blocks and len(out) < expected_len:
        mtf = list(range(256))
        randomized = dec.next_symbol(initial_model)
        transform_index = dec.next_bit_string(initial_model, block_bits)
        block = bytearray()

        while True:
            sel = dec.next_symbol(selector_model)
            if sel == 0 or sel == 1:
                zero_state = 1
                zero_count = 0
                while sel < 2:
                    if sel == 0:
                        zero_count += zero_state
                    else:
                        zero_count += 2 * zero_state
                    zero_state <<= 1
                    sel = dec.next_symbol(selector_model)
                b0 = mtf[0]
                block.extend([b0] * zero_count)

            if sel == 10:
                break
            elif sel == 2:
                symbol = 1
            else:
                symbol = dec.next_symbol(mtf_models[sel - 3])

            val = mtf.pop(symbol)
            mtf.insert(0, val)
            block.append(val)

        num_bytes = len(block)
        selector_model.reset()
        for m in mtf_models:
            m.reset()

        if dec.next_symbol(initial_model):
            comp_crc = dec.next_bit_string(initial_model, 32)
            end_of_blocks = 1

        # Inverse BWT
        counts = [0] * 256
        for b in block:
            counts[b] += 1
        cum = [0] * 256
        total = 0
        for i in range(256):
            cum[i] = total
            total += counts[i]
        transform = [0] * num_bytes
        for i, b in enumerate(block):
            transform[cum[b]] = i
            cum[b] += 1

        byte_count = 0
        count = 0
        last = 0
        rand_index = 0
        rand_count = RANDOMIZATION_TABLE[0]
        repeat = 0

        while byte_count < num_bytes or repeat > 0:
            if repeat > 0:
                repeat -= 1
                out.append(last)
                continue

            transform_index = transform[transform_index]
            byte = block[transform_index]
            if randomized and rand_count == byte_count:
                byte ^= 1
                rand_index = (rand_index + 1) & 255
                rand_count += RANDOMIZATION_TABLE[rand_index]
            byte_count += 1

            if count == 4:
                count = 0
                if byte == 0:
                    continue
                repeat = byte - 1
                out.append(last)
            else:
                if byte == last:
                    count += 1
                else:
                    count = 1
                    last = byte
                out.append(byte)

    calc_crc = zlib.crc32(out) & 0xFFFFFFFF
    print(f"Decoded {len(out)} bytes (expected {expected_len}), calc_crc={calc_crc:#010x}, comp_crc={comp_crc:#010x}")
    assert calc_crc == comp_crc, "CRC mismatch!"
    return bytes(out)

if __name__ == "__main__":
    raw = open("reference/macnasty/SoftShoppe5691.img.sit", "rb").read()
    # Entry compressed streams at 0xE9 (rsrc) and 0x1EA (data)
    rsrc_comp = raw[0xE9 : 0xE9 + 0x101]
    data_comp = raw[0x1EA : 0x1EA + 0x02272D]
    rsrc = decode_arsenic(rsrc_comp, 0x185)
    data = decode_arsenic(data_comp, 0x0C8054)
    open("reference/macnasty/SoftShoppe5691.img.rsrc", "wb").write(rsrc)
    open("reference/macnasty/SoftShoppe5691.img", "wb").write(data)
    print("Successfully unpacked SoftShoppe5691.img!")
