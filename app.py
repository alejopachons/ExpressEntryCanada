import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

# Configuración de página ancha
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

        # Limpieza y conversión
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

# --- 2. LÓGICA DE RESET (NUEVO) ---
# Definimos los valores por defecto
DEFAULT_START = date(2025, 1, 1)
DEFAULT_END = date.today()

def reset_filters():
    st.session_state.user_score = None
    st.session_state.date_range = (DEFAULT_START, DEFAULT_END)
    st.session_state.all_programs_check = True

# --- 3. SIDEBAR (CONFIGURACIÓN) ---
st.sidebar.header("⚙️ Configuración")

# Botón de Reset
if st.sidebar.button("🔄 Restablecer Filtros", type="primary"):
    reset_filters()

st.sidebar.markdown("---")

# A. INPUT PUNTAJE
st.sidebar.subheader("🎯 Tu Perfil")
# Agregamos key='user_score' para controlarlo desde el reset
user_score = st.sidebar.number_input(
    "Tu puntaje CRS:", 
    min_value=0, 
    max_value=1200, 
    value=None, 
    placeholder="Ej: 481",
    step=1,
    key='user_score' 
)

st.sidebar.markdown("---")

# B. FILTRO FECHAS
st.sidebar.subheader("📅 Rango de Fechas")

# Inicializar estado si no existe para evitar errores en primera carga
if 'date_range' not in st.session_state:
    st.session_state.date_range = (DEFAULT_START, DEFAULT_END)

date_range_input = st.sidebar.date_input(
    "Periodo:",
    value=st.session_state.date_range, # Usamos el estado
    min_value=df['drawDate'].min().date(),
    max_value=date.today(),
    format="DD/MM/YYYY",
    key='date_range'
)

# Validación de tupla (inicio, fin)
if len(date_range_input) == 2:
    start_date, end_date = date_range_input
else:
    start_date, end_date = DEFAULT_START, DEFAULT_END

st.sidebar.markdown("---")

# C. FILTRO PROGRAMAS
st.sidebar.subheader("📋 Tipos de Ronda")
unique_programs = sorted(df['drawName'].unique())

with st.sidebar.expander("Seleccionar Programas", expanded=False):
    # Checkbox para seleccionar todos (con key para reset)
    if 'all_programs_check' not in st.session_state:
        st.session_state.all_programs_check = True
        
    all_selected = st.checkbox("Seleccionar Todos", value=True, key='all_programs_check')
    
    if all_selected:
        selected_programs = unique_programs
    else:
        # Si se desmarca "Todos", mostramos la lista
        selected_programs = st.multiselect("Programas:", unique_programs, default=unique_programs)

# --- 4. FILTRADO ---
mask = (
    (df['drawDate'].dt.date >= start_date) & 
    (df['drawDate'].dt.date <= end_date) &
    (df['drawName'].isin(selected_programs))
)
df_filtered = df[mask]

# --- 5. DASHBOARD ---
st.title("🍁 Análisis: Puntaje vs. Cantidad de Invitaciones")

if df_filtered.empty:
    st.warning("No hay datos en este rango de fechas.")
    st.stop()

# Función para crear el gráfico combinado (Doble Eje)
def create_dual_axis_chart(data, title, score_benchmark):
    # Crear figura con eje secundario
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Barras (Cantidad Invitaciones) -> Eje Secundario (Derecha)
    fig.add_trace(
        go.Bar(
            x=data['drawDate'], 
            y=data['drawSize'], 
            name="Invitaciones",
            marker_color='rgba(135, 206, 250, 0.4)', # Azul claro transparente
            hoverinfo="y+x"
        ),
        secondary_y=True
    )

    # 2. Línea (Puntaje CRS) -> Eje Primario (Izquierda)
    fig.add_trace(
        go.Scatter(
            x=data['drawDate'], 
            y=data['drawCRS'], 
            name="Puntaje CRS",
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ),
        secondary_y=False
    )

    # 3. Línea de Usuario (Si existe)
    if score_benchmark is not None:
        fig.add_hline(
            y=score_benchmark, 
            line_dash="dot", 
            line_color="red", 
            secondary_y=False,
            annotation_text="Tú", 
            annotation_position="top left"
        )
        # Ajustar rango Y para asegurar que se vea la línea roja
        all_scores = list(data['drawCRS']) + [score_benchmark]
        min_y, max_y = min(all_scores), max(all_scores)
        fig.update_yaxes(range=[min_y - 20, max_y + 20], secondary_y=False)

    # Configuración Visual Limpia
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        title=dict(text=f"CRS vs Cantidad", font=dict(size=12), x=0.5),
        hovermode="x unified"
    )
    
    # Ejes
    fig.update_yaxes(title_text=None, secondary_y=False) # Izquierda (Puntaje)
    fig.update_yaxes(showgrid=False, secondary_y=True)   # Derecha (Cantidad)

    return fig

# --- LOGICA DE GRID (4 COLUMNAS) ---
programs_list = []
for name, group in df_filtered.groupby('drawName'):
    if not group.empty:
        programs_list.append((name, group.sort_values('drawDate')))

def chunked(iterable, n):
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]

# Iterar en bloques de 4
for batch in chunked(programs_list, 4):
    cols = st.columns(4)
    
    for i, (program_name, group_data) in enumerate(batch):
        with cols[i]:
            with st.container(border=True):
                # Título del programa
                st.markdown(f"**{program_name}**")
                
                # Obtener últimos datos
                last_row = group_data.iloc[-1]
                last_crs = last_row['drawCRS']
                last_date = last_row['drawDate'].strftime("%Y-%m-%d")
                
                # WARNING 1: FECHA
                st.info(f"📅 Última: {last_date}")

                # WARNING 2: COMPARACIÓN
                if user_score is not None and user_score > 0:
                    diff = user_score - last_crs
                    if diff >= 0:
                        st.success(f"✅ Calificas (+{diff:.0f})")
                    else:
                        st.error(f"❌ Faltan {abs(diff):.0f} pts")
                else:
                    st.warning("➖ Comparación: --")

                # GRÁFICO DOBLE EJE
                fig = create_dual_axis_chart(group_data, program_name, user_score)
                st.plotly_chart(fig, use_container_width=True)

# Tabla al final
with st.expander("📂 Ver Datos Tabulares"):
    st.dataframe(df_filtered[['drawDate', 'drawName', 'drawCRS', 'drawSize']], use_container_width=True)