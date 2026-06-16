import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA
# ==========================================
st.set_page_config(
    page_title="Tactical Dashboard ACS - Lanud RSN",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kustomisasi tema visual militer / profesional via markdown
st.markdown("""
    <style>
    .main-header { font-size:28px !important; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .sub-header { font-size:16px !important; color: #4B5563; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI PENYOKONG (HELPER FUNCTIONS)
# ==========================================
@st.cache_data(show_spinner=False)
def load_excel_data(file_path):
    """Membaca file Excel dengan aman dan menangani error pembacaan."""
    try:
        df = pd.read_excel(file_path)
        # Membersihkan spasi pada nama kolom agar tidak memicu KeyError
        df.columns = [str(col).strip() for col in df.columns]
        return df
    except Exception as e:
        st.error(f"⚠️ Gagal membaca file: {os.path.basename(file_path)}. Error: {e}")
        return None

def get_clean_param_name(filename):
    """Mengubah nama file teknis menjadi label parameter yang rapi."""
    fn = filename.lower()
    labels = []
    
    # Deteksi Tipe Data
    if "jumlah_kejadian" in fn:
        labels.append("[Frekuensi]")
    elif "persentase" in fn:
        labels.append("[Persentase]")
        
    # Deteksi Parameter Meteorologi
    if "temperature" in fn:
        labels.append("Suhu Udara (Temperature)")
    elif "tmaxmin" in fn:
        labels.append("Suhu Maksimum & Minimum")
    elif "visibility" in fn:
        labels.append("Jarak Pandang (Visibility)")
    elif "ws" in fn:
        labels.append("Kecepatan Angin (Wind Speed)")
    elif "rh" in fn:
        labels.append("Kelembapan Relatif (Relative Humidity)")
    elif "hs" in fn:
        labels.append("Tinggi Dasar Awan / Jam Cerah (HS)")
    else:
        labels.append(filename.split('_')[0])
        
    return " ".join(labels)

# ==========================================
# 3. SIDEBAR NAVIGATION & MENU
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/fighter-jet.png", width=80)
    st.title("Navigasi Operasional")
    
    menu_mode = st.radio(
        "Pilih Sumber Data:",
        ["📁 Aerodrome Climatological Summary (ACS)", "📤 Upload Data Manual (Taktis)"]
    )
    
    st.write("---")
    st.caption("⚡ **Sistem Informasi Cuaca Lanud Roesmin Nurjadin**")
    st.caption("Rapi, Bersih, & Tahan Banting v1.0")

# ==========================================
# 4. LOGIKA UTAMA APLIKASI
# ==========================================

# HEADER UTAMA APLIKASI
st.markdown('<p class="main-header">✈️ TACTICAL METEOROLOGICAL DASHBOARD</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Integrasi Informasi Klimatologi & Data Observasi untuk Mendukung Operasional Penerbangan Lanud RSN</p>', unsafe_allow_html=True)

df_active = None
source_info = ""

if menu_mode == "📁 Aerodrome Climatological Summary (ACS)":
    st.subheader("Data Statistik Historis Basis RSN (2021-2025)")
    
    # Lokasi direktori data lokal/GitHub
    DATA_DIR = "data"
    
    if os.path.exists(DATA_DIR):
        # Scan file .xlsx dan mengantisipasi double extension (.xlsx.xlsx)
        all_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.xlsx') or f.endswith('.xlsx.xlsx')]
        
        if all_files:
            # Membuat mapping nama file asli ke nama bersayap yang rapi
            file_mapping = {get_clean_param_name(f): f for f in all_files}
            
            selected_label = st.selectbox(
                "🎯 Pilih Parameter ACS RSN yang Ingin Dianalisis:",
                options=list(file_mapping.keys())
            )
            
            filename_target = file_mapping[selected_label]
            full_path = os.path.join(DATA_DIR, filename_target)
            
            # Load data ke DataFrame aktif
            df_active = load_excel_data(full_path)
            source_info = f"Sumber Data Internal: `data/{filename_target}`"
            
        else:
            st.warning(f"Folder `{DATA_DIR}/` ditemukan, tetapi tidak ada file `.xlsx` di dalamnya.")
    else:
        st.error(f"⚠️ Folder `{DATA_DIR}/` tidak terdeteksi di repositori Anda. Pastikan folder data sudah di-commit.")

else:
    # JIKA USER MEMILIH UPLOAD MANUAL
    st.subheader("Analisis Data Taktis Mandiri (Upload Manual)")
    st.info("Menu ini digunakan jika sewaktu-waktu Anda memiliki file data cuaca baru di luar dataset utama ACS.")
    
    uploaded_file = st.file_uploader(
        "Unggah File Excel Meteorologi (.xlsx):", 
        type=["xlsx"]
    )
    
    if uploaded_file is not None:
        df_active = load_excel_data(uploaded_file)
        source_info = f"Sumber Data: Upload Manual (`{uploaded_file.name}`)"
    else:
        st.info("💡 Silakan unggah file Excel melalui panel di atas untuk memulai analisis.")

# ==========================================
# 5. RENDER GRAFIK & VISUALISASI DATA DYNAMIC
# ==========================================
if df_active is not None:
    st.success(f"✅ Data Berhasil Dimuat! ({source_info})")
    
    # Tampilkan Ringkasan Data Sederhana di Atas Berbentuk Kolom Metric
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric(label="Total Baris Data", value=df_active.shape[0])
    with col_stat2:
        st.metric(label="Total Kolom/Variabel", value=df_active.shape[1])
        
    st.write("---")
    
    # GRID KONTROL GRAFIK (Fleksibel, mendeteksi kolom otomatis)
    st.markdown("### 📊 Pengaturan Visualisasi Grafik")
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    
    all_columns = list(df_active.columns)
    
    with col_ctrl1:
        x_axis = st.selectbox("Sumbu X (Kategori/Waktu/Jam):", options=all_columns, index=0)
    with col_ctrl2:
        # Menyaring kolom numerik atau memberikan semua pilihan
        y_axis = st.multiselect("Sumbu Y (Parameter Nilai):", options=all_columns, default=[all_columns[1]] if len(all_columns) > 1 else [all_columns[0]])
    with col_ctrl3:
        chart_type = st.selectbox("Tipe Grafik:", ["Garis (Line Chart)", "Batang (Bar Chart)"])
        
    # PROSES PEMBUATAN GRAFIK PLOTLY (Anti-Crash)
    if y_axis:
        try:
            if chart_type == "Garis (Line Chart)":
                fig = px.line(df_active, x=x_axis, y=y_axis, markers=True,
                              title=f"Analisis Grafik Garis Parameter Berdasarkan {x_axis}",
                              template="plotly_dark")
            else:
                fig = px.bar(df_active, x=x_axis, y=y_axis, barmode="group",
                             title=f"Analisis Grafik Batang Parameter Berdasarkan {x_axis}",
                             template="plotly_dark")
            
            # Kustomisasi tata letak grafik agar serasi dengan kebutuhan militer
            fig.update_layout(
                hovermode="x unified",
                xaxis_title=str(x_axis).upper(),
                yaxis_title="NILAI PARAMETER",
                legend_title="Variabel",
                margin=dict(l=40, r=40, t=50, b=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Gagal merender grafik dengan kolom yang dipilih. Pastikan tipe data kolom berupa angka. Error: {e}")
    else:
        st.warning("Silakan pilih minimal satu variabel Sumbu Y untuk memunculkan grafik.")
        
    st.write("---")
    
    # TABEL DATA INTERAKTIF
    with st.expander("🔍 Lihat Lembar Tabel Data Lengkap (Spreadsheet View)"):
        st.dataframe(df_active, use_container_width=True)
