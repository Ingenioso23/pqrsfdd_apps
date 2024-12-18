import os
import streamlit as st
import pandas as pd
import mysql.connector
from fpdf import FPDF
from database import create_connection

# Función para generar el PDF con mejor formato
def generar_pdf(radicado, fecha_solicitud, tipo_solicitud, id_cliente, nombre_cliente, descripcion, observacion, fecha_suceso, hora_suceso):
    # Crear la carpeta Solicitudes si no existe
    folder_path = "Solicitudes"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Crear el objeto FPDF
    pdf = FPDF()

    # Establecer márgenes
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    # Agregar una página
    pdf.add_page()

    # Establecer la fuente
    pdf.set_font('Arial', 'B', 14)

    # Título del PDF
    pdf.cell(0, 10, 'PQRSFDD', ln=True, align='C')
    pdf.ln(10)  # Salto de línea

    # Título de la solicitud
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Radicado: {radicado}', ln=True, align='L')
    pdf.ln(5)  # Salto de línea

    # Agregar los detalles de la solicitud en una tabla con bordes
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Fecha de Solicitud:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, fecha_solicitud, border=1, ln=True)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Tipo de Solicitud:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, tipo_solicitud, border=1, ln=True)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'ID del Cliente:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, str(id_cliente), border=1, ln=True)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Nombre del Cliente:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, nombre_cliente, border=1, ln=True)

    # Descripción con multi_cell para autoajuste
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Descripción:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 10, descripcion, border=1)
    pdf.ln(5)  # Salto de línea

    # Observación con multi_cell para autoajuste
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Observación:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 10, observacion, border=1)
    pdf.ln(5)  # Salto de línea

    # Fecha y Hora del Suceso ajustada en una sola celda
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Fecha y Hora:', border=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f'{fecha_suceso} {hora_suceso}', border=1, ln=True)

    # Definir la ruta completa del archivo PDF
    pdf_output_path = os.path.join(folder_path, f"Radicado_{radicado}.pdf")

    # Guardar el archivo PDF en la carpeta Solicitudes
    pdf.output(pdf_output_path)

    # Devolver la ruta del archivo generado
    return pdf_output_path

# Función principal de la página de solicitudes
def requests_page():
    # Título y subtítulo
    st.title("Gestión de Solicitudes")
    st.subheader("Visualización y Gestión de Solicitudes")

    # Conexión a la base de datos
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Consulta de los datos de la tabla sucesos
    query = """
    SELECT 
        sucesos.id_rad AS ID,
        clientes.nombre_completo AS Cliente,
        servicio_disponibles.nombre_serv AS Servicio,
        usuarios.nombre AS Responsable,
        sucesos.fecha AS Fecha,
        sucesos.hora AS Hora,
        sucesos.descripcion AS Descripción,
        tipo_estado.nombre_estado AS Estado,
        tipo_solicitud.nombre_sol AS Solicitud,
        clientes.id_cliente AS Id_cliente,
        sucesos.observacion AS Observacion
    FROM sucesos
    JOIN clientes ON sucesos.Id_cliente = clientes.id_cliente
    JOIN servicio_disponibles ON sucesos.id_servicio = servicio_disponibles.id_servicio
    JOIN usuarios ON sucesos.id_responsable = usuarios.id_usuario
    JOIN estado_del_tramite ON sucesos.id_rad = estado_del_tramite.radicado
    JOIN tipo_estado ON estado_del_tramite.id_tipo_estado = tipo_estado.id_tipo_estado
    JOIN tipo_solicitud ON estado_del_tramite.id_solicitud = tipo_solicitud.id_solicitud
    """
    cursor.execute(query)
    data = cursor.fetchall()

    # Convertir los datos a un DataFrame
    df = pd.DataFrame(data)

    # Verificar si los datos están vacíos
    if df.empty:
        st.warning("No se encontraron solicitudes.")
    else:
        # Filtros para los datos
        st.write("Filtrar Solicitudes:")
        cliente_seleccionado = st.selectbox("Filtrar por Responsable", options=["Todos"] + df["Responsable"].unique().tolist())
        if cliente_seleccionado != "Todos":
            df = df[df["Responsable"] == cliente_seleccionado]
        
        solicitud_seleccionado = st.selectbox("Filtrar por Tipo de Solicitud", options=["Todos"] + df["Solicitud"].unique().tolist())
        if solicitud_seleccionado != "Todos":
            df = df[df["Solicitud"] == solicitud_seleccionado]

        estado_seleccionado = st.selectbox("Filtrar por Estado", options=["Todos"] + df["Estado"].unique().tolist())
        if estado_seleccionado != "Todos":
            df = df[df["Estado"] == estado_seleccionado]

        st.write(f"Solicitudes filtradas ({len(df)}):")

        # Convertir las columnas de Fecha y Hora a formato adecuado
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.strftime('%Y-%m-%d')

        # Diseño de la tabla con bordes y todo en una sola línea por registro
        for _, row in df.iterrows():
            # Se usa un layout de columnas para crear una fila de datos
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 2, 1, 2, 1, 1, 1])

            # Escribir los valores de cada columna de la fila
            col1.markdown(f"<p style='font-weight: bold; margin: 0; padding: 5px;'>{row['ID']}</p>", unsafe_allow_html=True)
            col2.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Solicitud']}</p>", unsafe_allow_html=True)
            col3.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Cliente']}</p>", unsafe_allow_html=True)
            col4.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Servicio']}</p>", unsafe_allow_html=True)
            col5.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Responsable']}</p>", unsafe_allow_html=True)
            col6.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Fecha']}</p>", unsafe_allow_html=True)
            col7.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Estado']}</p>", unsafe_allow_html=True)

            # Agregar el botón "Ver"
            with col8:
                if st.button("Ver", key=f"ver_{row['ID']}"):
                    # Generar el PDF para el radicado correspondiente
                    pdf_path = generar_pdf(
                        row['ID'],
                        row['Fecha'],
                        row['Solicitud'],
                        row['Id_cliente'],
                        row['Cliente'],
                        row['Descripción'],
                        row['Observacion'],
                        row['Fecha'],
                        row['Hora']
                    )
                    st.success(f"Se ha generado el PDF para el Radicado {row['ID']}.")
                    st.download_button(label="Descargar PDF", data=open(pdf_path, "rb"), file_name=f"Radicado_{row['ID']}.pdf", mime="application/pdf")

    # Cierre de la conexión a la base de datos
    cursor.close()
    conn.close()

    # Botón para cerrar sesión
    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'
