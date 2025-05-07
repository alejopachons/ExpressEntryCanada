def run():

    import streamlit as st
    import pandas as pd
    import plotly.express as px
    from datetime import datetime


    # Cargar datos
    df_np = pd.read_csv("MPNP.csv", sep=";")

    # Limpiar datos
    df_np = df_np.rename(columns={
        "Fecha": "Fecha",
        "Draw": "Ronda",
        "Tipo": "Tipo",
        "Subtipo": "Subtipo",
        "Number of Letters of Advice to Apply issued": "Invitaciones",
        "Ranking score of lowest-ranked candidate invited": "Puntaje mínimo"
    })

    df_np["Fecha"] = pd.to_datetime(df_np["Fecha"], dayfirst=True)
    df_np = df_np.sort_values("Fecha")
    
    # Limpiar filas vacías o con datos inválidos
    df_np = df_np.dropna(subset=["Fecha"])
    df_np = df_np[df_np["Invitaciones"].notna()]

    # Sidebar
    st.sidebar.title("Filtros")
    
    # Filtro por Tipo
    st.sidebar.header("Tipo de Programa")
    tipos_unicos = df_np["Tipo"].sort_values().unique()
    selecciones_tipo = {}
    for tipo in tipos_unicos:
        selecciones_tipo[tipo] = st.sidebar.checkbox(tipo, value=False, key=f"tipo_{tipo}")
    
    tipos_seleccionados = [tipo for tipo, seleccionado in selecciones_tipo.items() if seleccionado]
    df_np_filtrado = df_np[df_np["Tipo"].isin(tipos_seleccionados)]

    # Filtro por Subtipo
    st.sidebar.header("Subtipo")
    subtipos_unicos = df_np["Subtipo"].dropna().sort_values().unique()
    selecciones_subtipo = {}
    for subtipo in subtipos_unicos:
        selecciones_subtipo[subtipo] = st.sidebar.checkbox(subtipo, value=False, key=f"subtipo_{subtipo}")
    
    subtipos_seleccionados = [subtipo for subtipo, seleccionado in selecciones_subtipo.items() if seleccionado]
    if subtipos_seleccionados:  # Solo filtrar si hay subtipos seleccionados
        df_np_filtrado = df_np_filtrado[df_np_filtrado["Subtipo"].isin(subtipos_seleccionados) | df_np_filtrado["Subtipo"].isna()]

    # Filtro por Año
    st.sidebar.header("Año")
    años_unicos = df_np["Fecha"].dt.year.sort_values().unique()
    selecciones_año = {}
    for año in años_unicos:
        selecciones_año[año] = st.sidebar.checkbox(str(año), value=True, key=f"año_{año}")
    
    años_seleccionados = [año for año, seleccionado in selecciones_año.items() if seleccionado]
    df_np_filtrado = df_np_filtrado[df_np_filtrado["Fecha"].dt.year.isin(años_seleccionados)]

    # Línea de referencia para el puntaje
    st.sidebar.header("Mi puntaje")
    ref_value = st.sidebar.number_input("Línea de referencia", value=None, placeholder="Ingrese su puntaje")

    # Contenido principal
    st.title("Manitoba Provincial Nominee Program (MPNP)")

    # Enlace oficial
    st.markdown(
        "Official MPNP website [Manitoba Provincial Nominee Program](https://immigratemanitoba.com/notices/eoi-draw/)",
        unsafe_allow_html=True
    )

    # Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de invitaciones", "{:,}".format(df_np_filtrado["Invitaciones"].sum()))
    col2.metric(
        "Puntaje mínimo promedio",
        "N/A" if pd.isna(df_np_filtrado["Puntaje mínimo"].mean()) else round(df_np_filtrado["Puntaje mínimo"].mean(), 0),
    )
    
    col3.metric("días desde el último sorteo",
                "N/A" if (datetime.today().date() - df_np_filtrado["Fecha"].max().date()).days else (datetime.today().date() - df_np["Fecha"].max().date()).days,
                )
    

    # Gráfico 1: Puntaje mínimo por fecha
    fig1 = px.line(df_np_filtrado, x="Fecha", y="Puntaje mínimo", color="Subtipo",
                  title="Puntaje mínimo por ronda", markers=True)
    
    # Añadir línea de referencia si existe
    if ref_value is not None:
        try:
            num_value = float(ref_value)
            if not pd.isna(num_value):
                fig1.add_hline(y=num_value, line_dash="dash", line_color="red", 
                              annotation_text=f"Mi puntaje: {num_value}", 
                              annotation_position="top right")
        except (ValueError, TypeError):
            st.sidebar.warning("Por favor ingrese un valor numérico válido")

    fig1.update_layout(height=300)
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2: Invitaciones por fecha
    fig2 = px.line(df_np_filtrado, x="Fecha", y="Invitaciones", color="Subtipo",
                  title="Invitaciones emitidas a lo largo del tiempo", markers=True)
    
    fig2.update_layout(height=300)
    st.plotly_chart(fig2, use_container_width=True)

    # Mostrar tabla de datos
    with st.expander("Ver tabla de datos"):
        st.dataframe(df_np_filtrado)