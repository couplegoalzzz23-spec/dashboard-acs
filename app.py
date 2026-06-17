import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. KONFIGURASI HALAMAN & TEMA
# ==========================================
st.set_page_config(
    page_title="Dashboard Operasional Lanud RSN",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kustomisasi CSS agar tampilan bersih, profesional, bergaya militer (Navy/Dark Blue)
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1, h2, h3 {color: #1a237e;}
    .stAlert {border-radius: 5px;}
    /* Menyembunyikan menu bawaan streamlit agar lebih rapi */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI LOAD DATA (DENGAN CACHE)
# ==========================================
@st.cache_data(show_spinner=False)
def load_local_data(filepath):
    """Fungsi tahan banting untuk membaca excel"""
    try:
        df = pd.read_excel(filepath)
        return df
    except Exception as e:
        return None

# ==========================================
# 3. SIDEBAR & NAVIGASI PENGGUNA
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Lambang_TNI_AU.png", width=100) # Bisa diganti logo Lanud RSN jika ada URL-nya
st.sidebar.title("Command Center")
st.sidebar.markdown("**Lanud Roesmin Nurjadin**")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "PILIH MODUL OPERASIONAL:",
    ("📊 Data Historis Cuaca (2021-2025)", "📤 Analisis Data Manual (ACS)")
)

# ==========================================
# 4. LOGIKA HALAMAN UTAMA
# ==========================================
st.title("Sistem Informasi Cuaca & Operasional")
st.markdown("Pangkalan TNI AU Roesmin Nurjadin (RSN)")

if menu == "📊 Data Historis Cuaca (2021-2025)":
    st.subheader("Analisis Data Historis (2021 - 2025)")
    st.info("Pilih jenis data pada menu di bawah untuk melihat visualisasi pergerakan cuaca.")
    
    # Membaca isi folder 'data'
    data_folder = "data"
    if os.path.exists(data_folder):
        files = [f for f in os.listdir(data_folder) if f.endswith('.xlsx')]
        
        if len(files) > 0:
            # Dropdown pilihan file
            selected_file = st.selectbox("Pilih Parameter Data:", files)
            file_path = os.path.join(data_folder, selected_file)
            
            # Load Data
            df = load_local_data(file_path)
            
            if df is not None and not df.empty:
                # Tampilkan Data Tabular & Grafik
                tab1, tab2 = st.tabs(["📈 Grafik Interaktif", "🗃️ Tabel Data Mentah"])
                
                with tab1:
                    # Asumsi dinamis: Kolom 1 adalah index (misal: Tahun/Bulan), sisanya adalah value
                    kolom_x = df.columns[0]
                    kolom_y = st.multiselect("Pilih variabel untuk ditampilkan di grafik:", df.columns[1:], default=df.columns[1:].tolist())
                    
                    if kolom_y:
                        # Membuat grafik garis interaktif (Line Chart)
                        fig = px.line(
                            df, 
                            x=kolom_x, 
                            y=kolom_y, 
                            markers=True,
                            title=f"Tren Visualisasi: {selected_file.replace('.xlsx', '')}",
                            template="plotly_white"
                        )
                        # Kustomisasi Layout Grafik
                        fig.update_layout(
                            legend_title_text='Parameter',
                            hovermode="x unified",
                            xaxis_title=kolom_x.capitalize(),
                            yaxis_title="Nilai/Jumlah"
                        )
                        # Gunakan container width agar responsif di HP/Tablet
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Silakan pilih minimal satu variabel untuk menampilkan grafik.")
                
                with tab2:
                    st.dataframe(df, use_container_width=True)
                    
            else:
                st.error("Gagal membaca file atau file kosong. Pastikan format Excel sudah benar.")
        else:
            st.warning("Tidak ada file Excel (.xlsx) di dalam folder 'data'.")
    else:
        st.error("Folder 'data' tidak ditemukan di dalam repository.")

# ==========================================
# 5. HALAMAN UPLOAD MANUAL (FILE ACS)
# ==========================================
elif menu == "📤 Analisis Data Manual (ACS)":
    st.subheader("Modul Analisis Berkas Mandiri")
    st.markdown("Fasilitas ini digunakan untuk mengunggah dan menganalisis laporan/data operasional (Excel/CSV) secara *real-time* tanpa perlu menyimpan ke *database*.")
    
    # Widget Upload
    uploaded_file = st.file_uploader("Unggah File Data ACS (Format: .xlsx, .xls, .csv)", type=['xlsx', 'xls', 'csv'])
    
    if uploaded_file is not None:
        try:
            # Deteksi format file
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            st.success(f"File '{uploaded_file.name}' berhasil dimuat!")
            
            # Layout dinamis
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write("**Pratinjau Data:**")
                st.dataframe(df_upload.head(10), use_container_width=True)
                
            with col2:
                st.write("**Pengaturan Visualisasi:**")
                # Pemilihan axis dinamis oleh user
                all_columns = df_upload.columns.tolist()
                x_axis = st.selectbox("Pilih Kolom untuk Sumbu X (Garis Horizontal):", all_columns)
                y_axis = st.selectbox("Pilih Kolom untuk Sumbu Y (Garis Vertikal):", all_columns, index=1 if len(all_columns)>1 else 0)
                jenis_grafik = st.radio("Pilih Jenis Grafik:", ["Garis (Line)", "Batang (Bar)"], horizontal=True)
                
                if st.button("Buat Grafik"):
                    if jenis_grafik == "Garis (Line)":
                        fig_up = px.line(df_upload, x=x_axis, y=y_axis, markers=True, template="plotly_dark" if "Gelap" in st.get_option("theme.base") else "plotly_white")
                    else:
                        fig_up = px.bar(df_upload, x=x_axis, y=y_axis, template="plotly_dark" if "Gelap" in st.get_option("theme.base") else "plotly_white")
                        
                    fig_up.update_layout(title=f"Grafik {y_axis} berdasarkan {x_axis}")
                    st.plotly_chart(fig_up, use_container_width=True)
                    
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file. Pastikan format data valid. Error: {e}")
