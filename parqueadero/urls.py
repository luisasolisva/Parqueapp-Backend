from django.urls import path
from .views import ParqueaderosCercanosView
from .views import RegistrarParqueaderoView, lista_parqueaderos
from .views import ModificarParqueaderoView, VerEspaciosParqueaderoView,EliminarParqueaderoView
from .views import CambiarEstadoEspaciosView, ObtenerMapaParqueaderoView, CrearMapaParqueaderoView, ModificarEspaciosParqueaderoView, EstadisticasAdminView, ParqueaderoDetailView
from . import views


urlpatterns = [
    path('cercanos/', ParqueaderosCercanosView.as_view(), name='parqueaderos_cercanos'),
    path('registrar-parqueadero/', RegistrarParqueaderoView.as_view(), name='Registrar-parqueadero'),
    path('listar/', lista_parqueaderos, name='lista_parqueaderos'),
    path('modificar/<uuid:id_parqueadero>/', ModificarParqueaderoView.as_view(), name='modificar_parqueadero'),
    path('crear-mapa/<uuid:id_parqueadero>/', CrearMapaParqueaderoView.as_view(), name='crear-mapa'),
    path('obtener-mapa/<uuid:id_parqueadero>/', ObtenerMapaParqueaderoView.as_view(), name='obtener-mapa'),
    path('cambiar-estado-espacios/<uuid:id_parqueadero>/', CambiarEstadoEspaciosView.as_view(), name='cambiar-estado-espacios'),
    path('estadisticas/<uuid:id_parqueadero>/', EstadisticasAdminView.as_view(), name='Estadisticas'),
    path('detalles-parqueadero/', ParqueaderoDetailView.as_view(), name='parqueadero_detalle'),
    path('eliminar-parqueadero/<uuid:id_parqueadero>/', EliminarParqueaderoView.as_view(), name='Eliminar_parqueadero'),
    path('modificar-espacios/<uuid:id_parqueadero>/', ModificarEspaciosParqueaderoView.as_view(), name="modificar_espacios_parqueadero"),
    path('espaciosadmin/<uuid:id_parqueadero>/', VerEspaciosParqueaderoView.as_view(), name="espacios_admin"),

]