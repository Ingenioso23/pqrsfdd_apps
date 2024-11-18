import streamlit as st
import mysql.connector
from database import create_connection

# Función para obtener los registros de una tabla desde la base de datos
def get_records_from_table(table_name):
    conn = create_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name}")
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return records

# Función para insertar un nuevo registro en una tabla
def insert_record_into_table(table_name, columns, values):
    conn = create_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(values))})"
    try:
        cursor.execute(query, tuple(values))
        conn.commit()
        st.success(f"Registro insertado en {table_name} exitosamente.")
    except Exception as e:
        st.error(f"Error al insertar el registro: {e}")
    finally:
        cursor.close()
        conn.close()

# Función para actualizar un registro de una tabla
def update_record_in_table(table_name, set_columns, set_values, where_column, where_value):
    conn = create_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    set_clause = ", ".join([f"{col} = %s" for col in set_columns])
    query = f"UPDATE {table_name} SET {set_clause} WHERE {where_column} = %s"
    try:
        cursor.execute(query, tuple(set_values + [where_value]))
        conn.commit()
        st.success(f"Registro actualizado en {table_name} exitosamente.")
    except Exception as e:
        st.error(f"Error al actualizar el registro: {e}")
    finally:
        cursor.close()
        conn.close()

# Función para eliminar un registro de una tabla
def delete_record_from_table(table_name, where_column, where_value):
    conn = create_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    query = f"DELETE FROM {table_name} WHERE {where_column} = %s"
    try:
        cursor.execute(query, (where_value,))
        conn.commit()
        st.success(f"Registro eliminado de {table_name} exitosamente.")
    except Exception as e:
        st.error(f"Error al eliminar el registro: {e}")
    finally:
        cursor.close()
        conn.close()

# Página de configuración de formularios
def form_configuration_page():
    st.subheader("Configuración de Formularios")
    st.write("Aquí puedes configurar los formularios de solicitud y respuesta a PQRSFDD.")

    # Menú horizontal para seleccionar tabla
    table_option = st.radio("Selecciona una tabla", [
        "tipo_documento", "grupo_poblacional", "eps", "regimen", "tipo_solicitud", 
        "responsable_servicio", "servicio_disponibles", "departamento", "ciudad", "tipo_estado"
    ])
    
    # Menú de operaciones (Crear, Editar, Borrar)
    operation = st.radio("Selecciona una operación", ["Crear", "Editar", "Borrar"])

    # Dependiendo de la operación, mostrar los formularios correspondientes
    if operation == "Crear":
        show_create_form(table_option)
    elif operation == "Editar":
        show_edit_form(table_option)
    elif operation == "Borrar":
        show_delete_form(table_option)

# Función para mostrar el formulario de creación
def show_create_form(table_name):
    st.write(f"Formulario para crear un nuevo registro en la tabla {table_name}")
    columns = get_columns_for_table(table_name)
    values = []
    
    for column in columns:
        value = st.text_input(f"Ingrese {column}")
        values.append(value)
    
    if st.button(f"Crear registro en {table_name}"):
        insert_record_into_table(table_name, columns, values)

# Función para mostrar el formulario de edición
def show_edit_form(table_name):
    st.write(f"Formulario para editar un registro de la tabla {table_name}")
    
    # Obtener los registros existentes para la tabla seleccionada
    records = get_records_from_table(table_name)
    record_options = [f"{record['id']} - {record['nombre']}" for record in records]
    
    record_to_edit = st.selectbox("Selecciona el registro a editar", record_options)
    
    # Obtener las columnas de la tabla
    columns = get_columns_for_table(table_name)
    record_id = record_to_edit.split(" - ")[0]
    
    # Mostrar campos para editar
    updated_values = []
    for column in columns:
        new_value = st.text_input(f"Nuevo valor para {column}")
        updated_values.append(new_value)
    
    if st.button(f"Actualizar registro en {table_name}"):
        update_record_in_table(table_name, columns, updated_values, "id", record_id)

# Función para mostrar el formulario de eliminación
def show_delete_form(table_name):
    st.write(f"Formulario para eliminar un registro de la tabla {table_name}")
    
    # Obtener los registros existentes para la tabla seleccionada
    records = get_records_from_table(table_name)
    record_options = [f"{record['id']} - {record['nombre']}" for record in records]
    
    record_to_delete = st.selectbox("Selecciona el registro a eliminar", record_options)
    record_id = record_to_delete.split(" - ")[0]
    
    if st.button(f"Eliminar registro de {table_name}"):
        delete_record_from_table(table_name, "id", record_id)

# Función para obtener las columnas de una tabla
def get_columns_for_table(table_name):
    # Esta función puede ser personalizada dependiendo de las tablas y columnas que tengas
    table_columns = {
        "tipo_documento": ["id_tipo_doc", "nombre_tipo_doc"],
        "grupo_poblacional": ["id_grupo", "nombre_pob"],
        "eps": ["id_eps", "nombre_eps"],
        "regimen": ["id_regimen", "nombre_reg"],
        "tipo_solicitud": ["id_solicitud", "nombre_sol"],
        "responsable_servicio": ["id_responsable", "nombre_res", "area"],
        "servicio_disponibles": ["id_servicio", "nombre_serv", "responsable"],
        "departamento": ["id_departamento", "nombre_dep"],
        "ciudad": ["id_ciudad", "nombre_ciu"],
        "tipo_estado": ["id_tipo_estado", "nombre_estado"]
    }
    
    return table_columns.get(table_name, [])

