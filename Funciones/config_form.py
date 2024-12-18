import streamlit as st
from database import create_connection
from mysql.connector import Error
import pandas as pd

def form_configuration_page():
    st.title("Gestión de Tablas")

    # Crear un menú de navegación para seleccionar la tabla
    tablas = ["Inicio", "Areas", "Ciudad", "Departamento", "IPS", "EPS", 
              "Grupo Poblacional", "Tipo Documento", "Tipo Estado", "Tipo Solicitud", "Roles", "Régimen"]
    tabla_seleccionada = st.sidebar.selectbox("Selecciona una Tabla", tablas)

    if tabla_seleccionada == "Inicio":
        st.subheader("Bienvenido a la Gestión de Tablas")
        st.write("Selecciona una tabla del menú para gestionar sus registros.")
    else:
        menu_acciones = ["Agregar Registro", "Modificar Registro", "Eliminar Registro", "Ver Registros"]
        accion = st.sidebar.selectbox(f"Acción para {tabla_seleccionada}", menu_acciones)

        if accion == "Agregar Registro":
            agregar_registro(tabla_seleccionada)
        elif accion == "Modificar Registro":
            modificar_registro(tabla_seleccionada)
        elif accion == "Eliminar Registro":
            eliminar_registro(tabla_seleccionada)
        elif accion == "Ver Registros":
            ver_registros(tabla_seleccionada)

    # Botón para cerrar sesión
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'

# Función para agregar registros
def agregar_registro(tabla):
    st.subheader(f"Agregar Registro en {tabla}")
    campos, alias = obtener_campos_tabla(tabla)

    inputs = {}
    for campo, alias_nombre in zip(campos, alias):
        inputs[campo] = st.text_input(f"{alias_nombre}")

    if st.button("Guardar"):
        if all(inputs.values()):
            try:
                conn = create_connection()
                cursor = conn.cursor()
                query = f"INSERT INTO {tabla.lower()} ({', '.join(campos)}) VALUES ({', '.join(['%s'] * len(campos))})"
                cursor.execute(query, tuple(inputs.values()))
                conn.commit()
                st.success(f"Registro agregado a la tabla {tabla} exitosamente.")
            except Error as e:
                st.error(f"Error al agregar el registro: {e}")
            finally:
                if conn:
                    cursor.close()
                    conn.close()
        else:
            st.error("Por favor, completa todos los campos.")

# Función para modificar registros
def modificar_registro(tabla):
    st.subheader(f"Modificar Registro en {tabla}")
    campos, _ = obtener_campos_tabla(tabla)
    id_campo = campos[0]

    id_valor = st.text_input(f"Ingrese {id_campo} del registro a modificar")
    if id_valor:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {tabla.lower()} WHERE {id_campo} = %s", (id_valor,))
        registro = cursor.fetchone()
        if registro:
            inputs = {campo: st.text_input(f"{campo}", value=valor) for campo, valor in zip(campos, registro)}
            if st.button("Actualizar"):
                try:
                    query = f"UPDATE {tabla.lower()} SET {', '.join([f'{campo} = %s' for campo in campos[1:]])} WHERE {id_campo} = %s"
                    cursor.execute(query, tuple(inputs.values())[1:] + (id_valor,))
                    conn.commit()
                    st.success(f"Registro en {tabla} actualizado exitosamente.")
                except Error as e:
                    st.error(f"Error al actualizar el registro: {e}")
                finally:
                    if conn:
                        cursor.close()
                        conn.close()
        else:
            st.error("No se encontró el registro con ese ID.")

# Función para eliminar registros
def eliminar_registro(tabla):
    st.subheader(f"Eliminar Registro en {tabla}")
    id_campo = obtener_campos_tabla(tabla)[0][0]

    id_valor = st.text_input(f"Ingrese {id_campo} del registro a eliminar")
    if st.button("Eliminar"):
        try:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {tabla.lower()} WHERE {id_campo} = %s", (id_valor,))
            conn.commit()
            st.success(f"Registro eliminado de la tabla {tabla}.")
        except Error as e:
            st.error(f"Error al eliminar el registro: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

# Función para ver registros
def ver_registros(tabla):
    st.subheader(f"Registros en {tabla}")
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {tabla.lower()}")
        registros = cursor.fetchall()
        columnas = [desc[0] for desc in cursor.description]
        if registros:
            df = pd.DataFrame(registros, columns=columnas)
            st.dataframe(df)
        else:
            st.info(f"No hay registros en la tabla {tabla}.")
    except Error as e:
        st.error(f"Error al obtener los registros: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

# Función para obtener los campos de una tabla y sus alias
def obtener_campos_tabla(tabla):
    """
    Obtiene los campos de la tabla para dinámicamente generar formularios.
    Devuelve los nombres de los campos y sus alias correspondientes.
    """
    campos = {
        "Areas": [("id_area", "ID Área"), ("nombre_area", "Nombre del Área")],
        "Ciudad": [("id_ciudad", "ID Ciudad"), ("nombre_ciu", "Nombre de la Ciudad"), ("id_departamento", "ID Departamento")],
        "Departamento": [("id_departamento", "Código DANE"), ("nombre_dep", "Nombre del Departamento")],
        "IPS": [("id_ips", "Código IPS"), ("nombre_ips", "Nombre de la IPS"), ("id_departamento", "Departamento"), ("id_ciudad", "Ciudad"), ("direccion", "Dirección")],
        "EPS": [("id_eps", "ID EPS"), ("nombre_eps", "Nombre de la EPS")],
        "Grupo Poblacional": [("id_grupo", "ID Grupo Poblacional"), ("nombre_pob", "Nombre del Grupo Poblacional")],
        "Tipo Documento": [("id_tipo_doc", "ID Tipo Documento"), ("nombre_tipo_doc", "Nombre del Tipo de Documento")],
        "Tipo Estado": [("id_tipo_estado", "ID Tipo de Estado"), ("nombre_estado", "Nombre del Estado")],
        "Tipo Solicitud": [("id_solicitud", "ID Tipo Solicitud"), ("nombre_sol", "Nombre de la Solicitud")],
        "Roles": [("id_rol", "ID Rol"), ("nombre_rol", "Nombre del Rol")],
        "Régimen": [("id_regimen", "ID Régimen"), ("nombre_reg", "Nombre del Régimen")],
    }
    
    # Obtener los campos y sus alias para la tabla solicitada
    tabla_campos = campos.get(tabla, [])

    # Desempacar los campos y sus alias
    nombres_campos = [campo[0] for campo in tabla_campos]
    alias_campos = [campo[1] for campo in tabla_campos]

    # Retornar los campos y sus alias
    return nombres_campos, alias_campos
