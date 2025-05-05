from django.urls import path
from .views import PasswordResetView, PasswordResetConfirmView
from .views import RegisterView, VistaActivacionCuenta
from .views import LoginView, ClienteStatusView, ClienteUpdateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='registro'),
    path('obtener-token/', TokenObtainPairView.as_view(), name='obtener_token'),
    path('activar-cuenta/<uidb64>/<token>/', VistaActivacionCuenta.as_view(), name='activar_cuenta'),
    path('token/renovar/', TokenRefreshView.as_view(), name='renovar_token'),
    path('reset-password/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    # Nuevas URLs para gestión de clientes - Mayk
    path('clientes/<int:cliente_id>/status/', ClienteStatusView.as_view(), name='cliente_status'), # Desactivar/activar cuenta de cliente
    path('clientes/<int:cliente_id>/update/', ClienteUpdateView.as_view(), name='cliente_update'), # Actualizar datos de cliente
]
