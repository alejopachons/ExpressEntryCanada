import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Configuración de estilo
sns.set(style="whitegrid")

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
tipos_unicos = df["Tipo de Ronda"].unique()

# Crear checkboxes
selecciones = {}
for tipo in tipos_unicos:
    selecciones[tipo] = st.sidebar.checkbox(tipo, value=False)

# Filtrar por selección
tipos_seleccionados = [tipo for tipo, seleccionado in selecciones.items() if seleccionado]
df_filtrado = df[df["Tipo de Ronda"].isin(tipos_seleccionados)]

st.title("Histórico de Invitaciones Express Entry (Canadá)")

# Gráfico 1: Invitaciones por fecha
st.subheader("Invitaciones emitidas a lo largo del tiempo")
fig1, ax1 = plt.subplots(figsize=(10, 4))
sns.lineplot(data=df_filtrado, x="Fecha", y="Invitaciones", hue="Tipo de Ronda", ax=ax1)
ax1.set_ylabel("Invitaciones")
ax1.set_xlabel("Fecha")
st.pyplot(fig1)

# Gráfico 2: CRS mínimo por fecha
st.subheader("Puntaje CRS mínimo por ronda")
fig2, ax2 = plt.subplots(figsize=(10, 4))
sns.lineplot(data=df_filtrado, x="Fecha", y="CRS mínimo", hue="Tipo de Ronda", ax=ax2, linestyle="--")
ax2.set_ylabel("CRS mínimo")
ax2.set_xlabel("Fecha")
st.pyplot(fig2)

# Mostrar tabla de datos
with st.expander("Ver tabla de datos"):
    st.dataframe(df_filtrado)
