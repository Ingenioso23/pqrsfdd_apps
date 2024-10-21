import streamlit as st

def kpis_page():
    st.subheader("Indicadores (KPIs)")
    st.write("Aquí puedes visualizar los indicadores clave de rendimiento.")

    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'