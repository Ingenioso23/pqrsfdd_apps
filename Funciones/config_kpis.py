import streamlit as st
import pandas as pd
import plotly.express as px
from database import create_connection

# Función para crear la conexión a la base de datos
# (Debes incluir tu lógica para `create_connection`)

# Layout y estilo del dashboard
st.set_page_config(
    page_title="Dashboard PQRSFDD",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Funciones para obtener los datos desde la base de datos
def get_total_requests():
    conn = create_connection()
    query = "SELECT COUNT(*) FROM sucesos"
    df = pd.read_sql(query, conn)
    conn.close()
    return df.iloc[0, 0]

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
def solicitudes_res():
    conn = create_connection()
    query = """
    SELECT tipo_estado.nombre_estado, COUNT(*) AS total
    FROM estado_del_tramite
    JOIN tipo_estado ON estado_del_tramite.id_tipo_estado = tipo_estado.id_tipo_estado
    WHERE tipo_estado.nombre_estado = "Contestada"
    GROUP BY tipo_estado.nombre_estado
    """
   
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Si el DataFrame está vacío, devuelve 0
    if df.empty:
        return 0
    
    # Extraer el total del DataFrame y convertirlo a entero
    total_respuestas = df["total"].iloc[0]
    return int(total_respuestas)

def solicitudes_tram():
    conn = create_connection()
    query = """
    SELECT tipo_estado.nombre_estado, COUNT(*) AS total
    FROM estado_del_tramite
    JOIN tipo_estado ON estado_del_tramite.id_tipo_estado = tipo_estado.id_tipo_estado
    WHERE tipo_estado.nombre_estado = "En Tramite"
    GROUP BY tipo_estado.nombre_estado
    """
   
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Si el DataFrame está vacío, devuelve 0
    if df.empty:
        return 0
    
    # Extraer el total del DataFrame y convertirlo a entero
    total_tramite = df["total"].iloc[0]
    return int(total_tramite)

def solicitudes_rec():
    conn = create_connection()
    query = """
    SELECT tipo_estado.nombre_estado, COUNT(*) AS total
    FROM estado_del_tramite
    JOIN tipo_estado ON estado_del_tramite.id_tipo_estado = tipo_estado.id_tipo_estado
    WHERE tipo_estado.nombre_estado = "Recibida"
    GROUP BY tipo_estado.nombre_estado
    """
   
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Si el DataFrame está vacío, devuelve 0
    if df.empty:
        return 0
    
    # Extraer el total del DataFrame y convertirlo a entero
    total_recibida = df["total"].iloc[0]
    return int(total_recibida)


def solicitudes_ven():
    conn = create_connection()
    query = """
    SELECT tipo_estado.nombre_estado, COUNT(*) AS total
    FROM estado_del_tramite
    JOIN tipo_estado ON estado_del_tramite.id_tipo_estado = tipo_estado.id_tipo_estado
    WHERE tipo_estado.nombre_estado = "Vencida"
    GROUP BY tipo_estado.nombre_estado
    """
   
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Si el DataFrame está vacío, devuelve 0
    if df.empty:
        return 0
    
    # Extraer el total del DataFrame y convertirlo a entero
    total_vencida = df["total"].iloc[0]
    return int(total_vencida)


def tiempo_promedio_respuesta():
    """
    Calcula el tiempo promedio de respuesta en días
    para los trámites con estado 'Contestada' (id_tipo_estado = 3).
    """
    conn = create_connection()
    
    # Consulta SQL para calcular la diferencia entre las fechas y el promedio
    query = """
    SELECT AVG(DATEDIFF(estado_del_tramite.fecha_respuesta, sucesos.fecha_rad)) AS tiempo_promedio
    FROM estado_del_tramite
    JOIN sucesos ON estado_del_tramite.radicado = sucesos.id_rad
    WHERE estado_del_tramite.id_tipo_estado = 3
    """
    
    # Ejecutar la consulta
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Si el resultado está vacío o no hay datos, devuelve 0
    if df.empty or pd.isna(df["tiempo_promedio"].iloc[0]):
        return 0
    
    # Retornar el promedio como entero
    return round(df["tiempo_promedio"].iloc[0], 2)  # Redondear a 2 decimales

# Diseño del dashboard
def kpis_page():
    st.title("Indicadores - PQRSFDD")


    # Primera fila: Métricas
    st.markdown("### Resumen General")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    total_requests = get_total_requests()
    col1.metric("Total Solicitudes", total_requests)
    col2.metric("Recibidas ", solicitudes_rec())
    col3.metric("En Tramite", solicitudes_tram())
    col4.metric("Contetadas", solicitudes_res())
    col5.metric("Vencidas", solicitudes_ven())
    col6.metric("Tiempo Prom. Respuestas", tiempo_promedio_respuesta(), "Días")

    # Segunda fila: Gráficas principales
    st.markdown("### Visualizaciones de Datos")
    col1, col2 = st.columns(2)
 # Solicitudes por tipo
    with col1:
        st.subheader("Solicitudes por Tipo")
        
        # Obtener los datos
        df_requests_by_type = get_requests_by_type()
        
        # Crear la gráfica con rango personalizado en el eje y
        fig1 = px.bar(
            df_requests_by_type,
            x='nombre_sol',
            y='total',
            title="Solicitudes por Tipo",
            color='total',
            color_continuous_scale="Viridis"
        )
        
        # Personalizar el layout para ajustar el eje y
        fig1.update_layout(
            yaxis=dict(
                tickmode='linear',    # Configurar el modo de ticks como lineal
                tick0=0,              # El primer tick será 1
                dtick=1,              # Incrementos de 1 entre ticks
                range=[0, df_requests_by_type["total"].max() + 1]  # Ajustar rango dinámico
            )
        )
        
        # Mostrar la gráfica
        st.plotly_chart(fig1, use_container_width=True)


    # Estado de solicitudes
    with col2:
        st.subheader("Estado de las Solicitudes")
        df_status = get_request_status()
        fig2 = px.pie(
            df_status,
            names='nombre_estado',
            values='total',
            title="Estado de las Solicitudes"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Tercera fila: Más visualizaciones
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Solicitudes por Mes")
        df_requests_by_month = pd.DataFrame({
            "Mes": ["Enero", "Febrero", "Marzo", "Abril"],
            "Solicitudes": [200, 180, 220, 250]
        })
        fig3 = px.line(df_requests_by_month, x="Mes", y="Solicitudes", title="Solicitudes Mensuales")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Tiempos Promedio por Tipo")
        df_response_times = pd.DataFrame({
            "Tipo": ["Consulta", "Queja", "Petición"],
            "Tiempo Promedio": [2.3, 4.5, 3.2]
        })
        fig4 = px.bar(df_response_times, x="Tipo", y="Tiempo Promedio", title="Tiempos de Respuesta")
        st.plotly_chart(fig4, use_container_width=True)

    # Agregar un botón para cerrar sesión
    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'

# Ejecutar la página principal del dashboard
#

# Llamar la función para mostrar la página de KPIs
# if __name__ == "__main__":
  #  kpis_page()
