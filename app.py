import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ==========================================
# 1. SETTING HALAMAN & UI THEME (TACTICAL NAVY)
# ==========================================
st.set_page_config(
    page_title="Tactical Dashboard ACS - Lanud RSN",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kustomisasi CSS untuk memberikan kesan dashboard militer yang premium dan bersih
st.markdown("""
    <style>
    /* Styling Header Utama */
    .main-title {
        font-size: 32px !important;
        font-weight: 800 !important;
        color: #1E3A8A;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 16px !important;
        color: #4B5563;
        margin-bottom: 25px;
    }
    /* Styling untuk Card Metrik */
    .metric-card {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1E3A8A;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI LOGIKA & PEMROSESAN DATA (BULLETPROOF)
# ==========================================
@st.cache_data(show_spinner=False)
def load_data(file_path_or_buffer):
    """Membaca file Excel secara aman dengan pembersihan otomatis."""
    try:
        df = pd.read_excel(file_path_or_buffer)
        # Menghapus spasi tak terlihat di awal/akhir nama kolom (Pemicu utama KeyError)
        df.columns = [str(col).strip() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"⚠️ **Gagal Memproses File:** {e}")
        return None

def dapatkan_nama_label(nama_file):
    """Mengubah nama file mentah menjadi label menu yang rapi dan informatif."""
    fn = nama_file.lower()
    tipe = "[Frekuensi]" if "jumlah_kejadian" in fn else "[Persentase]" if "persentase" in fn else "[Data]"
    
    if "temperature" in fn: parameter = "Suhu Udara (Temperature)"
    elif "tmaxmin" in fn: parameter = "Suhu Maksimum & Minimum"
    elif "visibility" in fn: parameter = "Jarak Pandang (Visibility)"
    elif "ws" in fn: parameter = "Kecepatan Angin (Wind Speed)"
    elif "rh" in fn: parameter = "Kelembapan Relatif (Relative Humidity)"
    elif "hs" in fn: parameter = "Tinggi Dasar Awan / Jam Cerah (HS)"
    else: parameter = nama_file.split('.')[0].replace('_', ' ').title()
    
    return f"{tipe} {parameter}"

# ==========================================
# 3. SIDEBAR PANEL CONTROL
# ==========================================
with st.sidebar:
    st.markdown("### 🦅 **OPERATIONAL CONTROL**")
    st.write("---")
    
    # Menu Pilihan Mode Utama
    mode_sumber = st.radio(
        "📂 **Pilih Sumber Data:**",
        ["Database Pusat ACS (Otomatis)", "Upload Manual Taktis (Awan/Kondisional)"],
        index=0
    )
    
    st.write("---")
    
    df_aktif = None
    sumber_info = ""
    
    if mode_sumber == "Database Pusat ACS (Otomatis)":
        FOLDER_DATA = "data"
        if os.path.exists(FOLDER_DATA):
            # Mendukung file .xlsx dan mengantisipasi bug nama file .xlsx.xlsx saat upload
            daftar_file = [f for f in os.listdir(FOLDER_DATA) if f.endswith('.xlsx') or f.endswith('.xlsx.xlsx')]
            
            if daftar_file:
                kamus_file = {dapatkan_nama_label(f): f for f in daftar_file}
                pilihan_label = st.selectbox("🎯 **Pilih Parameter Meteorologi:**", options=list(kamus_file.keys()))
                
                file_target = kamus_file[pilihan_label]
                jalur_lengkap = os.path.join(FOLDER_DATA, file_target)
                
                df_aktif = load_data(jalur_lengkap)
                sumber_info = f"Database Internal: `data/{file_target}`"
            else:
                st.warning(f"Folder '{FOLDER_DATA}' kosong. Silakan upload file `.xlsx` ke folder tersebut di GitHub.")
        else:
            st.error(f"⚠️ Folder `{FOLDER_DATA}/` tidak ditemukan di sistem root repositori.")
            
    else:
        # INTERAKSI UPLOAD MANUAL VIA SIDEBAR
        st.markdown("### 📤 **Upload File Baru**")
        file_diunggah = st.file_uploader("Seret file Excel (.xlsx) ke sini:", type=["xlsx"])
        if file_diunggah is not None:
            df_aktif = load_data(file_diunggah)
            sumber_info = f"Upload Taktis: `{file_diunggah.name}`"

    st.write("---")
    st.caption("⚡ **Sistem Dukungan Meteorologi Penerbangan**")
    st.caption("Lanud Roesmin Nurjadin — Rapi & Tahan Banting")

# ==========================================
# 4. MAIN DASHBOARD INTERFACE
# ==========================================
st.markdown('<p class="main-title">✈️ METEOROLOGICAL TACTICAL DASHBOARD</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Sistem Visualisasi Aerodrome Climatological Summary & Analisis Cuaca Operasional Lanud RSN</p>', unsafe_allow_html=True)

if df_aktif is not None:
    # --------------------------------------
    # TAMPILAN BANNER STATUS & METRIK UTAMA
    # --------------------------------------
    st.info(f"🟢 **Terhubung dengan Data Aktif** | {sumber_info}")
    
    # Baris Kartu Informasi (Metrics Cards)
    kolom_m1, kolom_m2, kolom_m3 = st.columns(3)
    with kolom_m1:
        st.markdown(f"<div class='metric-card'><small>TOTAL DATA OBSERVASI</small><br><b style='font-size:22px;'>{df_aktif.shape[0]}</b> Baris</div>", unsafe_allow_html=True)
    with kolom_m2:
        st.markdown(f"<div class='metric-card'><small>JUMLAH VARIABEL CUACA</small><br><b style='font-size:22px;'>{df_aktif.shape[1]}</b> Kolom</div>", unsafe_allow_html=True)
    with kolom_m3:
        # Mendeteksi otomatis kolom bertipe angka
        kolom_numerik = df_aktif.select_dtypes(include=['number']).columns.tolist()
        st.markdown(f"<div class='metric-card'><small>VARIABEL NUMERIK VALID</small><br><b style='font-size:22px;'>{len(kolom_numerik)}</b> Parameter</div>", unsafe_allow_html=True)
        
    st.write("")

    # --------------------------------------
    # TAMPILAN ANTARMUKA TABS INTERAKTIF
    # --------------------------------------
    tab_grafik, tab_tabel, tab_analisis = st.tabs([
        "📊 Visualisasi Grafik Interaktif", 
        "🗂️ Tabel Data Analitis", 
        "🔍 Ringkasan Statistik Dasar"
    ])
    
    semua_kolom = list(df_aktif.columns)
    
    # --- TAB 1: VISUALISASI UTAMA ---
    with tab_grafik:
        st.markdown("### 🛠️ Panel Konfigurasi Grafik Taktis")
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        
        with col_c1:
            sumbu_x = st.selectbox("Sumbu X (Referensi Waktu/Kategori):", options=semua_kolom, index=0, key="sb_x")
        with col_c2:
            pilihan_default = [kolom_numerik[0]] if kolom_numerik else [semua_kolom[1]] if len(semua_kolom) > 1 else [semua_kolom[0]]
            sumbu_y = st.multiselect("Sumbu Y (Parameter Nilai Meteorologi):", options=semua_kolom, default=pilihan_default, key="sb_y")
        with col_c3:
            jenis_grafik = st.selectbox("Model Tampilan:", ["Garis Tren (Line Chart)", "Batang Tegak (Bar Chart)", "Area Kumulatif (Area Chart)"], key="j_grafik")
            
        st.write("---")
        
        if sumbu_y:
            try:
                # Membuat visualisasi berdasarkan jenis yang dipilih
                if jenis_grafik == "Garis Tren (Line Chart)":
                    fig = px.line(df_aktif, x=sumbu_x, y=sumbu_y, markers=True, template="plotly_white")
                elif jenis_grafik == "Batang Tegak (Bar Chart)":
                    fig = px.bar(df_aktif, x=sumbu_x, y=sumbu_y, barmode="group", template="plotly_white")
                else:
                    fig = px.area(df_aktif, x=sumbu_x, y=sumbu_y, template="plotly_white")
                
                # Optimasi layout grafik agar interaktif, bersih, dan tajam saat dibaca
                fig.update_layout(
                    hovermode="x unified",
                    title=dict(text=f"Grafik Analisis Multivariabel Berdasarkan {sumbu_x}", font=dict(size=16, color="#1E3A8A")),
                    xaxis_title=str(sumbu_x).upper(),
                    yaxis_title="NILAI PARAMETER DATA CUACA",
                    legend_title="Parameter",
                    margin=dict(l=40, r=40, t=60, b=40),
                )
                
                # Menambahkan fitur Range Slider bawaan Plotly agar user bisa melakukan zoom-in waktu penerbangan secara presisi
                fig.update_xaxes(rangeslider_visible=True)
                
                # Render ke Streamlit
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ **Gagal Merender Grafik:** Pastikan kolom Sumbu Y yang dipilih berisi tipe data angka (Numerik). Detail Error: {e}")
        else:
            st.warning("⚠️ **Pemberitahuan:** Silakan pilih minimal satu parameter di Sumbu Y untuk memunculkan visualisasi grafik.")

    # --- TAB 2: DATA TABLE VIEW ---
    with tab_tabel:
        st.markdown("### 🗂️ Data Sheet View")
        st.write("Gunakan fitur pencarian (Ctrl+F) atau urutkan tabel langsung dengan mengeklik judul kolom di bawah ini:")
        
        # Menggunakan dataframe interaktif Streamlit terbaru yang mendukung filter langsung oleh user
        st.dataframe(
            df_aktif, 
            use_container_width=True, 
            column_config={col: st.column_config.Column(width="medium") for col in df_aktif.columns}
        )

    # --- TAB 3: STATISTICAL SUMMARY ---
    with tab_analisis:
        st.markdown("### 🔍 Ringkasan Statistik Deskriptif")
        st.write("Analisis otomatis nilai Minimum, Maksimum, dan Rata-rata dari parameter numerik yang tersedia:")
        
        if kolom_numerik:
            # Memunculkan tabel statistika deskriptif (count, mean, std, min, max) secara otomatis
            ringkasan_stat = df_aktif[kolom_numerik].describe().T
            st.dataframe(ringkasan_stat, use_container_width=True)
        else:
            st.info("Tidak ada parameter numerik yang ditemukan untuk dianalisis statistikonya.")

else:
    # TAMPILAN AWAL SEBELUM FILE DIPILIH/DIUPLOAD
    st.write("---")
    st.info("💡 **Petunjuk Awal:** Silakan pilih parameter cuaca di panel **Sidebar Navigasi** sebelah kiri untuk memuat data ACS otomatis, atau beralih ke mode **Upload Manual** untuk menganalisis file lokal baru.")
