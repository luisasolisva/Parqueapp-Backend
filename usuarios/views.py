from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer

class RegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer  # Usamos el serializer para registro

    def post(self, request):
        print("Datos recibidos:", request.data)  # Imprime los datos para depuración
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Usuario creado exitosamente. Por favor, verifica tu correo electrónico para activar tu cuenta."
            }, status=status.HTTP_201_CREATED)
        print("Errores del serializer:", serializer.errors)  # Imprime errores del serializer
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
# usuarios/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer
from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from rest_framework.permissions import AllowAny

class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer  # Aunque no es usado por APIView, no daña

    def post(self, request):
        # Validar los datos del serializer
        serializer = LoginSerializer(data=request.data, context={'request': request})  # Pasamos el contexto con el request
        if serializer.is_valid():
            # Obtener el usuario validado
            user = serializer.validated_data['user']

            if user.is_active:
                # Iniciar sesión
                login(request, user)
                
                # Generar token de autenticación
                token = default_token_generator.make_token(user)
                
                # Redirigir según el tipo de usuario
                if user.tipo_usuario == 'Operario':
                    return Response({
                        "message": "Inicio de sesión exitoso como Operario.",
                        "token": token,
                    }, status=status.HTTP_200_OK) 
                elif user.tipo_usuario == 'Usuario':
                    return Response({
                        "message": "Inicio de sesión exitoso como Usuario.",
                        "token": token,
                    }, status=status.HTTP_200_OK) 
                
                elif user.tipo_usuario == 'Cliente':
                    return Response({
                        "message": "Inicio de sesión exitoso como Cliente.",
                        "token": token,
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Cuenta inactiva."
                }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class VistaActivacionCuenta(APIView):
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación

    def get(self, request, uidb64, token):
        try:
            # Decodificar UID y obtener usuario
            uid = urlsafe_base64_decode(uidb64).decode('utf-8')
            usuario = get_object_or_404(Usuario, pk=uid)

            # Verificar si el token es válido
            if default_token_generator.check_token(usuario, token):
                usuario.is_active = True
                usuario.save()
                
                # **Redirigir al frontend en lugar de mostrar JSON**
                return redirect(f"{settings.FRONTEND_URL}/login?activado=true")
            
            return redirect(f"{settings.FRONTEND_URL}/error")
        
        except Exception:
            return redirect(f"{settings.FRONTEND_URL}/error")


from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import PasswordResetSerializer

class PasswordResetView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Se manda el correo de restablecimiento
            return Response({
                "message": "Si ese correo está registrado, te hemos enviado un correo con instrucciones para restablecer tu contraseña."
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import PasswordResetConfirmSerializer
from usuarios.models import Usuario

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uidb64, token):
        try:
            # Decodificar el ID del usuario
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Usuario.objects.get(id=uid)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            user = None

        # Verificar el token
        if user is not None and default_token_generator.check_token(user, token):
            # Validar y guardar la nueva contraseña
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)  # Guardamos la nueva contraseña
                return Response({"message": "Contraseña restablecida con éxito."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Token inválido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.permissions import IsAuthenticated
from .serializers import ClienteStatusSerializer, ClienteUpdateSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

class ClienteStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uidb64):
        # Verificar que el usuario que hace la petición sea un Operario
        if request.user.tipo_usuario != 'Operario':
            return Response(
                {"error": "Solo los operarios pueden realizar esta acción"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Decodificar el uidb64 para obtener el ID del usuario
            uid = urlsafe_base64_decode(uidb64).decode()
            cliente = get_object_or_404(Usuario, id=uid, tipo_usuario='Cliente')
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return Response(
                {"error": "Cliente no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cambiar el estado
        cliente.is_active = not cliente.is_active
        cliente.save()

        estado = "activada" if cliente.is_active else "desactivada"
        return Response({
            "message": f"Cuenta del cliente {estado} exitosamente",
            "is_active": cliente.is_active
        }, status=status.HTTP_200_OK)

class ClienteUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, uidb64):
        try:
            # Decodificar el uidb64 para obtener el ID del usuario
            uid = urlsafe_base64_decode(uidb64).decode()
            cliente = get_object_or_404(Usuario, id=uid, tipo_usuario='Cliente')
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return Response(
                {"error": "Cliente no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar que el usuario que hace la petición sea el mismo cliente o un Operario
        if request.user.id != cliente.id and request.user.tipo_usuario != 'Operario':
            return Response(
                {"error": "No tienes permiso para realizar esta acción"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Actualizar los datos
        serializer = ClienteUpdateSerializer(cliente, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Datos del cliente actualizados exitosamente",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
