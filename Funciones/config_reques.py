import streamlit as st
import pandas as pd
import mysql.connector
from database import create_connection

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
        tipo_solicitud.nombre_sol AS Solicitud
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
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 2, 1, 2, 1, 1])

            # Escribir los valores de cada columna de la fila
            col1.markdown(f"<p style='font-weight: bold; margin: 0; padding: 5px;'>{row['ID']}</p>", unsafe_allow_html=True)
            col2.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Solicitud']}</p>", unsafe_allow_html=True)
            col3.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Cliente']}</p>", unsafe_allow_html=True)
            col4.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Servicio']}</p>", unsafe_allow_html=True)
            col5.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Responsable']}</p>", unsafe_allow_html=True)
            col6.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Fecha']}</p>", unsafe_allow_html=True)
            col7.markdown(f"<p style='margin: 0; padding: 5px;'>{row['Estado']}</p>", unsafe_allow_html=True)

            # Agregar los botones "Ver" y "Responder" con lógica correspondiente
            """
            with col8:
                if st.button("Ver", key=f"ver_{row['ID']}"):
                    st.info(f"Ver detalles de la solicitud ID: {row['ID']}")
                    # Lógica para mostrar los detalles adicionales

            with col9:
                if st.button("Responder", key=f"responder_{row['ID']}"):
                    st.info(f"Responder solicitud ID: {row['ID']}")
                    # Lógica para responder la solicitud
"""
    # Cierre de la conexión a la base de datos
    cursor.close()
    conn.close()

    # Botón para cerrar sesión
    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'
