from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.encoding import force_bytes

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model

Usuario = get_user_model()

def send_activation_email(user):
    # Genera el token
    token = default_token_generator.make_token(user)
    
    # Codifica el id del usuario
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # URL de activación
    activation_link = f"http://localhost:8000/api/activar-cuenta/{uid}/{token}/"

    # Asunto del correo
    subject = "🔹 Activa Tu Cuenta En ParqueApp"

    # **Versión en HTML**
    html_content = render_to_string('correo_activacion.html', {
        'user': user,
        'activation_link': activation_link,
    })

    # **Versión en texto plano (por si el cliente no soporta HTML)**
    text_content = f"""Hola, {user.nombre} 👋

Bienvenido a ParqueApp, donde puedes reservar tu espacio de estacionamiento fácilmente.

Activa tu cuenta haciendo clic en el siguiente enlace:
{activation_link}

Si no solicitaste esta cuenta, puedes ignorar este mensaje.

Saludos, 
El equipo de ParqueApp 🚗
"""

    # Enviar el correo correctamente
    email = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [user.email])
    email.attach_alternative(html_content, "text/html")
    email.send()


# usuarios/utils.py
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode

def generar_enlace_activacion(usuario):
    # Codificar el ID del usuario en base64
    uidb64 = urlsafe_base64_encode(str(usuario.pk).encode())
    # Generar el token para la activación
    token = default_token_generator.make_token(usuario)
    # Retornar el enlace completo
    return f"http://localhost:8000/api/activar-cuenta/{uidb64}/{token}/"








from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.urls import reverse

def send_password_reset_email(user, token):
    # Convertir el UUID a string y luego a bytes
    user_id_str = str(user.pk)  # Convierte el UUID a string
    user_id_bytes = user_id_str.encode('utf-8')  # Luego lo conviertes a bytes

    # Crear el enlace para el restablecimiento de contraseña
    
    uid = urlsafe_base64_encode(str(user.pk).encode())
    reset_url = f"{settings.BACKEND_URL}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
    
    subject = "Restablece tu contraseña"
    message = render_to_string('password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
