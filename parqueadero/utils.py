EXTENSIONES_PERMITIDAS = ["jpg", "jpeg", "png"]
TAMANIO_MAXIMO_MB = 5  # Limite de tamaño en MB

def validar_imagen(imagen):
    extension = imagen.name.split(".")[-1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        return "Formato no permitido. Solo JPG, JPEG y PNG."
    
    if imagen.size > TAMANIO_MAXIMO_MB * 1024 * 1024:
        return f"Imagen demasiado grande. Máximo {TAMANIO_MAXIMO_MB}MB."

    return None



import qrcode
from io import BytesIO
import base64

def generar_qr(texto):
    qr = qrcode.make(texto)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{qr_base64}"



from django.core.mail import send_mail

def enviar_correo(destinatario, asunto, mensaje):
    send_mail(
        asunto,
        mensaje,
        'parqueappreservas@gmail.com',
        [destinatario],
        fail_silently=False,
    )
