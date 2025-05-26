import streamlit as st
import requests

def run():
    st.title("Draws")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 rondas recientes – Express Entry")
        
        # Cargar los datos desde el JSON
        url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            rounds = data.get("rounds", [])

            # Mostrar top 10
            for r in rounds[:3]:
                st.markdown(f"""
                <div style="font-size: 14px; line-height: 1.5;">
                    <strong>Ronda #{r['drawNumber']}</strong><br>
                    📅 Fecha: {r['drawDate']}<br>
                    🧭 Programa: {r.get('drawName', 'No especificado')}<br>
                    👥 Invitados: {r['drawSize']}<br>
                    🎯 CRS mínimo: {r['drawCRS']}<br>
                    ✍️ Detalles: {r.get('drawText2', 'No disponible')}
                </div>
                <hr>
                """, unsafe_allow_html=True)
        else:
            st.error("No se pudieron cargar los datos de Express Entry.")

    with col2:
        st.subheader("EOI Draws – Manitoba")
        st.components.v1.iframe(
            "https://immigratemanitoba.com/notices/eoi-draw/",
            height=500,
            scrolling=True
        )
