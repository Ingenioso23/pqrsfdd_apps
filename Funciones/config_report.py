import streamlit as st
from fpdf import FPDF
from io import BytesIO
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()
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

def fetch_data_from_db():
    """
    Recupera los datos agrupados por servicios y estados de trámites, contando cuántas solicitudes están
    en cada uno de los estados: Recibida, En Tramite, Contestada, Vencida.

    Returns:
        list: Lista de diccionarios con datos de servicios y estados de trámites.
    """
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT 
            servicio_disponibles.nombre_serv AS servicio,
            tipo_solicitud.nombre_sol AS tipo_solicitud,
            usuarios.nombre AS responsable,
            SUM(CASE WHEN estado_del_tramite.id_tipo_estado = 1 THEN 1 ELSE 0 END) AS recibidas,
            SUM(CASE WHEN estado_del_tramite.id_tipo_estado = 2 THEN 1 ELSE 0 END) AS en_tramite,
            SUM(CASE WHEN estado_del_tramite.id_tipo_estado = 3 THEN 1 ELSE 0 END) AS contestadas,
            SUM(CASE WHEN estado_del_tramite.id_tipo_estado = 4 THEN 1 ELSE 0 END) AS vencidas
        FROM sucesos
        JOIN estado_del_tramite ON sucesos.id_rad = estado_del_tramite.radicado
        JOIN tipo_solicitud ON tipo_solicitud.id_solicitud = estado_del_tramite.id_tipo_estado
        JOIN servicio_disponibles ON servicio_disponibles.id_servicio = sucesos.id_servicio
        JOIN usuarios ON sucesos.id_responsable = usuarios.id_usuario
        GROUP BY servicio_disponibles.nombre_serv, tipo_solicitud.nombre_sol, usuarios.nombre
        ORDER BY servicio, tipo_solicitud, responsable;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


def generate_report_by_service(data):
    """
    Genera un informe PDF con columnas: Servicio, Responsable,
    y las cantidades de solicitudes en cada uno de los estados: Recibida, En Tramite, Contestada, Vencida.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14, style="B")

    # Título
    logo_path = "logo_clinivida.jpg"  # Ruta del archivo del logo
    pdf.image(logo_path, x=10, y=8, w=30)  # (x, y, width)
    pdf.cell(200, 10, txt="Reporte de Trámites por Servicio", ln=True, align="C")
    # pdf.cell(200, 10, txt="Clinivida", ln=True, align="C")
    pdf.ln(6)  # Salto de línea

    # Encabezado
    pdf.set_font("Arial", size=7, style="BI" )
    pdf.cell(55, 10, txt="SERVICIO", border=1, align="C")
    pdf.cell(55, 10, txt="RESPONSABLE", border=1, align="C")
    pdf.cell(20, 10, txt="RECIBIDAS", border=1, align="C")
    pdf.cell(20, 10, txt="EN TRAMITE", border=1, align="C")
    pdf.cell(20, 10, txt="CONTESTADAS", border=1, align="C")
    pdf.cell(20, 10, txt="VENCIDAS", border=1, ln=True, align="C")
    
    # Agrupar los datos por servicio y responsable
    servicios_agrupados = {}
    for row in data:
        servicio = row["servicio"]
        responsable = row["responsable"]
        
        # Si el servicio ya está en el diccionario, actualizamos los valores
        if servicio not in servicios_agrupados:
            servicios_agrupados[servicio] = {
                "responsable": responsable,
                "recibidas": 0,
                "en_tramite": 0,
                "contestadas": 0,
                "vencidas": 0
            }
        
        # Sumar las cantidades según el estado
        servicios_agrupados[servicio]["recibidas"] += row["recibidas"]
        servicios_agrupados[servicio]["en_tramite"] += row["en_tramite"]
        servicios_agrupados[servicio]["contestadas"] += row["contestadas"]
        servicios_agrupados[servicio]["vencidas"] += row["vencidas"]

    # Ahora generamos el reporte con los datos agrupados
    pdf.set_font("Arial", size=7)
    for servicio, values in servicios_agrupados.items():
        pdf.cell(55, 10, txt=servicio, border=1, align="L")
        pdf.cell(55, 10, txt=values["responsable"], border=1, align="L")
        pdf.cell(20, 10, txt=str(values["recibidas"]), border=1, align="C")
        pdf.cell(20, 10, txt=str(values["en_tramite"]), border=1, align="C")
        pdf.cell(20, 10, txt=str(values["contestadas"]), border=1, align="C")
        pdf.cell(20, 10, txt=str(values["vencidas"]), border=1, ln=True, align="C")
        
        # Salto de línea después de cada fila de datos
        # pdf.ln(1)

    # Generar el contenido del PDF como bytes
    pdf_content = pdf.output(dest='S').encode('latin1')  # Convertir a bytes
    return BytesIO(pdf_content)  # Crear un objeto BytesIO a partir de los bytes
def reports_page():
    st.subheader("Reportes")
    st.write("Genera reportes agrupados por servicios disponibles.")

    if st.button("Generar Reporte de Servicios"):
        try:
            data = fetch_data_from_db()
            pdf_file = generate_report_by_service(data)

            # Descargar el PDF en Streamlit
            st.download_button(
                label="Descargar Reporte por Servicios",
                data=pdf_file,
                file_name="reporte_por_servicios.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error al generar el reporte: {e}")

    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'

