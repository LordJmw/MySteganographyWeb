# 🖼️ Steganografi LSB Modified

Aplikasi web untuk menyembunyikan pesan rahasia di dalam gambar menggunakan metode **LSB Modified** berbasis kunci dinamis dari nama pengguna.

---

## Daftar Isi

- [Gambaran Umum](#gambaran-umum)
- [Fitur](#fitur)
- [Instalasi](#instalasi)
- [Cara Menjalankan](#cara-menjalankan)
- [Cara Penggunaan](#cara-penggunaan)
- [Cara Kerja Sistem](#cara-kerja-sistem)
- [Struktur File](#struktur-file)
- [Kapasitas Pesan](#kapasitas-pesan)
- [Metrik Kualitas](#metrik-kualitas)
- [Keterbatasan](#keterbatasan)

---

## Gambaran Umum

Steganografi adalah teknik menyembunyikan informasi di dalam media (gambar, audio, video) sehingga keberadaan pesan tersebut tidak terdeteksi secara kasat mata. Aplikasi ini mengimplementasikan metode **LSB (Least Significant Bit) Modified** dengan karakteristik:

- **Kunci dari nama pengguna** — posisi sisip dan saluran warna ditentukan dari nama depan + belakang
- **Posisi acak** — piksel yang digunakan tersebar merata via generator bilangan prima (GenMod)
- **Jumlah bit variabel** — setiap piksel bisa menyimpan 1–3 bit per channel (bukan selalu 1)
- **Enkripsi XOR** — pesan dienkripsi sebelum disisipkan sehingga tidak bisa dibaca tanpa kunci nama yang benar

---

## Fitur

- Upload gambar cover (PNG, JPG, BMP)
- Input nama depan + belakang sebagai kunci
- Sisipkan pesan teks rahasia ke dalam gambar
- Tampilkan statistik: **PSNR**, **MSE**, jumlah piksel berubah, persentase perubahan
- Download gambar stego hasil sisipan
- Ekstrak kembali pesan dari gambar stego
- Validasi otomatis jika nama salah (pesan tidak bisa diekstrak)

---

## Instalasi

### Prasyarat

- Python **3.9** atau lebih baru
- pip

### Langkah Instalasi

```bash
# 1. Clone atau ekstrak project
git clone <repo-url>
cd AppSteganografi

# 2. (Opsional) Buat virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Isi `requirements.txt`

```
streamlit==1.28.1
Pillow==10.0.0
numpy==1.24.3
opencv-python==4.8.1.78
```

---

## Cara Menjalankan

```bash
streamlit run app.py
```

Browser akan terbuka otomatis di `http://localhost:8501`. Jika tidak, buka manual di browser.

---

## Cara Penggunaan

### Tab 1 — Sisipkan Pesan

1. Upload gambar cover (minimal **250 × 250 piksel**, format PNG/JPG/BMP)
2. Isi **Nama Depan** dan **Nama Belakang** — ini berfungsi sebagai kunci enkripsi
3. Tulis **Pesan Rahasia** di kolom teks
4. Klik tombol **🔒 Sisipkan Pesan**
5. Lihat hasil analisis (PSNR, MSE, piksel berubah)
6. Klik **💾 Download Gambar Stego** untuk menyimpan gambar hasil

> ⚠️ **Penting:** Catat nama yang digunakan. Ekstraksi hanya berhasil jika nama sama persis (huruf besar/kecil tidak sensitif).

---

### Tab 2 — Ekstrak Pesan

1. Upload gambar stego (gambar hasil sisipan dari Tab 1)
2. Isi **Nama Depan** dan **Nama Belakang** yang sama saat menyisipkan
3. Klik tombol **🔓 Ekstrak Pesan**
4. Pesan rahasia akan ditampilkan jika nama benar

---

## Cara Kerja Sistem

Sistem bekerja dalam 5 komponen utama yang saling terhubung:

### 1. Pembangkitan Kunci (`key_generator.py`)

Kunci `a`, `C`, `X0` untuk LCG dihasilkan dari kombinasi nama depan dan nama belakang:

```
Nama depan: "James", Nama belakang: "Wong"

LANGKAH 1 — XOR 3 huruf terakhir nama belakang:
    'o' = 01101111
    'n' = 01101110
    'g' = 01100111
    01101111 XOR 01101110 = 00000001
    00000001 XOR 01100111 = 01100110  <- hasil sementara

LANGKAH 2 — Fold 4 huruf pertama nama depan jadi 8 bit:
    'j' = 01101010
    'a' = 01100001
    'm' = 01101101
    'e' = 01100101
    01101010 XOR 01100001 = 00001011
    00001011 XOR 01101101 = 01100110
    01100110 XOR 01100101 = 00000011  <- hasil fold nama depan

LANGKAH 3 — Gabungkan:
    01100110 XOR 00000011 = 01100101  <- hasil akhir 8 bit

LANGKAH 4 — Ekstrak a, C, X0:
    3 bit pertama → a  = 011 = 3
    3 bit tengah  → C  = 001 = 1
    2 bit terakhir→ X0 = 01  = 1
    Hasil: a=3, C=1, X0=1
```

Jika `a` atau `C` bernilai 0, otomatis diubah menjadi 1.

---

### 2. Generator Posisi — GenMod (`position_gen.py`)

Menentukan **piksel mana** yang akan digunakan, tersebar merata di seluruh gambar:

```
N = total piksel (misal 250×250 = 62.500)
P = bilangan prima terbesar ≤ N  (misal 62.497)
g = primitive root modulo P      (misal 19)

Posisi ke-i = (g^i) mod P  →  dipetakan ke indeks 0..N-1
```

Hasilnya adalah urutan piksel yang terlihat acak tapi bisa direproduksi ulang selama kunci sama.

---

### 3. Generator Saluran Warna — S1 (`lcg.py`)

Menentukan **channel mana (R/G/B)** yang digunakan di setiap piksel via LCG modulus 7:

```
Xₙ₊₁ = (a × Xₙ + C) mod 7

Nilai  → Channel aktif
  0    → R
  1    → G
  2    → B
  3    → R dan G
  4    → R dan B
  5    → G dan B
  6    → R, G, dan B
```

---

### 4. Generator Jumlah Bit — S2 (`lcg.py`)

Menentukan **berapa bit** yang disisipkan per channel (1, 2, atau 3 bit) via LCG modulus 4:

```
Xₙ₊₁ = (a × Xₙ + C) mod 4
Jika hasil = 0 → ubah jadi 1
Nilai akhir = (hasil % 3) + 1   →  rentang 1–3
```

Seed S2 diturunkan langsung dari kunci `(a, C, X0)` sehingga selalu konsisten antara proses embed dan extract tanpa perlu file pendamping.

---

### 5. Proses Embedding & Extraction (`stego_core.py`)

**Embedding:**

```
Pesan teks
  → Konversi ke biner (8 bit per karakter)
  → Enkripsi dengan XOR menggunakan password dari nama
  → Tambahkan delimiter 16-bit (1111111100000000) di akhir
  → Untuk setiap bit data:
       Ambil posisi piksel  (dari GenMod)
       Ambil channel aktif  (dari S1)
       Ambil jumlah bit     (dari S2)
       Ganti LSB piksel dengan bit pesan
  → Simpan sebagai gambar PNG
```

**Extraction:**

```
Gambar stego
  → Regenerasi kunci, posisi, S1, S2 yang sama persis
  → Baca bit dari LSB piksel sesuai urutan
  → Kumpulkan bit ke buffer
  → Deteksi delimiter 1111111100000000
  → Ambil semua bit sebelum delimiter
  → Dekripsi dengan XOR menggunakan password dari nama
  → Konversi biner ke teks → pesan asli
```

---

### Diagram Alur Lengkap

```
EMBEDDING:
┌──────────┐    ┌─────────────┐    ┌─────────────┐
│  Gambar  │    │  Nama User  │    │   Pesan     │
│  Cover   │    │ Depan+Blkg  │    │  Rahasia    │
└────┬─────┘    └──────┬──────┘    └──────┬──────┘
     │                 │                  │
     │          ┌──────▼──────┐           │
     │          │ generate_   │           │
     │          │   keys()    │           │
     │          │ a, C, X0    │           │
     │          └──┬───┬───┬──┘           │
     │             │   │   │              │
     │      ┌──────▼─┐ │ ┌─▼──────┐      │
     │      │GenMod  │ │ │  LCG   │      │
     │      │Posisi  │ │ │S1 & S2 │      │
     │      └──┬─────┘ │ └──┬─────┘      │
     │         │        │    │            │
     │  ┌──────▼────────▼────▼────────────▼──┐
     │  │  XOR encrypt + embed ke LSB piksel  │
     └──►                                     │
        └──────────────┬──────────────────────┘
                       │
                ┌──────▼──────┐
                │  Gambar     │
                │   Stego     │
                └─────────────┘

EXTRACTION: proses sebaliknya dengan kunci yang sama
```

---

## Struktur File

```
AppSteganografi/
├── app.py              # UI Streamlit — tampilan web
├── stego_core.py       # Inti embed & extract LSB
├── key_generator.py    # Generate kunci a, C, X0 dari nama
├── position_gen.py     # GenMod — generator posisi piksel
├── lcg.py              # LCG untuk S1 (channel) dan S2 (jumlah bit)
├── utils.py            # Fungsi bantu: biner, XOR, LSB
├── requirements.txt    # Dependencies Python
└── README.md           # Dokumentasi ini
```

| File | Tanggung Jawab |
|------|----------------|
| `app.py` | Antarmuka pengguna berbasis Streamlit |
| `stego_core.py` | Orkestrasi proses embed dan extract |
| `key_generator.py` | Derivasi kunci `a`, `C`, `X0` dari nama depan dan belakang |
| `position_gen.py` | Urutan posisi piksel via primitive root |
| `lcg.py` | Deret S1 (channel) dan S2 (jumlah bit) |
| `utils.py` | Konversi biner, XOR, embed/extract LSB |

---

## Kapasitas Pesan

Kapasitas teoritis maksimal berdasarkan ukuran gambar (3 channel × maks 3 bit = 9 bit/piksel):

| Ukuran Gambar | Total Piksel | Kapasitas Maksimal |
|---------------|-------------|-------------------|
| 250 × 250     | 62.500      | ±70.312 karakter  |
| 500 × 500     | 250.000     | ±281.250 karakter |
| 1000 × 1000   | 1.000.000   | ±1.125.000 karakter |

> Kapasitas aktual sedikit lebih kecil karena overhead delimiter (16 bit).

---

## Metrik Kualitas

Setelah embedding, aplikasi menampilkan tiga metrik kualitas gambar:

### PSNR (Peak Signal-to-Noise Ratio)

Mengukur seberapa mirip gambar stego dengan gambar asli. Semakin tinggi semakin baik.

```
PSNR = 10 × log₁₀(255² / MSE)   [satuan: dB]
```

| Nilai PSNR | Interpretasi |
|-----------|-------------|
| > 40 dB   | Sangat baik — perubahan tidak terdeteksi |
| 30–40 dB  | Baik — perubahan sangat sulit terlihat |
| < 30 dB   | Cukup — mungkin ada artefak terlihat |

### MSE (Mean Squared Error)

Rata-rata kuadrat selisih nilai piksel antara gambar asli dan stego. Semakin kecil semakin baik.

### Persentase Piksel Berubah

```
% perubahan = (jumlah piksel unik yang disentuh / total piksel) × 100
```

---

## Keterbatasan

- **Format output harus PNG** — format lossy seperti JPG akan merusak LSB sehingga ekstraksi gagal. Selalu gunakan PNG saat menyimpan gambar stego.
- **Nama harus sama persis** — perbedaan satu huruf menghasilkan kunci berbeda dan pesan tidak bisa diekstrak.
- **Tidak cocok untuk keamanan tinggi** — ini adalah implementasi akademis. Untuk kebutuhan produksi gunakan enkripsi yang lebih kuat.
- **Ukuran minimal gambar 250 × 250 piksel** — gambar lebih kecil ditolak oleh aplikasi.
