from django.urls import path
from .views import RegisterView, VistaActivacionCuenta
from .views import LoginView, ClienteStatusView, ClienteUpdateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import SendResetCodeView, VerifyResetCodeView, ResetPasswordView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='registro'),
    path('obtener-token/', TokenObtainPairView.as_view(), name='obtener_token'),
    path('activar-cuenta/<uidb64>/<token>/', VistaActivacionCuenta.as_view(), name='activar_cuenta'),
    path('token/renovar/', TokenRefreshView.as_view(), name='renovar_token'),
    path('send-reset-code/', SendResetCodeView.as_view(), name='send_reset_code'),
    path('verify-reset-code/', VerifyResetCodeView.as_view(), name='verify_reset_code'),
    path('reset-password/', ResetPasswordView.as_view(), name='password_reset_confirm'),
    # URLs actualizadas para gestión de clientes usando uidb64
    path('clientes/<uidb64>/status/', ClienteStatusView.as_view(), name='cliente_status'), # Desactivar/activar cuenta de cliente
    path('clientes/<uidb64>/update/', ClienteUpdateView.as_view(), name='cliente_update'), # Actualizar datos de cliente
]
