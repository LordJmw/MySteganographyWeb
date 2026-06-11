"""
Fungsi-fungsi utilitas steganografi
"""


def text_to_bits(text: str) -> str:
    """Mengkonversi teks ke biner (8-bit per karakter)"""
    bits = ''
    for char in text:
        bits += format(ord(char), '08b')
    return bits


def bits_to_text(bits: str) -> str:
    """Mengkonversi biner ke teks"""
    text = ''
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) == 8:
            text += chr(int(byte, 2))
    return text


def xor_bits(bits1: str, bits2: str) -> str:
    """
    XOR dua string biner.
    Kedua string HARUS sama panjang - dipotong ke panjang minimum jika tidak.
    """
    min_len = min(len(bits1), len(bits2))
    bits1 = bits1[:min_len]
    bits2 = bits2[:min_len]
    return ''.join('1' if bits1[i] != bits2[i] else '0' for i in range(min_len))


def generate_password_bits(first_name: str, last_name: str, length: int) -> str:
    """
    Menghasilkan password bits dari nama untuk XOR, tepat sepanjang 'length' bit.
    Menggunakan 3 huruf terakhir nama belakang, diulang jika perlu.
    """
    last_3 = last_name[-3:].lower()
    if len(last_3) < 3:
        last_3 = last_3.rjust(3, 'x')

    # 24 bit dasar dari 3 karakter
    base_bits = ''
    for char in last_3:
        base_bits += format(ord(char), '08b')

    # Ulang sampai >= length, lalu potong tepat
    if len(base_bits) < length:
        repeat = (length // len(base_bits)) + 1
        base_bits = (base_bits * repeat)

    return base_bits[:length]


def get_channel_mask(s1_value: int) -> tuple:
    """Mengembalikan mask channel (R, G, B) aktif berdasarkan nilai S1"""
    channel_map = {
        0: (True, False, False),   # R
        1: (False, True, False),   # G
        2: (False, False, True),   # B
        3: (True, True, False),    # RG
        4: (True, False, True),    # RB
        5: (False, True, True),    # GB
        6: (True, True, True),     # RGB
    }
    return channel_map.get(s1_value, (True, True, True))


def embed_lsb(value: int, bits_to_embed: str, num_bits: int) -> int:
    """Menyisipkan bit ke LSB nilai piksel"""
    if num_bits <= 0 or num_bits > 8:
        return value

    bits = bits_to_embed[:num_bits]
    if len(bits) < num_bits:
        bits = bits.ljust(num_bits, '0')

    mask = ~((1 << num_bits) - 1) & 0xFF
    cleared_value = value & mask
    bits_int = int(bits, 2)
    return cleared_value | bits_int


def extract_lsb(value: int, num_bits: int) -> str:
    """Mengekstrak bit dari LSB nilai piksel"""
    if num_bits <= 0 or num_bits > 8:
        return ''
    mask = (1 << num_bits) - 1
    extracted = value & mask
    return format(extracted, f'0{num_bits}b')
