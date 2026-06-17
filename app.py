import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard ACS Interaktif", layout="wide")

# Fungsi Load Data dengan penyesuaian header
def load_and_clean(file_path):
    # ACS memiliki metadata, kita akan mencari baris yang berisi "(GMT)" sebagai header
    df = pd.read_csv(file_path, skiprows=10)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=['(GMT)'])
    return df

# Sidebar
model = st.sidebar.selectbox("Pilih Model", ["Model C", "Model E"])
bulan = st.sidebar.selectbox("Pilih Bulan", ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                                             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'])

# Path file (Asumsi penamaan di folder 'data')
filename = f"rata_rata_jumlah_kejadian_masuk_hs_2021_2025.xlsx.xlsx - {bulan}.csv" if model == "Model C" else f"rata_rata_persentase_temperature_2021_2025.xlsx - {bulan}.csv"
file_path = os.path.join("data", filename)

st.title(f"Visualisasi {model} - {bulan}")

if os.path.exists(file_path):
    df = load_and_clean(file_path)
    
    # Melakukan melting agar data siap diplot
    df_melted = df.melt(id_vars=['(GMT)'], var_name='Kategori', value_name='Persentase')
    
    # Plotting Stacked Bar Chart
    fig = px.bar(
        df_melted, 
        x='(GMT)', 
        y='Persentase', 
        color='Kategori',
        title=f"Distribusi {model} per Jam (GMT)",
        labels={'Persentase': 'Frekuensi (%)', '(GMT)': 'Waktu (GMT)'},
        barmode='stack'
    )
    
    fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
    st.plotly_chart(fig, use_container_width=True)
    
    # Tampilkan tabel di bawah untuk verifikasi data
    with st.expander("Lihat Data Mentah"):
        st.write(df)
else:
    st.warning("File tidak ditemukan. Pastikan file ada di folder 'data' dengan penamaan yang tepat.")
