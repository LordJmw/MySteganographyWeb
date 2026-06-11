"""
LCG untuk pembangkitan S1 (saluran warna) dan S2 (jumlah bit)
"""

def generate_s1(a: int, C: int, x0: int, n: int) -> list:
    """
    Menghasilkan deret S1 (saluran warna) dengan LCG modulus 7
    S1 = 0=R, 1=G, 2=B, 3=RG, 4=RB, 5=GB, 6=RGB
    
    Args:
        a: multiplier (1-7)
        C: increment (1-7)
        x0: seed awal
        n: jumlah nilai yang dibangkitkan
    
    Returns:
        list of S1 values (0-6)
    """
    result = []
    x = x0
    for _ in range(n):
        x = (a * x + C) % 7
        result.append(x)
    return result


def generate_s2(a: int, C: int, x0: int, n: int) -> list:
    """
    Menghasilkan deret S2 (jumlah bit per saluran) dengan LCG modulus 4
    Aturan:
    - Hasil mod 4 jika 0 diubah jadi 1
    - Kemudian mapping (hasil % 3) + 1
    
    Args:
        a: multiplier (1-7)
        C: increment (1-7)
        x0: seed awal
        n: jumlah nilai yang dibangkitkan
    
    Returns:
        list of S2 values (1-3)
    """
    result = []
    x = x0
    for _ in range(n):
        # LCG dengan modulus 4
        x = (a * x + C) % 4
        
        # Jika hasil 0, ubah jadi 1
        if x == 0:
            x = 1
        
        
        result.append(x)
    return result


def get_channel_mask(s1_value: int) -> tuple:
    """
    Mengembalikan mask channel berdasarkan nilai S1
    
    Returns:
        (red_active, green_active, blue_active)
    """
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