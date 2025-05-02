
from rest_framework import serializers
import re
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .models import Usuario  # Asumiendo que tu modelo es Usuario
from .utils import send_activation_email  # Importa la función de utils

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'email', 'telefono', 'tipo_usuario', 'password']

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("La contraseña debe contener al menos una letra mayúscula.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("La contraseña debe contener al menos un número.")
        if not re.search(r'[\W_]', value):
            raise serializers.ValidationError("La contraseña debe contener al menos un carácter especial.")
        return value

    def create(self, validated_data):
        usuario = Usuario.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],  # Se asegura de usar set_password correctamente
            nombre=validated_data['nombre'],
            apellido=validated_data['apellido'],
            telefono=validated_data['telefono'],
            tipo_usuario=validated_data['tipo_usuario'],
        )
        usuario.save()

        # Generar token de activación
        token = default_token_generator.make_token(usuario)

        # Llamar a la función send_activation_email importada de utils.py
        send_activation_email(usuario)

        return usuario



# usuarios/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        # Autenticación del usuario
        user = authenticate(request=self.context.get('request'), username=email, password=password)
        
        if user is None:
            raise serializers.ValidationError("Credenciales incorrectas.")
        
        # Devolver el usuario autenticado
        return {'user': user}
















from django.contrib.auth.tokens import default_token_generator
from usuarios.models import Usuario
from rest_framework import serializers

from rest_framework import serializers
from usuarios.models import Usuario
from django.contrib.auth.tokens import default_token_generator
from .utils import send_password_reset_email

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Validar si el usuario existe utilizando el modelo personalizado
        if not Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("No se encontró un usuario con ese correo electrónico.")
        return value

    def save(self):
        # Obtener el usuario con el email validado
        email = self.validated_data['email']
        user = Usuario.objects.get(email=email)
        
        # Generar el token de restablecimiento
        token = default_token_generator.make_token(user)
        
        # Enviar el correo con el enlace de restablecimiento
        send_password_reset_email(user, token)






from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from usuarios.models import Usuario

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        # Validar que la contraseña cumpla con las políticas de seguridad de Django
        try:
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def save(self, user):
        # Guardar la nueva contraseña
        user.set_password(self.validated_data['password'])
        user.save()
        return user
