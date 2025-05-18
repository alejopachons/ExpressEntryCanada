import streamlit as st

st.set_page_config(layout="wide", page_title="Canada calc")

# Sidebar para navegación
st.title("Selecciona entre EXpress entry y MPNP")
seleccion = st.radio("Ir a:", ["Express Entry", "MPNP"])
st.divider()

# Lógica de navegación
if seleccion == "Express Entry":
    from EE import run as run_ee
    run_ee()
elif seleccion == "MPNP":
    from MPNP import run as run_mpnp
    run_mpnp()  
    