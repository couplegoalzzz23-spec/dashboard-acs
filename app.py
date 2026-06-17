import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# CONFIG & INITIALIZATION
# ==========================================
st.set_page_config(
    page_title="Dashboard ACS Interaktif", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("✈️ Aerodrome Climatological Summary (ACS) Dashboard")
st.markdown("### Analisis Data Klimatologi Operasional Penerbangan (Periode 2021 - 2025)")
st.markdown("---")

# Menggunakan pathlib agar pembacaan folder aman di OS Windows maupun Linux (Server Streamlit)
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# ==========================================
# SIDEBAR NAVIGATION & MAPPING
# ==========================================
st.sidebar.header("📁 Navigasi Data")

# Mapping nama opsi yang rapi ke nama file asli di folder data Anda
FILE_MAPPING = {
    "Rata-rata Kejadian Masuk (RH)": "rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx",
    "Rata-rata Kejadian Masuk (Tmax/Tmin)": "rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx",
    "Persentase Heiligenschein (HS)": "rata_rata_persentase_hs_2021_2025.xlsx",
    "Persentase Temperatur": "rata_rata_persentase_temperature_2021_2025.xlsx",
    "Persentase Visibility": "rata_rata_persentase_visibility_2021_2025.xlsx",
    "Persentase Wind Speed (WS)": "rata_rata_persentase_ws_2021_2025.xlsx"
}

pilihan_parameter = st.sidebar.selectbox(
    "Pilih Parameter ACS yang Ingin Dianalisis:",
    options=list(FILE_MAPPING.keys())
)

file_terpilih = FILE_MAPPING[pilihan_parameter]
FULL_PATH = DATA_DIR / file_terpilih

# ==========================================
# ROBUST DATA LOADING FUNCTION (SAFE ENGINE)
# ==========================================
@st.cache_data(show_spinner="Sedang memuat data dari database...", ttl=3600)
def load_and_clean_data(file_path: Path):
    """
    Fungsi membaca Excel dengan proteksi eror format.
    Mencegah eror akibat adanya spasi gaib pada nama kolom di Excel.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan di folder data: {file_path.name}")
        
    # Membaca excel menggunakan engine openpyxl (paling stabil untuk .xlsx)
    df = pd.read_excel(file_path, engine="openpyxl")
    
    # PEMBERSIHAN DATA (Anti-Eror Masa Depan):
    # Menghapus spasi di awal/akhir nama kolom jika ada ketidaksengajaan saat input data
    df.columns = [str(col).strip() for col in df.columns]
    
    return df

# ==========================================
# MAIN APP LOGIC WITH ERROR HANDLING (TRY-EXCEPT)
# ==========================================
try:
    # Memuat data secara aman
    df = load_and_clean_data(FULL_PATH)
    
    # Menampilkan Informasi Ringkas di Atas
    st.subheader(f"📊 Tabel Data Terbuka: {pilihan_parameter}")
    
    # Fitur pencarian/filter cepat bawaan Streamlit
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📈 Visualisasi Grafik Interaktif")
    
    # Ambil daftar semua kolom yang tersedia di file Excel terpilih
    daftar_kolom = list(df.columns)
    
    if len(daftar_kolom) >= 2:
        # PENCEGAHAN CRASH GRAFIK: 
        # Coba deteksi kolom waktu otomatis (Bulan/Jam/Waktu), jika tidak ada pasang kolom pertama
        kandidat_x = [c for c in daftar_kolom if c.lower() in ['bulan', 'jam', 'waktu', 'tanggal', 'periode']]
        idx_default_x = daftar_kolom.index(kandidat_x[0]) if kandidat_x else 0
        
        # Coba deteksi kandidat sumbu Y (kolom selain X)
        kandidat_y = [c for c in daftar_kolom if c not in kandidat_x]
        idx_default_y = daftar_kolom.index(kandidat_y[0]) if kandidat_y else (1 if len(daftar_kolom) > 1 else 0)
        
        # Biarkan user memilih sumbu secara dinamis jika struktur kolom Excel berubah di masa depan
        col1, col2, col3 = st.columns(3)
        with col1:
            sumbu_x = st.selectbox("Sumbu X (Horizontal):", options=daftar_kolom, index=idx_default_x, key="sb_x")
        with col2:
            sumbu_y = st.selectbox("Sumbu Y (Vertikal/Nilai):", options=daftar_kolom, index=idx_default_y, key="sb_y")
        with col3:
            jenis_grafik = st.selectbox("Model Grafik:", options=["Garis (Line Chart)", "Batang (Bar Chart)", "Area Chart"])
            
        # Membuat grafik menggunakan Plotly secara dinamis
        if jenis_grafik == "Garis (Line Chart)":
            fig = px.line(df, x=sumbu_x, y=sumbu_y, title=f"Tren {sumbu_y} berdasarkan {sumbu_x}", markers=True)
        elif jenis_grafik == "Batang (Bar Chart)":
            fig = px.bar(df, x=sumbu_x, y=sumbu_y, title=f"Perbandingan {sumbu_y} berdasarkan {sumbu_x}")
        else:
            fig = px.area(df, x=sumbu_x, y=sumbu_y, title=f"Distribusi Area {sumbu_y} berdasarkan {sumbu_x}")
            
        # Kustomisasi tampilan grafik agar serasi dan modern
        fig.update_layout(
            hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        
        # Tampilkan grafik ke web
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("⚠️ File Excel ini memiliki kurang dari 2 kolom, tidak dapat diubah menjadi grafik tren.")

except FileNotFoundError as e:
    st.error(f"❌ **Eror Infrastruktur:** {e}")
    st.info("💡 Bereskan dengan memastikan nama file di folder `data/` pada GitHub sama persis dengan kode mapping.")

except Exception as e:
    st.error(f"⚠️ **Terjadi Kesalahan Teknis:** {e}")
    st.info("💡 Sistem tetap berjalan aman. Eror ini biasanya disebabkan oleh struktur isi sheet Excel yang tidak standar.")

# ==========================================
# FOOTER DASHBOARD
# ==========================================
st.markdown("---")
st.caption("Dashboard ACS v2.0 • Dilindungi sistem proteksi modular anti-crash.")
