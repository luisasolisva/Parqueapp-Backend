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

    # Determinar la plantilla según el tipo de usuario
    if user.tipo_usuario == "Cliente":
        subject = "🔹 Activa Tu Cuenta De Cliente En ParqueApp"
        template = "correo_activacion_cliente.html"
    
    elif user.tipo_usuario == "Operario":
        subject = "🔹 Tu Cuenta De Operario Está Lista 🛠️"
        template = "correo_activacion_operario.html"
    
    else:
        subject = "🔹 Bienvenido a ParqueApp 👋"
        template = "correo_activacion_usuario.html"

    # Generar contenido en HTML
    html_content = render_to_string(template, {
        'user': user,
        'activation_link': activation_link,
    })

    # Enviar el correo correctamente
    email = EmailMultiAlternatives(subject, html_content, settings.EMAIL_HOST_USER, [user.email])
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
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.conf import settings

def send_password_reset_email(user, code):
    # Convertir el ID del usuario
    uid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

    # Crear el enlace para verificar el código
    verify_url = f"{settings.BACKEND_URL}{reverse('verify_reset_code')}"


    subject = "Restablece tu contraseña"

    # Aquí generas el contenido HTML con el botón y los datos del usuario
    html_content = render_to_string('password_reset_email_code.html', {
        'user': user,
        'code': code,
        'verify_url': verify_url,
    })

    # Crear el correo con HTML
    msg = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
