import streamlit as st

def user_management_page():
    st.subheader("Gestión de Usuarios")
    st.write("Aquí puedes crear, modificar, eliminar y leer usuarios del sistema.")
    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'
    # Lógica para gestionar usuarios va aquí