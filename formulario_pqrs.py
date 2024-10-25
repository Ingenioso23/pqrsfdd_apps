import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Acceder a las variables de entorno
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_PORT = os.getenv('DATABASE_PORT')

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
st.set_page_config(page_title="Formulario PQRSFDD", layout="wide")

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
def submit_form(datos_cliente, datos_sucesos):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Insertar en la tabla clientes
            cursor.execute(""" 
                INSERT INTO clientes (id_cliente, tipo_id, nombre_completo, nro_celular, email, direccion, departamento, ciudad, afiliado_eps, regimen, afiliado_ips, grupo_poblacional, acepta_notificacion) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, datos_cliente)  # Aquí ya no es necesario convertir a tuple
            
            # Insertar en la tabla sucesos
            cursor.execute(""" 
                INSERT INTO sucesos (id_rad, fecha_rad, id_servicio, id_responsable, fecha, hora, descripcion, observacion, adjunto) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, datos_sucesos)  # Aquí ya no es necesario convertir a tuple
            
            connection.commit()  # Confirma los cambios
            st.success("¡Solicitud enviada exitosamente!")
            
        except Exception as e:
            connection.rollback()  # Revierte los cambios en caso de error
            st.error(f"Error al enviar la solicitud: {str(e)}")
        finally:
            cursor.close()
            connection.close()

# Función principal para mostrar el formulario
def main():
    st.header("FORMULARIO DE SOLICITUD PQRSFDD")

    st.subheader("Información de la Solicitud")
    fecha_solicitud = datetime.now()
    st.write("Fecha de Solicitud:", fecha_solicitud.strftime("%Y-%m-%d"))
    
    tipo_solicitud_data = fetch_options("SELECT id_solicitud, nombre_sol FROM tipo_solicitud")
    tipo_solicitud_opciones = [f"{row[0]} - {row[1]}" for row in tipo_solicitud_data]
    
    tipo_solicitud_seleccionado = st.selectbox("Tipo de Solicitud", tipo_solicitud_opciones)
    tipo_solicitud = tipo_solicitud_seleccionado.split(" - ")[0]

    st.subheader("Datos del Cliente")
    nombres_apellidos = st.text_input("Nombre(s) y Apellidos", value=st.session_state.get('nombres_apellidos', ''))
    tipo_identificacion_data = fetch_options("SELECT id_tipo_doc, nombre_tipo_doc FROM tipo_documento")
    tipo_identificacion_opciones = {row[1]: row[0] for row in tipo_identificacion_data}
    tipo_identificacion_seleccionado = st.selectbox("Tipo de Identificación", list(tipo_identificacion_opciones.keys()))
    tipo_identificacion = tipo_identificacion_opciones[tipo_identificacion_seleccionado]
    
    numero_documento = st.text_input("Número de Documento", value=st.session_state.get('numero_documento', ''))
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
    archivo_adjunto = st.file_uploader("Adjuntar Archivo", type=['pdf', 'jpg', 'jpeg', 'png'])

    # Si se seleccionó un archivo, se procesa
    if archivo_adjunto is not None:
        # Guardar el archivo en el sistema de archivos temporalmente
        ruta_archivo = f"adjuntos/{archivo_adjunto.name}"
        with open(ruta_archivo, "wb") as f:
            f.write(archivo_adjunto.getbuffer())

    if st.button("Enviar Solicitud"):
        if all([nombres_apellidos, tipo_identificacion, numero_documento, direccion, 
                 departamento, municipio, celular, correo, afiliado_eps, regimen, 
                 ips, grupo_poblacional, servicio, responsable, fecha_atencion, 
                 hora_atencion, descripcion]):
            
            # Generar el radicado
            radicado = generar_radicado(tipo_solicitud)

            # Datos del cliente como tupla
            datos_cliente = (
                numero_documento,  # El id_cliente se autoincrementa
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
                True
            )
            
            # Datos del suceso como tupla
            datos_sucesos = (
                radicado,
                fecha_solicitud,
                servicio,
                responsable,
                fecha_atencion,
                hora_atencion,
                descripcion,
                observacion,
                ruta_archivo if archivo_adjunto else None  # Ruta del archivo o None
            )

            # Enviar los datos a la base de datos
            submit_form(datos_cliente, datos_sucesos)

            for key in ["nombres_apellidos", "numero_documento", "direccion", "celular", "correo", "descripcion", "observacion"]:
                st.session_state[key] = ""
            
            st.rerun()

        else:
            st.warning("Por favor, complete todos los campos requeridos.")

if __name__ == "__main__":
    main()
