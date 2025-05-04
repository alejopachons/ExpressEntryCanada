import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Express Entry")

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
st.sidebar.header("Tipo de Ronda")

# Obtener tipos únicos
tipos_unicos = df["Tipo de Ronda"].sort_values().unique()

# Crear un diccionario de checkboxes para los tipos de ronda
selecciones_tipo = {}
for tipo in tipos_unicos:
    selecciones_tipo[tipo] = st.sidebar.checkbox(tipo, value=False,  key=f"tipo_{tipo}")

# Filtrar según los tipos de ronda seleccionados
tipos_seleccionados = [tipo for tipo, seleccionado in selecciones_tipo.items() if seleccionado]
df_filtrado = df[df["Tipo de Ronda"].isin(tipos_seleccionados)]

st.sidebar.header("Año")

# Obtener años únicos
años_unicos = df["Fecha"].dt.year.sort_values().unique()

# Crear un diccionario de checkboxes para los años
selecciones_año = {}
for año in años_unicos:
    selecciones_año[año] = st.sidebar.checkbox(str(año), value=True, key=f"año_{año}")

# Filtrar según los años seleccionados
años_seleccionados = [año for año, seleccionado in selecciones_año.items() if seleccionado]
df_filtrado = df_filtrado[df_filtrado["Fecha"].dt.year.isin(años_seleccionados)]

st.sidebar.header("My score")

# Add reference line input
ref_value2 = st.sidebar.number_input("Línea de referencia CRS", value=None, placeholder="Ingrese un valor")

st.title("Express Entry Invitations (Canada )")

# Add link
st.markdown(
    "Invitations for PR under EES [Oficial web site](https://www.canada.ca/en/immigration-refugees-citizenship/corporate/mandate/policies-operational-instructions-agreements/ministerial-instructions/express-entry-rounds.html#wb-auto-4).",
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)
col1.metric("Invitaciones", "{:,}".format(df_filtrado["Invitaciones"].sum()))
col2.metric(
    "Avg. CRS score",
    0 if pd.isna(df_filtrado["CRS mínimo"].mean()) else round(df_filtrado["CRS mínimo"].mean(), 0),
)

# Gráfico 2: CRS mínimo por fecha
fig2 = px.line(df_filtrado, x="Fecha", y="CRS mínimo", color="Tipo de Ronda",
               title="Puntaje CRS mínimo por ronda", markers=True)

fig2.update_layout(
    height=300
)

# Check if ref_value2 is a valid number, and add hline only if it is
if ref_value2 is not None:
    try:
        num_value = float(ref_value2)  # Try converting to float
        if not pd.isna(num_value):  # Check for NaN after conversion
            fig2.add_hline(y=num_value, line_dash="dash", line_color="red", annotation_text=f"My score: {num_value}", annotation_position="top right")
    except (ValueError, TypeError) as e:
        st.sidebar.warning(f"Invalid input '{ref_value2}' for reference line. Please enter a number. Error: {e}")

st.plotly_chart(fig2, use_container_width=True)

# Gráfico 1: Invitaciones por fecha
fig1 = px.line(df_filtrado, x="Fecha", y="Invitaciones", color="Tipo de Ronda",
               title="Invitaciones emitidas a lo largo del tiempo", markers=True)
fig1.update_layout(
    height=300
)

st.plotly_chart(fig1, use_container_width=True)


# Mostrar tabla opcional
# with st.expander("Ver tabla de datos"):
#     st.dataframe(df_filtrado)