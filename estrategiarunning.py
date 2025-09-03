import streamlit as st
import pandas as pd
import numpy as np

st.title("Simulador de Ritmo Ajustado por Pendiente y Altitud")

# ============================
# Entradas de usuario
# ============================
ritmo_min_km = st.number_input("Ritmo objetivo (min/km)", min_value=2.0, max_value=10.0, value=5.0, step=0.1)
altitud = st.number_input("Altitud de la carrera (msnm)", min_value=0, max_value=5000, value=2000, step=100)
temperatura = st.number_input("Temperatura (°C)", min_value=-10, max_value=40, value=15, step=1)

distancia_opcion = st.selectbox(
    "Selecciona la distancia de carrera",
    options=["10 km", "21.095 km", "42.195 km"],
    index=2
)

# Convertir selección a número
if distancia_opcion == "10 km":
    distancia_max = 10.0
elif distancia_opcion == "21.095 km":
    distancia_max = 21.095
else:
    distancia_max = 42.195

# ============================
# Subida de altimetría
# ============================
archivo = st.file_uploader("Sube el archivo CSV con distancia (km) y altitud (m)", type=["csv"])

if archivo is not None:
    df_raw = pd.read_csv(archivo)
    st.subheader("Altimetría cargada")
    st.dataframe(df_raw.head())

    # ============================
    # Ajuste por altitud y temperatura
    # ============================
    ritmo_seg = ritmo_min_km * 60
    factor_altitud = 1 + (altitud / 1000) * 0.02
    factor_temp = 1 + max(0, (temperatura - 15)) * 0.01
    ritmo_ajustado_base = ritmo_seg * factor_altitud * factor_temp

    # ============================
    # Interpolación de altimetría
    # ============================
    distancias_objetivo = np.arange(0, int(distancia_max) + 1, 1)
    if distancias_objetivo[-1] < distancia_max:
        distancias_objetivo = np.append(distancias_objetivo, distancia_max)

    df_interp = pd.DataFrame({"distancia_km": distancias_objetivo})
    df_interp["altitud_m"] = np.interp(distancias_objetivo, df_raw["distancia_km"], df_raw["altitud_m"])

    # ============================
    # Cálculo de pendiente
    # ============================
    df_interp["pendiente_%"] = df_interp["altitud_m"].diff() / df_interp["distancia_km"].diff() #* 100
    df_interp["pendiente_%"] = df_interp["pendiente_%"].fillna(0)

    # ============================
    # Ajuste de ritmo por pendiente
    # ============================
    factor_pendiente = 0.03  # sensibilidad
    df_interp["ritmo_seg"] = ritmo_ajustado_base * (1 + df_interp["pendiente_%"] / 100 * factor_pendiente)

    # ============================
    # Tiempo acumulado
    # ============================
    df_interp["tiempo_seg"] = df_interp["ritmo_seg"]
    df_interp["tiempo_acum_seg"] = df_interp["tiempo_seg"].cumsum()

    # Conversión a min:seg
    df_interp["ritmo"] = (df_interp["ritmo_seg"] / 60).apply(lambda x: f"{int(x)}:{int((x%1)*60):02d}")
    df_interp["tiempo_acum"] = (df_interp["tiempo_acum_seg"] / 60).apply(lambda x: f"{int(x)}:{int((x%1)*60):02d}")

    # ============================
    # Mostrar resultados
    # ============================
    st.subheader("Splits calculados")
    st.dataframe(df_interp[["distancia_km", "altitud_m", "pendiente_%", "ritmo", "tiempo_acum"]])

    tiempo_final = df_interp["tiempo_acum"].iloc[-1]
    st.success(f"Tiempo estimado total para {distancia_opcion}: {tiempo_final}")
