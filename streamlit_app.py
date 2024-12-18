import os
from dotenv import load_dotenv
from database import create_connection
import mysql.connector
from mysql.connector import Error
import streamlit as st
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt
import datetime
from Funciones import config_user, config_form, config_reques, config_report, config_kpis



# Backend para manejar la solicitud de cambio de contraseña
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel

load_dotenv()
app = FastAPI()

# Modelo de solicitud de cambio de contraseña
class ResetPasswordRequest(BaseModel):
    token: str
    newPassword: str

@app.post("/reset_password")
def reset_password(request: ResetPasswordRequest):
    try:
        # Decodificar el token y verificar la validez
        secret_key = "ipfo bzdz lwhq xsvt"
        decoded_token = jwt.decode(request.token, secret_key, algorithms=["HS256"])
        email = decoded_token['email']

        # Verificar que la contraseña sea segura (esto puede personalizarse)
        if len(request.newPassword) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres.")
        
        # Conectar a la base de datos y actualizar la contraseña
        conn = create_connection()
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(request.newPassword.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute("UPDATE usuarios SET contraseña = %s WHERE correo = %s", (hashed_password, email))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Contraseña actualizada con éxito."}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="El token ha expirado.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Token inválido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al actualizar la contraseña.")


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Cargar el CSS personalizado
local_css("styles.css")

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

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
    """
    Verifica si el usuario existe y si sus credenciales son válidas.

    Parámetros:
        email (str): Correo electrónico del usuario.
        password (str): Contraseña ingresada por el usuario.

    Retorna:
        dict: Información del usuario si las credenciales son válidas.
        None: Si las credenciales no son válidas o el usuario no existe.
    """
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Consulta para obtener la información del usuario
        cursor.execute("SELECT correo, contraseña, Estado_u FROM usuarios WHERE correo = %s", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if usuario:
            hashed_password = usuario['contraseña']
            # Verificar si la contraseña es correcta
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                return usuario
        return None
    except Error as e:
        st.error(f"Error al autenticar usuario: {e}")
        return None
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
    """
    Envía un correo electrónico con el mensaje especificado.
    """
    try:
        # Convertir EMAIL_PORT a entero, si es posible
        email_port = int(SMTP_PORT)
        
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        with smtplib.SMTP(SMTP_HOST, email_port) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        st.success(f"Correo enviado exitosamente a {to_email}.")
    except ValueError as ve:
        st.error(f"El puerto del servidor de correo no es válido: {ve}")
    except smtplib.SMTPException as smtp_error:
        st.error(f"Error al enviar el correo: {smtp_error}")


# Función para generar un token de recuperación de contraseña
def generate_recovery_token(email):
    """
    Genera un token JWT para la recuperación de contraseña.
    """
    secret_key = "ipfo bzdz lwhq xsvt"  # Cambiar esto por una clave segura
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    token = jwt.encode({'email': email, 'exp': expiration_time}, secret_key, algorithm='HS256')
    return token


# Función para la recuperación de contraseña
def recover_password(email):
    """
    Inicia el proceso de recuperación de contraseña enviando un correo con el enlace.
    """
    conn = create_connection()
    if conn is None:
        st.error("No se pudo conectar a la base de datos.")
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT correo FROM usuarios WHERE correo = %s", (email,))
    user = cursor.fetchone()

    if user:
        try:
            # Generar el token de recuperación
            token = generate_recovery_token(email)
            
            # Guardar el token en la base de datos
            cursor.execute("UPDATE usuarios SET token_val = %s WHERE correo = %s", (token, email))
            conn.commit()

            # Cambiar la URL al dominio y endpoint reales
            reset_link = f"https://recuperarpass.streamlit.app/reset_password?token={token}"
            message = f"Haz clic en el siguiente enlace para restablecer tu contraseña:\n\n{reset_link}\n\n Token: {token}"
            
            # Enviar el correo con el token
            send_email(email, "Recuperación de Contraseña", message)
            st.success(f"Se ha enviado un enlace de recuperación de contraseña a {email}.")
        except Exception as e:
            st.error(f"Error al generar el enlace de recuperación: {e}")
            
        finally:
            cursor.close()  # Asegúrate de que estos estén correctamente alineados
            conn.close()    # Asegúrate de que estos estén correctamente alineados
    else:
        st.error("El correo electrónico no está registrado.")
    


# Función para mostrar el formulario de inicio de sesión
def login_page():
    """
    Página de inicio de sesión.
    Permite a los usuarios ingresar al sistema si están activos y las credenciales son correctas.
    """
    st.subheader("Iniciar Sesión")
    email = st.text_input("Correo Electrónico")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        if email and password:
            usuario = authenticate_user(email, password)
            if usuario:
                if usuario['Estado_u'] == 0:  # Validar si el usuario está inactivo
                    st.error("Este usuario está inactivo. Por favor, contacta al administrador.")
                else:
                    st.success("¡Inicio de sesión exitoso!")
                    st.session_state['authenticated'] = True
                    st.session_state['page'] = 'dashboard'
            else:
                st.error("Credenciales incorrectas. Verifica tu correo y contraseña.")
        else:
            st.warning("Por favor, completa todos los campos.")

    st.markdown("[¿No tienes cuenta?](#)", unsafe_allow_html=False)
    if st.button("Registrarse"):
        st.session_state['page'] = 'register'

    st.markdown("[¿Olvidaste tu contraseña?](#)", unsafe_allow_html=False)
    if st.button("Recuperar Contraseña"):
        st.session_state['page'] = 'recover'

# Función para mostrar el formulario de registro de usuario
def register_page():
    st.subheader("Registrar Usuario")
    
    # Obtener datos de tipos de documento, roles, áreas y servicios
    tipos_documento = get_tipo_documento()
    roles = get_roles()
    areas = get_areas()

    tipo_id = st.selectbox("Tipo de Documento", [tipo[1] for tipo in tipos_documento])
    numero_documento = st.text_input("Número de Documento")
    correo = st.text_input("Correo Electrónico")
    
    # Verificar si el documento o correo ya existe
    if st.button("Verificar Documento/Correo"):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s OR correo = %s", (numero_documento, correo))
        if cursor.fetchone():
            st.error("El número de documento o correo ya existe.")
            cursor.close()
            conn.close()
            return
        cursor.close()
        conn.close()

    nombre = st.text_input("Nombre Completo")
    contraseña = st.text_input("Contraseña", type="password")
    rol = st.selectbox("Rol", [rol[1] for rol in roles])

    # Seleccionar área
    area_seleccionada = st.selectbox("Área", [area[1] for area in areas])
    area_id = next((area[0] for area in areas if area[1] == area_seleccionada), None)
    
    # Filtrar servicios disponibles en el área seleccionada
    if area_id:
        servicios = get_servicios_por_area(area_id)
        if servicios:
            servicio_seleccionado = st.selectbox("Servicio", [servicio[1] for servicio in servicios])
            servicio_id = next((servicio[0] for servicio in servicios if servicio[1] == servicio_seleccionado), None)
        else:
            servicio_seleccionado = None
            servicio_id = None
    else:
        servicio_seleccionado = None
        servicio_id = None

    if st.button("Crear Usuario"):
        tipo_doc_id = next((tipo[0] for tipo in tipos_documento if tipo[1] == tipo_id), None)
        rol_id = next((r[0] for r in roles if r[1] == rol), None)

        if tipo_doc_id and numero_documento and nombre and correo and contraseña and rol_id and area_id and servicio_id:
            try:
                # Encriptar la contraseña
                hashed_password = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())
                
                # Conectar a la base de datos
                conn = create_connection()
                cursor = conn.cursor()

                # Insertar el usuario en la base de datos
                cursor.execute(
                    "INSERT INTO usuarios (tipo_id, id_usuario, nombre, correo, contraseña, rol_id, Estado_u) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (tipo_doc_id, numero_documento, nombre, correo, hashed_password, rol_id, 0)
                )

                # Obtener el ID del usuario recién creado
                cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (numero_documento,))
                usuario_id = cursor.fetchone()[0]

                # Actualizar el servicio con el usuario como responsable
                cursor.execute(
                    "UPDATE areas SET responsable = %s WHERE id_area = %s",
                    (usuario_id, area_id)
                )

                conn.commit()
                st.success(f"Usuario '{nombre}' creado exitosamente y asignado al servicio '{servicio_seleccionado}' en el área '{area_seleccionada}'.")
            except Error as e:
                st.error(f"Error al crear el usuario: {e}")
            finally:
                if conn:
                    cursor.close()
                    conn.close()
        else:
            st.error("Por favor, completa todos los campos.")
    
    if st.button("Volver al Inicio de Sesión"):
        st.session_state['page'] = 'login'
        
def get_areas():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_area, area, responsable FROM areas")
        areas = cursor.fetchall()
        return areas
    except Error as e:
        st.error(f"Error al obtener áreas: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Función para obtener servicios por área
def get_servicios_por_area(area_id):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_servicio, nombre_serv, id_area FROM servicio_disponibles WHERE id_area = %s", (area_id,))
        servicios = cursor.fetchall()
        return servicios
    except Error as e:
        st.error(f"Error al obtener servicios: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Función para mostrar la página de recuperación de contraseña
def recover_password_page():
    st.subheader("Recuperar Contraseña")
    email = st.text_input("Correo Electrónico")

    if st.button("Enviar Enlace de Recuperación"):
        if email:
            recover_password(email)
        else:
            st.error("Por favor, ingresa tu correo electrónico.")

    if st.button("Volver al Inicio de Sesión"):
        st.session_state['page'] = 'login'

# Función para mostrar el dashboard
def dashboard_page():
    st.sidebar.header("Menú")
    menu_option = st.sidebar.selectbox("Selecciona una opción", ["Configuración de Usuarios", "Configuración de Formularios", "Solicitudes", "Reportes", "Indicadores (KPIs)"])

    if menu_option == "Configuración de Usuarios":
        config_user.user_management_page()
    elif menu_option == "Configuración de Formularios":
        config_form.form_configuration_page()
    elif menu_option == "Solicitudes":
        config_reques.requests_page()
    elif menu_option == "Reportes":
        config_report.reports_page()
    elif menu_option == "Indicadores (KPIs)":
        config_kpis.kpis_page()




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
    dashboard_page()


