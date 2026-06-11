"""
Pembangkitan kunci a, C, X0 dari nama depan dan nama belakang
Sesuai dengan metode di file Excel
"""

def ascii_to_bin(char: str) -> str:
    """Mengkonversi karakter ke biner 8-bit"""
    return format(ord(char), '08b')


def xor_bits(bit1: str, bit2: str) -> str:
    """XOR dua string biner"""
    return ''.join('1' if b1 != b2 else '0' for b1, b2 in zip(bit1, bit2))


def generate_keys(first_name: str, last_name: str) -> dict:
    """
    Menghasilkan a, C, X0 dari nama depan dan belakang
    
    Proses:
    1. Ambil 4 huruf pertama nama depan -> 32 bit biner
    2. Ambil 3 huruf terakhir nama belakang -> 24 bit
    3. XOR ketiga 8-bit password dari nama belakang
    4. Dari 8-bit hasil XOR:
       - 3 bit pertama = a (jika 0 ditambah 1)
       - 3 bit tengah = C (jika 0 ditambah 1)
       - 2 bit terakhir = X0
    
    Returns:
        dict with keys: a, C, x0
    """
    # 1. Ambil 4 huruf pertama nama depan
    first_4 = first_name[:4].lower()
    if len(first_4) < 4:
        first_4 = first_4.ljust(4, 'x')  # Padding jika kurang
    
    # 2. Ambil 3 huruf terakhir nama belakang
    last_3 = last_name[-3:].lower()
    if len(last_3) < 3:
        last_3 = last_3.rjust(3, 'x')  # Padding jika kurang
    
    print(f"4 huruf pertama nama depan: {first_4}")
    print(f"3 huruf terakhir nama belakang: {last_3}")
    
    # 3. XOR ketiga karakter password
    bin1 = ascii_to_bin(last_3[0])
    bin2 = ascii_to_bin(last_3[1])
    bin3 = ascii_to_bin(last_3[2])
    
    # XOR ketiganya
    xor12 = xor_bits(bin1, bin2)
    xor_result = xor_bits(xor12, bin3)
    
    #bagian nama depan
    b1 = ascii_to_bin(first_4[0])
    b2 = ascii_to_bin(first_4[1])
    b3 = ascii_to_bin(first_4[2])
    b4 = ascii_to_bin(first_4[3])
    first_xor = xor_bits(xor_bits(xor_bits(b1, b2), b3), b4)  # tetap 8 bit

    xor_result = xor_bits(xor_result, first_xor)  # gabung dengan hasil nama belakang
    
    print(f"Hasil XOR: {xor_result} (biner)")
    
    # 4. Ekstrak a, C, X0
    a_bits = xor_result[:3]
    c_bits = xor_result[3:6]
    x0_bits = xor_result[6:8]
    
    a_val = int(a_bits, 2)
    c_val = int(c_bits, 2)
    x0_val = int(x0_bits, 2)
    
    # Penyesuaian: a tidak boleh 0
    if a_val == 0:
        a_val = 1
        print("a = 0, disesuaikan menjadi 1")
    
    # Penyesuaian: C tidak boleh 0
    if c_val == 0:
        c_val = 1
        print("C = 0, disesuaikan menjadi 1")
    
    print(f"a = {a_val}, C = {c_val}, X0 = {x0_val}")
    
    return {
        'a': a_val,
        'C': c_val,
        'x0': x0_val
    }