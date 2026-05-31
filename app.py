import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Konfigurasi Halaman Web
st.set_page_config(page_title="Dashboard ACS Terintegrasi", layout="wide", page_icon="🌤️")

st.title("Dashboard Aerodrome Climatological Summary (ACS)")
st.subheader("Analisis Klimatologi Cuaca Operasional Periode 2021-2025")
st.markdown("---")

months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# 2. Fungsi Universal yang Sudah Diperbaiki (Mengunci Baris (GMT))
@st.cache_data
def load_acs_generic_data(file_name):
    if not os.path.exists(file_name):
        return None, None
        
    try:
        xls = pd.ExcelFile(file_name)
        actual_sheets = xls.sheet_names
    except Exception as e:
        return None, None

    # Cari sheet bulan pertama yang tersedia untuk mendeteksi kategori
    sample_sheet = next((s for s in actual_sheets if s.strip().lower() in [m.lower() for m in months]), actual_sheets[0])
    df_sample = pd.read_excel(file_name, sheet_name=sample_sheet, header=None)
    
    # PERBAIKAN: Kunci pencarian hanya pada baris yang kolom pertamanya adalah '(GMT)'
    header_row_idx = df_sample[df_sample[0].astype(str).str.strip().str.upper() == '(GMT)'].index
    
    if len(header_row_idx) > 0:
        r = header_row_idx[0]
        # Mengambil semua nama rentang kategori (kolom 1 sampai akhir)
        categories = [str(df_sample.iloc[r, c]).strip() for c in range(1, len(df_sample.columns)) 
                      if pd.notna(df_sample.iloc[r, c]) and str(df_sample.iloc[r, c]).strip() != '']
    else:
        # Pilihan cadangan jika standar (GMT) tidak ditemukan
        categories = [f"Kategori {i}" for i in range(1, len(df_sample.columns))]

    # Buat wadah data untuk grafik
    data_kategori = {k: [] for k in categories}
    
    for month in months:
        matched_sheet = next((s for s in actual_sheets if s.strip().lower() == month.lower()), None)
        
        if matched_sheet:
            try:
                df = pd.read_excel(file_name, sheet_name=matched_sheet, header=None)
                # Cari baris MEAN periode gabungan 2021-2025 (paling bawah)
                mean_rows = df[df[0].astype(str).str.strip().str.upper() == 'MEAN'].index.tolist()
                
                if mean_rows:
                    target_row = mean_rows[-1]
                    for idx, kategori in enumerate(categories, start=1):
                        if idx < len(df.columns):
                            val = df.iloc[target_row, idx]
                            # Menghapus data anomali atau kosong
                            if pd.isna(val) or (isinstance(val, (int, float)) and val > 100):
                                val = 0.0
                            data_kategori[kategori].append(round(float(val), 2))
                        else:
                            data_kategori[kategori].append(0.0)
                else:
                    for kategori in categories: data_kategori[kategori].append(0.0)
            except Exception:
                for kategori in categories: data_kategori[kategori].append(0.0)
        else:
            for kategori in categories: data_kategori[kategori].append(0.0)
            
    return pd.DataFrame(data_kategori, index=months), categories

# 3. Membuat Sistem Tab Navigasi di Dashboard
tab1, tab2, tab3 = st.tabs(["🌡️ Temperatur", "👁️ Visibility", "☁️ Cloud Height (HS)"])

# --- TAB 1: TEMPERATUR ---
with tab1:
    st.markdown("### Distribusi Persentase Temperatur Bulanan")
    file_temp = 'Persentase_Temp_2021-2025.xlsx'
    df_temp, cat_temp = load_acs_generic_data(file_temp)
    
    if df_temp is not None and not df_temp.empty:
        fig_temp = px.line(df_temp, x=df_temp.index, y=df_temp.columns, markers=True,
                            labels={'index': 'Bulan', 'value': 'Persentase (%)', 'variable': 'Rentang Suhu (°C)'})
        fig_temp.update_layout(hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', height=500)
        st.plotly_chart(fig_temp, use_container_width=True)
        st.dataframe(df_temp.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info(f"💡 File `{file_temp}` belum diunggah atau strukturnya tidak sesuai.")

# --- TAB 2: VISIBILITY ---
with tab2:
    st.markdown("### Distribusi Persentase Visibility Bulanan")
    file_vis = 'Persentase_Vis_2021-2025.xlsx'
    df_vis, cat_vis = load_acs_generic_data(file_vis)
    
    if df_vis is not None and not df_vis.empty:
        fig_vis = px.line(df_vis, x=df_vis.index, y=df_vis.columns, markers=True,
                           labels={'index': 'Bulan', 'value': 'Persentase (%)', 'variable': 'Rentang Jarak (m)'})
        fig_vis.update_layout(hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', height=500)
        st.plotly_chart(fig_vis, use_container_width=True)
        st.dataframe(df_vis.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info(f"💡 File `{file_vis}` belum diunggah ke GitHub. Silakan unggah file untuk melihat grafik Visibility.")

# --- TAB 3: CLOUD HEIGHT (HS) ---
with tab3:
    st.markdown("### Distribusi Persentase Cloud Height (HS) Bulanan")
    file_hs = 'Persentase_HS_2021-2025.xlsx'
    df_hs, cat_hs = load_acs_generic_data(file_hs)
    
    if df_hs is not None and not df_hs.empty:
        fig_hs = px.line(df_hs, x=df_hs.index, y=df_hs.columns, markers=True,
                          labels={'index': 'Bulan', 'value': 'Persentase (%)', 'variable': 'Rentang Tinggi (ft)'})
        fig_hs.update_layout(hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', height=500)
        st.plotly_chart(fig_hs, use_container_width=True)
        st.dataframe(df_hs.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info(f"💡 File `{file_hs}` belum diunggah ke GitHub. Silakan unggah file untuk melihat grafik Cloud Height.")
