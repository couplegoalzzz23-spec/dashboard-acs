import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. KONFIGURASI HALAMAN (TAMPILAN PROFESIONAL)
# ==========================================
st.set_page_config(
    page_title="Dashboard Operasional Lanud RSN",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan lebih rapi dan responsif
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0px;}
    .sub-header {font-size: 1.2rem; color: #4B5563; margin-bottom: 20px;}
    .st-emotion-cache-1y4p8pa {padding-top: 2rem;} /* Kurangi jarak atas */
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI UTAMA (TAHAN BANTING & CACHING)
# ==========================================
@st.cache_data(show_spinner=False)
def load_data(file_path):
    """Fungsi untuk membaca excel dengan penanganan error"""
    try:
        # Engine openpyxl wajib untuk format .xlsx
        df = pd.read_excel(file_path, engine='openpyxl')
        return df
    except Exception as e:
        return str(e)

def format_nama_file(filename):
    """Merubah nama file excel menjadi judul yang mudah dibaca"""
    name = filename.replace('.xlsx', '').replace('.xls', '')
    name = name.replace('_', ' ').title()
    return name

# ==========================================
# 3. STRUKTUR UI & NAVIGASI (SIDEBAR)
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/TNI_Angkatan_Udara_Logo.png/150px-TNI_Angkatan_Udara_Logo.png", width=100) # Bisa diganti logo Lanud RSN
st.sidebar.markdown("### PANEL KENDALI")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "PILIH MODE OPERASIONAL:",
    ["📊 Data Historis (Database)", "📤 Analisis Manual (Upload ACS)"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Sistem Informasi Cuaca & Penerbangan")
st.sidebar.caption("Pangkalan TNI AU Roesmin Nurjadin")

# ==========================================
# 4. LOGIKA MENU 1: DATA HISTORIS (DATABASE DATA/)
# ==========================================
if menu == "📊 Data Historis (Database)":
    st.markdown('<p class="main-header">Data Historis Operasional</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Analisis pengaruh cuaca terhadap persentase dan kejadian masuk (2021-2025)</p>', unsafe_allow_html=True)
    
    # Cek folder data
    DATA_DIR = "data"
    if not os.path.exists(DATA_DIR):
        st.error(f"⚠️ Direktori '{DATA_DIR}' tidak ditemukan di server/github.")
    else:
        # Ambil semua file excel di folder data
        file_list = [f for f in os.listdir(DATA_DIR) if f.endswith(('.xlsx', '.xls'))]
        
        if not file_list:
            st.warning("⚠️ Tidak ada file Excel ditemukan di dalam folder 'data'.")
        else:
            # Buat dictionary untuk mapping nama file asli dengan nama yang diformat
            file_dict = {format_nama_file(f): f for f in file_list}
            
            col1, col2 = st.columns([3, 1])
            with col1:
                pilihan_data = st.selectbox("Pilih Parameter Data:", options=list(file_dict.keys()))
            with col2:
                jenis_grafik = st.selectbox("Jenis Visualisasi:", ["Line Chart (Tren)", "Bar Chart (Perbandingan)"])
            
            # Load Data
            file_path = os.path.join(DATA_DIR, file_dict[pilihan_data])
            df = load_data(file_path)
            
            if isinstance(df, str): # Jika error saat membaca (mengembalikan string error)
                st.error(f"Gagal membaca file: {df}")
            elif df.empty:
                st.warning("Data kosong.")
            else:
                st.markdown("---")
                # Area Visualisasi & Tabel menggunakan Tab agar hemat tempat di Tablet/HP
                tab1, tab2 = st.tabs(["📈 Visualisasi Data", "📋 Tabel Data Mentah"])
                
                with tab1:
                    try:
                        # Logika dinamis: Asumsi kolom pertama adalah X (misal: Tahun/Bulan), sisanya Y
                        kolom_x = df.columns[0]
                        kolom_numerik = df.select_dtypes(include=['number']).columns.tolist()
                        
                        if kolom_x in kolom_numerik:
                            kolom_numerik.remove(kolom_x)
                            
                        if not kolom_numerik:
                            st.info("Tidak ada kolom angka untuk dibuatkan grafik.")
                        else:
                            if jenis_grafik == "Line Chart (Tren)":
                                fig = px.line(df, x=kolom_x, y=kolom_numerik, markers=True, template="plotly_white")
                            else:
                                fig = px.bar(df, x=kolom_x, y=kolom_numerik, barmode='group', template="plotly_white")
                                
                            fig.update_layout(
                                legend_title_text='Parameter',
                                hovermode="x unified",
                                margin=dict(l=0, r=0, t=30, b=0) # Memaksimalkan ruang di layar HP
                            )
                            # use_container_width=True membuat grafik responsif ke HP/PC
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error("Terjadi kesalahan saat membuat visualisasi. Pastikan format tabel excel sudah benar.")
                
                with tab2:
                    # Tabel interaktif
                    st.dataframe(df, use_container_width=True)

# ==========================================
# 5. LOGIKA MENU 2: UPLOAD MANUAL (FILE ACS)
# ==========================================
elif menu == "📤 Analisis Manual (Upload ACS)":
    st.markdown('<p class="main-header">Analisis Data Mandiri</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Unggah file data operasional terbaru (.xlsx / .xls) untuk analisis cepat.</p>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Seret dan jatuhkan file Excel ke sini, atau klik tombol Browse", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        df_upload = load_data(uploaded_file)
        
        if isinstance(df_upload, str):
            st.error(f"Gagal memproses file: {df_upload}")
        else:
            st.success(f"File **{uploaded_file.name}** berhasil dimuat!")
            st.markdown("---")
            
            # Tampilkan kontrol visualisasi untuk data upload
            col_x, col_y = st.columns(2)
            with col_x:
                pilih_x = st.selectbox("Pilih Kolom untuk Sumbu X (Waktu/Kategori):", df_upload.columns)
            with col_y:
                kolom_num = df_upload.select_dtypes(include=['number']).columns.tolist()
                pilih_y = st.multiselect("Pilih Kolom untuk Sumbu Y (Nilai Angka):", kolom_num, default=kolom_num[:1] if kolom_num else None)
            
            if pilih_x and pilih_y:
                fig_up = px.line(df_upload, x=pilih_x, y=pilih_y, markers=True, template="plotly_white")
                fig_up.update_layout(hovermode="x unified")
                st.plotly_chart(fig_up, use_container_width=True)
                
            st.markdown("#### Detail Tabel")
            st.dataframe(df_upload, use_container_width=True)
