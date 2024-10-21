import streamlit as st

def form_configuration_page():
    st.subheader("Configuración de Formularios")
    st.write("Aquí puedes configurar los formularios de solicitud y respuesta a PQRSFDD.")
    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'
    # Lógica para configurar formularios va aquí