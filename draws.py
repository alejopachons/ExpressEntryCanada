def run_draws():
    import streamlit as st

    st.set_page_config(layout="wide")
    st.title("Draws")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Express Entry – Canadá")
        st.components.v1.iframe(
            "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/mandate/policies-operational-instructions-agreements/ministerial-instructions/express-entry-rounds.html",
            height=700,
            scrolling=True
        )

    with col2:
        st.subheader("EOI Draws – Manitoba")
        st.components.v1.iframe(
            "https://immigratemanitoba.com/notices/eoi-draw/",
            height=700,
            scrolling=True
        )
