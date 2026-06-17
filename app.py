import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. KONFIGURASI HALAMAN 
# ==========================================
st.set_page_config(page_title="Dashboard ACS Interaktif", page_icon="✈️", layout="wide")

st.title("✈️ Dashboard Aerodrome Climatological Summary (ACS)")
st.markdown("### Visualisasi Data Klimatologi Operasional (Periode 2021 - 2025)")
st.markdown("---")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# ==========================================
# 2. NAVIGASI & KONTROL PEMBACAAN EXCEL
# ==========================================
st.sidebar.header("📁 Pengaturan Data")

FILE_MAPPING = {
    "Jumlah Kejadian Masuk (RH)": "rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx",
    "Jumlah Kejadian Masuk (Tmax/Tmin)": "rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx",
    "Persentase Heiligenschein (HS)": "rata_rata_persentase_hs_2021_2025.xlsx",
    "Persentase Temperatur": "rata_rata_persentase_temperature_2021_2025.xlsx",
    "Persentase Visibility": "rata_rata_persentase_visibility_2021_2025.xlsx",
    "Persentase Wind Speed (WS)": "rata_rata_persentase_ws_2021_2025.xlsx"
}

pilihan_parameter = st.sidebar.selectbox("Pilih Parameter ACS:", options=list(FILE_MAPPING.keys()))

st.sidebar.markdown("---")
st.sidebar.header("🔧 Perbaikan Format Excel")
st.sidebar.write("Gunakan ini jika kolom tabel membaca judul besar laporan:")
# FITUR BARU: Mengabaikan baris judul laporan yang di-merge di Excel
baris_header = st.sidebar.number_input("Tabel asli dimulai pada baris ke- (Skip judul):", min_value=0, max_value=15, value=0)

file_terpilih = FILE_MAPPING[pilihan_parameter]
FULL_PATH = DATA_DIR / file_terpilih

# ==========================================
# 3. FUNGSI MEMBACA DATA
# ==========================================
@st.cache_data(show_spinner="Memuat data ACS...", ttl=3600)
def load_data(file_path: Path, header_row: int):
    if not file_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {file_path.name}")
    
    # header=header_row adalah kunci untuk melewati judul yang di-merge
    df = pd.read_excel(file_path, engine="openpyxl", header=header_row)
    df.columns = [str(col).strip() for col in df.columns]
    return df

# ==========================================
# 4. LOGIKA UTAMA & VISUALISASI
# ==========================================
try:
    # Eksekusi pembacaan data
    df = load_data(FULL_PATH, baris_header)
    
    # Tampilkan tabel mentah untuk konfirmasi
    st.subheader(f"📊 Tabel Data: {pilihan_parameter}")
    st.write("*(Cek tabel ini. Pastikan baris paling atas yang berwarna abu-abu adalah nama kolom yang benar, bukan judul laporan. Jika salah, ubah angka di menu sebelah kiri!)*")
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📈 Analisis Grafik Interaktif")
    
    daftar_kolom = list(df.columns)
    
    if len(daftar_kolom) >= 2:
        col_x, col_y, col_jenis = st.columns(3)
        with col_x:
            sumbu_x = st.selectbox("Sumbu X (Bulan/Jam/Kategori):", options=daftar_kolom, index=0)
        with col_y:
            sumbu_y = st.selectbox("Sumbu Y (Nilai Parameter):", options=daftar_kolom, index=1)
        with col_jenis:
            jenis_grafik = st.selectbox("Model Tampilan Grafik:", options=["Grafik Garis", "Grafik Batang", "Titik Sebaran (Scatter)"])

        # FITUR BARU: Menggabungkan nilai (Rata-rata) jika ada banyak data bertumpuk di 1 bulan
        df_agregasi = df.groupby(sumbu_x, as_index=False)[sumbu_y].mean()
        
        # Membuat Plotly Chart
        if jenis_grafik == "Grafik Garis":
            fig = px.line(df_agregasi, x=sumbu_x, y=sumbu_y, markers=True, title=f"Rata-rata Tren {sumbu_y} terhadap {sumbu_x}")
        elif jenis_grafik == "Grafik Batang":
            fig = px.bar(df_agregasi, x=sumbu_x, y=sumbu_y, title=f"Rata-rata {sumbu_y} berdasarkan {sumbu_x}")
        else:
            # Gunakan data asli (df) tanpa agregasi untuk melihat sebaran semua data per bulan/jam
            fig = px.scatter(df, x=sumbu_x, y=sumbu_y, title=f"Sebaran Seluruh Data {sumbu_y} terhadap {sumbu_x}")
            
        fig.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("⚠️ Data di dalam Excel ini kurang dari 2 kolom, tidak dapat divisualisasikan menjadi grafik.")

except Exception as e:
    st.error(f"⚠️ **Terjadi Kesalahan:** {e}")
