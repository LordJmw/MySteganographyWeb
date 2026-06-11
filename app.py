"""
Steganografi LSB Modified - Streamlit Application
"""

import streamlit as st
import numpy as np
from PIL import Image
import io

# ==================== KONFIGURASI HALAMAN ====================
st.set_page_config(
    page_title="Steganografi LSB Modified",
    page_icon="🖼️",
    layout="wide"
)

from stego_core import embed_message, extract_message


# ==================== UI STREAMLIT ====================

st.title("🖼️ Steganografi LSB Modified")
st.markdown("Sembunyikan pesan rahasia ke dalam gambar dengan metode LBS Modified (1-3 bit per channel)")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📖 Informasi")
    st.markdown("""
    ### Metode yang digunakan:
    1. **Kunci (a, C, X₀)** dari nama depan & belakang
    2. **S1 (Saluran)** - LCG mod 7
    3. **S2 (Jumlah bit)** - LCG mod 4 → mapping 1-3
    4. **Posisi** - Generator modulus dinamis (bilangan prima)
    5. **LSB Modified** - 1-3 bit per saluran
    6. **PSNR** - Mengukur kualitas gambar
    """)
    
    st.divider()
    
    st.header("📊 Parameter")
    st.metric("Maks bit per channel", "3")
    st.metric("Maks bit per pixel", "9")
    st.metric("Minimal ukuran", "250×250 px")

# Tab
tab1, tab2 = st.tabs(["📝 Sisipkan Pesan", "🔍 Ekstrak Pesan"])

# ==================== TAB 1: EMBEDDING ====================
with tab1:
    st.header("Sisipkan Pesan Rahasia")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader(
            "Pilih gambar (minimal 250×250 pixel)",
            type=['png', 'jpg', 'jpeg', 'bmp'],
            key="embed_img"
        )
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Gambar Cover", use_container_width=True)
            st.caption(f"Ukuran: {image.width} × {image.height} pixel")
            
            if image.width < 250 or image.height < 250:
                st.warning("⚠️ Gambar kurang dari 250×250 pixel!")
    
    with col2:
        first_name = st.text_input("Nama Depan", placeholder="Contoh: James", key="fn_embed")
        last_name = st.text_input("Nama Belakang", placeholder="Contoh: Bond", key="ln_embed")
        secret_message = st.text_area("Pesan Rahasia", placeholder="Tulis pesan di sini...", height=100)
        
        embed_btn = st.button("🔒 Sisipkan Pesan", type="primary", use_container_width=True)
    
    if embed_btn:
        if uploaded_file is None:
            st.error("❌ Silakan pilih gambar terlebih dahulu!")
        elif not first_name or not last_name:
            st.error("❌ Silakan isi nama depan dan nama belakang!")
        elif not secret_message:
            st.error("❌ Silakan isi pesan rahasia!")
        else:
            with st.spinner("Memproses penyisipan..."):
                try:
                    # Simpan sementara
                    temp_path = "temp_cover.png"
                    image.save(temp_path)
                    
                    # Proses
                    result = embed_message(temp_path, secret_message, first_name, last_name, "stego_result.png")
                    print(result["percentage_changed"])
                    if result['success']:
                        st.success("✅ Pesan berhasil disisipkan!")
                        
                        # Tampilkan hasil
                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.subheader("📷 Gambar Asli")
                            st.image(image, use_container_width=True)
                        with col_res2:
                            st.subheader("🔒 Gambar Stego")
                            stego_img = Image.open("stego_result.png")
                            st.image(stego_img, use_container_width=True)
                        
                        # Metrik
                        st.subheader("📊 Hasil Analisis")
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("PSNR", f"{result['psnr']} dB")
                        m2.metric("MSE", f"{result['mse']:.7f}")
                        m3.metric("Karakter", f"{result['total_chars']}")
                        m4.metric("Piksel Berubah", f"{result['pixels_changed']}")
                        m5.metric("Persentase Perubahan", f"{result['percentage_changed']}%",help="(Piksel Berubah / Total Piksel) × 100%")
                      

                        

                        # Download
                        with open("stego_result.png", "rb") as f:
                            st.download_button(
                                label="💾 Download Gambar Stego",
                                data=f,
                                file_name="stego_image.png",
                                mime="image/png"
                            )
                    else:
                        st.error(f"❌ {result['error']}")
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan: {str(e)}")

# ==================== TAB 2: EXTRACTION ====================
with tab2:
    st.header("Ekstrak Pesan dari Gambar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        stego_file = st.file_uploader(
            "Pilih gambar stego",
            type=['png', 'jpg', 'jpeg', 'bmp'],
            key="extract_img"
        )
        
        if stego_file is not None:
            stego_img = Image.open(stego_file)
            st.image(stego_img, caption="Gambar Stego", use_container_width=True)
    
    with col2:
        ext_first_name = st.text_input("Nama Depan (sama saat embedding)", placeholder="Contoh: James", key="fn_extract")
        ext_last_name = st.text_input("Nama Belakang (sama saat embedding)", placeholder="Contoh: Bond", key="ln_extract")
        
        extract_btn = st.button("🔓 Ekstrak Pesan", type="primary", use_container_width=True)
    
    if extract_btn:
        if stego_file is None:
            st.error("❌ Silakan pilih gambar stego terlebih dahulu!")
        elif not ext_first_name or not ext_last_name:
            st.error("❌ Silakan isi nama depan dan nama belakang!")
        else:
            with st.spinner("Mengekstrak pesan..."):
                try:
                    temp_path = "temp_stego.png"
                    stego_img.save(temp_path)
                    
                    result = extract_message(temp_path, ext_first_name, ext_last_name)
                    
                    if result['success'] and result['message']:
                        st.success("✅ Pesan berhasil diekstrak!")
                        st.subheader("📝 Pesan Rahasia")
                        st.code(result['message'], language="text")
                        st.caption(f"Panjang: {result['total_chars']} karakter")
                    else:
                        st.warning("⚠️ Tidak ditemukan pesan. Periksa kembali nama yang dimasukkan!")
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan: {str(e)}")

st.markdown("---")
st.caption("© 2026 - Steganografi LSB Modified")