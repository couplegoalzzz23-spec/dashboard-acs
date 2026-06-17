import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA
# ==========================================
st.set_page_config(
    page_title="Dashboard ACS Interaktif", 
    page_icon="✈️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Judul yang disesuaikan untuk konteks operasional penerbangan
st.title("✈️ Dashboard Aerodrome Climatological Summary (ACS)")
st.markdown("### Visualisasi Data Klimatologi Operasional (Periode 2021 - 2025)")
st.markdown("---")

# ==========================================
# 2. DEFINISI JALUR FOLDER (ANTI-EROR OS)
# ==========================================
# Ini memastikan skrip selalu mencari di dalam folder "data" yang ada di root yang sama
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# ==========================================
# 3. NAVIGASI & MAPPING FILE EXCEL
# ==========================================
st.sidebar.header("📁 Parameter Meteorologi")

# Nama di kiri (kunci) adalah yang tampil di web.
# Nama di kanan (nilai) WAJIB SAMA PERSIS dengan nama file di folder "data" GitHub.
FILE_MAPPING = {
    "Jumlah Kejadian Masuk (RH)": "rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx",
    "Jumlah Kejadian Masuk (Tmax/Tmin)": "rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx",
    "Persentase Heiligenschein (HS)": "rata_rata_persentase_hs_2021_2025.xlsx",
    "Persentase Temperatur": "rata_rata_persentase_temperature_2021_2025.xlsx",
    "Persentase Visibility": "rata_rata_persentase_visibility_2021_2025.xlsx",
    "Persentase Wind Speed (WS)": "rata_rata_persentase_ws_2021_2025.xlsx"
}

pilihan_parameter = st.sidebar.selectbox(
    "Pilih Parameter ACS:",
    options=list(FILE_MAPPING.keys())
)

# Menentukan file yang akan dibaca
file_terpilih = FILE_MAPPING[pilihan_parameter]
FULL_PATH = DATA_DIR / file_terpilih

# ==========================================
# 4. FUNGSI MEMBACA DATA (DENGAN CACHE & PROTEKSI)
# ==========================================
@st.cache_data(show_spinner="Memuat data ACS...", ttl=3600)
def load_data(file_path: Path):
    if not file_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {file_path.name}")
    
    # Engine openpyxl wajib digunakan untuk file .xlsx agar tahan banting
    df = pd.read_excel(file_path, engine="openpyxl")
    
    # Pembersihan otomatis: menghapus spasi gaib di nama kolom
    df.columns = [str(col).strip() for col in df.columns]
    return df

# ==========================================
# 5. LOGIKA UTAMA & VISUALISASI
# ==========================================
try:
    # Eksekusi pembacaan data
    df = load_data(FULL_PATH)
    
    st.subheader(f"📊 Tabel Data Mentah: {pilihan_parameter}")
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📈 Analisis Grafik Interaktif")
    
    daftar_kolom = list(df.columns)
    
    # Syarat membuat grafik minimal ada 2 kolom
    if len(daftar_kolom) >= 2:
        # Menyiapkan dropdown cerdas agar pengguna bisa mengatur sumbu X dan Y sendiri
        # Ini mencegah eror jika nama kolom di Excel Anda tidak lazim
        col_x, col_y, col_jenis = st.columns(3)
        
        with col_x:
            # Sumbu X biasanya Bulan/Waktu (default ke kolom pertama)
            sumbu_x = st.selectbox("Sumbu X (Kategori/Waktu):", options=daftar_kolom, index=0)
            
        with col_y:
            # Sumbu Y biasanya nilai/parameter (default ke kolom kedua)
            sumbu_y = st.selectbox("Sumbu Y (Nilai Parameter):", options=daftar_kolom, index=1)
            
        with col_jenis:
            jenis_grafik = st.selectbox("Model Tampilan Grafik:", options=["Grafik Garis", "Grafik Batang", "Grafik Area"])
            
        # Membuat Plotly Chart berdasarkan pilihan
        if jenis_grafik == "Grafik Garis":
            fig = px.line(df, x=sumbu_x, y=sumbu_y, markers=True, title=f"Tren {sumbu_y} terhadap {sumbu_x}")
        elif jenis_grafik == "Grafik Batang":
            fig = px.bar(df, x=sumbu_x, y=sumbu_y, title=f"Perbandingan {sumbu_y} berdasarkan {sumbu_x}")
        else:
            fig = px.area(df, x=sumbu_x, y=sumbu_y, title=f"Distribusi Area {sumbu_y} terhadap {sumbu_x}")
            
        # Kustomisasi tampilan agar rapi
        fig.update_layout(
            hovermode="x unified",
            xaxis_title=sumbu_x,
            yaxis_title=sumbu_y,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # Tampilkan grafik
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("⚠️ Data di dalam Excel ini kurang dari 2 kolom, tidak dapat divisualisasikan menjadi grafik.")

# ==========================================
# 6. PENANGANAN EROR (ERROR HANDLING)
# ==========================================
except FileNotFoundError as e:
    st.error(f"❌ **Gagal Memuat File:** {e}")
    st.info("💡 Pastikan nama file di `FILE_MAPPING` (di dalam app.py) sama persis hurufnya dengan nama file di folder `data/`.")
except Exception as e:
    st.error(f"⚠️ **Terjadi Kesalahan Pembacaan Data:** {e}")
    st.info("💡 Periksa format file Excel Anda, pastikan tidak ada sel yang rusak atau berantakan.")
