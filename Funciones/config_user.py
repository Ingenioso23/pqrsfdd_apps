import streamlit as st
from database import create_connection
from mysql.connector import Error
import bcrypt


def user_management_page():
    st.title("Gestión de Usuarios")

    # Crear un menú de navegación
    menu = ["Inicio", "Crear Usuario", "Modificar Usuario", "Activar/Desactivar Usuario", "Eliminar Usuario", "Ver Usuarios"]
    choice = st.sidebar.selectbox("Menú", menu)

    if choice == "Inicio":
        st.subheader("Bienvenido a la Gestión de Usuarios")
        st.write("Selecciona una opción del menú para administrar usuarios.")
    elif choice == "Crear Usuario":
        crear_usuario()
    elif choice == "Modificar Usuario":
        modificar_usuario()
    elif choice == "Activar/Desactivar Usuario":
        activar_desactivar_usuario()
    elif choice == "Eliminar Usuario":
        eliminar_usuario()
    elif choice == "Ver Usuarios":
        ver_usuarios()

    # Botón para cerrar sesión
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'


# Función para crear un usuario
def crear_usuario():
    st.subheader("Crear Usuario")
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
    usuarios = get_usuarios()

    if usuarios:
        id_usuario = st.selectbox("Selecciona un Usuario", [f"{usuario[1]} ({usuario[0]})" for usuario in usuarios])
        usuario_seleccionado = next((usuario for usuario in usuarios if f"{usuario[1]} ({usuario[0]})" == id_usuario), None)

        if usuario_seleccionado:
            id_usuario = usuario_seleccionado[0]
            nombre = st.text_input("Nombre Completo", usuario_seleccionado[1])
            correo = st.text_input("Correo Electrónico", usuario_seleccionado[2])
            roles = get_roles()
            rol = st.selectbox("Rol", [rol[1] for rol in roles], index=[rol[0] for rol in roles].index(usuario_seleccionado[3]))

            if st.button("Actualizar Usuario"):
                rol_id = next((r[0] for r in roles if r[1] == rol), None)
                actualizar_usuario(id_usuario, nombre, correo, rol_id)
    else:
        st.info("No hay usuarios registrados para modificar.")


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
            cursor.execute("UPDATE usuarios SET Estado_u = %s WHERE id_usuario = %s", (nuevo_estado, id_usuario))
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
                rol_nombre = get_rol_nombre(usuario[3])
                st.write(f"Documento: {usuario[0]}, Nombre: {usuario[1]}, Correo: {usuario[2]}, Rol: {rol_nombre}, Estado: {'Activo' if usuario[4] == 1 else 'Inactivo'}")
        else:
            st.info("No hay usuarios registrados.")
    except Error as e:
        st.error(f"Error al obtener usuarios: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()


# Función para actualizar un usuario
def actualizar_usuario(id_usuario, nombre, correo, rol):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET nombre = %s, correo = %s, rol_id = %s WHERE id_usuario = %s", (nombre, correo, rol, id_usuario))
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
    cursor = conn.cursor()
    cursor.execute("SELECT id_tipo_doc, nombre_tipo_doc FROM tipo_documento")
    tipos_documento = cursor.fetchall()
    cursor.close()
    conn.close()
    return tipos_documento


def get_roles():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_rol, nombre_rol FROM roles")
    roles = cursor.fetchall()
    cursor.close()
    conn.close()
    return roles


def get_usuarios():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombre, correo, rol_id FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return usuarios


def get_rol_nombre(rol_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_rol FROM roles WHERE id_rol = %s", (rol_id,))
    rol = cursor.fetchone()
    cursor.close()
    conn.close()
    return rol[0] if rol else "N/A"
