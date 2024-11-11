import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = 'smtp.gmail.com'  # Para Gmail
SMTP_PORT = 587                # Puerto para TLS
SMTP_USER = 'desarrolladorgas@gmail.com'  # Tu correo
SMTP_PASSWORD = 'ipfo bzdz lwhq xsvtn'  # Tu contraseña

def enviar_correo(destinatario, asunto, mensaje):
    # Crear el mensaje de correo
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(mensaje, 'plain'))

    # Enviar el correo
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # Inicia la conexión segura
            server.login(SMTP_USER, SMTP_PASSWORD)  # Inicia sesión
            server.sendmail(SMTP_USER, destinatario, msg.as_string())  # Envía el correo
        return True
    except Exception as e:
        print(f"Error al enviar correo a {destinatario}: {e}")
        return False

enviar_correo('nyra28@gmail.com', 'Asunto de prueba', 'Este es un mensaje de prueba.')
