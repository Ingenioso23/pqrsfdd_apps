import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuración de la página de Streamlit (debe ser la primera línea)
st.set_page_config(page_title="Formulario de Respuesta PQRSFDD")

LOGO_PATH = "logo_clinivida.jpg"
MAX_FILE_SIZE_MB = 2
# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_PORT = os.getenv('DATABASE_PORT')

# Configuración del servidor de correo
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

LOGO_PATH = "logo_clinivida.jpg"

# Crear conexión a la base de datos
def create_connection():
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
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Función para enviar correos
def enviar_correo(destinatario, asunto, mensaje):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(mensaje, 'plain'))

    try:
        # Conexión explícita al servidor SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # Usa TLS para seguridad
            server.login(SMTP_USER, SMTP_PASSWORD)  # Inicia sesión en el servidor
            server.sendmail(SMTP_USER, destinatario, msg.as_string())  # Enviar correo
        return True
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
        return False


# Función para obtener los radicados pendientes
def obtener_radicados(usuario):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT 
                sucesos.id_rad,
                clientes.nombre_completo AS nombre_solicitante,
                sucesos.fecha AS fecha_solicitud,
                clientes.email AS correo,
                tipo_estado.nombre_estado AS estado_actual,
                usuarios.nombre AS responsable
            FROM sucesos
            INNER JOIN estado_del_tramite edt ON sucesos.id_rad = edt.radicado
            INNER JOIN tipo_estado ON tipo_estado.id_tipo_estado = edt.id_tipo_estado
            INNER JOIN usuarios ON sucesos.id_responsable = usuarios.id_usuario
            INNER JOIN clientes ON sucesos.id_cliente = clientes.id_cliente
            WHERE sucesos.id_responsable = %s
            AND edt.id_tipo_estado != 3;
        """
        try:
            cursor.execute(query, (usuario,))
            resultados = cursor.fetchall()
            return resultados
        except Exception as e:
            print(f"Error al ejecutar la consulta: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    else:
        print("No se pudo establecer conexión con la base de datos.")
    return []

# Guardar archivos adjuntos
def save_uploaded_file(file, radicado):
    # Crear la ruta del directorio usando el radicado
    carpeta_destino = os.path.join("uploads_res", radicado)
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Ruta del archivo
    ruta_archivo = os.path.join(carpeta_destino, file.name)
    
    # Guardar el archivo en el directorio
    with open(ruta_archivo, "wb") as f:
        f.write(file.getbuffer())
        
    return ruta_archivo

def process_files_and_save_paths(files, radicado):
    rutas_archivos = []
    for file in files:
        if file is None:
            continue

        file_size = len(file.getvalue())
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.warning(f"El archivo {file.name} supera el límite de {MAX_FILE_SIZE_MB} MB.")
            continue

        ruta_archivo = save_uploaded_file(file, radicado)
        rutas_archivos.append(ruta_archivo)

    # Unir rutas con comas
    return ",".join(rutas_archivos) if rutas_archivos else None

def obtener_usuario(id_usuario):
    """Consulta la información del usuario con el ID proporcionado."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id_usuario, nombre, correo, Estado_u 
                FROM usuarios 
                WHERE id_usuario = %s
            """
            cursor.execute(query, (id_usuario,))
            resultado = cursor.fetchone()
            cursor.close()
            connection.close()
            return True
        except mysql.connector.Error as err:
            st.error(f"Error al consultar la base de datos: {err}")
    return None

# Formulario de Respuesta PQRSFDD

st.markdown('<style>body{font-family:sans-serif;}</style>', unsafe_allow_html=True)

# Header con logo y título
st.image(LOGO_PATH, width=100)
st.title("FORMULARIO DE RESPUESTA PQRSFDD")

# Obtener el usuario logueado
usuario_l = st.text_input("Usuario Logueado", placeholder="Ingrese su ID de usuario")
usuario_logueado = obtener_usuario(usuario_l)
if usuario_logueado:
    radicados = obtener_radicados(usuario_l)
    if radicados:
        st.write("Radicados Pendientes:")
        radicado_seleccionado = st.selectbox("Seleccione un Radicado", options=[r["id_rad"] for r in radicados])
        radicado_data = next(r for r in radicados if r["id_rad"] == radicado_seleccionado)
        
        # Mostrar datos del radicado
        st.text_input("Nombre del Solicitante", value=radicado_data["nombre_solicitante"], disabled=True)
        st.date_input("Fecha de Solicitud", value=radicado_data["fecha_solicitud"], disabled=True)

        correo = st.text_input("Correo Electrónico", value=radicado_data["correo"], disabled=True)
        
        # Estado actual y posibilidad de cambiarlo
        estado_actual = st.selectbox("Estado Actual", ["Recibida", "En Tramite", "Contestada", "Vencida"], index=["Recibida", "En Tramite", "Contestada", "Vencida"].index(radicado_data["estado_actual"]))
        
        # Fecha de respuesta (solo si el estado es 'Contestado')
        if estado_actual == "Contestada":
            fecha_respuesta = st.date_input("Fecha de Respuesta", value=datetime.now())
        
        # Descripción y adjuntos
        descripcion = st.text_area("Descripción de la Respuesta")
        archivo = st.file_uploader("Adjuntar Archivo(s)", type=['pdf', 'jpg', 'jpeg', 'png'], accept_multiple_files=True)

        # Botones
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Enviar"):
                # Guardar adjuntos
                if archivo:
                    rutas_adjuntos = process_files_and_save_paths(archivo, radicado_seleccionado)
                else:
                    rutas_adjuntos = None

                # Actualizar estado en la base de datos
                connection = create_connection()
                if connection:
                    cursor = connection.cursor()
                    try:
                        estado_map = {
                            "Recibida": 1,
                            "En Tramite": 2,
                            "Contestada": 3,
                            "Vencida": 4
                        }
                        estado_numerico = estado_map.get(estado_actual, None)
                        query = """
                            UPDATE estado_del_tramite 
                            SET id_tipo_estado = %s, 
                                fecha_respuesta = %s, 
                                descripcion_res = %s, 
                                adjunto_res = %s
                            WHERE radicado = %s
                        """

                        cursor.execute(query, (
                            estado_numerico, 
                            fecha_respuesta if estado_actual == "Contestada" else None, 
                            descripcion, 
                            rutas_adjuntos if rutas_adjuntos else None, 
                            radicado_seleccionado
                        ))
                        connection.commit()
                        
                        # Enviar correo al solicitante
                        mensaje = (
                            f"Su solicitud con radicado {radicado_seleccionado} ha sido respondida.\n"
                            f"Respuesta: {descripcion} \n"
                            f"Te invitamos a contestar la encuenta de satisfacción siguiente: \n"
                            f"https://forms.gle/pjpNxWQPA7mYvyvs9"
                        )
                        enviar_correo(correo, "Respuesta PQRSFDD", mensaje)
                        
                        st.success("Respuesta enviada correctamente.")
                    except Exception as e:
                        connection.rollback()
                        st.error(f"Error al actualizar el estado: {e}")
                    finally:
                        cursor.close()
                        connection.close()
        with col2:
            if st.button("Borrar"):
                st.rerun()
    else:
        st.info("No tiene radicados pendientes.")

