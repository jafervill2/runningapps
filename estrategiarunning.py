import streamlit as st
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt

st.title("Simulador de Ritmo Ajustado por Pendiente y Altitud")

# ============================
# Entradas de usuario
# ============================
st.write("Ingresa tu tiempo ideal de carrera")

col1, col2 = st.columns(2)

ritmo_min = col1.number_input("Minutos por km", min_value=0, max_value=20, value=5, step=1)
ritmo_seg = col2.number_input("Segundos", min_value=0, max_value=59, value=0, step=1)

# Convertir a decimal en minutos
ritmo_min_km = ritmo_min + ritmo_seg / 60

st.write(f"Tu ritmo es: {ritmo_min}:{ritmo_seg:02d} min/km")

# Entrada del usuario: altitud de entrenamiento
alt_entrenamiento = st.number_input("Altitud de entrenamiento (msnm)", min_value=0, max_value=5000, value=500, step=100)

temperaturale = st.number_input("Temperatura entrenamiento (°C)", min_value=12, max_value=40, value=25, step=1)
temperaturalc = st.number_input("Temperatura carrera (°C)", min_value=12, max_value=40, value=25, step=1)

distancia_opcion = st.selectbox(
    "Selecciona la distancia de carrera",
    options=["10 Km", "21.095 Km", "42.195 Km"],
    index=2
)

# Convertir selección a número
if distancia_opcion == "10 Km":
    distancia_max = 10.0
elif distancia_opcion == "21.095 Km":
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
    st.dataframe(df_raw, height=600)

    # ============================
    # Ajuste por altitud y temperatura
    # ============================
    alt_carrera = df_raw["altitud_m"].mean()
    st.info(f"Altitud promedio de la carrera: {alt_carrera:.0f} msnm")


    # ============================
    # Parámetros de fatiga
    # ============================
    a = st.number_input("Parámetro a (ajuste de fatiga)", min_value=-10.0, max_value=10.0, value=0.0, step=0.5, format="%.2f")
    b = st.number_input("Parámetro b (pendiente de la curva sigmoidal)", min_value=0.01, max_value=10.0, value=1.0, step=0.01, format="%.2f")

    
    ritmo_seg = ritmo_min_km * 60
    delta_alt = (alt_carrera - alt_entrenamiento) / 1000
    factor_altitud =  delta_alt * 0.02/0.3
    factor_temp = (temperaturalc - temperaturale) * 0.01/5
    st.success(f"{factor_altitud}: {factor_temp} : {1+(factor_altitud + factor_temp)}")
    ritmo_ajustado_base = ritmo_seg * (1+(factor_altitud + factor_temp))

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
    df_interp["pendiente_%"] = df_interp["altitud_m"].diff() / df_interp["distancia_km"].diff()
    df_interp["pendiente_%"] = df_interp["pendiente_%"].fillna(0)

    # ============================
    # Ajuste de ritmo por pendiente
    # ============================
    factor_pendiente = 18/60
    df_interp["ritmo_seg"] = ritmo_ajustado_base * (1 + df_interp["pendiente_%"] / 100 * factor_pendiente)

    # ============================
    # Ajuste por fatiga (sigmoidal)
    # ============================
    def fatiga_ajuste(distancia_km, dist_total, a, b):
        dist1 = dist_total / 3
        dist2 = 2 * dist1
        s = (a / (1 + np.exp(-b * (dist1 - distancia_km)))) - \
            (a / (1 + np.exp(-b * (distancia_km - dist2))))
        return 1 + s

    df_interp["factor_fatiga"] = df_interp["distancia_km"].apply(
        lambda d: fatiga_ajuste(d, distancia_max, a/100, b)
    )
    df_interp["ritmo_seg"] *= df_interp["factor_fatiga"]

    # ============================
    # Tiempo acumulado
    # ============================
    df_interp["dist_segmento"] = df_interp["distancia_km"].diff().fillna(0)
    df_interp["tiempo_seg"] = df_interp["ritmo_seg"] * df_interp["dist_segmento"]
    df_interp["tiempo_acum_seg"] = df_interp["tiempo_seg"].cumsum()

    # Formatos
    df_interp["ritmo"] = (df_interp["ritmo_seg"] / 60).apply(lambda x: f"{int(x)}:{int((x%1)*60):02d}")

    def format_hms(segundos):
        h = int(segundos // 3600)
        m = int((segundos % 3600) // 60)
        s = int(segundos % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    df_interp["tiempo_acum"] = df_interp["tiempo_acum_seg"].apply(format_hms)
    
    # ============================
    # Mostrar resultados
    # ============================
    st.subheader("Splits calculados")
    #st.dataframe(df_interp[["distancia_km", "altitud_m", "pendiente_%", "ritmo min/Km", "tiempo_acum"]])

    st.dataframe(    df_interp[["distancia_km", "altitud_m", "pendiente_%", "ritmo", "tiempo_acum"]]
        .style.format({
            "distancia_km": "{:.1f}",
            "altitud_m": "{:.1f}",
            "pendiente_%": "{:.1f}"
        })
    )



    tiempo_final = df_interp["tiempo_acum"].iloc[-1]
    tiempo_final_seg = df_interp["tiempo_acum_seg"].iloc[-1]
    ritmo_medio=format_hms(tiempo_final_seg/distancia_max)
    st.success(f"Tiempo estimado total para {distancia_opcion}: {tiempo_final}")
    st.success(f"Ritmo promedio para {distancia_opcion}: {ritmo_medio} min/Km")

   
