import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ==========================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="ACS Dashboard - Mil Av",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kustomisasi Tema Gelap (Dark Mode) yang lebih presisi
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    h1, h2, h3, p { color: #FAFAFA; }
    .stDataFrame { border-radius: 8px; }
    /* Mempercantik Metrics */
    div[data-testid="metric-container"] {
        background-color: #262730;
        border: 1px solid #4B4B4B;
        padding: 10px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI UNTUK MEMUAT & MEMBERSIHKAN DATA
# ==========================================
# Fungsi ini dirancang "tahan banting" menggunakan error handling
@st.cache_data(show_spinner="Memuat Data Climatological...")
def load_data(uploaded_file):
    try:
        if uploaded_file is None:
            return pd.DataFrame()
            
        # Membaca CSV dan melewati baris header yang berantakan (biasanya baris ke-9 atau ke-10 pada data ACS standar)
        # Menyesuaikan dengan format gambar, kita akan mencari baris yang berisi 'TIME' atau '(GMT)'
        # Untuk kepraktisan simulasi ini, mari kita baca langsung
        df = pd.read_csv(uploaded_file, skiprows=9)
        
        # Bersihkan spasi pada nama kolom
        df.columns = df.columns.str.strip()
        
        # Buang baris yang isinya NaN semua atau baris footer seperti 'MEAN'
        df = df.dropna(how='all')
        df = df[~df.iloc[:, 0].astype(str).str.contains("MEAN|TOTAL", case=False, na=False)]
        
        return df
        
    except Exception as e:
        st.error(f"Gagal memuat file: {e}")
        return pd.DataFrame()

# ==========================================
# 3. SIDEBAR & NAVIGASI
# ==========================================
with st.sidebar:
    # Menampilkan Logo jika ada file logo.png di folder
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #4B90E2;'>BMKG - ACS Ops</h2>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.header("🎛️ Filter Panel")
    
    # 3.1 Pilihan Stasiun
    selected_station = st.selectbox(
        "Pilih Stasiun:",
        ["Lanud Roesmin Nurjadin", "Lanud Halim Perdanakusuma", "Lanud Iswahjudi"]
    )
    
    # 3.2 Pilihan Parameter
    selected_param = st.selectbox(
        "Pilih Parameter ACS:",
        ["Cloud Base Height (Hs)", "Surface Temperature", "Visibility", "Wind Speed"]
    )
    
    # 3.3 Upload File
    st.markdown("---")
    st.markdown("**📂 Upload Data Operasional (.csv)**")
    uploaded_files = st.file_uploader("Upload file ACS per bulan", type=['csv'], accept_multiple_files=True)
    
    # Ekstrak nama bulan dari file yang diupload
    available_months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    selected_month = st.selectbox("Pilih Bulan:", available_months)

# ==========================================
# 4. KONTEN UTAMA (MAIN AREA)
# ==========================================
st.title("AERODROME CLIMATOLOGICAL SUMMARY (ACS)")
st.caption(f"📍 Stasiun: {selected_station} | Parameter: {selected_param}")

# ==========================================
# 5. LOGIKA PENAMPILAN DATA & VISUALISASI
# ==========================================
if uploaded_files:
    # Cari file yang sesuai dengan bulan yang dipilih
    # Misal nama file: rata_rata_jumlah_kejadian_masuk_hs_2021_2025 - Desember.csv
    target_file = None
    for file in uploaded_files:
        if selected_month.lower() in file.name.lower():
            target_file = file
            break
            
    if target_file:
        # Load Data
        df = load_data(target_file)
        
        if not df.empty:
            # Layout Kolom untuk Tabel dan Informasi Singkat
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(f"Tabel Frekuensi Historis - {selected_month}")
                # Render Tabel, asumsikan kolom pertama adalah TIME (GMT)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("Ringkasan Operasional")
                st.info(f"**Data Bersumber Dari:** {target_file.name}")
                st.metric(label="Total Jam Pengamatan", value="24 Jam", delta="Sesuai Standar WMO")
                st.metric(label="Periode ACS", value="2021 - 2025")
                st.markdown("""
                **Catatan Taktis:**
                Tabel di samping menampilkan persentase kejadian historis untuk parameter yang dipilih. 
                Waktu yang digunakan adalah **GMT/UTC**. Tambahkan +7 untuk konversi ke WIB.
                """)
            
            # --- BAGIAN VISUALISASI GRAFIK INTERAKTIF ---
            st.markdown("---")
            st.subheader(f"📈 Tren Distribusi {selected_param} per Jam")
            
            # Asumsi: Kolom pertama adalah waktu (0-23), kolom sisanya adalah kelas/range (misal: <150, <200, dst)
            time_col = df.columns[0]
            value_cols = df.columns[1:]
            
            # Mengubah format data tabel menjadi format panjang (melt) agar mudah dibaca oleh Plotly
            df_melted = df.melt(id_vars=[time_col], value_vars=value_cols, 
                                var_name="Kategori/Range", value_name="Frekuensi (%)")
            
            # Memastikan tipe data Frekuensi adalah numerik
            df_melted["Frekuensi (%)"] = pd.to_numeric(df_melted["Frekuensi (%)"], errors='coerce').fillna(0)
            
            # Membuat Bar Chart Interaktif
            fig = px.bar(
                df_melted, 
                x=time_col, 
                y="Frekuensi (%)", 
                color="Kategori/Range",
                title=f"Distribusi Frekuensi {selected_param} - Bulan {selected_month}",
                labels={time_col: "Waktu (GMT)", "Frekuensi (%)": "Persentase Kejadian (%)"},
                barmode='group', # atau 'stack' jika ingin ditumpuk
                color_discrete_sequence=px.colors.sequential.Blues_r # Tema warna yang elegan
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#FAFAFA'),
                xaxis=dict(tickmode='linear', tick0=0, dtick=1), # Memaksa sumbu x tampil 0,1,2..23
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("⚠️ Data berhasil dibaca, namun tabel kosong atau format tidak sesuai. Periksa kembali struktur CSV yang diunggah.")
    else:
        st.info(f"👉 File untuk bulan **{selected_month}** belum diunggah. Silakan upload file yang sesuai pada panel di sebelah kiri.")

else:
    # Tampilan awal jika belum ada file yang diunggah
    st.info("👋 Selamat Datang! Silakan unggah satu atau beberapa file `.csv` ACS Anda pada panel di sebelah kiri untuk memulai analisis.")
    
    # Menampilkan Gambar Placeholder (Opsional)
    # st.image("https://images.unsplash.com/photo-1540962351504-03099e0a754b?ixlib=rb-4.0.3", caption="Aviation Weather Ready")
