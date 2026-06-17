import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="ACS Dashboard - SSK II", layout="wide", initial_sidebar_state="collapsed")

# --- JUDUL DASHBOARD ---
st.title("Sistem Informasi Cuaca dan Iklim")
st.subheader("Bandara Sultan Syarif Kasim II")

# --- FUNGSI PEMBACAAN DATA ---
@st.cache_data
def load_acs_data(model_type, bulan):
    """
    Membaca file CSV ACS dari folder 'data', melewati baris metadata, 
    dan mengambil tabel utama.
    """
    if model_type == "Model C":
        # Format penamaan file berdasarkan data Anda
        filename = f"rata_rata_jumlah_kejadian_masuk_hs_2021_2025.xlsx.xlsx - {bulan}.csv"
        filepath = os.path.join("data", filename)
        
        try:
            # Skiprows disesuaikan dengan format tabel Model C (umumnya baris ke-10 adalah header kolom '< 150' dst)
            df = pd.read_csv(filepath, skiprows=10)
            # Membersihkan kolom yang tidak bernama atau kosong (Unused columns)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(subset=['(GMT)']) # Pastikan baris waktu valid
            # Pastikan kolom waktu berupa integer 0-23
            df['(GMT)'] = pd.to_numeric(df['(GMT)'], errors='coerce')
            df = df.dropna(subset=['(GMT)']).astype({'(GMT)': 'int'})
            return df
        except FileNotFoundError:
            return None
            
    elif model_type == "Model E":
        filename = f"rata_rata_persentase_temperature_2021_2025.xlsx - {bulan}.csv"
        filepath = os.path.join("data", filename)
        
        try:
            # Skiprows disesuaikan dengan format tabel Model E
            df = pd.read_csv(filepath, skiprows=10)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(subset=['(GMT)'])
            df['(GMT)'] = pd.to_numeric(df['(GMT)'], errors='coerce')
            df = df.dropna(subset=['(GMT)']).astype({'(GMT)': 'int'})
            return df
        except FileNotFoundError:
            return None

# --- FUNGSI VISUALISASI HEATMAP ---
def create_heatmap(df, z_cols, time_mode, title, colorscale='Blues'):
    plot_df = df.copy()
    
    # Penyesuaian Zona Waktu (WIB = GMT + 7)
    if time_mode == "Lokal (WIB)":
        plot_df['(GMT)'] = (plot_df['(GMT)'] + 7) % 24
        plot_df = plot_df.sort_values(by='(GMT)').reset_index(drop=True)
        y_label = "Waktu (WIB)"
    else:
        y_label = "Waktu (GMT)"

    # Memastikan format waktu dua digit (00:00)
    y_time_str = plot_df['(GMT)'].apply(lambda x: f"{x:02d}:00")

    fig = go.Figure(data=go.Heatmap(
        z=plot_df[z_cols].values,
        x=z_cols,
        y=y_time_str,
        colorscale=colorscale,
        hoverongaps=False,
        hovertemplate=(
            f"<b>{y_label}: %{{y}}</b><br>" +
            "Kategori: %{x}<br>" +
            "Frekuensi: %{z}%<extra></extra>"
        )
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='white')),
        xaxis=dict(side="top", title="Kategori", showgrid=False),
        yaxis=dict(title=y_label, autorange="reversed", type='category', showgrid=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=40, r=40, t=80, b=40),
        height=700
    )
    return fig

# --- TATA LETAK UTAMA ---
# Membuat Tab Navigasi
tab1, tab2, tab3 = st.tabs(["☁️ Model C (Cloud)", "🌡️ Model E (Temperature)", "🧭 Wind Rose"])

# Filter Kontrol di atas tab (Bisa juga dipindah ke st.sidebar)
col_filter1, col_filter2 = st.columns([1, 1])
with col_filter1:
    daftar_bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    selected_bulan = st.selectbox("Pilih Bulan:", daftar_bulan)

with col_filter2:
    mode_waktu = st.radio("Mode Waktu:", ["Lokal (WIB)", "GMT"], horizontal=True)

# --- TAB 1: MODEL C (CLOUD) ---
with tab1:
    st.markdown("### Frekuensi Tinggi Dasar Awan Terendah (< 4/8 Oktas)")
    
    df_cloud = load_acs_data("Model C", selected_bulan)
    
    if df_cloud is not None:
        # Menentukan kolom kategori tinggi awan (mengambil semua kolom kecuali waktu)
        cloud_categories = [col for col in df_cloud.columns if '<' in col]
        
        fig_cloud = create_heatmap(
            df=df_cloud, 
            z_cols=cloud_categories, 
            time_mode=mode_waktu, 
            title=f"Distribusi Kejadian Dasar Awan - Bulan {selected_bulan}",
            colorscale='Blues'
        )
        st.plotly_chart(fig_cloud, use_container_width=True)
    else:
        st.warning(f"⚠️ Data file untuk Model C bulan {selected_bulan} tidak ditemukan di folder 'data'.")

# --- TAB 2: MODEL E (TEMPERATURE) ---
with tab2:
    st.markdown("### Frekuensi Rentang Suhu Permukaan")
    
    df_temp = load_acs_data("Model E", selected_bulan)
    
    if df_temp is not None:
        # Menentukan kolom kategori suhu (biasanya berisi tanda '-')
        temp_categories = [col for col in df_temp.columns if '-' in col or '>' in col]
        
        fig_temp = create_heatmap(
            df=df_temp, 
            z_cols=temp_categories, 
            time_mode=mode_waktu, 
            title=f"Distribusi Rentang Suhu - Bulan {selected_bulan}",
            colorscale='OrRd' # Menggunakan palet Oranye-Merah untuk suhu
        )
        st.plotly_chart(fig_temp, use_container_width=True)
    else:
        st.warning(f"⚠️ Data file untuk Model E bulan {selected_bulan} tidak ditemukan di folder 'data'.")

# --- TAB 3: WIND ROSE ---
with tab3:
    st.markdown("### Distribusi Arah dan Kecepatan Angin")
    st.info("Modul Wind Rose dalam tahap pengembangan. Tempatkan fungsi Plotly Polar Chart di sini nantinya.")
