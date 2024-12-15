import streamlit as st
import pandas as pd
import plotly.express as px
from database import create_connection

# Función para crear la conexión a la base de datos
# (Debes incluir tu lógica para `create_connection`)
COLORS = ["#b9d45b", "#e0ecac", "#bba8c5", "#623e77", "#908895"]
# Layout y estilo del dashboard
st.set_page_config(
    page_title="Dashboard PQRSFDD",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Funciones para obtener los datos desde la base de datos
def get_response_times_by_service_and_responsible():
    conn = create_connection()
    query = """
        SELECT 
            tipo_solicitud.nombre_sol AS servicio,
            usuarios.nombre AS responsable,
            AVG(DATEDIFF(estado_del_tramite.fecha_respuesta, sucesos.fecha_rad)) AS tiempo_promedio
        FROM sucesos
        JOIN estado_del_tramite ON sucesos.id_rad = estado_del_tramite.radicado
        JOIN tipo_solicitud ON estado_del_tramite.id_solicitud = tipo_solicitud.id_solicitud
        JOIN usuarios ON sucesos.id_responsable = usuarios.id_usuario
        WHERE estado_del_tramite.id_tipo_estado = 3
        GROUP BY tipo_solicitud.nombre_sol, usuarios.nombre
        ORDER BY servicio, responsable;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def get_requests_by_service():
    conn = create_connection()
    query = """
    SELECT servicio_disponibles.nombre_serv, COUNT(*) AS total
    FROM sucesos
    JOIN servicio_disponibles ON sucesos.id_servicio = servicio_disponibles.id_servicio
    GROUP BY servicio_disponibles.nombre_serv
    ORDER BY total DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

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

def get_requests_by_month_and_type():
    conn = create_connection()  # Conexión a tu base de datos
    query = """
        SELECT 
            MONTH(sucesos.fecha_rad) AS mes,
            tipo_solicitud.nombre_sol AS tipo_solicitud,
            COUNT(*) AS total_solicitudes
        FROM sucesos
        JOIN estado_del_tramite ON sucesos.id_rad = estado_del_tramite.radicado
        JOIN tipo_solicitud ON estado_del_tramite.id_solicitud = tipo_solicitud.id_solicitud
        GROUP BY MONTH(sucesos.fecha_rad), tipo_solicitud.nombre_sol
        ORDER BY MONTH(sucesos.fecha_rad), tipo_solicitud.nombre_sol;

    """
    df = pd.read_sql(query, conn)
    conn.close()

    # Mapear números de mes a nombres de mes
    meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    df["Mes"] = df["mes"].map(meses)  # Reemplaza el número de mes por su nombre
    return df[["Mes", "tipo_solicitud", "total_solicitudes"]]  # Devolver columnas necesarias


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

def get_response_times_by_type():
    conn = create_connection()  # Conexión a la base de datos
    query = """
        SELECT 
            tipo_solicitud.nombre_sol AS tipo_solicitud,
            AVG(DATEDIFF(estado_del_tramite.fecha_respuesta, sucesos.fecha_rad)) AS tiempo_promedio
        FROM sucesos
        JOIN estado_del_tramite ON sucesos.id_rad = estado_del_tramite.radicado
        JOIN tipo_solicitud ON estado_del_tramite.id_solicitud = tipo_solicitud.id_solicitud
        WHERE estado_del_tramite.id_tipo_estado = 3  -- Solo solicitudes contestadas
        GROUP BY tipo_solicitud.nombre_sol
        ORDER BY tipo_solicitud.nombre_sol;
    """
    df = pd.read_sql(query, conn)
    conn.close()

    return df  # DataFrame con columnas: tipo_solicitud, tiempo_promedio


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
            labels={"total": "Solicitudes", "nombre_sol": "Tipo de Solicitud"},
            color='nombre_sol',
            color_discrete_sequence=COLORS
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
            color_discrete_sequence=COLORS
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Tercera fila: Más visualizaciones
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Solicitudes por Mes y Tipo")

        # Obtener datos de la base de datos
        df_requests_by_month_and_type = get_requests_by_month_and_type()

        # Crear la gráfica usando los datos de la base de datos
        fig3 = px.bar(
            df_requests_by_month_and_type,
            x="Mes",
            y="total_solicitudes",
            color="tipo_solicitud",  # Agrupación por tipo de solicitud
            labels={"total_solicitudes": "Solicitudes", "tipo_solicitud": "Tipo de Solicitud"},
            color_discrete_sequence=COLORS,
            barmode="stack"  # Barras apiladas
        )

        # Configuración del eje Y
        fig3.update_layout(
            yaxis=dict(
                tickmode='linear',    # Configurar el modo de ticks como lineal
                tick0=0,              # El primer tick será 0
                dtick=1,              # Incrementos de 1 entre ticks
            )
        )

        # Mostrar la gráfica en Streamlit
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Tiempos Promedio por Tipo")

        # Obtener datos de la base de datos
        df_response_times = get_response_times_by_type()

        # Crear la gráfica usando los datos de la base de datos
        fig4 = px.bar(
            df_response_times,
            x="tipo_solicitud",  # Eje X: Tipo de Solicitud
            y="tiempo_promedio",  # Eje Y: Tiempo Promedio
            labels={"tipo_solicitud": "Tipo de Solicitud", "tiempo_promedio": "Tiempo Promedio (días)"},
            color="tipo_solicitud",  # Colores basados en el valor del tiempo promedio
            color_discrete_sequence=COLORS
        )

        # Configurar el eje Y
        fig4.update_layout(
            yaxis=dict(
                tickmode='linear',    # Modo de ticks lineal
                tick0=0,              # Comienza desde 0
                dtick=1               # Incrementos de 1
            )
        )

        # Mostrar la gráfica en Streamlit
        st.plotly_chart(fig4, use_container_width=True)
    col5, col6 = st.columns(2)
    # Solicitudes por Servicio
    with col5:
        st.subheader("Solicitudes por Servicio")
        
        # Obtener los datos
        df_requests_by_service = get_requests_by_service()
        
        # Crear la gráfica
        fig5 = px.bar(
            df_requests_by_service,
            x='nombre_serv',
            y='total',
            color='nombre_serv',
            color_discrete_sequence=COLORS
        )
        
        # Ajustar layout
        fig5.update_layout(
            xaxis_title="Servicio",
            yaxis_title="Cantidad de Solicitudes",
            yaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1,
                range=[0, df_requests_by_service["total"].max() + 1]
            ),
            showlegend=False
        )
        
        # Mostrar la gráfica
        st.plotly_chart(fig5, use_container_width=True)
        
            # Cuarta fila: Tiempo de respuesta por servicio y responsable
    
    with col6:
        st.subheader("Tiempo de Respuesta por Responsable")

        # Obtener datos de la base de datos
        df_response_times = get_response_times_by_service_and_responsible()

        # Crear la gráfica usando los datos
        fig6 = px.bar(
            df_response_times,
            x="servicio",
            y="tiempo_promedio",
            color="responsable",
            barmode="group",  # Agrupar barras por responsable
            labels={"tiempo_promedio": "Días"},  # Etiquetas del eje y
            color_discrete_sequence=COLORS
        )
        
        # Personalizar el layout para mayor claridad
        fig6.update_layout(
            xaxis_title="Tipo Solicitud",
            yaxis_title="Tiempo Promedio (Días)",
            legend_title="Responsable",
            xaxis_tickangle=-45  # Girar etiquetas del eje x
        )
        
        # Mostrar la gráfica
        st.plotly_chart(fig6, use_container_width=True)




    # Agregar un botón para cerrar sesión
    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'
