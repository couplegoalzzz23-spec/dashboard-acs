import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. KONFIGURASI ANTARMUKA (UI)
# ==========================================
st.set_page_config(
    page_title="Dashboard Operasional Lanud RSN",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema Militer Profesional (Navy Blue & Clean)
st.markdown("""
    <style>
    .main {background-color: #f4f6f9;}
    h1, h2, h3 {color: #1a237e;}
    .block-container {padding-top: 2rem;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ENGINE PEMROSES DATA (ANTI-CRASH)
# ==========================================
def bersihkan_data(df):
    """Fungsi ajaib untuk mengubah data berantakan jadi aman untuk grafik dan tabel"""
    if df is None or df.empty:
        return df
        
    # Hapus baris atau kolom yang 100% kosong (NaN)
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    # Pastikan semua nama kolom adalah teks murni agar PyArrow tidak crash
    df.columns = [str(col).strip() for col in df.columns]
    
    # Periksa tipe data setiap kolom
    for col in df.columns:
        if df[col].dtype == 'object':
            # Jika teks, paksa jadi string bersih
            df[col] = df[col].fillna('').astype(str).str.strip()
        else:
            # Jika angka, pastikan murni numerik
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

@st.cache_data(show_spinner=False)
def load_data_lokal(filepath, baris_header):
    """Membaca file dari folder GitHub dengan parameter pemotong baris judul"""
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, header=baris_header)
        else:
            df = pd.read_excel(filepath, engine='openpyxl', header=baris_header)
        return bersihkan_data(df)
    except Exception as e:
        return f"Gagal membaca berkas: {e}"

# ==========================================
# 3. NAVIGASI SIDEBAR (COMMAND CENTER)
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Lambang_TNI_AU.png", width=100)
st.sidebar.title("Command Center")
st.sidebar.markdown("**Lanud Roesmin Nurjadin**")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "PILIH MODUL OPERASIONAL:",
    ("📊 Analisis Data Historis", "📤 Upload Analisis Mandiri")
)

# ==========================================
# 4. HALAMAN UTAMA - DASHBOARD
# ==========================================
st.title("Sistem Informasi Cuaca & Operasional")
st.markdown("Pangkalan TNI AU Roesmin Nurjadin (RSN)")
st.markdown("---")

# ------------------------------------------
# MODUL 1: DATA HISTORIS (DARI GITHUB)
# ------------------------------------------
if menu == "📊 Analisis Data Historis":
    st.subheader("Modul Data Historis (2021 - 2025)")
    
    data_folder = "data"
    if os.path.exists(data_folder):
        # Membaca file CSV dan XLSX dari folder data
        files = [f for f in os.listdir(data_folder) if f.endswith(('.xlsx', '.csv'))]
        
        if len(files) > 0:
            col_file, col_header = st.columns([3, 1])
            with col_file:
                selected_file = st.selectbox("Pilih Dokumen Data:", files)
            with col_header:
                # FITUR BARU: Melewati baris judul laporan di Excel
                baris_header = st.number_input("Mulai dari Baris ke-", min_value=0, max_value=20, value=2, 
                                               help="Ubah angka ini jika tabel data tidak terbaca dengan benar karena ada judul laporan di baris atas Excel.")
            
            file_path = os.path.join(data_folder, selected_file)
            
            # Load Data
            hasil_load = load_data_lokal(file_path, baris_header)
            
            if isinstance(hasil_load, str):
                st.error(hasil_load)
            elif hasil_load is not None and not hasil_load.empty:
                
                tab1, tab2 = st.tabs(["📈 Tampilan Visual (Grafik)", "🗃️ Tampilan Tabular (Data Mentah)"])
                
                with tab1:
                    kolom_x = hasil_load.columns[0]
                    opsi_y = hasil_load.columns[1:].tolist()
                    
                    kolom_y = st.multiselect(
                        "Pilih Parameter Cuaca/Kejadian:", 
                        opsi_y, 
                        default=opsi_y[:1] if opsi_y else None
                    )
                    
                    if kolom_y:
                        try:
                            # Membuat Grafik
                            fig = px.line(
                                hasil_load, x=kolom_x, y=kolom_y, markers=True,
                                title=f"Tren Pergerakan Data",
                                template="plotly_white"
                            )
                            fig.update_layout(
                                hovermode="x unified", 
                                xaxis_title=str(kolom_x).upper(),
                                yaxis_title="NILAI / JUMLAH",
                                legend_title_text="Keterangan Parameter"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Grafik gagal dibuat. Pastikan data yang diplih berbentuk angka, atau sesuaikan pengaturan 'Mulai dari Baris ke-'. Detail: {e}")
                    else:
                        st.info("Pilih minimal satu parameter di atas untuk memunculkan grafik.")
                
                with tab2:
                    # Ubah ke string agar kebal dari error tampilan PyArrow Browser
                    st.dataframe(hasil_load.astype(str), use_container_width=True)
            else:
                st.warning("Data kosong. Coba ubah nilai 'Mulai dari Baris ke-' jika format Excel memiliki banyak judul.")
        else:
            st.warning("Tidak ada file (.xlsx / .csv) di dalam folder 'data'.")
    else:
        st.error("Folder bernama 'data' tidak ditemukan di sistem. Pastikan nama foldernya menggunakan huruf kecil semua.")

# ------------------------------------------
# MODUL 2: UPLOAD MANDIRI (FILE ACS)
# ------------------------------------------
elif menu == "📤 Upload Analisis Mandiri":
    st.subheader("Modul Analisis Berkas Cepat (ACS)")
    st.markdown("Fasilitas operasional untuk visualisasi data seketika tanpa perlu menyimpan ke server.")
    
    col_upload, col_header_up = st.columns([3, 1])
    with col_upload:
        uploaded_file = st.file_uploader("Pilih Berkas Operasional (.xlsx, .csv)", type=['xlsx', 'csv'])
    with col_header_up:
        baris_header_up = st.number_input("Tabel Mulai Baris ke-", min_value=0, max_value=20, value=0,
                                          help="Jika baris 1-4 berisi kop surat/judul, isi dengan angka 4.")
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_up = pd.read_csv(uploaded_file, header=baris_header_up)
            else:
                df_up = pd.read_excel(uploaded_file, engine='openpyxl', header=baris_header_up)
                
            df_up = bersihkan_data(df_up)
            st.success("Berkas terverifikasi dan siap dianalisis.")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("**Pratinjau Data:**")
                st.dataframe(df_up.head(20).astype(str), use_container_width=True)
                
            with c2:
                st.markdown("**Panel Kontrol Visual:**")
                list_kolom = df_up.columns.tolist()
                
                sumbu_x = st.selectbox("Parameter Horizontal (Sumbu X):", list_kolom, key="sx")
                sumbu_y = st.selectbox("Parameter Vertikal (Sumbu Y):", list_kolom, index=1 if len(list_kolom)>1 else 0, key="sy")
                jenis_chart = st.radio("Model Tampilan:", ["Garis (Line Chart)", "Batang (Bar Chart)"], horizontal=True)
                
                if st.button("Eksekusi Grafik", type="primary"):
                    try:
                        if "Garis" in jenis_chart:
                            fig_up = px.line(df_up, x=sumbu_x, y=sumbu_y, markers=True, template="plotly_white")
                        else:
                            fig_up = px.bar(df_up, x=sumbu_x, y=sumbu_y, template="plotly_white")
                            
                        fig_up.update_layout(title=f"Analisis {sumbu_y} terhadap {sumbu_x}")
                        st.plotly_chart(fig_up, use_container_width=True)
                    except Exception as e:
                        st.error(f"Gagal mengeksekusi grafik. Pastikan Parameter Vertikal berisi data angka. Detail: {e}")
                        
        except Exception as file_err:
            st.error(f"Sistem gagal mengekstrak berkas. Format mungkin tidak sesuai. Detail: {file_err}")
