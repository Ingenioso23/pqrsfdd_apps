import streamlit as st

def requests_page():
    st.subheader("Solicitudes")
    st.write("Aquí puedes ingresar respuestas a las solicitudes asignadas.")
    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'
    
    # Lógica para gestionar solicitudes va aquí