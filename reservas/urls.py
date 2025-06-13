
from django.urls import path
from .views import (
    CrearReservaView, CancelarReservaView, DetalleReservaView, ReservasParqueaderoView, ListaEspaciosDisponiblesView, ValidarReservaView, ModificarReservaView, MapaDisponibilidadView
)





urlpatterns = [
    # URLs relacionadas con reservas
    path('cancelar_reserva/<uuid:id_reserva>/', CancelarReservaView.as_view(), name='cancelar_reserva'),
    path('detalle_reserva/<uuid:id_reserva>/', DetalleReservaView.as_view(), name='detalle_reserva'),
    path('crear_reserva/<uuid:id_parqueadero>/<uuid:id_espacio>/', CrearReservaView.as_view(), name='crear_reserva'),
    path('reservas_parqueadero/<uuid:id_parqueadero>/', ReservasParqueaderoView.as_view(), name='reservas_parqueadero'),
    path('espacios_disponibles/<uuid:id_parqueadero>/', ListaEspaciosDisponiblesView.as_view(), name='Espacios_disponibles'),
    path("validar_qr/", ValidarReservaView.as_view(), name="validar_reserva"),
    path('modificar-reserva/<uuid:id_reserva>/', ModificarReservaView.as_view(), name='modificar_reserva'),
    path('mapa-disponibilidad/<uuid:id_parqueadero>/', MapaDisponibilidadView.as_view(), name='mapa-disponibilidad'),

    
]





