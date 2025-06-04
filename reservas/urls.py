
from django.urls import path
from .views import CrearReservaView, CancelarReservaView, DetalleReservaView, ReservasParqueaderoView, ListaEspaciosDisponiblesView

urlpatterns = [

    path('cancelar_reserva/<uuid:id_reserva>/', CancelarReservaView.as_view(), name='cancelar_reserva'),
    path('detalle_reserva/<uuid:id_reserva>/', DetalleReservaView.as_view(), name='detalle_reserva'),
    path('crear_reserva/<uuid:id_parqueadero>/<uuid:id_espacio>/', CrearReservaView.as_view(), name='crear_reserva'),
    path('reservas_parqueadero/<uuid:id_parqueadero>/', ReservasParqueaderoView.as_view(), name='reservas_parqueadero'),
    path('Lista_espaciosdis/<uuid:id_parqueadero>/', ListaEspaciosDisponiblesView.as_view(), name="espacios_disponibles"),

]




















