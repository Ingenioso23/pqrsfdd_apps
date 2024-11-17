import streamlit as st
from database import create_connection
from mysql.connector import Error

def user_management_page():
    st.subheader("Gestión de Usuarios")
    st.write("Administra los usuarios del sistema: Crear, Modificar, Activar/Desactivar y Eliminar.")

    # Opciones para seleccionar la acción
    action = st.selectbox("Selecciona una acción", ["Crear Usuario", "Modificar Usuario", "Activar/Desactivar Usuario", "Eliminar Usuario", "Ver Todos los Usuarios"])

    if action == "Crear Usuario":
        crear_usuario()
    elif action == "Modificar Usuario":
        modificar_usuario()
    elif action == "Activar/Desactivar Usuario":
        activar_desactivar_usuario()
    elif action == "Eliminar Usuario":
        eliminar_usuario()
    elif action == "Ver Todos los Usuarios":
        ver_usuarios()

    # Botón para cerrar sesión
    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'

# Función para crear un usuario
def crear_usuario():
    st.subheader("Crear Usuario")
    
    # Cargar datos necesarios para los selectbox
    tipos_documento = get_tipo_documento()
    roles = get_roles()

    tipo_id = st.selectbox("Tipo de Documento", [tipo[1] for tipo in tipos_documento])
    numero_documento = st.text_input("Número de Documento")
    nombre = st.text_input("Nombre Completo")
    correo = st.text_input("Correo Electrónico")
    contraseña = st.text_input("Contraseña", type="password")
    rol = st.selectbox("Rol", [rol[1] for rol in roles])

    if st.button("Crear Usuario"):
        tipo_doc_id = next((tipo[0] for tipo in tipos_documento if tipo[1] == tipo_id), None)
        rol_id = next((r[0] for r in roles if r[1] == rol), None)
        
        if tipo_doc_id and numero_documento and nombre and correo and contraseña and rol_id:
            try:
                hashed_password = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (tipo_id, id_usuario, nombre, correo, contraseña, rol_id, Estado_u) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (tipo_doc_id, numero_documento, nombre, correo, hashed_password, rol_id, 1)
                )
                conn.commit()
                st.success("Usuario creado exitosamente.")
            except Error as e:
                st.error(f"Error al crear el usuario: {e}")
            finally:
                if conn:
                    cursor.close()
                    conn.close()
        else:
            st.error("Por favor, completa todos los campos.")

# Función para modificar un usuario
def modificar_usuario():
    st.subheader("Modificar Usuario")
    
    id_usuario = st.text_input("Número de Documento del Usuario a Modificar")
    
    if st.button("Buscar Usuario"):
        usuario = buscar_usuario(id_usuario)
        if usuario:
            nombre = st.text_input("Nombre Completo", usuario['nombre'])
            correo = st.text_input("Correo Electrónico", usuario['correo'])
            rol = st.text_input("ID de Rol", usuario['rol_id'])
            if st.button("Actualizar Usuario"):
                actualizar_usuario(id_usuario, nombre, correo, rol)
        else:
            st.error("Usuario no encontrado.")

# Función para activar o desactivar un usuario
def activar_desactivar_usuario():
    st.subheader("Activar/Desactivar Usuario")
    
    id_usuario = st.text_input("Número de Documento del Usuario")
    estado = st.selectbox("Nuevo Estado", ["Activar", "Desactivar"])
    nuevo_estado = 1 if estado == "Activar" else 0

    if st.button("Actualizar Estado"):
        try:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET Estado_u = %s WHERE id_usuario = %s",
                (nuevo_estado, id_usuario)
            )
            conn.commit()
            st.success("Estado del usuario actualizado.")
        except Error as e:
            st.error(f"Error al actualizar el estado: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

# Función para eliminar un usuario
def eliminar_usuario():
    st.subheader("Eliminar Usuario")
    
    id_usuario = st.text_input("Número de Documento del Usuario a Eliminar")

    if st.button("Eliminar Usuario"):
        try:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            st.success("Usuario eliminado exitosamente.")
        except Error as e:
            st.error(f"Error al eliminar el usuario: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

# Función para ver todos los usuarios
def ver_usuarios():
    st.subheader("Lista de Usuarios")

    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, nombre, correo, rol_id, Estado_u FROM usuarios")
        usuarios = cursor.fetchall()
        if usuarios:
            for usuario in usuarios:
                st.write(f"Documento: {usuario[0]}, Nombre: {usuario[1]}, Correo: {usuario[2]}, Rol ID: {usuario[3]}, Estado: {'Activo' if usuario[4] == 1 else 'Inactivo'}")
        else:
            st.info("No hay usuarios registrados.")
    except Error as e:
        st.error(f"Error al obtener usuarios: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

# Función para buscar un usuario específico
def buscar_usuario(id_usuario):
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario = cursor.fetchone()
        return usuario
    except Error as e:
        st.error(f"Error al buscar el usuario: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()
    return None

# Función para actualizar un usuario
def actualizar_usuario(id_usuario, nombre, correo, rol):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET nombre = %s, correo = %s, rol_id = %s WHERE id_usuario = %s",
            (nombre, correo, rol, id_usuario)
        )
        conn.commit()
        st.success("Usuario actualizado exitosamente.")
    except Error as e:
        st.error(f"Error al actualizar el usuario: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

# Funciones auxiliares
def get_tipo_documento():
    conn = create_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT id_tipo_doc, nombre_tipo_doc FROM tipo_documento")
    tipos_documento = cursor.fetchall()
    cursor.close()
    conn.close()
    return tipos_documento

def get_roles():
    conn = create_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT id_rol, nombre_rol FROM roles")
    roles = cursor.fetchall()
    cursor.close()
    conn.close()
    return roles
