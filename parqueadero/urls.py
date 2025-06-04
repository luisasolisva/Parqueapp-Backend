from django.urls import path
from .views import ParqueaderosCercanosView
from .views import RegistrarParqueaderoView, lista_parqueaderos, CancelarReservaView, DetalleReservaView, ReservasParqueaderoView
from .views import ModificarParqueaderoView, VerEspaciosParqueaderoView,EliminarParqueaderoView,CrearReservaView
from .views import  ListaEspaciosDisponiblesView, GuardarEspaciosDisponiblesView, ModificarEspaciosParqueaderoView, EstadisticasAdminView, ParqueaderoDetailView
from . import views


urlpatterns = [
    path('cercanos/', ParqueaderosCercanosView.as_view(), name='parqueaderos_cercanos'),
    path('registrar-parqueadero/', RegistrarParqueaderoView.as_view(), name='Registrar-parqueadero'),
    path('listar/', lista_parqueaderos, name='lista_parqueaderos'),
    path('modificar/<uuid:id_parqueadero>/', ModificarParqueaderoView.as_view(), name='modificar_parqueadero'),
    path('guardar-espacios/<uuid:id_parqueadero>/', GuardarEspaciosDisponiblesView.as_view(), name='Guardar_espacios'),
    path('estadisticas/<uuid:id_parqueadero>/', EstadisticasAdminView.as_view(), name='Estadisticas'),
    path('detalles-parqueadero/<uuid:id_parqueadero>/', ParqueaderoDetailView.as_view(), name='parqueadero_detalle'),
    path('eliminar-parqueadero/<uuid:id_parqueadero>/', EliminarParqueaderoView.as_view(), name='Eliminar_parqueadero'),
    path('modificar-espacios/<uuid:id_parqueadero>/', ModificarEspaciosParqueaderoView.as_view(), name="modificar_espacios_parqueadero"),
    path('lista-espaciosdis/<uuid:id_parqueadero>/', ListaEspaciosDisponiblesView.as_view(), name="espacios_disponibles"),
    path('reservas/<uuid:id_parqueadero>/<uuid:id_espacio>/', CrearReservaView.as_view(), name='crear_reserva'),
    path('espaciosadmin/<uuid:id_parqueadero>/', VerEspaciosParqueaderoView.as_view(), name="espacios_admin"),
    path("reservas/<uuid:id_reserva>/cancelar/", CancelarReservaView.as_view(), name="cancelar_reserva"),
    path("reservas/<uuid:id_reserva>/detalles/", DetalleReservaView.as_view(), name="detalle_reserva"),
    path('reservas/parqueadero/<uuid:id_parqueadero>/', ReservasParqueaderoView.as_view(), name="reservas_parqueadero"),

]