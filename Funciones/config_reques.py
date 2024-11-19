import streamlit as st
import pandas as pd
import mysql.connector
from database import create_connection

# Página de solicitudes
def requests_page():
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

    if df.empty:
        st.warning("No se encontraron solicitudes.")
    else:
        # Mostrar tabla con filtros
        st.write("Tabla de Solicitudes:")
        cliente_seleccionado = st.selectbox("Filtrar por Responsable", options=["Todos"] + df["Responsable"].unique().tolist())
        if cliente_seleccionado != "Todos":
            df = df[df["Responsable"] == cliente_seleccionado]
        
        solicitud_seleccionado = st.selectbox("Filtrar por Tipo de Solicitud", options=["Todos"] + df["Solicitud"].unique().tolist())
        if cliente_seleccionado != "Todos":
            df = df[df["Solicitud"] == solicitud_seleccionado]

        estado_seleccionado = st.selectbox("Filtrar por Estado", options=["Todos"] + df["Estado"].unique().tolist())
        if estado_seleccionado != "Todos":
            df = df[df["Estado"] == estado_seleccionado]

        st.write("Solicitudes filtradas:")

        # Tabla con botones
        for _, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(11)
            col1.write(row["ID"])
            col2.write(row["Solicitud"])
            col3.write(row["Cliente"])
            col4.write(row["Servicio"])
            col5.write(row["Responsable"])
            col6.write(row["Fecha"])
            col7.write(row["Hora"])
            col8.write(row["Descripción"])
            col9.write(row["Estado"])
            
            # Botón "Ver"
            if col10.button("Ver", key=f"ver_{row['ID']}"):
                st.info(f"Ver detalles de la solicitud ID: {row['ID']}")
                # Lógica para mostrar los detalles adicionales

            # Botón "Responder"
            if col11.button("Responder", key=f"responder_{row['ID']}"):
                st.info(f"Responder solicitud ID: {row['ID']}")
                # Lógica para responder la solicitud

    # Cierre de la conexión
    cursor.close()
    conn.close()

    # Botón para cerrar sesión
    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'
