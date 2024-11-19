import streamlit as st
import pandas as pd
import plotly
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector
from datetime import datetime
from database import create_connection

# Función para crear la conexión a la base de datos
print(plotly.__version__)

# Función para obtener el número total de solicitudes
def get_total_requests():
    conn = create_connection()
    query = "SELECT COUNT(*) FROM sucesos"
    df = pd.read_sql(query, conn)
    conn.close()
    return df.iloc[0, 0]

# Función para obtener el número de solicitudes por tipo
def get_requests_by_type():
    conn = create_connection()
    query = """
    SELECT tipo_solicitud.nombre_sol, COUNT(*) AS total
    FROM estado_del_tramite
    JOIN tipo_solicitud ON estado_del_tramite.id_solicitud = tipo_solicitud.id_solicitud
    GROUP BY tipo_solicitud.nombre_sol
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Función para obtener el estado de las solicitudes
def get_request_status():
    conn = create_connection()
    query = """
    SELECT tipo_estado.nombre_estado, COUNT(*) AS total
    FROM estado_del_tramite
    JOIN tipo_estado ON estado_del_tramite.id_tipo_estado = tipo_estado.id_tipo_estado
    GROUP BY tipo_estado.nombre_estado
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Función para obtener tiempos de respuesta por tipo de solicitud
def get_response_times_by_type():
    conn = create_connection()
    query = """
    SELECT tipo_solicitud.nombre_sol, AVG(DATEDIFF(estado_del_tramite.fecha_respuesta, sucesos.fecha)) AS avg_response_time
    FROM estado_del_tramite
    JOIN sucesos ON estado_del_tramite.radicado = sucesos.id_rad
    JOIN tipo_solicitud ON estado_del_tramite.id_solicitud = tipo_solicitud.id_solicitud
    GROUP BY tipo_solicitud.nombre_sol
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Función para obtener solicitudes por servicio disponible
def get_requests_by_service():
    conn = create_connection()
    query = """
    SELECT servicio_disponibles.nombre_serv, COUNT(*) AS total
    FROM sucesos
    JOIN servicio_disponibles ON sucesos.id_servicio = servicio_disponibles.id_servicio
    GROUP BY servicio_disponibles.nombre_serv
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Función para obtener solicitudes por mes
def get_requests_by_month():
    conn = create_connection()
    query = """
    SELECT MONTH(sucesos.fecha) AS month, COUNT(*) AS total
    FROM sucesos
    GROUP BY MONTH(sucesos.fecha)
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Función principal para mostrar la página de KPIs
def kpis_page():
    st.subheader("Indicadores (KPIs)")
    st.write("Aquí puedes visualizar los indicadores clave de rendimiento de tu sistema PQRSFDD.")

    # Mostrar número total de solicitudes
    total_requests = get_total_requests()
    st.metric("Número Total de Solicitudes", total_requests)

    # Solicitudes por tipo de solicitud
    st.write("Solicitudes por Tipo")
    df_requests_by_type = get_requests_by_type()
    fig1 = px.bar(df_requests_by_type, x='nombre_sol', y='total', title="Solicitudes por Tipo")
    st.plotly_chart(fig1)

    # Estados de las solicitudes
    st.write("Estado de las Solicitudes")
    df_status = get_request_status()
    fig2 = px.pie(df_status, names='nombre_estado', values='total', title="Estado de las Solicitudes")
    st.plotly_chart(fig2)

    # Tiempos de respuesta por tipo de solicitud
    st.write("Tiempos de Respuesta por Tipo de Solicitud")
    df_response_times = get_response_times_by_type()
    fig3 = px.bar(df_response_times, x='nombre_sol', y='avg_response_time', title="Promedio de Tiempos de Respuesta por Tipo de Solicitud")
    st.plotly_chart(fig3)

    # Solicitudes por servicio disponible
    st.write("Solicitudes por Servicio Disponible")
    df_requests_by_service = get_requests_by_service()
    fig4 = px.bar(df_requests_by_service, x='nombre_serv', y='total', title="Solicitudes por Servicio Disponible")
    st.plotly_chart(fig4)

    # Solicitudes por mes
    st.write("Solicitudes por Mes")
    df_requests_by_month = get_requests_by_month()
    fig5 = px.line(df_requests_by_month, x='month', y='total', title="Solicitudes por Mes")
    st.plotly_chart(fig5)

    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'

# Llamar la función para mostrar la página de KPIs
# if __name__ == "__main__":
  #  kpis_page()
