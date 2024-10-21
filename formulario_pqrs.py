import streamlit as st
import pandas as pd
import mysql.connector
from database import create_connection
import uuid
from datetime import datetime
from PIL import Image
import pytz

# Configuración de la página
st.set_page_config(page_title="Formulario PQRSFDD", layout="wide")

def obtener_hora_actual_colombia():
    zona_horaria_colombia = pytz.timezone('America/Bogota')
    hora_actual = datetime.now(zona_horaria_colombia).time()
    return hora_actual

# Función para obtener los datos de un campo desplegable
def fetch_options(query):
    conn = create_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Función para generar el radicado
def generar_radicado(tipo_solicitud):
    conn = create_connection()
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%d%m%Y")
    
    # Obtener el último consecutivo de la tabla sucesos
    cursor.execute("SELECT MAX(SUBSTRING(id_rad, 5, 6)) FROM sucesos WHERE id_rad LIKE %s", (f'RAD.%{fecha_actual}%',))
    ultimo_consecutivo = cursor.fetchone()[0]
    
    if ultimo_consecutivo:
        nuevo_consecutivo = int(ultimo_consecutivo) + 1
    else:
        nuevo_consecutivo = 1
        
    # Formatear el consecutivo a 6 dígitos
    consecutivo_formateado = f"{nuevo_consecutivo:06d}"
    # Generar el radicado final
    radicado = f"RAD.{consecutivo_formateado}{fecha_actual}-{tipo_solicitud}"
    
    cursor.close()
    conn.close()
    
    return radicado

# Función para enviar datos a la base de datos
def submit_form(data_cliente, data_suceso, data_estado, radicado):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        # Insertar en la tabla clientes
        cursor.execute("""INSERT INTO clientes (tipo_id, nombre_completo, nro_celular, direccion, departamento, ciudad, afiliado_eps, regimen, afiliado_ips, grupo_poblacional, acepta_notificacion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", data_cliente)
        id_cliente = cursor.lastrowid  # Obtener el ID generado para el cliente

        # Insertar en la tabla sucesos
        cursor.execute("""INSERT INTO sucesos (id_rad, fecha_rad, id_servicio, id_responsable, fecha, hora, descripcion, observacion, adjunto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", (radicado,) + data_suceso)

        # Insertar en la tabla estado_del_tramite
        cursor.execute("""INSERT INTO estado_del_tramite (id_rad, fecha_vencimiento, Id_usuario, id_tipo_estado, fecha_respuesta, adjunto) VALUES (%s, %s, %s, %s, %s, %s)""", (radicado,) + data_estado)

        # Confirmar cambios en la base de datos
        conn.commit()
        st.success(f"¡Solicitud enviada exitosamente! Número de radicado: {radicado}")

    except Exception as e:
        conn.rollback()
        st.error(f"Error al enviar la solicitud: {str(e)}")
    
    finally:
        cursor.close()
        conn.close()

fecha_solicitud = datetime.now()

# Función principal para mostrar el formulario
def main():
    st.header("FORMATO DE PETICIONES, QUEJAS, RECLAMO, SUGERENCIAS, FELICITACIONES, DENUNCIAS - DESISTIMIENTO")

    st.subheader("Información de la Solicitud")
    st.write("Fecha de Solicitud:", fecha_solicitud.strftime("%Y-%m-%d"))
    tipo_solicitud = st.selectbox("Tipo de Solicitud", fetch_options("SELECT nombre_sol FROM tipo_solicitud").values)
    id_tipo_solicitud = tipo_solicitud[0]  # Se asume que el id es la primera columna
    nombre_tipo_solicitud = tipo_solicitud[1]  # Se asume que el nombre es la segunda columna

    st.subheader("Datos del Cliente")
    nombres_apellidos = st.text_input("Nombre(s) y Apellidos", value=st.session_state.get('nombres_apellidos', ''))
    tipo_identificacion = st.selectbox("Tipo de Identificación", fetch_options("SELECT nombre_tipo_doc FROM tipo_documento").values.flatten())
    numero_documento = st.text_input("Número de Documento", value=st.session_state.get('numero_documento', ''))
    direccion = st.text_input("Dirección de Residencia", value=st.session_state.get('direccion', ''))
    departamento = st.selectbox("Departamento", fetch_options("SELECT nombre_dep FROM departamento").values.flatten())
    municipio = st.selectbox("Municipio", fetch_options("SELECT nombre_ciu FROM ciudad").values.flatten())
    celular = st.text_input("Celular", value=st.session_state.get('celular', ''))
    correo = st.text_input("Correo Electrónico", value=st.session_state.get('correo', ''))
    afiliado_eps = st.selectbox("Afiliado a la EPS", fetch_options("SELECT nombre_eps FROM eps").values.flatten())
    regimen = st.selectbox("Régimen", fetch_options("SELECT nombre_reg FROM regimen").values.flatten())
    ips = st.selectbox("Organismo de Salud IPS", fetch_options("SELECT nombre_ips FROM ips").values.flatten())
    grupo_poblacional = st.selectbox("Grupo Poblacional", fetch_options("SELECT nombre_pob FROM grupo_poblacional").values.flatten())

    st.subheader("Describa lo sucedido durante el proceso de atención")
    servicio = st.selectbox("Servicio", fetch_options("SELECT nombre_serv FROM servicio_disponibles").values.flatten())
    colaborador_responsable = st.selectbox("Nombre del Colaborador o Responsable", fetch_options("SELECT nombre_res FROM responsable_servicio").values.flatten())
    descripcion = st.text_area("Descripción", value=st.session_state.get('descripcion', ''))
    observaciones = st.text_area("Observaciones", value=st.session_state.get('observaciones', ''))
    fecha_hora_suceso = st.date_input("Fecha del Suceso", value=datetime.now())
    hora_suceso = st.time_input("Hora del Suceso")
    archivo_adjunto = st.file_uploader("Adjunta un archivo (Máx. 2MB)", type=['jpg', 'jpeg', 'png', 'pdf'])
    st.caption("Arrastra y suelta el archivo aquí o haz clic para seleccionarlo.")
    consent = st.checkbox("Acepto que se me notifique por correo electrónico sobre el estado de mi solicitud.", value=st.session_state.get('consent', False))

    # Botón Enviar
    if st.button("Enviar"):
        if consent and all([nombres_apellidos, numero_documento, correo]):
            # Generar el radicado
            radicado = generar_radicado(id_tipo_solicitud)
            
            # Datos para cliente
            data_cliente = (tipo_identificacion, nombres_apellidos, celular, direccion, departamento, municipio, afiliado_eps, regimen, ips, grupo_poblacional, consent)
            
            # Datos para suceso
            data_suceso = (fecha_solicitud, servicio, colaborador_responsable, fecha_hora_suceso, hora_suceso, descripcion, observaciones, archivo_adjunto.read() if archivo_adjunto else None)
            
            # Datos para estado del trámite (ejemplo simplificado)
            data_estado = (None, fecha_solicitud, None, None, None, None)
            
            submit_form(data_cliente, data_suceso, data_estado, radicado)

        else:
            st.error("Por favor, completa todos los campos obligatorios.")

    # Botón Borrar
    if st.button("Borrar"):
        # Limpiar los campos del formulario
        st.session_state['nombres_apellidos'] = ''
        st.session_state['numero_documento'] = ''
        st.session_state['direccion'] = ''
        st.session_state['celular'] = ''
        st.session_state['correo'] = ''
        st.session_state['descripcion'] = ''
        st.session_state['observaciones'] = ''
        st.session_state['consent'] = False
        
        # Redibujar la página para reflejar los cambios
        st.rerun()

if __name__ == "__main__":
    main()
