import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

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
        st.error(f"Error: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.stop()

# --- 2. SIDEBAR CONFIGURACIÓN ---
st.sidebar.header("⚙️ Configuración")

# A. INPUT DE PUNTAJE USUARIO
st.sidebar.subheader("🎯 Tu Perfil")
user_score = st.sidebar.number_input(
    "Ingresa tu puntaje CRS:", 
    min_value=0, 
    max_value=1200, 
    value=450, 
    step=1,
    help="Escribe tu puntaje para compararlo con las rondas históricas."
)

st.sidebar.markdown("---")

# B. FILTRO DE FECHA (SLIDER)
st.sidebar.subheader("📅 Rango de Fechas")
min_date = df['drawDate'].min().date()
max_date = df['drawDate'].max().date()

start_date, end_date = st.sidebar.slider(
    "Selecciona el periodo:",
    min_value=min_date,
    max_value=max_date,
    value=(date(2023, 1, 1), max_date), # Por defecto desde 2023
    format="DD/MM/YYYY"
)

st.sidebar.markdown("---")

# C. FILTRO DE TIPO DE RONDA (CHECKBOXES)
st.sidebar.subheader("📋 Tipos de Ronda")

# Obtenemos programas únicos ordenados
unique_programs = sorted(df['drawName'].unique())

# Contenedor expandible para no saturar la barra si son muchos
with st.sidebar.expander("Seleccionar Programas", expanded=True):
    # Opción para marcar/desmarcar todos
    all_selected = st.checkbox("Seleccionar Todos", value=True)
    
    selected_programs = []
    if all_selected:
        selected_programs = unique_programs
        # Mostramos la lista pero deshabilitada o visualmente indicamos que están todos
        st.caption("✅ Todos los programas seleccionados")
    else:
        # Generamos un checkbox por cada programa
        for prog in unique_programs:
            if st.checkbox(prog, value=False):
                selected_programs.append(prog)

# --- 3. FILTRADO DE DATOS ---
mask = (
    (df['drawDate'].dt.date >= start_date) & 
    (df['drawDate'].dt.date <= end_date) &
    (df['drawName'].isin(selected_programs))
)
df_filtered = df[mask]

# --- 4. ÁREA PRINCIPAL ---
st.title("🍁 Análisis de Rondas Express Entry")

if user_score > 0:
    st.info(f"💡 Tu puntaje es **{user_score}**. La línea roja punteada en los gráficos indica tu posición.")

if df_filtered.empty:
    st.warning("No hay datos para los filtros seleccionados. Intenta ampliar el rango de fechas o seleccionar más programas.")
    st.stop()

# --- 5. GENERACIÓN DE GRÁFICOS (UNO POR TIPO) ---

# Agrupamos por nombre de programa para iterar
grouped = df_filtered.groupby('drawName')

# Contenedor principal
st.markdown("### Comportamiento por Tipo de Ronda")

for program_name, group_data in grouped:
    # Ordenamos por fecha para que la línea salga bien
    group_data = group_data.sort_values(by='drawDate')
    
    # Solo mostramos si hay datos en el rango
    if len(group_data) > 0:
        with st.container():
            st.markdown(f"#### 📌 {program_name}")
            
            # Métricas rápidas encima del gráfico
            last_draw = group_data.iloc[-1]
            diff = user_score - last_draw['drawCRS']
            
            col_metrics1, col_metrics2 = st.columns([3, 1])
            with col_metrics2:
                if diff >= 0:
                    st.success(f"Estás +{diff:.0f} pts sobre la última ronda")
                else:
                    st.error(f"Te faltan {abs(diff):.0f} pts")

            # Gráfico de Línea
            fig = px.line(
                group_data, 
                x='drawDate', 
                y='drawCRS',
                markers=True,
                text='drawCRS', # Mostrar el número en el punto
                title=f"Histórico CRS: {program_name}"
            )
            
            # Personalización visual
            fig.update_traces(textposition="bottom right", line_color='#1f77b4')
            
            # AGREGAR LÍNEA ROJA (PUNTAJE DEL USUARIO)
            fig.add_hline(
                y=user_score, 
                line_dash="dash", 
                line_color="red", 
                annotation_text="Tu Puntaje", 
                annotation_position="top left"
            )
            
            # Ajustar eje Y para que siempre se vea la línea roja aunque esté lejos de los datos
            y_max = max(group_data['drawCRS'].max(), user_score) + 20
            y_min = min(group_data['drawCRS'].min(), user_score) - 20
            fig.update_layout(yaxis_range=[y_min, y_max])
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")

# Tabla Final Resumen
with st.expander("📂 Ver Datos en Tabla"):
    st.dataframe(df_filtered[['drawDate', 'drawName', 'drawCRS', 'drawSize']])