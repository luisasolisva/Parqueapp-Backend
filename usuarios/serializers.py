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

    def create(self, validated_data):
            usuario = Usuario.objects.create_user(
                email=validated_data['email'].lower(),
                password=validated_data['password'],  # Se asegura de usar set_password correctamente
                nombre=validated_data['nombre'].title(),
                apellido=validated_data['apellido'].title(),
                telefono=validated_data['telefono'],
                tipo_usuario=validated_data['tipo_usuario'],
            )
            usuario.save()

            # Generar token de activación
            token = default_token_generator.make_token(usuario)

            # Llamar a la función send_activation_email importada de utils.py
            send_activation_email(usuario)

            return usuario



from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import send_activation_email  # Asegúrate de importar la función correctamente

from django.contrib.auth import get_user_model
User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = User.objects.filter(email=email).first()

        if not user:
            raise serializers.ValidationError({"error": "El correo o la contraseña no son correctos. Verifica e intenta nuevamente."})

        if not user.is_active:
            # Reenviar correo de activación
            send_activation_email(user)
            raise serializers.ValidationError({
                "error": "Tu cuenta aún no ha sido activada. Te hemos enviado nuevamente un correo de activación."
            })

        user = authenticate(request=self.context.get('request'), username=email, password=password)

        if user is None:
            raise serializers.ValidationError({"error": "El correo o la contraseña no son correctos. Verifica e intenta nuevamente."})

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

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
    code = serializers.CharField(max_length=4)

    def validate(self, data):
        try:
            user = Usuario.objects.get(codigo_restauracion=data['code'])
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Código incorrecto.")

        # Verificar expiración del código
        if not user.codigo_creado or timezone.now() - user.codigo_creado > timedelta(minutes=10):
            raise serializers.ValidationError("El código ha expirado.")

        user.codigo_validado = True
        user.save()

        # Retornar el ID del usuario para que el frontend lo almacene
        return {"user_id": user.id}




from rest_framework import serializers
from usuarios.models import Usuario
from rest_framework import serializers
from usuarios.models import Usuario
from django.utils import timezone
from datetime import timedelta

class PasswordResetConfirmSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data

    def save(self):
        try:
            user = Usuario.objects.get(id=self.validated_data['user_id'])
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Usuario no válido para el restablecimiento de contraseña.")

        if not user.codigo_validado:
            raise serializers.ValidationError("Primero debes validar tu código de restauración.")

        user.set_password(self.validated_data['password'])
        user.codigo_restauracion = None
        user.codigo_creado = None
        user.codigo_validado = False

        user.save()

