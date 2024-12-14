import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
LOGO_PATH = "logo_clinivida.jpg"
MAX_FILE_SIZE_MB = 2
# Cargar las variables de entorno desde el archivo .env
load_dotenv()


# Acceder a las variables de entorno
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_PORT = os.getenv('DATABASE_PORT')

#Para Correo
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

def enviar_correo(destinatario, asunto, mensaje):
    # Crear el mensaje de correo
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(mensaje, 'plain'))

    # Enviar el correo
    try:
        # print("Entro por el TRY")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
             # print("entro al with")
            server.starttls()  # Inicia la conexión segura
            server.login(SMTP_USER, SMTP_PASSWORD)  # Inicia sesión
            server.sendmail(SMTP_USER, destinatario, msg.as_string())  # Envía el correo
        return True
    except Exception as e:
        # print("Entro por el Except")
        print(f"Error al enviar correo a {destinatario}: {e}")
        return False

def obtener_datos_cliente(numero_documento):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = "SELECT nombre_completo, nro_celular, email, direccion, departamento, ciudad, afiliado_eps, regimen, afiliado_ips, grupo_poblacional FROM clientes WHERE id_cliente = %s"
        cursor.execute(query, (numero_documento,))
        resultado = cursor.fetchone()
        cursor.close()
        connection.close()
        return resultado
    return None


def save_uploaded_file(file, radicado):
    # Crear la ruta del directorio usando el radicado
    carpeta_destino = os.path.join("uploads", radicado)
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
        # Verificar tamaño del archivo
        if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.warning(f"El archivo {file.name} supera el límite de {MAX_FILE_SIZE_MB} MB.")
            continue

        # Guardar archivo y agregar la ruta a la lista
        ruta_archivo = save_uploaded_file(file, radicado)
        rutas_archivos.append(ruta_archivo)
    
    # Si hay rutas guardadas, convertir en string separado por comas
    return ",".join(rutas_archivos) if rutas_archivos else None

# Crear conexión a la base de datos MySQL
def create_connection():
    try:
        connection = mysql.connector.connect(
            host=DATABASE_HOST,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME,
            port=DATABASE_PORT
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Configuración de la página
st.set_page_config(page_title="Formulario PQRSFDD")

@st.cache_data
def obtener_hora_actual_colombia():
    zona_horaria_colombia = pytz.timezone('America/Bogota')
    hora_actual = datetime.now(zona_horaria_colombia).time()
    return hora_actual

# Función para obtener los datos de un campo desplegable
@st.cache_data
def fetch_options(query):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return results
    return []

# Función para generar el radicado
def generar_radicado(tipo_solicitud):
    fecha_actual = datetime.now().strftime("%d%m%Y")
    
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = "SELECT MAX(SUBSTRING(id_rad, 5, 6)) FROM sucesos WHERE id_rad LIKE %s"
        cursor.execute(query, (f'RAD.%{fecha_actual}%',))
        ultimo_consecutivo = cursor.fetchone()[0]

        if ultimo_consecutivo:
            nuevo_consecutivo = int(ultimo_consecutivo) + 1
        else:
            nuevo_consecutivo = 1
            
        consecutivo_formateado = f"{nuevo_consecutivo:06d}"
        radicado = f"RAD.{consecutivo_formateado}{fecha_actual}-{tipo_solicitud}"
        
        cursor.close()
        connection.close()
        return radicado
    return None

# Función para enviar datos a la base de datos
def submit_form(datos_cliente, datos_sucesos, datos_tramite,  radicado):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            numero_documento = datos_cliente[0]
            # print(numero_documento)
            tipo_identificacion = datos_cliente[1]
            # print(tipo_identificacion)
            email = datos_cliente[4]
            # print(email)

            # Verificamos si el cliente ya existe en la base de datos
            cursor.execute("""SELECT COUNT(*) FROM clientes WHERE id_cliente = %s AND tipo_id = %s """, (numero_documento, tipo_identificacion))
            resultado = cursor.fetchone()
            cliente_existe = resultado[0] if resultado is not None else 0

            if cliente_existe:
            # Si el cliente ya existe, actualizamos los campos
                cursor.execute("""
                UPDATE clientes SET 
                    nombre_completo = %s, 
                    nro_celular = %s, 
                    email = %s, 
                    direccion = %s, 
                    departamento = %s, 
                    ciudad = %s, 
                    afiliado_eps = %s, 
                    regimen = %s, 
                    afiliado_ips = %s, 
                    grupo_poblacional = %s, 
                    acepta_notificacion = %s 
                WHERE tipo_id = %s AND id_cliente = %s
            """, datos_cliente[2:] + (tipo_identificacion, numero_documento))
            else:
            # Si el cliente no existe, insertamos un nuevo registro
                cursor.execute(""" 
                INSERT INTO clientes (id_cliente, tipo_id, nombre_completo, nro_celular, email, direccion, departamento, ciudad, afiliado_eps, regimen, afiliado_ips, grupo_poblacional, acepta_notificacion) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, datos_cliente)

        # Insertar en la tabla sucesos independientemente de si el cliente existía o no
            cursor.execute(""" 
            INSERT INTO sucesos (id_rad, id_cliente, fecha_rad, id_servicio, id_responsable, fecha, hora, descripcion, observacion, adjunto) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, datos_sucesos)
        
        # Insertar en la tabla tramite independientemente de si el cliente existía o no.add
            cursor.execute("""
                       INSERT INTO estado_del_tramite (radicado, id_solicitud, fecha_vencimiento, id_usuario, id_tipo_estado, fecha_respuesta, adjunto_res)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       """, datos_tramite)
        # Tras registrar la solicitud, enviar notificaciones por correo
            correo_cliente = datos_cliente[4]  # Asume que el correo del cliente está en la posición 4 de datos_cliente
            mensaje_cliente = f"Solicitud enviada, su número de radicado es {radicado}"
            enviar_correo(correo_cliente, "Confirmación de solicitud PQRSFDD", mensaje_cliente)

            # Obtener el correo del usuario responsable desde la tabla de usuarios
            cursor.execute("SELECT correo FROM usuarios WHERE id_usuario = %s", (datos_sucesos[3],))
            correo_responsable = cursor.fetchone()[0]
            mensaje_responsable = (
                f"Tiene una solicitud pendiente por responder con número de radicado {radicado}. \n "
                f"Tipo de Solicitud: {datos_tramite[1]} \n "
                f"Fecha de radicado: {datos_sucesos[2]} \n "
                f"Fecha de vencimiento: {datos_tramite[2]} \n\n"
                f"Descripción: {datos_sucesos[7]} \n "
                f"Observación: {datos_sucesos[8]} \n "
                f"Adjunto: {datos_sucesos[9]} \n\n"
                f"Ingrese al sistema y responda las pqrsfdd pendientes: \n"
                f"https://musical-goldfish-jqxwqr64xrvfg74-8505.app.github.dev/"
            )
            enviar_correo(correo_responsable, "Nueva solicitud pendiente en PQRSFDD", mensaje_responsable)

            connection.commit()     
            
            
            
            connection.commit()  
            
            
            st.session_state.clear()
            
            return True, radicado
            

            
            # Recargar la página

            
            
        except Exception as e:
            connection.rollback()  # Revierte los cambios en caso de error
            return False, str(e)
        finally:
            cursor.close()
            connection.close()

# Función principal para mostrar el formulario
def main():
    st.image(LOGO_PATH, width=300) 
    st.header("FORMULARIO DE SOLICITUD PQRSFDD")

    st.subheader("Información de la Solicitud")
    fecha_solicitud = datetime.now()
    st.write("Fecha de Solicitud:", fecha_solicitud.strftime("%Y-%m-%d"))
    
    tipo_solicitud_data = fetch_options("SELECT id_solicitud, nombre_sol FROM tipo_solicitud")
    tipo_solicitud_opciones = [f"{row[0]} - {row[1]}" for row in tipo_solicitud_data]
    
    tipo_solicitud_seleccionado = st.selectbox("Tipo de Solicitud", tipo_solicitud_opciones)
    tipo_solicitud = tipo_solicitud_seleccionado.split(" - ")[0]

    st.subheader("Datos del Cliente")
    
    tipo_identificacion_data = fetch_options("SELECT id_tipo_doc, nombre_tipo_doc FROM tipo_documento")
    tipo_identificacion_opciones = {row[1]: row[0] for row in tipo_identificacion_data}
    tipo_identificacion_seleccionado = st.selectbox("Tipo de Identificación", list(tipo_identificacion_opciones.keys()))
    tipo_identificacion = tipo_identificacion_opciones[tipo_identificacion_seleccionado]
    
    numero_documento = st.text_input("Número de Documento", value=st.session_state.get('numero_documento', ''))
    
    if numero_documento:
        datos_cliente = obtener_datos_cliente(numero_documento)
        if datos_cliente is not None:
            st.session_state.nombres_apellidos = datos_cliente[0]
            st.session_state.celular = datos_cliente[1]
            st.session_state.correo = datos_cliente[2]
            st.session_state.direccion = datos_cliente[3]
            st.session_state.departamento = datos_cliente[4]
            st.session_state.ciudad = datos_cliente[5]
            st.session_state.afiliado_eps = datos_cliente[6]
            st.session_state.regimen = datos_cliente[7]
            st.session_state.afiliado_ips = datos_cliente[8]
            st.session_state.grupo_poblacional = datos_cliente[9]

            # Actualiza los valores de los inputs
            nombres_apellidos = st.session_state.nombres_apellidos
            celular = st.session_state.celular
            correo = st.session_state.correo
            direccion = st.session_state.direccion
            departamento = st.session_state.departamento
            ciudad = st.session_state.ciudad
            afiliado_eps = st.session_state.afiliado_eps
            regimen = st.session_state.regimen
            afiliado_ips = st.session_state.afiliado_ips
            grupo_poblacional = st.session_state.grupo_poblacional
        else:
            st.session_state.nombres_apellidos = ''
            st.session_state.celular = ''
            st.session_state.correo = ''
            st.session_state.direccion = ''
            st.session_state.departamento = ''
            st.session_state.ciudad = ''
            st.session_state.afiliado_eps = ''
            st.session_state.regimen = ''
            st.session_state.afiliado_ips = ''
            st.session_state.grupo_poblacional = ''
            
            nombres_apellidos = st.session_state.nombres_apellidos
            celular = st.session_state.celular
            correo = st.session_state.correo
            direccion = st.session_state.direccion
            departamento = st.session_state.departamento
            ciudad = st.session_state.ciudad
            afiliado_eps = st.session_state.afiliado_eps
            regimen = st.session_state.regimen
            afiliado_ips = st.session_state.afiliado_ips
            grupo_poblacional = st.session_state.grupo_poblacional
        
    nombres_apellidos = st.text_input("Nombre(s) y Apellidos", value=st.session_state.get('nombres_apellidos', ''))
    
    direccion = st.text_input("Dirección de Residencia", value=st.session_state.get('direccion', ''))
    
    departamento_data = fetch_options("SELECT id_departamento, nombre_dep FROM departamento")
    departamento_opciones = {row[1]: row[0] for row in departamento_data}
    departamento_seleccionado = st.selectbox("Departamento", list(departamento_opciones.keys()))
    departamento = departamento_opciones[departamento_seleccionado]

    municipio_data = fetch_options("SELECT id_ciudad, nombre_ciu FROM ciudad")
    municipio_opciones = {row[1]: row[0] for row in municipio_data}
    municipio_seleccionado = st.selectbox("Municipio", list(municipio_opciones.keys()))
    municipio = municipio_opciones[municipio_seleccionado]
    
    celular = st.text_input("Celular", value=st.session_state.get('celular', ''))
    correo = st.text_input("Correo Electrónico", value=st.session_state.get('correo', ''))

    eps_data = fetch_options("SELECT id_eps, nombre_eps FROM eps")
    eps_opciones = {row[1]: row[0] for row in eps_data}
    eps_seleccionado = st.selectbox("Afiliado a la EPS", list(eps_opciones.keys()))
    
    afiliado_eps = eps_opciones[eps_seleccionado]
    # print(afiliado_eps)
   
    regimen_data = fetch_options("SELECT id_regimen, nombre_reg FROM regimen")
    regimen_opciones = {row[1]: row[0] for row in regimen_data}
    regimen_seleccionado = st.selectbox("Régimen", list(regimen_opciones.keys()))
    regimen = regimen_opciones[regimen_seleccionado]

    
   
    ips_data = fetch_options("SELECT id_ips, nombre_ips FROM ips")
    ips_opciones = {row[1]: row[0] for row in ips_data}
    ips_seleccionado = st.selectbox("Organismo de Salud IPS", list(ips_opciones.keys()), index=0)
    ips = ips_opciones[ips_seleccionado]


    grupo_poblacional_data = fetch_options("SELECT id_grupo, nombre_pob FROM grupo_poblacional")
    grupo_poblacional_opciones = {row[1]: row[0] for row in grupo_poblacional_data}
    grupo_poblacional_seleccionado = st.selectbox("Grupo Poblacional", list(grupo_poblacional_opciones.keys()))
    grupo_poblacional = grupo_poblacional_opciones[grupo_poblacional_seleccionado]

    st.subheader("Describa lo sucedido durante el proceso de atención")
    
    servicio_data = fetch_options("SELECT id_servicio, nombre_serv FROM servicio_disponibles")
    if servicio_data:
        servicio_opciones = {row[1]: row[0] for row in servicio_data}
        servicio_seleccionado = st.selectbox("Servicio", list(servicio_opciones.keys()))
        servicio = servicio_opciones[servicio_seleccionado]
    else:
        servicio_seleccionado = None
        st.write("No existen Servicio en la Base de Datos")

    # Consulta para obtener los responsables asociados al servicio seleccionado de forma segura
    responsable_data = fetch_options(f"""
    SELECT u.id_usuario, u.nombre 
    FROM usuarios u 
    JOIN servicio_disponibles sd ON u.id_usuario = sd.responsable 
    WHERE sd.id_servicio = {servicio}
    """)

    if responsable_data:
        responsable_opciones = {row[1]: row[0] for row in responsable_data}
        responsable_seleccionado = st.selectbox("Responsable de Atención", list(responsable_opciones.keys()))
        responsable = responsable_opciones[responsable_seleccionado]
    else:
        responsable_seleccionado = None
        st.write("No existen Responsables asociados a este servicio.")

    fecha_atencion = st.date_input("Fecha de Atención", datetime.today())
    hora_atencion = st.time_input("Hora del Suceso",obtener_hora_actual_colombia())
    descripcion = st.text_area("Descripción del Suceso", value=st.session_state.get('descripcion', ''))
    observacion = st.text_area("Observaciones", value=st.session_state.get('observacion', ''))

    # Carga de archivo
    archivo_adjuntos = st.file_uploader("Adjuntar Archivo(s)", type=['pdf', 'jpg', 'jpeg', 'png'], accept_multiple_files=True)

    consent = st.checkbox("Acepto que se me notifique por correo electrónico sobre el estado de mi solicitud")
    if consent:
        estado = True
    else:
        estado = False

    if st.button("Enviar Solicitud"):
        # Validación de campos obligatorios
    
        if all([nombres_apellidos,numero_documento, direccion, celular, correo, descripcion]):
            
            # Generar el radicado
            radicado = generar_radicado(tipo_solicitud)
            
            ruta_adjuntos = process_files_and_save_paths(archivo_adjuntos, radicado) if archivo_adjuntos else None
            fecha_vencimiento = fecha_solicitud + timedelta(days=1)
            # Datos del cliente como tupla
            datos_cliente = (
                numero_documento,  
                tipo_identificacion,
                nombres_apellidos,
                celular,
                correo,
                direccion,
                departamento,
                municipio,
                afiliado_eps,
                regimen,
                ips,
                grupo_poblacional,
                estado
            )
            
            # Datos del suceso como tupla
            datos_sucesos = (
                radicado,
                numero_documento,
                fecha_solicitud,
                servicio,
                responsable,
                fecha_atencion,
                hora_atencion,
                descripcion,
                observacion,
                ruta_adjuntos
            )
            
            datos_tramite = (
                radicado,
                tipo_solicitud,
                fecha_vencimiento,
                responsable,
                1,
                None,
                None
            )

            # Enviar los datos a la base de datos
            exito, mensaje = submit_form(datos_cliente, datos_sucesos, datos_tramite, radicado)
            
            if exito:
                st.success(f"¡Solicitud enviada y radicada! Nro Radicado: {mensaje}")
                # Preguntar si desea enviar otro radicado
                
              
            else:
            
            
                st.error(f"Error al enviar la solicitud: {mensaje}")

        else:
            st.warning("Por favor, complete todos los campos requeridos.")
    if st.button("Borrar"):
        st.session_state.numero_documento = ''
        st.session_state.nombres_apellidos = ''
        st.session_state.celular = ''
        st.session_state.correo = ''
        st.session_state.direccion = ''
        st.session_state.departamento = ''
        st.session_state.ciudad = ''
        st.session_state.afiliado_eps = ''
        st.session_state.regimen = ''
        st.session_state.afiliado_ips = ''
        st.session_state.grupo_poblacional = ''
            
        nombres_apellidos = st.session_state.nombres_apellidos
        celular = st.session_state.celular
        correo = st.session_state.correo
        direccion = st.session_state.direccion
        departamento = st.session_state.departamento
        ciudad = st.session_state.ciudad
        afiliado_eps = st.session_state.afiliado_eps
        regimen = st.session_state.regimen
        afiliado_ips = st.session_state.afiliado_ips
        grupo_poblacional = st.session_state.grupo_poblacional
        
        st.rerun()
        if st.button("Cancelar"):
            st.session_state.numero_documento = ''
            st.session_state.nombres_apellidos = ''
            st.session_state.celular = ''
            st.session_state.correo = ''
            st.session_state.direccion = ''
            st.session_state.departamento = ''
            st.session_state.ciudad = ''
            st.session_state.afiliado_eps = ''
            st.session_state.regimen = ''
            st.session_state.afiliado_ips = ''
            st.session_state.grupo_poblacional = ''
            
               
if __name__ == "__main__":
    main()
