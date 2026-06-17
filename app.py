import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Dashboard Operasional Lanud RSN",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1, h2, h3 {color: #1a237e;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI PEMBERSIH DATA (TAHAN BANTING)
# ==========================================
def clean_dataframe(df):
    """Membersihkan data agar PyArrow dan Plotly tidak crash"""
    # 1. Pastikan semua nama kolom adalah string
    df.columns = df.columns.astype(str)
    
    # 2. Cek setiap kolom, jika tipenya campuran/teks (object), paksa jadi string murni
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
        else:
            # Jika angka, biarkan tetap angka (agar grafik bisa dibaca)
            df[col] = pd.to_numeric(df[col], errors='ignore')
            
    return df

@st.cache_data(show_spinner=False)
def load_local_data(filepath):
    try:
        # Gunakan engine openpyxl secara eksplisit
        df = pd.read_excel(filepath, engine='openpyxl')
        return clean_dataframe(df)
    except Exception as e:
        st.error(f"Gagal memproses file {filepath}. Error: {e}")
        return None

# ==========================================
# 3. SIDEBAR
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Lambang_TNI_AU.png", width=100)
st.sidebar.title("Command Center")
st.sidebar.markdown("**Lanud Roesmin Nurjadin**")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "PILIH MODUL OPERASIONAL:",
    ("📊 Data Historis Cuaca", "📤 Analisis Data Manual")
)

# ==========================================
# 4. MODUL: DATA HISTORIS CUACA
# ==========================================
st.title("Sistem Informasi Cuaca & Operasional")
st.markdown("Pangkalan TNI AU Roesmin Nurjadin (RSN)")

if menu == "📊 Data Historis Cuaca":
    st.subheader("Analisis Data Historis (2021 - 2025)")
    
    data_folder = "data"
    if os.path.exists(data_folder):
        files = [f for f in os.listdir(data_folder) if f.endswith('.xlsx')]
        
        if len(files) > 0:
            selected_file = st.selectbox("Pilih Parameter Data:", files)
            file_path = os.path.join(data_folder, selected_file)
            
            df = load_local_data(file_path)
            
            if df is not None and not df.empty:
                tab1, tab2 = st.tabs(["📈 Grafik Interaktif", "🗃️ Tabel Data Mentah"])
                
                with tab1:
                    try:
                        kolom_x = df.columns[0]
                        kolom_y = st.multiselect(
                            "Pilih variabel untuk grafik:", 
                            df.columns[1:], 
                            default=df.columns[1:2].tolist() # Tampilkan 1 garis dulu agar aman
                        )
                        
                        if kolom_y:
                            fig = px.line(
                                df, x=kolom_x, y=kolom_y, markers=True,
                                title=f"Tren: {selected_file}",
                                template="plotly_white"
                            )
                            fig.update_layout(hovermode="x unified")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Pilih minimal satu variabel.")
                    except Exception as e:
                        st.error(f"Gagal membuat grafik. Pastikan isi kolom berupa angka. Detail Error: {e}")
                
                with tab2:
                    try:
                        st.dataframe(df)
                    except Exception as e:
                        st.error("PyArrow gagal membaca tabel. Menampilkan mode fallback:")
                        # Mode aman jika dataframe modern crash
                        st.table(df.head(50).astype(str))
                        
            else:
                st.warning("Data kosong atau tidak dapat dibaca.")
        else:
            st.warning("Tidak ada file Excel (.xlsx) di folder 'data'.")
    else:
        st.error("Folder 'data' tidak ditemukan. Pastikan namanya huruf kecil 'data' di GitHub.")

# ==========================================
# 5. MODUL: UPLOAD MANUAL
# ==========================================
elif menu == "📤 Analisis Data Manual":
    st.subheader("Modul Analisis Berkas Mandiri")
    
    uploaded_file = st.file_uploader("Unggah File Data (.xlsx, .csv)", type=['xlsx', 'csv'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file, engine='openpyxl')
                
            df_upload = clean_dataframe(df_upload)
            st.success("File berhasil dimuat!")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write("**Pratinjau Data:**")
                try:
                    st.dataframe(df_upload.head(20))
                except:
                    st.table(df_upload.head(10).astype(str))
                
            with col2:
                st.write("**Pengaturan Visualisasi:**")
                all_columns = df_upload.columns.tolist()
                
                x_axis = st.selectbox("Sumbu X (Horizontal):", all_columns)
                y_axis = st.selectbox("Sumbu Y (Vertikal):", all_columns, index=1 if len(all_columns)>1 else 0)
                jenis_grafik = st.radio("Jenis Grafik:", ["Garis (Line)", "Batang (Bar)"], horizontal=True)
                
                if st.button("Buat Grafik"):
                    try:
                        if jenis_grafik == "Garis (Line)":
                            fig_up = px.line(df_upload, x=x_axis, y=y_axis, markers=True, template="plotly_white")
                        else:
                            fig_up = px.bar(df_upload, x=x_axis, y=y_axis, template="plotly_white")
                        st.plotly_chart(fig_up, use_container_width=True)
                    except Exception as e:
                        st.error(f"Grafik gagal dibuat. Pastikan sumbu Y adalah angka. Detail: {e}")
                        
        except Exception as e:
            st.error(f"Sistem gagal membaca file. Error: {e}")
