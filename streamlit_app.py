import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import math

# Konfigurasi halaman
st.set_page_config(
    page_title="EcoEngineer Pro-Dash",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #E8F5E8;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
    }
    .status-pass {
        color: #4CAF50;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .status-fail {
        color: #F44336;
        font-weight: bold;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Data Baku Mutu PP No. 22 Tahun 2021 (Domestik)
BAKU_MUTU = {
    'BOD5': 30,      # mg/L
    'COD': 100,      # mg/L
    'TSS': 30,       # mg/L
    'pH': (6, 9),    # rentang
    'NH3-N': 5       # mg/L
}

def calculate_unit_sizing(Q, td, surface_loading_rate=24):
    """
    Menghitung dimensi bak pengolahan
    Q: debit (m³/hari)
    td: waktu tinggal (jam)
    surface_loading_rate: m³/m².hari (default 24 untuk bak aerasi)
    """
    # Volume bak (m³)
    V = Q * td / 24
    
    # Luas permukaan (m²)
    A = Q / surface_loading_rate
    
    # Dimensi (asumsi H = 3-4m untuk bak aerasi)
    H = 3.5
    L = math.sqrt(A * 3)  # Panjang 3x lebar
    W = math.sqrt(A / 3)
    
    return {
        'Volume': round(V, 2),
        'Luas': round(A, 2),
        'Panjang': round(L, 2),
        'Lebar': round(W, 2),
        'Tinggi': H
    }

def stoichiometry_coagulant(BOD_in, Q, coagulant_type='FeCl3'):
    """
    Menghitung kebutuhan koagulan
    """
    # Rasio mg koagulan / mg BOD (estimasi jar test)
    ratios = {
        'FeCl3': 8,    # mg/mg BOD
        'Alum': 10,    # mg/mg BOD
        'PAC': 6       # mg/mg BOD
    }
    
    dosage = BOD_in * ratios.get(coagulant_type, 8) * Q / 1000  # kg/hari
    return round(dosage, 2)

def calculate_efficiency(influent, effluent):
    """Menghitung efisiensi penyisihan (%)"""
    return ((influent - effluent) / influent * 100) if influent > 0 else 0

def check_regulation(effluent):
    """Cek kepatuhan baku mutu"""
    status = {}
    for param, limit in BAKU_MUTU.items():
        if param == 'pH':
            status[param] = effluent[param] >= limit[0] and effluent[param] <= limit[1]
        else:
            status[param] = effluent[param] <= limit
    return status

# Header
st.markdown('<h1 class="main-header">🌱 EcoEngineer Pro-Dash</h1>', unsafe_allow_html=True)
st.markdown("**Dashboard Desain & Monitoring Instalasi Pengolahan Limbah**")

# Sidebar untuk navigasi
st.sidebar.title("📋 Menu")
page = st.sidebar.selectbox("Pilih Fitur:", [
    "🏗️ Unit Sizing", 
    "🧪 Stoichiometry", 
    "📊 Simulasi Real-time", 
    "✅ Regulatory Checker"
])

# Halaman 1: Automatic Unit Sizing
if page == "🏗️ Unit Sizing":
    st.header("🏗️ Automatic Unit Sizing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Data")
        Q = st.number_input("**Debit (Q)** (m³/hari)", min_value=1.0, value=100.0, step=10.0)
        td = st.number_input("**Waktu Tinggal (t_d)** (jam)", min_value=1.0, value=24.0, step=1.0)
        SLR = st.number_input("**Surface Loading Rate** (m³/m².hari)", min_value=5.0, value=24.0, step=1.0)
    
    with col2:
        if st.button("💾 Hitung Dimensi", type="primary"):
            dimensions = calculate_unit_sizing(Q, td, SLR)
            
            st.subheader("📐 Hasil Dimensi Bak")
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("**Volume**", f"{dimensions['Volume']} m³")
            with col_b:
                st.metric("**Luas**", f"{dimensions['Luas']} m²")
            with col_c:
                st.metric("**P x L x T**", f"{dimensions['Panjang']} x {dimensions['Lebar']} x {dimensions['Tinggi']} m")
            
            # Gambar 3D sederhana
            fig = go.Figure(data=[go.Mesh3d(
                x=[0, dimensions['Panjang'], dimensions['Panjang'], 0,
                   0, dimensions['Panjang'], dimensions['Panjang'], 0],
                y=[0, 0, dimensions['Lebar'], dimensions['Lebar'],
                   0, 0, dimensions['Lebar'], dimensions['Lebar']],
                z=[0, 0, 0, 0, dimensions['Tinggi'], dimensions['Tinggi'], 
                   dimensions['Tinggi'], dimensions['Tinggi']],
                color='lightblue',
                opacity=0.7
            )])
            fig.update_layout(title="Visualisasi 3D Bak", scene=dict(
                xaxis_title='Panjang (m)',
                yaxis_title='Lebar (m)',
                zaxis_title='Tinggi (m)'
            ))
            st.plotly_chart(fig, use_container_width=True)

# Halaman 2: Stoichiometry Calculator
elif page == "🧪 Stoichiometry":
    st.header("🧪 Stoichiometry Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Data")
        BOD_in = st.number_input("**BOD Masuk** (mg/L)", min_value=0.0, value=200.0)
        Q_stoich = st.number_input("**Debit** (m³/hari)", min_value=1.0, value=100.0)
        coagulant = st.selectbox("**Jenis Koagulan**", ['FeCl3', 'Alum', 'PAC'])
    
    with col2:
        dosage = stoichiometry_coagulant(BOD_in, Q_stoich, coagulant)
        st.metric("**Kebutuhan Koagulan**", f"{dosage} kg/hari")
        
        st.info(f"**Rasio**: 1 mg {coagulant} per {8 if coagulant=='FeCl3' else 10 if coagulant=='Alum' else 6} mg BOD")
    
    # Tabel rekomendasi
    st.subheader("📋 Rekomendasi Jar Test")
    jar_data = {
        'Koagulan': ['FeCl3', 'Alum', 'PAC'],
        'Dosis Optimal': ['200-800 mg/L', '300-1000 mg/L', '150-600 mg/L'],
        'pH Optimal': ['6.5-7.5', '6.0-7.5', '6.5-8.0']
    }
    st.table(pd.DataFrame(jar_data))

# Halaman 3: Interactive Simulation
elif page == "📊 Simulasi Real-time":
    st.header("📊 Interactive Simulation")
    
    # Sliders untuk parameter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        BOD_in_sim = st.slider("**BOD Masuk** (mg/L)", 50, 500, 200)
    with col2:
        Q_sim = st.slider("**Debit** (m³/hari)", 50, 500, 100)
    with col3:
        efficiency = st.slider("**Efisiensi (%)**", 50.0, 95.0, 85.0, 0.5)
    
    # Hitung output
    BOD_out_sim = BOD_in_sim * (1 - efficiency/100)
    
    # Grafik real-time
    fig = make_subplots(rows=2, cols=2,
                       subplot_titles=('Efisiensi Penyisihan', 'Konsentrasi BOD', 
                                    'Dimensi vs Debit', 'Regulatory Status'),
                       specs=[[{"secondary_y": False}, {"secondary_y": False}],
                              [{"secondary_y": False}, {"secondary_y": False}]])
    
    # Plot 1: Efisiensi
    fig.add_trace(go.Scatter(x=[50,100,200,300,400,500], 
                           y=[95,90,85,80,75,70],
                           mode='lines+markers',
                           name='Efisiensi'), row=1, col=1)
    
    # Plot 2: BOD in/out
    fig.add_trace(go.Bar(x=['Masuk', 'Keluar'], y=[BOD_in_sim, BOD_out_sim],
                        marker_color=['#FF6384', '#36A2EB']), row=1, col=2)
    
    # Plot 3: Dimensi vs Debit
    dims = calculate_unit_sizing(Q_sim, 24)
    fig.add_trace(go.Scatter(x=[50,100,200,300,400,500],
                           y=[calculate_unit_sizing(q,24)['Volume'] for q in [50,100,200,300,400,500]],
                           mode='lines', name='Volume'), row=2, col=1)
    
    # Plot 4: Regulatory
    status_color = 'green' if BOD_out_sim <= BAKU_MUTU['BOD5'] else 'red'
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=BOD_out_sim,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "BOD (mg/L)"},
        delta={'reference': BAKU_MUTU['BOD5']},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': status_color},
            'steps': [
                {'range': [0, 30], 'color': 'green'},
                {'range': [30, 100], 'color': 'red'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': BAKU_MUTU['BOD5']}
        }), row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True)

# Halaman 4: Regulatory Checker
elif page == "✅ Regulatory Checker":
    st.header("✅ Regulatory Checker")
    st.markdown("**PP No. 22 Tahun 2021 - Baku Mutu Domestik**")
    
    # Input data effluent
    st.subheader("📥 Input Data Effluent")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        BOD_eff = st.number_input("**BOD5** (mg/L)", 0.0, 200.0, 25.0)
    with col2:
        COD_eff = st.number_input("**COD** (mg/L)", 0.0, 500.0, 80.0)
    with col3:
        TSS_eff = st.number_input("**TSS** (mg/L)", 0.0, 200.0, 20.0)
    with col4:
        pH_eff = st.number_input("**pH**", 4.0, 12.0, 7.0)
    
    if st.button("🔍 Cek Kepatuhan", type="primary"):
        effluent_data = {'BOD5': BOD_eff, 'COD': COD_eff, 'TSS': TSS_eff, 'pH': pH_eff}
        status = check_regulation(effluent_data)
        
        # Status keseluruhan
        overall_status = all(status.values())
        status_class = "status-pass" if overall_status else "status-fail"
        status_text = "✅ LULUS" if overall_status else "❌ GAGAL"
        
        st.markdown(f'<div class="metric-card"><h3>Status Keseluruhan: <span class="{status_class}">{status_text}</span></h3></div>', 
                   unsafe_allow_html=True)
        
        # Tabel detail
        results_df = pd.DataFrame({
            'Parameter': list(status.keys()),
            'Hasil (mg/L)': [effluent_data[k] if k != 'pH' else f"{effluent_data[k]:.1f}" for k in status.keys()],
            'Baku Mutu': [f"{BAKU_MUTU[k]}" if k != 'pH' else f"{BAKU_MUTU[k][0]}-{BAKU_MUTU[k][1]}" for k in status.keys()],
            'Status': ['✅ Lulus' if status[k] else '❌ Gagal' for k in status.keys()]
        })
        
        st.table(results_df)
        
        # Gauge charts
        fig = make_subplots(rows=1, cols=3, 
                           subplot_titles=('BOD5', 'COD', 'TSS'),
                           specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]])
        
        params = ['BOD5', 'COD', 'TSS']
        values = [BOD_eff, COD_eff, TSS_eff]
        limits = [BAKU_MUTU[p] for p in params]
        
        for i, (param, val, limit) in enumerate(zip(params, values, limits)):
            color = 'green' if val <= limit else 'red'
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=val,
                domain={'x': [i*0.33, (i+1)*0.33], 'y': [0, 1]},
                title={'text': param},
                gauge={
                    'axis': {'range': [0, max(limit*1.5, 100)]},
                    'bar': {'color': color},
                    'steps': [{'range': [0, limit], 'color': 'green'}, 
                             {'range': [limit, max(limit*1.5, 100)], 'color': 'red'}],
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': limit}
                }), row=1, col=i+1)
        
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**© 2024 EcoEngineer Pro-Dash | Dibuat dengan ❤️ untuk Industri Lingkungan**")
