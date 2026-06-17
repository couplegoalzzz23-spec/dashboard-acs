import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. SIMULASI DATA / MEMBACA DATA ---
# (Sesuaikan bagian ini dengan cara Anda memuat data CSV asli)
@st.cache_data
def load_sample_data():
    # Contoh struktur data Model C (Cloud Height Frequencies)
    hours = list(range(24))
    data = {
        'TIME (GMT)': hours,
        '< 150 ft': [0,0,0,1,2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        '< 200 ft': [0,0,0,0,1,3,2,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
        '< 300 ft': [1,0,0,0,2,4,3,1,1,0,0,0,1,2,1,0,0,0,0,0,1,1,1,0],
        '< 500 ft': [1,0,1,2,4,5,3,2,1,0,1,2,2,3,2,1,0,0,1,2,3,2,2,1],
        '< 1000 ft': [7,9,12,7,8,5,3,1,0,0,0,0,1,2,1,0,0,0,1,1,2,3,4,5],
        '< 1500 ft': [24,29,30,30,30,30,29,27,24,23,24,23,23,21,20,18,15,12,11,13,14,12,12,11]
    }
    return pd.DataFrame(data)

df = load_sample_data()

# --- 2. KONFIGURASI DASHBOARD INTERAKTIF ---
st.title("📊 Aerodrome Climatological Summary Interactive Matrix")
st.write("Visualisasi interaktif frekuensi kejadian berdasarkan jam operasi.")

# Fitur Informatif: Pilihan Konversi Waktu (Sangat penting untuk operasional penerbangan)
time_mode = st.radio("Pilih Format Waktu:", ["GMT (UTC)", "Lokal (WIB / UTC+7)"], horizontal=True)

# Salinan data untuk manipulasi visual
plot_df = df.copy()

if time_mode == "Lokal (WIB / UTC+7)":
    # Menggeser jam (+7 jam untuk WIB)
    plot_df['TIME (GMT)'] = (plot_df['TIME (GMT)'] + 7) % 24
    plot_df = plot_df.sort_values(by='TIME (GMT)').reset_index(drop=True)
    time_label = "Jam (Lokal/WIB)"
else:
    time_label = "Jam (GMT)"

# Ekstrak kolom kategori (mengabaikan kolom waktu)
categories = [col for col in plot_df.columns if col != 'TIME (GMT)']

# --- 3. PEMBUATAN PLOTLY HEATMAP ---
# Menggunakan graph_objects untuk kontrol penuh tata letak
fig = go.Figure(data=go.Heatmap(
    z=plot_df[categories].values,                           # Nilai persentase/frekuensi
    x=categories,                                           # Sumbu X (Kategori Tinggi/Suhu)
    y=plot_df['TIME (GMT)'].astype(str) + ":00",            # Sumbu Y (Waktu sebagai String agar rapi)
    colorscale='YlGnBu',                                    # Palet warna profesional (Kuning-Hijau-Biru)
    reversescale=False,
    hoverongaps=False,
    hovertemplate=(
        "<b>" + time_label + ": %{y}</b><br>" +
        "Kategori: %{x}<br>" +
        "Frekuensi: %{z}%<extra></extra>"                  # Tampilan informasi saat kursor digeser
    )
))

# Kustomisasi Desain Layout agar mirip standar visualisasi modern
fig.update_layout(
    title=f"Matriks Distribusi Frekuensi ({time_mode})",
    xaxis_title="Rentang Parameter / Spesifikasi",
    yaxis_title=time_label,
    yaxis=dict(autorange="reversed"),                      # Jam diurutkan dari atas (00:00) ke bawah
    xaxis=dict(side="top"),                                 # Meletakkan label kategori di atas seperti tabel asli
    height=600,
    margin=dict(l=50, r=50, b=30, t=100),
)

# Menampilkan di Streamlit
st.plotly_chart(fig, use_container_width=True)

# --- 4. INSIGHT CARD (INFORMASI TAMBAHAN) ---
st.markdown("---")
### 💡 Informasi Operasional Utama
col1, col2 = st.columns(2)
with col1:
    max_val = plot_df[categories].values.max()
    st.metric(label="Frekuensi Tertinggi dalam Matriks", value=f"{max_val}%")
with col2:
    st.info("Warna yang lebih gelap menunjukkan probabilitas kejadian atau persistensi fenomena yang lebih tinggi pada jam tersebut.")
