import streamlit as st

# Sidebar para navegación
st.sidebar.title("Navegación")
seleccion = st.sidebar.radio("Ir a:", ["Express Entry", "MPNP"])

# Lógica de navegación
if seleccion == "Express Entry":
    from app import run as run_app
    run_app()
elif seleccion == "MPNP":
    from MPNP import run as run_mpnp
    run_mpnp()