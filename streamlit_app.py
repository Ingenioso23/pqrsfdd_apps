import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import streamlit as st
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt
import datetime
from Funciones import config_user, config_form, config_reques


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_PORT = os.getenv('DATABASE_PORT')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')

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

# Función para obtener tipos de documento desde la base de datos
def get_tipo_documento():
    conn = create_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT id_tipo_doc, nombre_tipo_doc FROM tipo_documento")
    tipos_documento = cursor.fetchall()
    cursor.close()
    conn.close()
    return tipos_documento

# Función para obtener roles desde la base de datos
def get_roles():
    conn = create_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT id_rol, nombre_rol FROM roles")
    roles = cursor.fetchall()
    cursor.close()
    conn.close()
    return roles

# Función para autenticar al usuario
def authenticate_user(email, password):
    conn = create_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    cursor.execute("SELECT contraseña FROM usuarios WHERE correo = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        hashed_password = user[0]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True
    return False

# Función para registrar un nuevo usuario
def register_user(tipo_id, numero_documento, nombre, email, password, rol):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = create_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (tipo_id, id_usuario, nombre, correo, contraseña, rol_id, Estado_u) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (tipo_id, numero_documento, nombre, email, hashed_password, rol, 0))
        conn.commit()
        st.success("¡Usuario registrado exitosamente!")
    except Error as e:
        st.error(f"Error al registrar el usuario: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Función para enviar un correo electrónico
def send_email(to_email, subject, message):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    with smtplib.SMTP(EMAIL_HOST, int(EMAIL_PORT)) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# Función para generar un token de recuperación de contraseña
def generate_recovery_token(email):
    secret_key = "noqf hcym whjc ibor"  # Cambia esto por tu clave secreta
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    token = jwt.encode({'email': email, 'exp': expiration_time}, secret_key, algorithm='HS256')
    return token

# Función para recuperar la contraseña
def recover_password(email):
    conn = create_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT correo FROM usuarios WHERE correo = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        token = generate_recovery_token(email)
        reset_link = f"https://sistema-pqrsfdd.streamlit.app/reset_password?token={token}"
        message = f"Haz clic en el siguiente enlace para restablecer tu contraseña: {reset_link}"
        send_email(email, "Recuperación de Contraseña", message)
        st.success(f"Se ha enviado un enlace para recuperar la contraseña a {email}")
    else:
        st.error("El correo electrónico no está registrado.")

# Función para mostrar el formulario de inicio de sesión
def login_page():
    st.subheader("Iniciar Sesión")
    email = st.text_input("Correo Electrónico")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        if authenticate_user(email, password):
            st.success("¡Inicio de sesión exitoso!")
            st.session_state['authenticated'] = True
            st.session_state['page'] = 'dashboard'
        else:
            st.error("Credenciales incorrectas")

# Función para mostrar el formulario de registro de usuario
def register_page():
    st.subheader("Registrar Usuario")
    tipos_documento = get_tipo_documento()
    roles = get_roles()
    
    tipo_id = st.selectbox("Tipo de Documento", [tipo[1] for tipo in tipos_documento])
    numero_documento = st.text_input("Número de Documento")
    nombre = st.text_input("Nombre Completo")
    email = st.text_input("Correo Electrónico")
    password = st.text_input("Contraseña", type="password")
    rol = st.selectbox("Rol", [rol[1] for rol in roles])

    if st.button("Registrar"):
        if tipo_id and numero_documento and nombre and email and password and rol:
            tipo_doc_id = next((tipo[0] for tipo in tipos_documento if tipo[1] == tipo_id), None)
            rol_id = next((r[0] for r in roles if r[1] == rol), None)
            
            if tipo_doc_id is None or rol_id is None:
                st.error("El tipo de documento o el rol seleccionado no es válido.")
            else:
                register_user(tipo_doc_id, numero_documento, nombre, email, password, rol_id)
        else:
            st.error("Por favor, completa todos los campos.")

# Función para mostrar la página de recuperación de contraseña
def recover_password_page():
    st.subheader("Recuperar Contraseña")
    email = st.text_input("Correo Electrónico")

    if st.button("Enviar Enlace de Recuperación"):
        if email:
            recover_password(email)
        else:
            st.error("Por favor, ingresa tu correo electrónico.")

# Función para mostrar el dashboard
def dashboard_page():
    st.title("Dashboard")
    st.sidebar.header("Menú")
    menu_option = st.sidebar.selectbox("Selecciona una opción", ["Configuración de Usuarios", "Configuración de Formularios", "Solicitudes", "Reportes", "Indicadores (KPIs)"])

    if menu_option == "Configuración de Usuarios":
        config_user.user_management_page()
    elif menu_option == "Configuración de Formularios":
        config_form.form_configuration_page()
    elif menu_option == "Solicitudes":
        config_reques.requests_page()
    elif menu_option == "Reportes":
        reports_page()
    elif menu_option == "Indicadores (KPIs)":
        kpis_page()



def reports_page():
    st.subheader("Reportes")
    st.write("Aquí puedes generar reportes.")
    # Lógica para generar reportes va aquí

def kpis_page():
    st.subheader("Indicadores (KPIs)")
    st.write("Aquí puedes visualizar los indicadores clave de rendimiento.")
    # Lógica para mostrar KPIs va aquí

# Gestión de la navegación entre páginas
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if 'page' not in st.session_state:
    st.session_state['page'] = 'login'

if st.session_state['page'] == 'login':
    login_page()
elif st.session_state['page'] == 'register':
    register_page()
elif st.session_state['page'] == 'recover':
    recover_password_page()
elif st.session_state['page'] == 'dashboard':
    if st.session_state['authenticated']:
        dashboard_page()
    else:
        st.error("Debes iniciar sesión para acceder al dashboard.")

# Agregar botones de navegación
if st.session_state['authenticated']:
    if st.button("Cerrar Sesión"):
        st.session_state['authenticated'] = False
        st.session_state['page'] = 'login'
