import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date

# Configuración de página ancha para que caben los 4 gráficos
st.set_page_config(layout="wide", page_title="Dashboard Express Entry")

# --- 1. CARGA DE DATOS ---
@st.cache_data(ttl=3600)
def load_data():
    url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and 'rounds' in data:
            df = pd.DataFrame(data['rounds'])
        else:
            return pd.DataFrame()

        # Limpieza
        df['drawDate'] = pd.to_datetime(df['drawDate'], errors='coerce')
        df['drawCRS'] = pd.to_numeric(df['drawCRS'], errors='coerce')
        df['drawSize'] = df['drawSize'].astype(str).str.replace(',', '', regex=False)
        df['drawSize'] = pd.to_numeric(df['drawSize'], errors='coerce')
        df['drawName'] = df['drawName'].fillna('General / No especificado')
        
        # Eliminar filas sin fecha válida
        df = df.dropna(subset=['drawDate'])
        
        return df.sort_values(by='drawDate', ascending=False)
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.stop()

# --- 2. SIDEBAR CONFIGURACIÓN ---
st.sidebar.header("⚙️ Configuración")

# A. INPUT DE PUNTAJE (VACÍO AL INICIO)
st.sidebar.subheader("🎯 Tu Perfil")
user_score = st.sidebar.number_input(
    "Ingresa tu puntaje CRS:", 
    min_value=0, 
    max_value=1200, 
    value=None,  # <--- Esto hace que el campo inicie vacío
    placeholder="Ej: 481",
    step=1
)

st.sidebar.markdown("---")

# B. FILTRO DE FECHA (DATEPICKER)
st.sidebar.subheader("📅 Rango de Fechas")

# Definir fechas por defecto: 1 Ene 2025 a Hoy
default_start = date(2025, 1, 1)
default_end = date.today()

# El date_input devuelve una tupla con (inicio, fin)
date_range = st.sidebar.date_input(
    "Selecciona el periodo:",
    value=(default_start, default_end),
    min_value=df['drawDate'].min().date(),
    max_value=date.today(),
    format="DD/MM/YYYY"
)

# Validar que se hayan seleccionado ambas fechas (inicio y fin)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = default_start, default_end

st.sidebar.markdown("---")

# C. FILTRO DE TIPO DE RONDA
st.sidebar.subheader("📋 Tipos de Ronda")
unique_programs = sorted(df['drawName'].unique())

with st.sidebar.expander("Seleccionar Programas", expanded=False):
    all_selected = st.checkbox("Seleccionar Todos", value=True)
    if all_selected:
        selected_programs = unique_programs
    else:
        selected_programs = st.multiselect("Elige los programas:", unique_programs, default=unique_programs)

# --- 3. FILTRADO DE DATOS ---
mask = (
    (df['drawDate'].dt.date >= start_date) & 
    (df['drawDate'].dt.date <= end_date) &
    (df['drawName'].isin(selected_programs))
)
df_filtered = df[mask]

# --- 4. ÁREA PRINCIPAL ---
st.title("🍁 Análisis de Rondas Express Entry")

if user_score:
    st.info(f"💡 Comparando con tu puntaje: **{user_score}**")

if df_filtered.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# --- 5. GRID DE GRÁFICOS (4 POR FILA) ---

# Obtener lista de DataFrames agrupados
programs_list = []
for name, group in df_filtered.groupby('drawName'):
    if not group.empty:
        programs_list.append((name, group.sort_values('drawDate')))

# Función para dividir la lista en bloques de 4 (chunks)
def chunked(iterable, n):
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]

# Iterar sobre los programas en grupos de 4
for batch in chunked(programs_list, 4):
    cols = st.columns(4) # Crear 4 columnas
    
    for i, (program_name, group_data) in enumerate(batch):
        with cols[i]:
            # Contenedor visual para cada tarjeta
            with st.container(border=True):
                # Título pequeño para que quepa
                st.markdown(f"**{program_name}**")
                
                # Métricas compactas
                last_crs = group_data.iloc[-1]['drawCRS']
                last_date = group_data.iloc[-1]['drawDate'].strftime("%d/%m/%y")
                
                if user_score:
                    diff = user_score - last_crs
                    color_delta = "normal" if diff >= 0 else "inverse"
                    st.metric("Última ronda", f"{last_crs} pts", f"{diff:+.0f} vs tú", delta_color=color_delta)
                else:
                    st.metric("Última ronda", f"{last_crs} pts", f"{last_date}")

                # Gráfico Simplificado (Sparkline style)
                fig = px.line(
                    group_data, 
                    x='drawDate', 
                    y='drawCRS',
                    markers=True,
                    height=200 # Altura fija pequeña
                )
                
                # Diseño minimalista para la grilla pequeña
                fig.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis_title=None,
                    yaxis_title=None,
                    showlegend=False
                )
                
                # Línea roja del usuario
                if user_score:
                    fig.add_hline(y=user_score, line_dash="dot", line_color="red", line_width=2)
                    # Ajustar zoom vertical para ver la línea roja si está lejos
                    y_vals = list(group_data['drawCRS']) + [user_score]
                    fig.update_yaxes(range=[min(y_vals)-10, max(y_vals)+10])

                st.plotly_chart(fig, use_container_width=True)

# Tabla al final
with st.expander("📂 Ver Tabla de Datos"):
    st.dataframe(df_filtered[['drawDate', 'drawName', 'drawCRS', 'drawSize']], use_container_width=True)