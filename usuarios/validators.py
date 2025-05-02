# usuarios/validators.py
from django.core.exceptions import ValidationError
import re

class CustomPasswordComplexityValidator:
    def __init__(self):
        # Definir las reglas de complejidad, en este caso, debe contener al menos una letra y un número
        self.regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')

    def validate(self, password, user=None):
        # Validar la contraseña con la expresión regular
        if not self.regex.match(password):
            raise ValidationError('La contraseña debe tener al menos 8 caracteres, incluir letras y números.')
        
    def get_help_text(self):
        return 'La contraseña debe tener al menos 8 caracteres, incluir letras y números.'
