import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard Express Entry")

# --- 1. CARGA DE DATOS ---
@st.cache_data(ttl=3600)
def load_data():
    # URL del JSON oficial
    url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Extraemos la lista de rondas
        if isinstance(data, dict) and 'rounds' in data:
            df = pd.DataFrame(data['rounds'])
        else:
            st.error("La estructura del JSON no es la esperada (no se encontró la clave 'rounds').")
            return pd.DataFrame()

        # --- LIMPIEZA Y CONVERSIÓN ---
        
        # 1. FECHAS: Convertir 'drawDate' a datetime
        df['drawDate'] = pd.to_datetime(df['drawDate'], errors='coerce')
        
        # 2. PUNTAJE (CRS): La clave correcta es 'drawCRS'
        # Viene como texto ("400"), lo pasamos a número
        df['drawCRS'] = pd.to_numeric(df['drawCRS'], errors='coerce')
        
        # 3. INVITACIONES (Size): Limpiar comas (ej: "8,500" -> 8500)
        df['drawSize'] = df['drawSize'].astype(str).str.replace(',', '', regex=False)
        df['drawSize'] = pd.to_numeric(df['drawSize'], errors='coerce')
        
        # 4. NOMBRE DEL PROGRAMA: Rellenar nulos
        df['drawName'] = df['drawName'].fillna('General / No especificado')
        
        # 5. AÑO: Extraer para el filtro
        df['Year'] = df['drawDate'].dt.year

        # Ordenar por fecha descendente (lo más nuevo arriba)
        return df.sort_values(by='drawDate', ascending=False)

    except Exception as e:
        st.error(f"Error al procesar los datos: {e}")
        return pd.DataFrame()

# Cargar el DataFrame
df = load_data()

if df.empty:
    st.stop()

# --- 2. SIDEBAR (FILTROS) ---
st.sidebar.title("🍁 Filtros")

# Filtro de Año
all_years = sorted(df['Year'].dropna().unique(), reverse=True)
selected_years = st.sidebar.multiselect("Seleccionar Años", all_years, default=all_years[:2])

# Filtro de Programa
all_programs = df['drawName'].unique()
selected_programs = st.sidebar.multiselect("Tipo de Ronda", all_programs, default=all_programs)

# Aplicar filtros
df_filtered = df.copy()

if selected_years:
    df_filtered = df_filtered[df_filtered['Year'].isin(selected_years)]

if selected_programs:
    df_filtered = df_filtered[df_filtered['drawName'].isin(selected_programs)]

# --- 3. DASHBOARD PRINCIPAL ---

st.title("🍁 Dashboard Express Entry (Canadá)")
st.markdown(f"Mostrando **{len(df_filtered)}** rondas de invitación.")

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Promedio CRS", f"{df_filtered['drawCRS'].mean():.0f}")
col2.metric("Mínimo CRS", f"{df_filtered['drawCRS'].min():.0f}")
col3.metric("Total Invitaciones", f"{df_filtered['drawSize'].sum():,.0f}")
col4.metric("Última Ronda", df_filtered['drawDate'].max().strftime('%Y-%m-%d') if not df_filtered.empty else "-")

st.markdown("---")

# GRÁFICOS

# 1. Línea de Tiempo del CRS
st.subheader("📈 Evolución del Puntaje CRS")
fig_line = px.line(df_filtered, 
                   x='drawDate', 
                   y='drawCRS', 
                   color='drawName',
                   markers=True,
                   title="Puntaje CRS por Fecha y Tipo de Ronda",
                   labels={'drawCRS': 'Puntaje CRS', 'drawDate': 'Fecha'})
st.plotly_chart(fig_line, use_container_width=True)

# 2. Relación Volumen vs Puntaje (Scatter)
st.subheader("🔍 Relación: Cantidad de Invitaciones vs. Puntaje CRS")
fig_scatter = px.scatter(df_filtered, 
                         x='drawSize', 
                         y='drawCRS', 
                         color='drawName', 
                         size='drawSize',
                         hover_data=['drawDate'],
                         title="¿Afecta el tamaño de la ronda al puntaje CRS?")
st.plotly_chart(fig_scatter, use_container_width=True)

# 3. Tabla de Datos
st.markdown("---")
with st.expander("📂 Ver Tabla de Datos Completa"):
    st.dataframe(
        df_filtered[['drawNumber', 'drawDate', 'drawName', 'drawCRS', 'drawSize']]
        .style.format({
            "drawCRS": "{:.0f}",
            "drawSize": "{:,.0f}"
        }),
        use_container_width=True
    )