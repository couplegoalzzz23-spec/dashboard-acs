import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Dashboard ACS Temperatur",
    page_icon="🌡️",
    layout="wide"
)

st.title("📊 Aerodrome Climatological Summary (ACS)")
st.subheader("Persentase Kejadian Temperatur Bulanan (2021-2025)")
st.markdown("---")

# ==========================================
# 2. FUNGSI PEMBACAAN DATA "TAHAN BANTING"
# ==========================================
@st.cache_data(show_spinner="Memproses data Excel...")
def load_and_process_data(uploaded_file):
    months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    categories = ['5 - 0', '0 - 5', '5 - 10', '10 - 15', '15 - 20', '20 - 25', '25 - 30', '30 - 35', '> 35']
    
    # Menyiapkan dictionary untuk menampung data yang sudah dirapikan
    summary_data = []
    
    try:
        # Membaca seluruh sheet dalam Excel
        xls = pd.ExcelFile(uploaded_file)
        
        for month in months:
            # Memastikan sheet bulan tersebut ada di dalam file
            if month in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=month, header=None)
                
                # FITUR TAHAN BANTING: 
                # Daripada memaku pada baris 250 (yang bisa error jika data meleset),
                # kita cari baris yang di kolom pertamanya mengandung kata "MEAN" atau "RATA-RATA"
                mean_row_data = None
                for idx in range(len(df)):
                    cell_val = str(df.iloc[idx, 0]).strip().upper()
                    if 'MEAN' in cell_val or 'RATA' in cell_val:
                        mean_row_data = df.iloc[idx, 1:10].values
                        break
                
                # Fallback: Jika kata MEAN tidak ditemukan, coba ambil baris 250 sesuai script aslimu
                if mean_row_data is None:
                    try:
                        mean_row_data = df.iloc[250, 1:10].values
                    except IndexError:
                        # Jika baris 250 tidak ada, isi dengan 0
                        mean_row_data = [0] * 9
                
                # Membersihkan dan membulatkan data
                cleaned_values = []
                for val in mean_row_data:
                    try:
                        cleaned_values.append(round(float(val), 2))
                    except (ValueError, TypeError):
                        cleaned_values.append(0.0)
                        
                # Memasukkan ke list rekap
                summary_data.append([month] + cleaned_values)
                
        # Membuat DataFrame rapi dari hasil ekstraksi
        df_summary = pd.DataFrame(summary_data, columns=['Bulan'] + categories)
        return df_summary

    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")
        return pd.DataFrame()

# ==========================================
# 3. ANTARMUKA UPLOAD & TAMPILAN
# ==========================================
st.sidebar.header("📁 Upload Data")
st.sidebar.markdown("Silakan unggah file `Persentase_Temp_2021-2025.xlsx`")
uploaded_file = st.sidebar.file_uploader("Upload Excel ACS", type=['xlsx'])

if uploaded_file is not None:
    # Memproses data
    df_plot = load_and_process_data(uploaded_file)
    
    if not df_plot.empty:
        # Mengubah bentuk data (Melt) agar cocok dibaca oleh Plotly Express
        df_melted = df_plot.melt(
            id_vars=['Bulan'], 
            value_vars=df_plot.columns[1:], 
            var_name='Kategori Temperatur', 
            value_name='Persentase (%)'
        )
        
        # --- A. VISUALISASI GRAFIK INTERAKTIF ---
        st.markdown("### 📈 Grafik Fluktuasi Temperatur")
        
        fig = px.line(
            df_melted, 
            x='Bulan', 
            y='Persentase (%)', 
            color='Kategori Temperatur',
            markers=True, # Menambahkan titik pada setiap bulan
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        
        fig.update_layout(
            xaxis_title="Bulan",
            yaxis_title="Persentase Kejadian (%)",
            hovermode="x unified", # Menampilkan tooltip interaktif saat di-hover
            legend_title="Kategori (°C)",
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        
        # Menampilkan grafik di Streamlit
        st.plotly_chart(fig, use_container_width=True)
        
        # --- B. TABEL DATA INFORMATIF ---
        st.markdown("---")
        st.markdown("### 📋 Tabel Detail Persentase Kejadian (%)")
        st.markdown("Tabel di bawah ini menampilkan rincian data per bulan. Anda bisa mengklik judul kolom untuk mengurutkan data.")
        
        # Mengatur index menjadi Bulan agar tampilan tabel lebih rapi
        df_display = df_plot.set_index('Bulan')
        
        # Menampilkan tabel interaktif bawaan Streamlit
        st.dataframe(
            df_display, 
            use_container_width=True,
            height=450 # Mengatur tinggi agar semua bulan terlihat tanpa scroll berlebih
        )
        
else:
    st.info("👈 Menunggu file Excel diunggah dari panel sebelah kiri. Pastikan nama sheet di dalam file adalah nama-nama bulan (Januari, Februari, dst).")
