import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# ==========================================
# CONFIGURATION & PAGE SETTINGS
# ==========================================
st.set_page_config(
    page_title="ACS Interactive Dashboard",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk memperindah tampilan tata letak
st.markdown("""
    <style>
    .main-title { font-size:2.4rem !important; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem; }
    .sub-title { font-size:1.1rem !important; color: #4B5563; margin-bottom: 2rem; }
    .metric-card { background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 5px solid #2563EB; }
    </style>
""", unsafe_style_html=True)

# ==========================================
# DEMO DATA FALLBACK (Tahan Banting / No-File Safety)
# ==========================================
SAMPLE_MODEL_C = """AERODROME CLIMATOLOGICAL SUMMARY
TABULAR FORM MODEL C, MONTH : DESEMBER (DEMO DATA)
TOTAL OF OBSERVATION : 720, OBSERVATION TIME : 24 HRS
LATITUDE : 0.28 N LONGITUDE : 101.26 E, ELEVATION ABOVE MSL : 27 M
FREQUENCIES (PERCENT) OF HEIGHT OF THE BASE OF THE LOWEST CLOUD LAYER
(GMT),< 150,< 200,< 300,< 500,< 1000,< 1500
0,0,0,1,1,7,24
1,0,0,0,0,9,29
2,0,0,0,0,12,30
3,0,0,0,0,7,30
4,0,0,0,0,8,30
5,0,0,0,0,5,30
6,0,0,0,0,3,29
7,0,0,0,0,1,27
8,0,0,0,0,0,24
9,0,0,0,0,0,23
10,0,0,0,0,0,24
11,0,0,0,0,0,23
12,0,0,0,0,1,23
13,0,0,0,0,1,20
14,0,0,0,0,1,18
15,0,0,0,0,0,15
16,0,0,0,0,0,12
17,0,0,0,0,0,10
18,0,0,0,0,0,11
19,0,0,0,0,0,14
20,0,0,0,0,0,15
21,0,0,0,0,0,16
22,0,0,0,0,0,18
23,0,0,0,0,1,20"""

SAMPLE_MODEL_E = """AERODROME CLIMATOLOGICAL SUMMARY
TABULAR FORM MODEL E, MONTH : DESEMBER (DEMO DATA)
TOTAL NUMBER OF OBSERVATION : 720, OBSERVATION TIME : 24 HRS
LATITUDE : 0.28 N LONGITUDE : 101.26 E, ELEVATION ABOVE MSL : 27 M
FREQUENCIES (PERCENT) OF SURFACE TEMPERATURE
(GMT),20 - 25,25 - 30,30 - 35
0,80.65,19.35,0.00
1,38.71,61.29,0.00
2,6.45,93.55,0.00
3,3.23,93.55,3.23
4,3.23,90.32,6.45
5,3.23,64.52,32.25
6,0.00,50.00,50.00
7,0.00,55.00,45.00
8,5.00,70.00,25.00
9,15.00,80.00,5.00
10,40.00,60.00,0.00
11,60.00,40.00,0.00
12,75.00,25.00,0.00
13,85.00,15.00,0.00
14,90.00,10.00,0.00
15,92.00,8.00,0.00
16,95.00,5.00,0.00
17,95.00,5.00,0.00
18,95.00,5.00,0.00
19,95.00,5.00,0.00
20,90.00,10.00,0.00
21,88.00,12.00,0.00
22,85.00,15.00,0.00
23,82.00,18.00,0.00"""

# ==========================================
# CORE PARSING FUNCTION (Robust Scanner)
# ==========================================
def parse_acs_data(file_content_str):
    """
    Membaca string file CSV ACS secara aman, mengekstrak metadata header,
    dan mengembalikan dataframe numerik berbasis jam (0-23).
    """
    lines = [line.strip() for line in file_content_str.split('\n')]
    
    # Inisialisasi metadata default
    meta = {
        "model_type": "Format Tidak Dikenal",
        "month": "Tidak Terdeteksi",
        "lat_long": "Tidak Terdeteksi",
        "elevation": "Tidak Terdeteksi",
        "total_obs": "Tidak Terdeteksi"
    }
    
    gmt_line_idx = -1
    
    # Pemindaian Header & Deteksi Baris Kunci
    for idx, line in enumerate(lines[:20]):
        line_upper = line.upper()
        if "MODEL C" in line_upper:
            meta["model_type"] = "Model C (Tinggi Dasar Awan Rendah / Cloud Base Height)"
        elif "MODEL E" in line_upper:
            meta["model_type"] = "Model E (Persentase Suhu Permukaan / Surface Temperature)"
            
        if "MONTH :" in line_upper:
            meta["month"] = line.split("MONTH :")[-1].split(",")[0].strip()
        if "LATITUDE" in line_upper:
            meta["lat_long"] = line.split(",")[0].strip() if "," in line else line
        if "ELEVATION" in line_upper:
            meta["elevation"] = line.split("ELEVATION")[-1].replace("ABOVE MSL", "").replace(":", "").strip()
        if "TOTAL" in line_upper:
            meta["total_obs"] = line.split("OBSERVATION")[-1].replace(":", "").strip()
            
        # Mencari letak header tabel utama
        if "(GMT)" in line:
            gmt_line_idx = idx
            
    if gmt_line_idx == -1:
        return None, None, "Gagal memproses: Kolom indeks waktu '(GMT)' tidak ditemukan."

    # Pembersihan Nama Kolom
    header_cols = [c.replace('"', '').strip() for c in lines[gmt_line_idx].split(',')]
    while header_cols and header_cols[-1] == '':
        header_cols.pop()
        
    # Ekstraksi Baris Data Numerik Jam 00 s.d 23
    data_matrix = []
    for line in lines[gmt_line_idx + 1:]:
        if not line or line.startswith(','):
            continue
        parts = [p.replace('"', '').strip() for p in line.split(',')]
        
        try:
            # Validasi apakah kolom pertama adalah representasi jam integer asli
            hour_val = int(float(parts[0]))
            if 0 <= hour_val <= 23:
                row_aligned = parts[:len(header_cols)]
                numeric_row = []
                for val in row_aligned:
                    try:
                        numeric_row.append(float(val))
                    except ValueError:
                        numeric_row.append(0.0)
                data_matrix.append(numeric_row)
        except (ValueError, IndexError):
            continue  # Mengabaikan baris rata-rata (MEAN) atau catatan kaki otomatis

    if not data_matrix:
        return None, None, "Struktur baris tabel tidak sesuai standar rentang jam 0-23."
        
    df = pd.DataFrame(data_matrix, columns=header_cols)
    df[header_cols[0]] = df[header_cols[0]].astype(int)
    df = df.set_index(header_cols[0])
    
    return df, meta, None

# ==========================================
# SIDEBAR CONTROL PANEL (Menu Input Manual)
# ==========================================
st.sidebar.title("🎛️ Panel Kontrol ACS")

data_source = st.sidebar.radio(
    "Pilih Sumber Data:",
    ["Gunakan Data Demo Bawaan", "Upload File CSV Manual"]
)

uploaded_file = None
file_string_content = ""

if data_source == "Upload File CSV Manual":
    uploaded_file = st.sidebar.file_uploader(
        "Unggah File Model C atau Model E (.csv):",
        type=["csv"],
        help="Pastikan struktur file memiliki baris berisi koordinat dan tabel indeks jam (GMT)"
    )
    if uploaded_file is not None:
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8", errors="ignore"))
        file_string_content = stringio.read()
    else:
        st.sidebar.info("💡 Silakan upload file untuk melihat pembaruan grafik.")
        # Fallback ke demo jika di-pilih upload tapi file belum ada
        file_string_content = SAMPLE_MODEL_C 
else:
    demo_type = st.sidebar.selectbox("Pilih Jenis Data Demo:", ["Model C (Cloud Height)", "Model E (Temperature)"])
    file_string_content = SAMPLE_MODEL_C if "Model C" in demo_type else SAMPLE_MODEL_E

# Proses Data
df_clean, metadata, error_msg = parse_acs_data(file_string_content)

# Opsi Konversi Jam Operasional
st.sidebar.subheader("🕒 Pengaturan Waktu")
tz_option = st.sidebar.selectbox(
    "Geser Zona Waktu Tampilan:",
    ["Sesuai File Asli (GMT / UTC)", "Waktu Indonesia Barat (WIB / GMT+7)", "Waktu Indonesia Tengah (WITA / GMT+8)", "Waktu Indonesia Timur (WIT / GMT+9)"]
)

tz_offset = 0
if "WIB" in tz_option: tz_offset = 7
elif "WITA" in tz_option: tz_offset = 8
elif "WIT" in tz_option: tz_offset = 9

# ==========================================
# MAIN DASHBOARD INTERFACE
# ==========================================
st.markdown('<div class="main-title">Interactive Aerodrome Climatological Summary</div>', unsafe_style_html=True)
st.markdown('<div class="sub-title">Analisis Dinamis Distribusi Frekuensi Parameter Cuaca Penerbangan</div>', unsafe_style_html=True)

if error_msg:
    st.error(error_msg)
else:
    # Mengaplikasikan Pergeseran Zona Waktu secara Dinamis
    df_plot = df_clean.copy()
    time_label = "Jam (GMT)"
    if tz_offset != 0:
        df_plot.index = (df_plot.index + tz_offset) % 24
        df_plot = df_plot.sort_index()
        time_label = f"Jam Lokal Tampilan (GMT+{tz_offset})"

    # Tampilan Informasi Stasiun / Metadata Panel Top
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><b>Tipe Ringkasan</b><br><span style="color:#2563EB;font-weight:bold;">{metadata["model_type"]}</span></div>', unsafe_style_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><b>Bulan Analisis</b><br><span style="color:#2563EB;font-weight:bold;">{metadata["month"]}</span></div>', unsafe_style_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><b>Posisi Stasiun / Koordinat</b><br><span style="color:#10B981;font-weight:bold;">{metadata["lat_long"]}</span></div>', unsafe_style_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><b>Elevasi & Batas Sampel</b><br><span style="color:#10B981;font-weight:bold;">{metadata["elevation"]} ({metadata["total_obs"]})</span></div>', unsafe_style_html=True)

    st.markdown("---")

    # Penyajian Tab Menu Visualisasi Interaktif
    tab1, tab2, tab3 = st.tabs(["📊 Grafis Batang Akumulatif", "🔥 Peta Panas (Heatmap Diurnal)", "📋 Lembar Data Terurai"])

    with tab1:
        st.subheader("Distribusi Kontribusi Frekuensi Per Jam")
        # Melebur kolom dataframe agar kompatibel dengan Plotly Express Stacked Bar
        df_melted = df_plot.reset_index().melt(id_vars=df_plot.index.name, var_name="Kategori Parameter", value_name="Persentase Kejadian (%)")
        
        fig_bar = px.bar(
            df_melted,
            x=df_plot.index.name,
            y="Persentase Kejadian (%)",
            color="Kategori Parameter",
            title=f"Variasi Diurnal Persentase Kejadian Berdasarkan {time_label}",
            labels={df_plot.index.name: time_label},
            barmode="stack",
            text_auto='.1f' if len(df_plot.columns) < 5 else False
        )
        fig_bar.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1), hovermode="x unified")
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("Analisis Matriks Kepadatan Jam vs Parameter")
        # Membuat visualisasi Heatmap Interaktif yang sangat disukai praktisi meteorologi
        fig_heat = go.Figure(data=go.Heatmap(
            z=df_plot.values.T,
            x=df_plot.index,
            y=df_plot.columns,
            colorscale='Viridis',
            colorbar=dict(title="Frekuensi (%)"),
            hovertemplate=f"{time_label}: %{{x}}<br>Rentang: %{{y}}<br>Nilai: %{{z}}%<extra></extra>"
        ))
        fig_heat.update_layout(
            title=f"Korelasi Kepadatan Waktu Terhadap Parameter ({time_label})",
            xaxis=dict(title=time_label, tickmode='linear', tick0=0, dtick=1),
            yaxis=dict(title="Kategori / Rentang Kelas Data")
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with tab3:
        st.subheader("Tabel Konvensional Hasil Ekstraksi Sistem")
        st.markdown("Data di bawah ini disesuaikan berdasarkan pergeseran waktu yang Anda tentukan di panel kiri:")
        
        # Tampilan Tabel Pandas interaktif bawaan Streamlit
        st.dataframe(df_plot.style.format("{:.2f}").background_gradient(cmap='Blues'), use_container_width=True)
        
        # Fitur unduh instan ke bentuk csv bersih untuk kebutuhan olah lanjut
        csv_download = df_plot.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Unduh File CSV Bersih Hasil Olahan",
            data=csv_download,
            file_name=f"ACS_Clean_Export_{metadata['month']}.csv",
            mime='text/csv'
        )
