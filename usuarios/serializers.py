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
        """ Verifica que la contraseña cumpla con los requisitos de seguridad. """
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("La contraseña debe incluir al menos una letra mayúscula.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("La contraseña debe incluir al menos un número.")
        if not re.search(r'[\W_]', value):
            raise serializers.ValidationError("La contraseña debe incluir al menos un carácter especial (@, #, !, etc.).")
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



from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

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
        
        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Devolver usuario autenticado y tokens
        return {
            'user': user,
            'refresh': str(refresh),
            'access': access_token,
        }

class ClienteStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['is_active']
        read_only_fields = ['is_active']

class ClienteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'telefono']
        extra_kwargs = {
            'nombre': {'required': False},
            'apellido': {'required': False},
            'telefono': {'required': False}
        }

    def validate(self, data):
        # Validar que al menos un campo sea proporcionado
        if not any(data.values()):
            raise serializers.ValidationError("Debe proporcionar al menos un campo para actualizar")
        return data



from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from usuarios.models import Usuario
from usuarios.utils import send_password_reset_email
import random

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("No se encontró un usuario con ese correo electrónico.")
        return value

    def save(self):
        email = self.validated_data['email']
        user = Usuario.objects.get(email=email)

        code = str(random.randint(1000, 9999))
        user.codigo_restauracion = code
        user.codigo_creado = timezone.now()
        user.codigo_validado = False
        user.save()

        send_password_reset_email(user, code)


class PasswordResetCodeConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4)

    def validate(self, data):
        try:
            user = Usuario.objects.get(email=data['email'])
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado.")

        if user.codigo_restauracion != data['code']:
            raise serializers.ValidationError("Código incorrecto.")

        if not user.codigo_creado or timezone.now() - user.codigo_creado > timedelta(minutes=10):
            raise serializers.ValidationError("El código ha expirado.")

        user.codigo_validado = True
        user.save()

        return data


from rest_framework import serializers
from usuarios.models import Usuario

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data

    def save(self):
        try:
            user = Usuario.objects.get(email=self.validated_data['email'])
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("No se encontró un usuario con ese correo electrónico.")

        if not user.codigo_validado:
            raise serializers.ValidationError("Primero debes validar tu código.")

        user.set_password(self.validated_data['password'])
        user.codigo_restauracion = None
        user.codigo_creado = None
        user.codigo_validado = False
        user.save()
