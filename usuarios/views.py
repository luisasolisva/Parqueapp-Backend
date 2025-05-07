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

    
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny
from django.contrib.auth import login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Inicio de sesión exitoso.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "tipo_usuario": user.tipo_usuario,
            }, status=status.HTTP_200_OK)

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



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .serializers import (
    PasswordResetSerializer,
    PasswordResetCodeConfirmSerializer,
    PasswordResetConfirmSerializer
)
class SendResetCodeView(APIView):
    permission_classes = [AllowAny]

    def get_serializer(self, *args, **kwargs):
        return PasswordResetSerializer(*args, **kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Código enviado al correo si el usuario existe."}, status=status.HTTP_200_OK)



class VerifyResetCodeView(APIView):
    permission_classes = [AllowAny]

    def get_serializer(self, *args, **kwargs):
        return PasswordResetCodeConfirmSerializer(*args, **kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "Código verificado. Ahora puedes cambiar tu contraseña."}, status=status.HTTP_200_OK)




class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def get_serializer(self, *args, **kwargs):
        return PasswordResetConfirmSerializer(*args, **kwargs)

    def post(self, request):
        # Obtén el serializer y valida la información
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Guarda los datos (restablece la contraseña si todo es válido)
        serializer.save()

        return Response({"message": "Contraseña restablecida con éxito."}, status=status.HTTP_200_OK)
