import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import math

st.set_page_config(page_title="EcoEngineer Pro-Dash", page_icon="🌱", layout="wide")

st.markdown("""
<style>
.main-header {font-size: 2.5rem; color: #2E7D32; text-align: center;}
.metric-card {background-color: #E8F5E8; padding: 1rem; border-radius: 10px; border-left: 5px solid #4CAF50;}
.status-pass {color: #4CAF50; font-weight: bold; font-size: 1.2rem;}
.status-fail {color: #F44336; font-weight: bold; font-size: 1.2rem;}
</style>
""", unsafe_allow_html=True)

BAKU_MUTU = {'BOD5': 30, 'COD': 100, 'TSS': 30, 'pH': (6, 9)}

def calculate_unit_sizing(Q, td, surface_loading_rate=24):
    V = Q * td / 24
    A = Q / surface_loading_rate
    H = 3.5
    L = math.sqrt(A * 3)
    W = math.sqrt(A / 3)
    return {'Volume': round(V, 2), 'Luas': round(A, 2), 'Panjang': round(L, 2), 'Lebar': round(W, 2), 'Tinggi': H}

def stoichiometry_coagulant(BOD_in, Q, coagulant_type='FeCl3'):
    ratios = {'FeCl3': 8, 'Alum': 10, 'PAC': 6}
    dosage = BOD_in * ratios.get(coagulant_type, 8) * Q / 1000
    return round(dosage, 2)

def check_regulation(effluent):
    status = {}
    for param, limit in BAKU_MUTU.items():
        if param == 'pH':
            status[param] = effluent[param] >= limit[0] and effluent[param] <= limit[1]
        else:
            status[param] = effluent[param] <= limit
    return status

st.markdown('<h1 class="main-header">🌱 EcoEngineer Pro-Dash</h1>', unsafe_allow_html=True)

page = st.sidebar.selectbox("Pilih Fitur:", ["🏗️ Unit Sizing", "🧪 Stoichiometry", "📊 Simulasi", "✅ Checker"])

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
elif page == "📊 Simulasi":
    st.header("📊 Interactive Simulation")
    col1, col2, col3 = st.columns(3)
    with col1:
        BOD_in_sim = st.slider("BOD Masuk", 50, 500, 200)
    with col2:
        Q_sim = st.slider("Debit", 50, 500, 100)
    with col3:
        efficiency = st.slider("Efisiensi %", 50.0, 95.0, 85.0)
    
    BOD_out_sim = BOD_in_sim * (1 - efficiency/100)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=['Masuk', 'Keluar'], y=[BOD_in_sim, BOD_out_sim],
                        marker_color=['#FF6384', '#36A2EB']))
    st.plotly_chart(fig, use_container_width=True)

elif page == "✅ Checker":
    st.header("✅ Regulatory Checker")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        BOD_eff = st.number_input("BOD5 mg/L", 0.0, 200.0, 25.0)
    with col2:
        COD_eff = st.number_input("COD mg/L", 0.0, 500.0, 80.0)
    with col3:
        TSS_eff = st.number_input("TSS mg/L", 0.0, 200.0, 20.0)
    with col4:
        pH_eff = st.number_input("pH", 4.0, 12.0, 7.0)
    
    if st.button("🔍 Cek Kepatuhan"):
        effluent_data = {'BOD5': BOD_eff, 'COD': COD_eff, 'TSS': TSS_eff, 'pH': pH_eff}
        status = check_regulation(effluent_data)
        overall_status = all(status.values())
        status_text = "✅ LULUS" if overall_status else "❌ GAGAL"
        st.markdown(f'<div class="metric-card"><h3>{status_text}</h3></div>', unsafe_allow_html=True)
        
        results_df = pd.DataFrame({
            'Parameter': list(status.keys()),
            'Hasil': [effluent_data[k] for k in status.keys()],
            'Status': ['✅ Lulus' if status[k] else '❌ Gagal' for k in status.keys()]
        })
        st.table(results_df)
