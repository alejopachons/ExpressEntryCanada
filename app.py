# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# Cargar datos
df = pd.read_csv("Canada.csv", sep=";")

# Limpiar datos
df = df.rename(columns={
    "Date": "Fecha",
    "Round type": "Tipo de Ronda",
    "Invitations issued": "Invitaciones",
    "CRS score of lowest-ranked candidate invited": "CRS mínimo"
})

df["Fecha"] = pd.to_datetime(df["Fecha"])
df = df.sort_values("Fecha")

# Sidebar
st.sidebar.header("Filtros")
tipo_ronda = st.sidebar.multiselect(
    "Selecciona el tipo de ronda",
    options=df["Tipo de Ronda"].unique(),
    default=df["Tipo de Ronda"].unique()
)

# Filtrar datos
df_filtrado = df[df["Tipo de Ronda"].isin(tipo_ronda)]

st.title("Histórico de Invitaciones Express Entry (Canadá)")

# Gráfico 1: Invitaciones por fecha
fig1 = px.line(df_filtrado, x="Fecha", y="Invitaciones", color="Tipo de Ronda",
               title="Invitaciones emitidas a lo largo del tiempo")
st.plotly_chart(fig1, use_container_width=True)

# Gráfico 2: CRS mínimo por fecha
fig2 = px.line(df_filtrado, x="Fecha", y="CRS mínimo", color="Tipo de Ronda",
               title="Puntaje CRS mínimo por ronda")
st.plotly_chart(fig2, use_container_width=True)

# Mostrar tabla opcional
with st.expander("Ver tabla de datos"):
    st.dataframe(df_filtrado)
