import streamlit as st
from database import create_connection
from mysql.connector import Error
import pandas as pd

def form_configuration_page():
    st.title("Gestión de Tablas")

    # Crear un menú de navegación para seleccionar la tabla
    tablas = ["Inicio", "areas", "Ciudad", "Departamento", "IPS", "EPS", 
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
    campos, valores = obtener_campos_tabla(tabla)

    inputs = {}
    for campo in campos:
        inputs[campo] = st.text_input(f"{campo}")

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

# Función para obtener los campos de una tabla
def obtener_campos_tabla(tabla):
    """
    Obtiene los campos de la tabla para dinámicamente generar formularios.
    """
    campos = {
        "areas": ["id_area", "nombre_area"],
        "Ciudad": ["id_ciudad", "nombre_ciu", "id_departamento"],
        "Departamento": ["id_departamento", "nombre_dep"],
        "IPS": ["id_ips", "nombre_ips", "id_departamento", "id_ciudad", "direccion"],
        "EPS": ["id_eps", "nombre_eps"],
        "Grupo Poblacional": ["id_grupo", "nombre_pob"],
        "Tipo Documento": ["id_tipo_doc", "nombre_tipo_doc"],
        "Tipo Estado": ["id_tipo_estado", "nombre_estado"],
        "Tipo Solicitud": ["id_solicitud", "nombre_sol"],
        "Roles": ["id_rol", "nombre_rol"],
        "Régimen": ["id_regimen", "nombre_reg"],
    }
    return campos.get(tabla, []), ["%s"] * len(campos.get(tabla, []))

