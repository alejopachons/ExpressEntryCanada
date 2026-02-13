import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard Express Entry")

# --- 1. FUNCIÓN DE CARGA ROBUSTA ---
@st.cache_data(ttl=3600)
def load_data():
    url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Intentar normalizar la estructura
        if isinstance(data, dict) and 'rounds' in data:
            df = pd.DataFrame(data['rounds'])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            st.error("Formato JSON no reconocido")
            return pd.DataFrame()

        # --- DIAGNÓSTICO: Normalizar nombres de columnas ---
        # Convertimos todo a minúsculas y quitamos espacios para evitar errores de tipeo
        df.columns = df.columns.str.lower().str.strip()
        
        # Mapeo inteligente de columnas (Renombrar a estándar)
        # Buscamos columnas que "se parezcan" a lo que necesitamos
        rename_map = {}
        
        for col in df.columns:
            if 'date' in col: rename_map[col] = 'drawDate'
            elif 'crs' in col or 'score' in col: rename_map[col] = 'crsScore'
            elif 'size' in col or 'invitations' in col: rename_map[col] = 'drawSize'
            elif 'name' in col or 'program' in col: rename_map[col] = 'drawName'
            elif 'number' in col and 'draw' in col: rename_map[col] = 'drawNumber'

        df = df.rename(columns=rename_map)
        
        # Validación de columnas críticas
        required_cols = ['drawDate', 'crsScore', 'drawSize', 'drawName']
        missing = [c for c in required_cols if c not in df.columns]
        
        if missing:
            st.warning(f"⚠️ Columnas faltantes o no identificadas: {missing}")
            st.write("Columnas disponibles en el JSON:", df.columns.tolist())
            return df # Retornamos lo que haya para mostrar la tabla al menos

        # --- LIMPIEZA DE DATOS ---
        df['drawDate'] = pd.to_datetime(df['drawDate'], errors='coerce')
        df['crsScore'] = pd.to_numeric(df['crsScore'], errors='coerce')
        # Limpiar comas en números (ej: "1,500" -> 1500)
        df['drawSize'] = df['drawSize'].astype(str).str.replace(',', '', regex=False)
        df['drawSize'] = pd.to_numeric(df['drawSize'], errors='coerce')
        df['drawName'] = df['drawName'].fillna('Unknown')
        df['Year'] = df['drawDate'].dt.year

        return df.sort_values(by='drawDate', ascending=False)

    except Exception as e:
        st.error(f"Error crítico cargando datos: {e}")
        return pd.DataFrame()

# Cargar datos
df = load_data()

# --- SI NO HAY DATOS O FALTAN COLUMNAS CLAVE ---
if df.empty:
    st.stop()

# Verificar si logramos identificar las columnas necesarias para los gráficos
cols_ok = all(col in df.columns for col in ['drawDate', 'crsScore', 'drawSize', 'drawName'])

if not cols_ok:
    st.error("No se pudieron generar los gráficos porque faltan columnas clave. Revisa la tabla abajo.")
else:
    # --- INTERFAZ GRÁFICA (Solo si los datos están bien) ---
    st.title("🍁 Dashboard Express Entry")
    
    # Filtros
    years = sorted(df['Year'].dropna().unique(), reverse=True)
    selected_years = st.sidebar.multiselect("Filtro Año", years, default=years[:2] if len(years)>1 else years)
    
    if selected_years:
        df_filtered = df[df['Year'].isin(selected_years)]
    else:
        df_filtered = df

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Promedio CRS", f"{df_filtered['crsScore'].mean():.0f}")
    c2.metric("Total Invitaciones", f"{df_filtered['drawSize'].sum():,.0f}")
    c3.metric("Mínimo CRS", f"{df_filtered['crsScore'].min():.0f}")

    # Gráficos
    st.subheader("Tendencia del CRS")
    fig = px.line(df_filtered, x='drawDate', y='crsScore', color='drawName', markers=True)
    st.plotly_chart(fig, use_container_width=True)

# --- TABLA DE REGISTROS (SE MUESTRA SIEMPRE) ---
st.markdown("---")
st.subheader("📂 Registro de Rondas (Tabla de Datos)")

# Mostramos el dataframe completo, sea cual sea su estado
st.dataframe(
    df.style.format({
        "crsScore": "{:.0f}", 
        "drawSize": "{:,.0f}"
    }, na_rep="-"),
    use_container_width=True
)