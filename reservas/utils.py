from pyzbar.pyzbar import decode
from PIL import Image

def extraer_codigo_qr(imagen_path):
    """Convierte la imagen del QR en texto."""
    imagen = Image.open(imagen_path)
    codigos = decode(imagen)

    if codigos:
        return codigos[0].data.decode("utf-8")  # ✅ Devuelve el texto del QR
    return None  # ✅ Si no encuentra código, devuelve `None`
