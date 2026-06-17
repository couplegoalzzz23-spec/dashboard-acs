import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Konfigurasi halaman utama web
st.set_page_config(
    page_title="Dashboard Analisis Cuaca & Klimatologi Bandara",
    layout="wide",
    page_icon="📊"
)

st.title("🛫 Dashboard Interaktif Data Klimatologi Operasional (2021-2025)")
st.markdown("Aplikasi web untuk visualisasi dinamis *Aerodrome Climatological Summary* (ACS) dan data parameter cuaca.")

# ==================== SIDEBAR & MENU KONTROL ====================
st.sidebar.header("⚙️ Pengaturan & Unggah Data")

# Menu Pilihan Sumber Data
sumber_data = st.sidebar.radio(
    "Pilih Sumber Data:",
    ["Data Repositori (Folder 'data')", "Unggah Manual File ACS Baru"]
)

@st.cache_data
def proses_file_excel(file_source):
    """
    Fungsi membaca file Excel secara aman. 
    Mendukung file dengan banyak sheet (bulanan) maupun sheet tunggal.
    """
    try:
        xl = pd.ExcelFile(file_source)
        all_sheets = xl.sheet_names
        df_list = []
        
        for sheet in all_sheets:
            df_sheet = pd.read_excel(file_source, sheet_name=sheet)
            # Membersihkan baris/kolom kosong agar tidak error
            df_sheet = df_sheet.dropna(how='all')
            if not df_sheet.empty:
                # Tambahkan kolom penanda sheet (misal nama bulan) jika ada beberapa sheet
                if len(all_sheets) > 1:
                    df_sheet['Bulan/Sheet'] = sheet
                df_list.append(df_sheet)
                
        if df_list:
            df_gabungan = pd.concat(df_list, ignore_index=True)
            # Mengubah nama kolom menjadi string untuk mencegah error plotting
            df_gabungan.columns = df_gabungan.columns.astype(str)
            return df_gabungan
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal memproses file Excel: {e}")
        return pd.DataFrame()

# Inisialisasi DataFrame kosong
df_utama = pd.DataFrame()
nama_parameter = ""

# ==================== LOGIKA PENYEDIAAN DATA ====================
if sumber_data == "Data Repositori (Folder 'data')":
    FOLDER_DATA = "data"
    if os.path.exists(FOLDER_DATA):
        # Membaca semua file .xlsx di dalam folder data secara otomatis
        daftar_file = [f for f in os.listdir(FOLDER_DATA) if f.endswith(('.xlsx', '.xls'))]
        
        if daftar_file:
            pilihan_file = st.sidebar.selectbox("Pilih Parameter Meteorologi:", sorted(daftar_file))
            path_file = os.path.join(FOLDER_DATA, pilihan_file)
            df_utama = proses_file_excel(path_file)
            nama_parameter = pilihan_file.replace("rata_rata_", "").replace("_2021_2025.xlsx", "").upper()
        else:
            st.sidebar.warning("Tidak ada file .xlsx di dalam folder 'data'.")
    else:
        st.sidebar.error(f"Folder '{FOLDER_DATA}' tidak ditemukan di root GitHub Anda.")

else:
    # MENU UPLOAD MANUAL FILE ACS
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Unggah File ACS Baru")
    uploaded_file = st.sidebar.file_uploader(
        "Pilih file Excel format (.xlsx) hasil ekspor ACS Anda:", 
        type=["xlsx"]
    )
    if uploaded_file is not None:
        df_utama = proses_file_excel(uploaded_file)
        nama_parameter = uploaded_file.name.split(".")[0].upper()
        st.sidebar.success("Data manual berhasil dimuat!")
    else:
        st.info("Silakan unggah file Excel ACS melalui menu di sebelah kiri untuk melihat visualisasinya.")

# ==================== ANTARMUKA VISUALISASI DATA ====================
if not df_utama.empty:
    st.subheader(f"📈 Analisis Grafik Interaktif: {nama_parameter}")
    
    # Deteksi otomatis kolom yang tersedia di dalam file (Menjamin anti-error)
    semua_kolom = df_utama.columns.tolist()
    
    # Memisahkan kolom numerik untuk sumbu Y otomatis
    kolom_numerik = df_utama.select_dtypes(include=['number']).columns.tolist()
    # Singkirkan 'Tahun' dari pilihan sumbu Y jika terdeteksi angka agar tidak rancu
    if 'Tahun' in kolom_numerik:
        kolom_numerik.remove('Tahun')
        
    # Pembuatan Layout Filter Dinamis
    col1, col2, col3 = st.columns(3)
    with col1:
        sumbu_x = st.selectbox(
            "Sumbu X (Kategori/Waktu):", 
            options=['Bulan/Sheet', 'Tahun'] + [k for k in semua_kolom if k not in ['Bulan/Sheet', 'Tahun']]
        )
    with col2:
        sumbu_y = st.selectbox(
            "Sumbu Y (Parameter/Nilai):", 
            options=kolom_numerik if kolom_numerik else semua_kolom
        )
    with col3:
        tipe_grafik = st.selectbox(
            "Model Tampilan Grafik:", 
            ["Grafik Garis (Line Chart)", "Grafik Batang (Bar Chart)", "Grafik Area"]
        )

    # Filter Tahun Otomatis jika kolom 'Tahun' terdeteksi di dalam file
    if 'Tahun' in semua_kolom:
        try:
            tahun_unik = sorted(df_utama['Tahun'].dropna().unique().astype(int))
            if len(tahun_unik) > 1:
                rentang_tahun = st.slider(
                    "Saring Berdasarkan Rentang Tahun:", 
                    min_value=int(min(tahun_unik)), 
                    max_value=int(max(tahun_unik)), 
                    value=(int(min(tahun_unik)), int(max(tahun_unik)))
                )
                df_utama = df_utama[(df_utama['Tahun'] >= rentang_tahun[0]) & (df_utama['Tahun'] <= rentang_tahun[1])]
        except Exception:
            pass # Lewati filter jika konversi tipe data tahun gagal

    # Pembuatan Grafik Interaktif berbasis Plotly
    try:
        # Menentukan pewarnaan garis/batang (legend group) secara cerdas
        pembeda_warna = 'Bulan/Sheet' if sumbu_x == 'Tahun' and 'Bulan/Sheet' in semua_kolom else None
        if sumbu_x == 'Bulan/Sheet':
            pembeda_warna = 'Tahun' if 'Tahun' in semua_kolom else None

        if tipe_grafik == "Grafik Garis (Line Chart)":
            fig = px.line(df_utama, x=sumbu_x, y=sumbu_y, color=pembeda_warna, markers=True,
                          title=f"Tren Distribusi {sumbu_y} Terhadap {sumbu_x}", template="plotly_white")
        elif tipe_grafik == "Grafik Batang (Bar Chart)":
            fig = px.bar(df_utama, x=sumbu_x, y=sumbu_y, color=pembeda_warna, barmode="group",
                         title=f"Perbandingan {sumbu_y} Terhadap {sumbu_x}", template="plotly_white")
        else:
            fig = px.area(df_utama, x=sumbu_x, y=sumbu_y, color=pembeda_warna,
                          title=f"Akumulasi Area Kepadatan {sumbu_y}", template="plotly_white")
        
        # Mengatur agar grafik bisa memunculkan nilai saat kursor digerakkan (hovermode)
        fig.update_layout(hovermode="x unified", legend_title_text="Kategori")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as graph_err:
        st.error(f"Kombinasi kolom tidak cocok untuk grafik ini. Silakan ubah pilihan Sumbu X atau Sumbu Y. (Detail: {graph_err})")

    # Penyajian data mentah di bawah grafik
    with st.expander("🔍 Periksa Lembar Tabel Data Mentah (Spreadsheet)"):
        st.dataframe(df_utama, use_container_width=True)
