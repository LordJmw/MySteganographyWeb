"""
Generator posisi dengan modulus dinamis (Incremental)
"""

import math


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def largest_prime_leq(n: int) -> int:
    for i in range(n, 1, -1):
        if is_prime(i):
            return i
    return 2


def find_primitive_root(p: int) -> int:
    if p == 2:
        return 1
    
    phi = p - 1
    factors = []
    temp = phi
    i = 2
    while i * i <= temp:
        if temp % i == 0:
            factors.append(i)
            while temp % i == 0:
                temp //= i
        i += 1
    if temp > 1:
        factors.append(temp)
    
    for g in range(2, p):
        ok = True
        for factor in factors:
            if pow(g, phi // factor, p) == 1:
                ok = False
                break
        if ok:
            return g
    return 2


def generate_positions_incremental(width: int, height: int, max_bits: int):
    """
    Generator posisi incremental (yield satu per satu)
    """
    total_pixels = width * height
    modulus = largest_prime_leq(total_pixels)
    generator = find_primitive_root(modulus)
    
    current = 1
    for _ in range(max_bits):
        current = (current * generator) % modulus
        pos = (current - 1) % total_pixels
        yield pos