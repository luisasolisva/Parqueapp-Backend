from django.urls import path
from .views import CrearReservaView

urlpatterns = [
    path('crear-reserva/', CrearReservaView.as_view(), name='crear-reserva'),
]
