import streamlit as st
from database import create_connection
import hashlib  # Para encriptar la nueva contraseña

# Función para conectar a la base de datos
def conectar_bd():
    conn = create_connection()  # Cambia la ruta a tu base de datos
    return conn

# Función para actualizar la contraseña
def actualizar_contraseña(token, nueva_contraseña):
    conn = create_connection() 
    cursor = conn.cursor()
    
    # Verificamos si el token es válido
    cursor.execute("SELECT * FROM usuarios WHERE token = ?", (token,))
    usuario = cursor.fetchone()
    
    if usuario:
        # Encriptamos la nueva contraseña
        nueva_contraseña_encriptada = hashlib.sha256(nueva_contraseña.encode()).hexdigest()
        
        # Actualizamos la contraseña en la base de datos
        cursor.execute("UPDATE usuarios SET contraseña = ? WHERE token = ?", (nueva_contraseña_encriptada, token))
        conn.commit()
        conn.close()
        return True
    else:
        conn.close()
        return False

# Función para el formulario de restablecimiento
st.title("Restablecer Contraseña")

# Campos de entrada
token = st.text_input("Ingresa el token recibido:")
nueva_contraseña = st.text_input("Nueva contraseña:", type="password")

# Si el botón es presionado
if st.button("Restablecer contraseña"):
    if token and nueva_contraseña:
        # Actualizamos la contraseña en la base de datos
        exito = actualizar_contraseña(token, nueva_contraseña)
        
        if exito:
            st.success("Contraseña restablecida exitosamente.")
        else:
            st.error("Token inválido o no encontrado en la base de datos.")
    else:
        st.warning("Por favor, completa todos los campos.")
