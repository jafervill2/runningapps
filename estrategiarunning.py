import streamlit as st
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt

st.title("Simulador de Ritmo Ajustado por Altimetría y Fatiga")

# ==============================
# ENTRADAS MANUALES
# ==============================

# Ritmo en min y seg
col1, col2 = st.columns(2)
ritmo_min = col1.number_input("Ritmo objetivo (min)", min_value=2, max_value=10, value=5, step=1)
ritmo_seg = col2.number_input("Ritmo objetivo (seg)", min_value=0, max_value=59, value=0, step=1)
ritmo_objetivo = ritmo_min + ritmo_seg / 60

# Altura entrenamiento
alt_entren = st.number_input("Altura de entrenamiento (msnm)", min_value=0, max_value=5000, value=1000, step=50)

# Distancia de carrera
distancia_op = st.selectbox("Selecciona la distancia", ["10 km", "21.095 km", "42.195 km"])
dist_total = {"10 km": 10.0, "21.095 km": 21.095, "42.195 km": 42.195}[distancia_op]

# Parámetros de fatiga
a = st.number_input("Parámetro a (ajuste de fatiga)", min_value=-0.1, max_value=0.1, value=0.0, step=0.01, format="%.2f")
b = st.number_input("Parámetro b (pendiente de la curva sigmoidal)", min_value=0.01, max_value=10.0, value=1.0, step=0.01, format="%.2f")

# ==============================
# CARGA DE ALTIMETRÍA
# ==============================

file = st.file_uploader("Carga el archivo CSV de altimetría", type=["csv"])
if file:
    df_raw = pd.read_csv(file)
    df_raw.columns = ["distancia_km", "altitud_m"]

    # altura promedio de la carrera
    alt_prom = df_raw["altitud_m"].mean()

    # interpolar a cada km hasta la distancia total
    kms = np.arange(0, dist_total + 0.001, 1.0)
    df_interp = pd.DataFrame({
        "distancia_km": kms,
        "altitud_m": np.interp(kms, df_raw["distancia_km"], df_raw["altitud_m"])
    })

    # pendiente %
    df_interp["pendiente_%"] = df_interp["altitud_m"].diff().fillna(0)

    # ritmo base en seg/km
    ritmo_seg_base = ritmo_objetivo * 60

    # ajuste por altitud relativa
    ajuste_alt = 1 + (df_interp["altitud_m"] - alt_entren) / 10000
    df_interp["ritmo_seg"] = ritmo_seg_base * ajuste_alt

    # ==============================
    # AJUSTE POR FATIGA
    # ==============================

    def fatiga_ajuste(distancia_km, dist_total, a, b):
        dist1 = dist_total / 3
        dist2 = 2 * dist1
        s = (a / (1 + np.exp(-b * (dist1 - distancia_km)))) - \
            (a / (1 + np.exp(-b * (distancia_km - dist2))))
        return 1 + s

    df_interp["factor_fatiga"] = df_interp["distancia_km"].apply(
        lambda d: fatiga_ajuste(d, dist_total, a, b)
    )
    df_interp["ritmo_seg"] *= df_interp["factor_fatiga"]

    # ==============================
    # CÁLCULO DE TIEMPOS
    # ==============================

    # formato de ritmo mm:ss
    def format_pace(segundos):
        m = int(segundos // 60)
        s = int(segundos % 60)
        return f"{m:02d}:{s:02d}"

    # formato hh:mm:ss
    def format_hms(segundos):
        h = int(segundos // 3600)
        m = int((segundos % 3600) // 60)
        s = int(segundos % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # distancia del split
    df_interp["dist_segmento"] = df_interp["distancia_km"].diff().fillna(0)

    # tiempo del split
    df_interp["tiempo_seg"] = df_interp["ritmo_seg"] * df_interp["dist_segmento"]
    df_interp["tiempo_split"] = df_interp["tiempo_seg"].apply(format_hms)

    # tiempo acumulado
    df_interp["tiempo_acum_seg"] = df_interp["tiempo_seg"].cumsum()
    df_interp["tiempo_acum"] = df_interp["tiempo_acum_seg"].apply(format_hms)

    # ritmo mostrado
    df_interp["ritmo"] = df_interp["ritmo_seg"].apply(format_pace)

    # ==============================
    # SALIDA
    # ==============================

    st.subheader("Primeras 10 filas de altimetría")
    st.dataframe(df_raw.head(10))

    st.subheader("Últimas 10 filas de altimetría")
    st.dataframe(df_raw.tail(10))

    st.subheader("Splits ajustados")
    st.dataframe(df_interp[["distancia_km", "altitud_m", "ritmo", "tiempo_split", "tiempo_acum"]])