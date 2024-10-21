import streamlit as st

def reports_page():
    st.subheader("Reportes")
    st.write("Aquí puedes generar reportes.")

    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'
    # Lógica para configurar formularios de reportes va aquí