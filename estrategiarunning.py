import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from io import BytesIO

# -----------------------
# Funciones auxiliares
# -----------------------
def mmss_a_seg(texto):
    try:
        m, s = texto.split(":")
        return int(m) * 60 + int(s)
    except:
        return None

def seg_a_mmss(seg):
    m = int(seg // 60)
    s = int(round(seg % 60))
    return f"{m:02d}:{s:02d}"

def format_hms(segundos):
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def export_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="PlanCarrera")
    return output.getvalue()

# -----------------------
# App
# -----------------------
st.title("🏃 Simulador de Estrategia de Carrera")

# Cargar archivo base
df = pd.read_excel("AnalisisGPXs.xlsx", sheet_name="gpx carreras")
df.columns = df.columns.str.strip().str.replace(" ", "_")

carreras = df["Carrera"].unique().tolist()
carrera = st.selectbox("Selecciona la carrera", carreras)

# -----------------------
# Bloque 1: Datos de carrera
# -----------------------
with st.container():
    st.header("📌 Datos básicos de la carrera")
    col1, col2 = st.columns(2)
    ritmo_text = col1.text_input("Ritmo ideal (mm:ss)", "06:00")
    distancia = col2.number_input("Distancia oficial (km)", min_value=5.0, max_value=50.0, value=21.095, step=0.001)

# -----------------------
# Bloque 2: Ajustes ambientales
# -----------------------
with st.container():
    st.header("🌡️ Ajustes ambientales y fisiológicos")
    col1, col2 = st.columns(2)
    alt_entrenamiento = col1.number_input("Altitud de entrenamiento (msnm)", min_value=0, max_value=5000, value=500, step=100)
    temp_entreno = col2.number_input("Temperatura de entrenamiento (°C)", min_value=5, max_value=40, value=25, step=1)
    col3, col4 = st.columns(2)
    temp_carrera = col3.number_input("Temperatura de la carrera (°C)", min_value=5, max_value=40, value=12, step=1)
    fatiga_a = col4.slider("Fatiga a (%)", -10.0, 10.0, 0.0, 0.5)
    fatiga_b = st.slider("Fatiga b", 0.1, 5.0, 1.0, 0.1)

# -----------------------
# Calcular estrategia
# -----------------------
if st.button("Calcular estrategia"):
    datos = df[df["Carrera"] == carrera].reset_index(drop=True)

    # … aquí metes la lógica que ya tienes para: 
    # - distancias 3D
    # - interpolación cada 500 m
    # - pendiente
    # - corrección por altitud/temp
    # - ajuste por fatiga
    # - cálculo de RAP
    # (la dejamos sin expandir porque ya la tienes implementada en tu versión actual)

    # Ejemplo de cómo graficar bien en Streamlit:
    fig, ax = plt.subplots(figsize=(12,4))
    ax.plot([0,5,10,15], [6,5.5,5.8,6.2], label="RAP (min/km)")  # <-- reemplaza con tus datos reales
    ax.axhline(y=6.0, color="r", linestyle="--", label="Ritmo base")
    ax.set_xlabel("Distancia (km)")
    ax.set_ylabel("Ritmo (min/km)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)  # ✅ esta es la forma recomendada en Streamlit