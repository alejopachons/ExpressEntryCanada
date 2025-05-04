# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

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
st.sidebar.title("Filtros")
st.sidebar.header("Round Type")

# Obtener tipos únicos
tipos_unicos = df["Tipo de Ronda"].sort_values().unique()

# Crear un diccionario de checkboxes
selecciones = {}
for tipo in tipos_unicos:
    selecciones[tipo] = st.sidebar.checkbox(tipo, value=False)

# Filtrar según los checkboxes seleccionados
tipos_seleccionados = [tipo for tipo, seleccionado in selecciones.items() if seleccionado]
df_filtrado = df[df["Tipo de Ronda"].isin(tipos_seleccionados)]


st.title("Invitaciones Express Entry (Canadá)")

col1, col2 = st.columns(2)
col1.metric("Invitaciones", "{:,}".format(df_filtrado["Invitaciones"].sum()))
col2.metric("Avg. CRS score", round(df_filtrado["CRS mínimo"].mean(),0))

# Gráfico 1: Invitaciones por fecha
fig1 = px.line(df_filtrado, x="Fecha", y="Invitaciones", color="Tipo de Ronda",
               title="Invitaciones emitidas a lo largo del tiempo", markers=True)
fig1.update_layout(
    height=300
)
st.plotly_chart(fig1, use_container_width=True)

# Gráfico 2: CRS mínimo por fecha
fig2 = px.line(df_filtrado, x="Fecha", y="CRS mínimo", color="Tipo de Ronda",
               title="Puntaje CRS mínimo por ronda", markers=True)
fig2.update_layout(
        height=300
)
st.plotly_chart(fig2, use_container_width=True)

# Mostrar tabla opcional
with st.expander("Ver tabla de datos"):
    st.dataframe(df_filtrado)
