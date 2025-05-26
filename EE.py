def run():
    
    import streamlit as st
    import pandas as pd
    import numpy as np
    import plotly.express as px
    from datetime import datetime

    # Cargar datos
    df = pd.read_csv("Canada.csv", sep=";")

    # Limpiar datos
    df = df.rename(columns={
        "Date": "Fecha",
        "Round type": "Tipo de Ronda",
        "Invitations issued": "Invitaciones",
        "CRS score of lowest-ranked candidate invited": "CRS mínimo"
    })

    df["Fecha"] = pd.to_datetime(df["Fecha"], format='%d/%m/%Y')
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
    # ref_value2 = st.sidebar.number_input("Línea de referencia CRS", value=None, placeholder="Ingrese un valor")

    st.title("Express Entry Invitations (Canada )")

    # Add link
    st.markdown(
        "Invitations for PR under EES [Oficial web site](https://www.canada.ca/en/immigration-refugees-citizenship/corporate/mandate/policies-operational-instructions-agreements/ministerial-instructions/express-entry-rounds.html).",
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Invitaciones", "{:,}".format(df_filtrado["Invitaciones"].sum()))
    
    if not df_filtrado["Fecha"].dropna().empty:
        fecha_max = df_filtrado["Fecha"].max()
        dias = (datetime.today().date() - fecha_max.date()).days
    else:
        fecha_max = df["Fecha"].max()
        dias = (datetime.today().date() - fecha_max.date()).days
    col2.metric("Días desde el último sorteo", dias)
    
    col3.metric(
        "Avg. CRS score",
        0 if pd.isna(df_filtrado["CRS mínimo"].mean()) else int(df_filtrado["CRS mínimo"].mean()),
    )
    
    with col4:
        ref_value2 = st.number_input("Mi puntaje", value=None, placeholder="Ingrese un valor",format="%0f")

    gh1, gh2 = st.columns(2)
    
    with gh1:

        # Gráfico 1: CRS mínimo por fecha
        fig1 = px.line(df_filtrado, x="Fecha", y="CRS mínimo", color="Tipo de Ronda",
                    title="Puntaje CRS mínimo por ronda", markers=True)

        fig1.add_vline(x="2025-01-01",line_dash="dash", line_color="gray")
        
        # Check if ref_value2 is a valid number, and add hline only if it is
        if ref_value2 is not None:
            try:
                num_value = float(ref_value2)  # Try converting to float
                if not pd.isna(num_value):  # Check for NaN after conversion
                    fig1.add_hline(y=num_value, line_dash="dash", line_color="red", annotation_text=f"My score: {num_value}", annotation_position="top right")
            except (ValueError, TypeError) as e:
                st.sidebar.warning(f"Invalid input '{ref_value2}' for reference line. Please enter a number. Error: {e}")

        fig1.update_layout(
            height=400,
            margin=dict(t=40, l=0, r=0, b=0),
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(size=10)
            ),
            legend=dict(orientation="h", y=-0.3)  # leyenda horizontal debajo
        )
        st.plotly_chart(fig1, use_container_width=True)
        
    with gh2:

        # Gráfico 2: Invitaciones por fecha
        fig2 = px.line(df_filtrado, x="Fecha", y="Invitaciones", color="Tipo de Ronda",
                    title="Invitaciones emitidas a lo largo del tiempo", markers=True)
        fig2.add_vline(x="2025-01-01",line_dash="dash", line_color="gray")
        
        fig2.update_layout(
            height=400,
            margin=dict(t=40, l=0, r=0, b=0),
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(size=10)
            ),
            legend=dict(orientation="h", y=-0.3)  # leyenda horizontal debajo
        )

        st.plotly_chart(fig2, use_container_width=True)


    # Mostrar tabla opcional
    # with st.expander("Ver tabla de datos"):
    #     st.dataframe(df_filtrado)