import streamlit as st
import requests


st.title("Restablecer Contraseña")

token = st.text_input("Ingresa el token recibido:")
nueva_contraseña = st.text_input("Nueva contraseña:", type="password")
if st.button("Restablecer contraseña"):
    if token and nueva_contraseña:
        # Enviar solicitud al backend
        response = requests.post("http://localhost:3000/reset_password", json={
            "token": token,
            "newPassword": nueva_contraseña
        })
        if response.status_code == 200:
            st.success("Contraseña restablecida exitosamente.")
        else:
            st.error(response.json().get("error", "No se pudo restablecer la contraseña."))
    else:
        st.warning("Por favor, completa todos los campos.")
