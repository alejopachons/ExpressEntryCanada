import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date

# Configuración de página
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

# --- 2. SIDEBAR ---
st.sidebar.header("⚙️ Configuración")

# A. INPUT DE PUNTAJE (VACÍO AL INICIO)
st.sidebar.subheader("🎯 Tu Perfil")
user_score = st.sidebar.number_input(
    "Ingresa tu puntaje CRS:", 
    min_value=0, 
    max_value=1200, 
    value=None, 
    placeholder="Ej: 481",
    step=1
)

st.sidebar.markdown("---")

# B. FILTRO DE FECHA (DATEPICKER)
st.sidebar.subheader("📅 Rango de Fechas")
default_start = date(2025, 1, 1)
default_end = date.today()

date_range = st.sidebar.date_input(
    "Selecciona el periodo:",
    value=(default_start, default_end),
    min_value=df['drawDate'].min().date(),
    max_value=date.today(),
    format="DD/MM/YYYY"
)

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

# --- 3. FILTRADO ---
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

# --- NUEVO: PESTAÑAS PARA ORGANIZAR LA VISTA ---
tab1, tab2 = st.tabs(["📊 Grid de Programas", "⚖️ Comparativa: Puntaje vs Cantidad"])

# --- TAB 1: EL GRID DE 4 GRÁFICOS (LO QUE YA TENÍAS) ---
with tab1:
    programs_list = []
    for name, group in df_filtered.groupby('drawName'):
        if not group.empty:
            programs_list.append((name, group.sort_values('drawDate')))

    def chunked(iterable, n):
        for i in range(0, len(iterable), n):
            yield iterable[i:i + n]

    for batch in chunked(programs_list, 4):
        cols = st.columns(4)
        for i, (program_name, group_data) in enumerate(batch):
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f"**{program_name}**")
                    last_crs = group_data.iloc[-1]['drawCRS']
                    last_date = group_data.iloc[-1]['drawDate'].strftime("%d/%m/%y")
                    
                    if user_score:
                        diff = user_score - last_crs
                        color_delta = "normal" if diff >= 0 else "inverse"
                        st.metric("Última ronda", f"{last_crs} pts", f"{diff:+.0f} vs tú", delta_color=color_delta)
                    else:
                        st.metric("Última ronda", f"{last_crs} pts", f"{last_date}")

                    fig = px.line(group_data, x='drawDate', y='drawCRS', markers=True, height=200)
                    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_title=None, yaxis_title=None, showlegend=False)
                    
                    if user_score:
                        fig.add_hline(y=user_score, line_dash="dot", line_color="red", line_width=2)
                        y_vals = list(group_data['drawCRS']) + [user_score]
                        fig.update_yaxes(range=[min(y_vals)-10, max(y_vals)+10])

                    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: EL NUEVO GRÁFICO DE COMPARACIÓN ---
with tab2:
    st.subheader("¿Cómo afecta el tamaño de la ronda al puntaje?")
    st.markdown("Este gráfico combina dos variables para encontrar tendencias:")
    st.markdown("- **Barras Verdes:** Cantidad de invitaciones (Eje Derecho).")
    st.markdown("- **Línea Azul:** Puntaje CRS mínimo (Eje Izquierdo).")
    
    # Crear gráfico de doble eje con graph_objects
    fig_combo = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Barras (Invitaciones)
    fig_combo.add_trace(
        go.Bar(
            x=df_filtered['drawDate'], 
            y=df_filtered['drawSize'], 
            name="Invitaciones Enviadas",
            marker_color='rgba(46, 204, 113, 0.4)', # Verde translúcido
            hoverinfo="x+y"
        ),
        secondary_y=True,
    )

    # 2. Línea (Puntaje)
    fig_combo.add_trace(
        go.Scatter(
            x=df_filtered['drawDate'], 
            y=df_filtered['drawCRS'], 
            name="Puntaje Mínimo (CRS)",
            mode='lines+markers',
            line=dict(color='rgb(31, 119, 180)', width=3),
            marker=dict(size=8)
        ),
        secondary_y=False,
    )

    # Línea del usuario en el gráfico comparativo también
    if user_score:
        fig_combo.add_hline(y=user_score, line_dash="dash", line_color="red", annotation_text="Tu Puntaje")

    # Configuración de ejes y diseño
    fig_combo.update_layout(
        title="Relación Histórica: Volumen vs. Exigencia",
        hovermode="x unified", # Muestra ambos datos al pasar el mouse por una fecha
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Títulos de los ejes
    fig_combo.update_yaxes(title_text="<b>Puntaje CRS</b>", secondary_y=False)
    fig_combo.update_yaxes(title_text="<b>Cantidad de Invitaciones</b>", secondary_y=True, showgrid=False)

    st.plotly_chart(fig_combo, use_container_width=True)
    
    # Análisis de Correlación
    # Calculamos correlación solo si hay suficientes datos
    if len(df_filtered) > 2:
        corr = df_filtered['drawCRS'].corr(df_filtered['drawSize'])
        
        st.info(f"""
        📊 **Dato Estadístico:** La correlación actual es de **{corr:.2f}**.
        * (Cercano a -1 significa que cuando invitan a más gente, el puntaje baja drásticamente).
        * (Cercano a 0 significa que no hay relación clara).
        """)

# --- TABLA AL FINAL (COMÚN) ---
with st.expander("📂 Ver Tabla de Datos"):
    st.dataframe(df_filtered[['drawDate', 'drawName', 'drawCRS', 'drawSize']], use_container_width=True)