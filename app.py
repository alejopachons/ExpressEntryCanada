# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

# Obtener tipos únicos
tipos_unicos = df["Tipo de Ronda"].unique()

# Crear checkboxes por tipo de ronda
selecciones = {}
for tipo in tipos_unicos:
    selecciones[tipo] = st.sidebar.checkbox(tipo, value=False)

# Filtrar según los checkboxes seleccionados
tipos_seleccionados = [tipo for tipo, seleccionado in selecciones.items() if seleccionado]
df_filtrado = df[df["Tipo de Ronda"].isin(tipos_seleccionados)]

st.title("Histórico de Invitaciones Express Entry (Canadá)")

# Gráfico combinado con doble eje
fig = go.Figure()

for tipo in tipos_seleccionados:
    df_tipo = df_filtrado[df_filtrado["Tipo de Ronda"] == tipo]
    
    # Línea para Invitaciones (eje izquierdo)
    fig.add_trace(go.Scatter(
        x=df_tipo["Fecha"],
        y=df_tipo["Invitaciones"],
        name=f"Invitaciones - {tipo}",
        mode="lines",
        yaxis="y1"
    ))

    # Línea para CRS mínimo (eje derecho)
    fig.add_trace(go.Scatter(
        x=df_tipo["Fecha"],
        y=df_tipo["CRS mínimo"],
        name=f"CRS mínimo - {tipo}",
        mode="lines",
        line=dict(dash="dot"),  # Línea punteada para distinguir
        yaxis="y2"
    ))

# Configurar diseño del gráfico
fig.update_layout(
    title="Invitaciones y Puntaje CRS mínimo por Ronda",
    xaxis=dict(title="Fecha"),
    yaxis=dict(
        title="Invitaciones",
        side="left"
    ),
    yaxis2=dict(
        title="CRS mínimo",
        overlaying="y",
        side="right"
    ),
    legend=dict(orientation="h"),
    # height=400
)

st.plotly_chart(fig, use_container_width=True)

# Mostrar tabla opcional
with st.expander("Ver tabla de datos"):
    st.dataframe(df_filtrado)
