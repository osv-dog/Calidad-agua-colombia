# Esqueleto de la app de EDA (se completa en el paso del EDA)
import streamlit as st

st.set_page_config(page_title="EDA - Calidad del Agua", layout="wide")
st.title("EDA: Calidad del Agua para Consumo Humano en Colombia")

seccion = st.sidebar.radio("Sección", [
    "1. Conexión y vista general",
    "2. Valores faltantes",
    "3. Valores atípicos",
    "4. Distribuciones",
    "5. Correlaciones",
    "6. Conclusiones",
])
st.write(f"Sección seleccionada: {seccion}")
