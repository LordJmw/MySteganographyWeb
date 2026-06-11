"""
Inti proses embedding dan extraction LSB (Fixed v2)

Perbaikan:
  #1  - Delimiter 16-bit unik '1111111100000000' mengganti '00000000'
  #4  - Metadata path konsisten via _metadata_path()
  #6  - Loop ekstraksi benar-benar membaca bit dari piksel
  #7  - S2 seed tidak lagi bergantung pada jumlah iterasi (max_bits)
        → S2 seed sekarang diturunkan langsung dari kunci (x0 XOR a XOR C)
        sehingga embed dan extract selalu identik tanpa perlu metadata
"""

import os
import numpy as np
from PIL import Image

from key_generator import generate_keys
from position_gen import generate_positions_incremental
from utils import (
    text_to_bits, bits_to_text, xor_bits,
    generate_password_bits, get_channel_mask,
    embed_lsb, extract_lsb
)

DELIMITER = '1111111100000000'   # 16-bit, pola 0xFF+0x00
DELIMITER_LEN = len(DELIMITER)   # 16


def _make_lcg_gen(a: int, C: int, x0: int, modulus: int):
    """Generator LCG tak terbatas"""
    x = x0
    while True:
        x = (a * x + C) % modulus
        yield x


def _s2_seed(a: int, C: int, x0: int) -> int:
    """
    Seed untuk generator S2 yang INDEPENDENT dari panjang pesan.
    Diturunkan langsung dari kunci sehingga selalu sama di embed & extract.
    """
    raw = (a * 31 + C * 17 + x0 * 7) % 4
    return raw if raw != 0 else 1


def embed_message(
    image_path: str,
    message: str,
    first_name: str,
    last_name: str,
    output_path: str = "stego_result.png"
) -> dict:
    """Menyisipkan pesan ke dalam gambar"""

    img = Image.open(image_path).convert('RGB')
    img_array = np.array(img, dtype=np.uint8)
    original_array = img_array.copy()
    height, width, _ = img_array.shape

    keys = generate_keys(first_name, last_name)
    a, C, x0 = keys['a'], keys['C'], keys['x0']

    # Enkripsi pesan
    message_bits = text_to_bits(message)
    password_bits = generate_password_bits(first_name, last_name, len(message_bits))
    encrypted_bits = xor_bits(message_bits, password_bits)

    data_to_hide = encrypted_bits + DELIMITER
    total_bits_needed = len(data_to_hide)

    print(f"=== DEBUG EMBEDDING ===")
    print(f"Pesan: '{message}'")
    print(f"Panjang pesan (bit): {len(message_bits)}")
    print(f"Total bits to hide (incl. delimiter): {total_bits_needed}")

    total_pixels = width * height
    max_bits = total_pixels * 3 * 3
    if total_bits_needed > max_bits:
        return {
            'success': False,
            'error': f'Pesan terlalu panjang! Kapasitas maksimal: {max_bits // 8} karakter'
        }

    pos_gen = generate_positions_incremental(width, height, total_bits_needed)
    s1_gen = _make_lcg_gen(a, C, x0, 7)
    s2_gen = _make_lcg_gen(a, C, _s2_seed(a, C, x0), 4)  # seed independen

    bit_index = 0
    pixels_touched = set()

    while bit_index < total_bits_needed:
        pos = next(pos_gen)
        row = pos // width
        col = pos % width
        pixels_touched.add(pos)

        s1_val = next(s1_gen)
        r_active, g_active, b_active = get_channel_mask(s1_val)

        raw_s2 = next(s2_gen)
        if raw_s2 == 0:
            raw_s2 = 1
        s2_val = (raw_s2 % 3) + 1

        remaining = total_bits_needed - bit_index
        if s2_val > remaining:
            s2_val = remaining

        bits_chunk = data_to_hide[bit_index:bit_index + s2_val]

        if r_active:
            img_array[row, col, 0] = embed_lsb(img_array[row, col, 0], bits_chunk, s2_val)
        if g_active:
            img_array[row, col, 1] = embed_lsb(img_array[row, col, 1], bits_chunk, s2_val)
        if b_active:
            img_array[row, col, 2] = embed_lsb(img_array[row, col, 2], bits_chunk, s2_val)

        bit_index += s2_val

    # Statistik
    diff = original_array.astype(float) - img_array.astype(float)
    mse = np.mean(diff ** 2)
    psnr = 10 * np.log10(255 ** 2 / mse) if mse > 0 else 100.0

    unique_pixels_changed = len(pixels_touched)
    percentage_changed = (unique_pixels_changed / total_pixels) * 100

    stego_img = Image.fromarray(img_array, 'RGB')
    stego_img.save(output_path)

    # Simpan metadata
    metadata_path = _metadata_path(output_path)
    with open(metadata_path, 'w') as f:
        f.write(str(bit_index))
    print(f"✅ Metadata disimpan ke: {metadata_path} ({bit_index} bits)")

    return {
        'success': True,
        'psnr': round(psnr, 2),
        'mse': round(float(mse), 7),
        'total_bits_embedded': bit_index,
        'total_chars': len(message),
        'pixels_changed': unique_pixels_changed,
        'percentage_changed': round(percentage_changed, 6),
        'output_path': output_path,
        'a': a, 'C': C, 'x0': x0
    }


def extract_message(
    image_path: str,
    first_name: str,
    last_name: str
) -> dict:
    """
    Mengekstrak pesan dari gambar stego.
    Mencari delimiter tanpa bergantung pada file metadata.
    """
    img = Image.open(image_path).convert('RGB')
    img_array = np.array(img, dtype=np.uint8)
    height, width, _ = img_array.shape

    keys = generate_keys(first_name, last_name)
    a, C, x0 = keys['a'], keys['C'], keys['x0']

    total_pixels = width * height
    # Batas aman: cukup besar untuk pesan panjang, tidak buang waktu
    max_bits = min(total_pixels * 3 * 3, 500_000)

    print(f"=== DEBUG EXTRACTION ===")

    pos_gen = generate_positions_incremental(width, height, max_bits)
    s1_gen = _make_lcg_gen(a, C, x0, 7)
    s2_gen = _make_lcg_gen(a, C, _s2_seed(a, C, x0), 4)  # seed sama persis dengan embed

    extracted_buffer = ''

    for _ in range(max_bits):
        pos = next(pos_gen)
        row = pos // width
        col = pos % width

        s1_val = next(s1_gen)
        r_active, g_active, b_active = get_channel_mask(s1_val)

        raw_s2 = next(s2_gen)
        if raw_s2 == 0:
            raw_s2 = 1
        s2_val = (raw_s2 % 3) + 1

        # Baca dari channel pertama yang aktif (semua channel berisi bit yang sama)
        if r_active:
            extracted_buffer += extract_lsb(img_array[row, col, 0], s2_val)
        elif g_active:
            extracted_buffer += extract_lsb(img_array[row, col, 1], s2_val)
        elif b_active:
            extracted_buffer += extract_lsb(img_array[row, col, 2], s2_val)

        # Cari delimiter
        if len(extracted_buffer) >= DELIMITER_LEN:
            idx = extracted_buffer.find(DELIMITER)
            if idx != -1:
                encrypted_bits = extracted_buffer[:idx]
                print(f"🔐 Delimiter ditemukan di posisi {idx}, panjang data: {len(encrypted_bits)} bit")

                if len(encrypted_bits) == 0:
                    return {'success': False, 'message': '', 'total_chars': 0,
                            'error': 'Pesan kosong'}

                password_bits = generate_password_bits(first_name, last_name, len(encrypted_bits))
                decrypted_bits = xor_bits(encrypted_bits, password_bits)
                message = bits_to_text(decrypted_bits)

                print(f"✅ Pesan diekstrak: '{message}'")
                return {
                    'success': True,
                    'message': message,
                    'total_chars': len(message)
                }

    return {
        'success': False,
        'message': '',
        'total_chars': 0,
        'error': 'Delimiter tidak ditemukan. Pastikan nama sama dengan saat embedding.'
    }


def _metadata_path(image_path: str) -> str:
    """Path metadata konsisten: buang ekstensi, tambahkan _metadata.txt"""
    base = os.path.splitext(image_path)[0]
    return base + '_metadata.txt'
