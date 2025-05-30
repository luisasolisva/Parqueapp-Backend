EXTENSIONES_PERMITIDAS = ["jpg", "jpeg", "png"]
TAMANIO_MAXIMO_MB = 5  # Limite de tamaño en MB

def validar_imagen(imagen):
    extension = imagen.name.split(".")[-1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        return "Formato no permitido. Solo JPG, JPEG y PNG."
    
    if imagen.size > TAMANIO_MAXIMO_MB * 1024 * 1024:
        return f"Imagen demasiado grande. Máximo {TAMANIO_MAXIMO_MB}MB."

    return None
