import streamlit as st
from database import create_connection
from mysql.connector import Error
import bcrypt
import pandas as pd


def user_management_page():
    st.title("Gestión de Usuarios")

    # Crear un menú de navegación
    menu = ["Inicio", "Crear Usuario", "Modificar Usuario", "Activar/Desactivar Usuario", "Eliminar Usuario", "Ver Usuarios", "Servicios"]
    choice = st.sidebar.selectbox("Menú Usuarios", menu)

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
    elif choice == "Servicios":
        ver_servicios()

    # Botón para cerrar sesión
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'

def ver_servicios():
    st.subheader("Responsables por Área de Servicio")

    # Obtener datos de la base de datos
    try:
        areas = get_areas()  # Lista: [(id_area, area)]
       # st.write("Áreas obtenidas:", areas)

        usuarios = get_usuarios()  # Lista: [(id_usuario, nombre, correo, rol_id)]
    except Exception as e:
        st.error(f"Error al obtener datos: {e}")
        return

    # Validar datos
    if not areas:
        st.warning("No hay áreas disponibles.")
        return

    if not usuarios:
        st.warning("No hay usuarios disponibles.")
        return

    # Mostrar las áreas disponibles
    opciones_areas = [
        f"{area[1]} (ID: {area[0]})" for area in areas
    ]

    area_seleccionada = st.selectbox("Seleccione un Área", opciones_areas)

    # Validar selección del área
    try:
        id_area_seleccionada = int(area_seleccionada.split("ID: ")[1][:-1])
        area_datos = next((area for area in areas if area[0] == id_area_seleccionada), None)
    except (IndexError, ValueError) as e:
        st.error(f"Error procesando el área seleccionada: {e}")
        return

    if not area_datos:
        st.warning("Área no encontrada.")
        return

    # Obtener servicios relacionados al área seleccionada
    servicios = get_servicios_por_area(id_area_seleccionada)  # Lista: [(id_servicio, nombre_serv)]
    if not servicios:
        st.warning("No hay servicios disponibles para esta área.")
        return

    # Seleccionar un servicio específico
    servicio_seleccionado = st.selectbox(
        "Seleccione un Servicio",
        [f"{servicio[1]} (ID: {servicio[0]})" for servicio in servicios]
    )

    try:
        id_servicio_seleccionado = int(servicio_seleccionado.split("ID: ")[1][:-1])
    except (IndexError, ValueError) as e:
        st.error(f"Error procesando el servicio seleccionado: {e}")
        return

    # Obtener el responsable actual del área (basado en id_usuario en la tabla `areas`)
    area_responsable = next(
        (area for area in areas if area[0] == id_area_seleccionada),
        None
    )

    id_responsable_actual = area_responsable[2] if area_responsable else None

    responsable_actual = next(
        (usuario[1] for usuario in usuarios if usuario[0] == id_responsable_actual),
        "Sin responsable"
    )

    st.write(f"Responsable Actual del Área: {responsable_actual}")

    # Seleccionar nuevo responsable
    nuevo_responsable = st.selectbox(
        "Seleccione el Nuevo Responsable",
        [f"{usuario[1]} (ID: {usuario[0]})" for usuario in usuarios]
    )

    try:
        nuevo_responsable_id = int(nuevo_responsable.split("ID: ")[1][:-1])
    except (IndexError, ValueError) as e:
        st.error(f"Error procesando el nuevo responsable seleccionado: {e}")
        return

    # Botón para actualizar
    if st.button("Actualizar Responsable"):
        try:
            actualizar_responsable(id_area_seleccionada, nuevo_responsable_id)
            st.success(
                f"Responsable del área '{area_datos[1]}' actualizado a {nuevo_responsable.split(' (ID: ')[0]}."
            )
        except Exception as e:
            st.error(f"Error al actualizar el responsable: {e}")

def actualizar_responsable(area_id, nuevo_responsable_id):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE areas SET responsable = %s WHERE id_area = %s",
            (nuevo_responsable_id, area_id)
        )
        conn.commit()  # Se debe llamar con paréntesis
        #st.success("Responsable actualizado correctamente.")
    except Error as e:
        st.error(f"Error al actualizar el responsable: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Función para crear un usuario
def crear_usuario():
    st.subheader("Crear Usuario")
    
    # Obtener datos de tipos de documento, roles, áreas y servicios
    tipos_documento = get_tipo_documento()
    roles = get_roles()
    areas = get_areas()
    
    tipo_id = st.selectbox("Tipo de Documento", [tipo[1] for tipo in tipos_documento])
    numero_documento = st.text_input("Número de Documento")
    correo = st.text_input("Correo Electrónico")
    
    if st.button("Verificar Documento/Correo"):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s OR correo = %s", (numero_documento, correo))
        if cursor.fetchone():
            st.error("El número de documento o correo ya existe.")
            return
        cursor.close()
        conn.close()

    nombre = st.text_input("Nombre Completo")
    contraseña = st.text_input("Contraseña", type="password")
    rol = st.selectbox("Rol", [rol[1] for rol in roles])
    
    # Seleccionar área
    area_seleccionada = st.selectbox("Área", [area[1] for area in areas])
    area_id = next((area[0] for area in areas if area[1] == area_seleccionada), None)
    
    # Filtrar servicios disponibles en el área seleccionada
    servicios = get_servicios_por_area(area_id)
    servicio_seleccionado = st.selectbox("Servicio", [servicio[1] for servicio in servicios])
    servicio_id = next((servicio[0] for servicio in servicios if servicio[1] == servicio_seleccionado), None)

    if st.button("Crear Usuario"):
        tipo_doc_id = next((tipo[0] for tipo in tipos_documento if tipo[1] == tipo_id), None)
        rol_id = next((r[0] for r in roles if r[1] == rol), None)

        if tipo_doc_id and numero_documento and nombre and correo and contraseña and rol_id and area_id and servicio_id:
            try:
                hashed_password = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())
                conn = create_connection()
                cursor = conn.cursor()
                
                # Insertar usuario
                cursor.execute(
                    "INSERT INTO usuarios (tipo_id, id_usuario, nombre, correo, contraseña, rol_id, Estado_u) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (tipo_doc_id, numero_documento, nombre, correo, hashed_password, rol_id, 1)
                )
                
                # Obtener el ID del usuario recién creado
                cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (numero_documento,))
                usuario_id = cursor.fetchone()[0]
                
                # Actualizar el servicio con el usuario como responsable
                cursor.execute(
                    "UPDATE areas SET responsable = %s WHERE id_area = %s",
                    (usuario_id, area_id)
                )
                
                conn.commit()
                st.success(f"Usuario '{nombre}' creado exitosamente y asignado al servicio '{servicio_seleccionado}' en el área '{area_seleccionada}'.")
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
        id_usuario = st.selectbox("Selecciona un Usuario", [f"{usuario[1]}" for usuario in usuarios])
        usuario_seleccionado = next((usuario for usuario in usuarios if f"{usuario[1]}" == id_usuario), None)

        if usuario_seleccionado:
            id_usuario = usuario_seleccionado[0]
            nombre = st.text_input("Nombre Completo", usuario_seleccionado[1])
            correo = st.text_input("Correo Electrónico", usuario_seleccionado[2])
            roles = get_roles()
            rol = st.selectbox("Rol", [rol[1] for rol in roles], index=[rol[0] for rol in roles].index(usuario_seleccionado[3]))

            # Nuevo campo para actualizar la contraseña
            nueva_contraseña = st.text_input("Nueva Contraseña (dejar en blanco para no cambiar)", type="password")

            if st.button("Actualizar Usuario"):
                rol_id = next((r[0] for r in roles if r[1] == rol), None)

                # Si se ha ingresado una nueva contraseña, se genera el hash
                if nueva_contraseña:
                    hashed_password = bcrypt.hashpw(nueva_contraseña.encode('utf-8'), bcrypt.gensalt())
                else:
                    hashed_password = None

                actualizar_usuario(id_usuario, nombre, correo, rol_id, hashed_password)
    else:
        st.info("No hay usuarios registrados para modificar.")


# Función para activar o desactivar un usuario
def activar_desactivar_usuario():
    st.subheader("Activar/Desactivar Usuario")
    usuarios = get_usuarios()
    id_usuario = st.selectbox("Selecciona un Usuario", [f"{usuario[1]}" for usuario in usuarios])
    usuario_seleccionado = next((usuario for usuario in usuarios if f"{usuario[1]}" == id_usuario), None)
    
    estado = st.selectbox("Nuevo Estado", ["Activar", "Desactivar"])
    nuevo_estado = 1 if estado == "Activar" else 0

    if st.button("Actualizar Estado"):
        try:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE usuarios SET Estado_u = %s WHERE id_usuario = %s", (nuevo_estado, usuario_seleccionado[0]))
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
        query = """
            SELECT u.id_usuario, u.nombre, u.correo, r.nombre_rol, 
                   CASE WHEN u.Estado_u = 1 THEN 'Activo' ELSE 'Inactivo' END AS estado
            FROM usuarios u
            JOIN roles r ON u.rol_id = r.id_rol
        """
        cursor.execute(query)
        usuarios = cursor.fetchall()
        
        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(usuarios, columns=["Documento", "Nombre", "Correo", "Rol", "Estado"])
        st.dataframe(df)
    except Error as e:
        st.error(f"Error al obtener usuarios: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Función para actualizar un usuario
def actualizar_usuario(id_usuario, nombre, correo, rol, hashed_password=None):
    try:
        conn = create_connection()
        cursor = conn.cursor()

        if hashed_password:
            # Si se ha ingresado una nueva contraseña
            cursor.execute(
                "UPDATE usuarios SET nombre = %s, correo = %s, rol_id = %s, contraseña = %s WHERE id_usuario = %s",
                (nombre, correo, rol, hashed_password, id_usuario)
            )
        else:
            # Si no se ha ingresado una nueva contraseña
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
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_tipo_doc, nombre_tipo_doc FROM tipo_documento")
        tipos_documento = cursor.fetchall()
        return tipos_documento
    except Error as e:
        st.error(f"Error al obtener Tipo Documentos: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_roles():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_rol, nombre_rol FROM roles")
        roles = cursor.fetchall()
        return roles
    except Error as e:
        st.error(f"Error al obtener roles: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_usuarios():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, nombre, correo, rol_id FROM usuarios")
        usuarios = cursor.fetchall()
        return usuarios
    except Error as e:
        st.error(f"Error al obtener usuarios: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_rol_nombre(rol_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_rol FROM roles WHERE id_rol = %s", (rol_id,))
    rol = cursor.fetchone()
    cursor.close()
    conn.close()
    return rol[0] if rol else "N/A"

def get_servicios():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_servicio, nombre_serv FROM servicio_disponibles")
    servicios = cursor.fetchall()
    cursor.close()
    conn.close()
    return servicios

def get_areas():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_area, area, responsable FROM areas")
        areas = cursor.fetchall()
        return areas
    except Error as e:
        st.error(f"Error al obtener áreas: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Función para obtener servicios por área
def get_servicios_por_area(area_id):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_servicio, nombre_serv, id_area FROM servicio_disponibles WHERE id_area = %s", (area_id,))
        servicios = cursor.fetchall()
        return servicios
    except Error as e:
        st.error(f"Error al obtener servicios: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
