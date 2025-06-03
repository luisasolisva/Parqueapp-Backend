from django.urls import path
from .views import ParqueaderosCercanosView
from .views import RegistrarParqueaderoView, lista_parqueaderos
from .views import ModificarParqueaderoView, VerEspaciosParqueaderoView,EliminarParqueaderoView,CrearReservaView
from .views import  ListaEspaciosDisponiblesView, GuardarEspaciosDisponiblesView, ModificarEspaciosParqueaderoView, EstadisticasAdminView, ParqueaderoDetailView
from . import views


urlpatterns = [
    path('cercanos/', ParqueaderosCercanosView.as_view(), name='parqueaderos_cercanos'),
    path('Registrar-parqueadero/', RegistrarParqueaderoView.as_view(), name='Registrar-parqueadero'),
    path('lista/', lista_parqueaderos, name='lista_parqueaderos'),
    path('Modificar/<uuid:id_parqueadero>/', ModificarParqueaderoView.as_view(), name='modificar_parqueadero'),
    path('Guardar_espacios/<uuid:id_parqueadero>/', GuardarEspaciosDisponiblesView.as_view(), name='Guardar_espacios'),
    path('Ver_espacios/<uuid:id_parqueadero>', VerEspaciosParqueaderoView.as_view(), name='ver_espacios'),
    path('Estadisticas/<uuid:id_parqueadero>/', EstadisticasAdminView.as_view(), name='Estadisticas'),
    path('Detalles_parqueadero/<uuid:id_parqueadero>/', ParqueaderoDetailView.as_view(), name='parqueadero_detalle'),
    path('Eliminar_parqueadero/<uuid:id_parqueadero>/', EliminarParqueaderoView.as_view(), name='Eliminar_parqueadero'),
    path('Modificar_espacios/<uuid:id_parqueadero>/', ModificarEspaciosParqueaderoView.as_view(), name="modificar_espacios_parqueadero"),
    path('Ver_espacios/<uuid:id_parqueadero>/', VerEspaciosParqueaderoView.as_view(), name="ver_espacios"),
    path('reservas/<uuid:id_parqueadero>/<uuid:id_espacio>/', CrearReservaView.as_view(), name='crear_reserva'),
]
