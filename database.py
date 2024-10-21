from dotenv import load_dotenv
import os
import mysql.connector
from mysql.connector import Error
import streamlit as st
# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_PORT = os.getenv('DATABASE_PORT')


# Función para conectar a la base de datos
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=DATABASE_HOST,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME,
            port=DATABASE_PORT
        )
        return connection
    except Error as e:
        st.error(f"Error de conexión: {e}")
    return connection
