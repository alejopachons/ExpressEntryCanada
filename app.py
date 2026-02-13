import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(layout="wide", page_title="Dashboard Express Entry Canadá")

# --- 1. FUNCIÓN DE CARGA DE DATOS ---
@st.cache_data(ttl=3600)  # Cachear datos por 1 hora para no saturar el servidor
def load_data():
    url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Dependiendo de la estructura del JSON, los datos pueden estar en una lista directa 
        # o bajo una clave como 'rounds'. Ajustamos para leer la estructura de IRCC.
        # Generalmente es una lista directa de objetos.
        if isinstance(data, dict) and 'rounds' in data:
            df = pd.DataFrame(data['rounds'])
        else:
            df = pd.DataFrame(data)

        # Limpieza y conversión de tipos
        # Mapeamos columnas clave (los nombres en el JSON pueden variar ligeramente, ajustamos los estándar)
        # Nota: Ajusta los nombres de las claves ('drawDate', 'crsScore', etc.) si el JSON cambia.
        
        # Convertir fecha
        df['drawDate'] = pd.to_datetime(df['drawDate'])
        
        # Convertir números (limpiar comas si vienen como string)
        df['crsScore'] = pd.to_numeric(df['crsScore'], errors='coerce')
        df['drawSize'] = pd.to_numeric(df['drawSize'].astype(str).str.replace(',', ''), errors='coerce')
        
        # Limpiar nombres de programas (a veces vienen con HTML o muy largos)
        df['drawName'] = df['drawName'].fillna('Unknown')
        
        # Extraer año para filtros
        df['Year'] = df['drawDate'].dt.year
        
        return df.sort_values(by='drawDate', ascending=False)
        
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

# Cargar datos
df = load_data()

if df.empty:
    st.stop()

# --- 2. BARRA LATERAL (SIDEBAR) & FILTROS ---
st.sidebar.header("🛠️ Configuración")

st.sidebar.markdown("---")
st.sidebar.write("### Filtros")

# Filtro de Años
years = sorted(df['Year'].unique(), reverse=True)
selected_years = st.sidebar.multiselect("Selecciona Años", years, default=years[:2]) # Default últimos 2 años

# Filtro de Tipo de Ronda
program_types = df['drawName'].unique()
selected_programs = st.sidebar.multiselect("Tipo de Ronda", program_types, default=program_types)

# Aplicar filtros
if not selected_years:
    df_filtered = df.copy()
else:
    df_filtered = df[df['Year'].isin(selected_years)]

if selected_programs:
    df_filtered = df_filtered[df_filtered['drawName'].isin(selected_programs)]

# --- 3. CUERPO PRINCIPAL ---

st.title("🍁 Dashboard de Rondas Express Entry")
st.markdown(f"Análisis de **{len(df_filtered)}** rondas filtradas desde la fuente oficial de Canadá.")

# --- KPIs (Métricas Clave) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Invitaciones (ITAs)", f"{df_filtered['drawSize'].sum():,.0f}")
with col2:
    st.metric("Promedio CRS", f"{df_filtered['crsScore'].mean():.0f}")
with col3:
    st.metric("CRS Mínimo", f"{df_filtered['crsScore'].min():.0f}")
with col4:
    st.metric("CRS Máximo", f"{df_filtered['crsScore'].max():.0f}")

st.markdown("---")

# --- GRÁFICOS ---

# Fila 1: Comportamiento del CRS y Tamaño de Invitaciones
c1, c2 = st.columns((2, 1))

with c1:
    st.subheader("Tendencia del Puntaje CRS")
    fig_crs = px.line(df_filtered, 
                      x='drawDate', 
                      y='crsScore', 
                      color='drawName',
                      markers=True,
                      title="Evolución del Puntaje CRS por Tipo de Ronda",
                      labels={'crsScore': 'Puntaje CRS', 'drawDate': 'Fecha', 'drawName': 'Programa'})
    st.plotly_chart(fig_crs, use_container_width=True)

with c2:
    st.subheader("Distribución de Invitaciones")
    fig_pie = px.pie(df_filtered, values='drawSize', names='drawName', title="Total ITAs por Programa")
    st.plotly_chart(fig_pie, use_container_width=True)

# Fila 2: Análisis de Volatilidad y Volumen
c3, c4 = st.columns(2)

with c3:
    st.subheader("Volatilidad del CRS (Boxplot)")
    st.markdown("Este gráfico muestra la variabilidad de los puntajes. Cajas más grandes indican mayor inestabilidad en los requisitos.")
    fig_box = px.box(df_filtered, x='drawName', y='crsScore', color='drawName', 
                     title="Distribución de Puntajes por Programa")
    st.plotly_chart(fig_box, use_container_width=True)

with c4:
    st.subheader("Volumen de Invitaciones por Fecha")
    fig_bar = px.bar(df_filtered, x='drawDate', y='drawSize', color='drawName',
                     title="Cantidad de Invitaciones por Ronda")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- 4. DATOS CRUDOS ---
with st.expander("📂 Ver Datos Detallados (Tabla)"):
    st.dataframe(df_filtered[['drawDate', 'drawName', 'crsScore', 'drawSize', 'drawNumber']].style.format({
        "crsScore": "{:.0f}",
        "drawSize": "{:,.0f}"
    }))
    
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar CSV Filtrado", data=csv, file_name="express_entry_data.csv", mime="text/csv")