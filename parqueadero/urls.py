from django.urls import path
from .views import ParqueaderosCercanosView
from .views import RegistrarParqueaderoView, lista_parqueaderos
from .views import ModificarParqueaderoView, VerEspaciosParqueaderoView
from .views import  ListaEspaciosDisponiblesView, GuardarEspaciosDisponiblesView, ModificarEspaciosParqueaderoView
from . import views


urlpatterns = [
    path('cercanos/', ParqueaderosCercanosView.as_view(), name='parqueaderos_cercanos'),
    path('Registrar-parqueadero/', RegistrarParqueaderoView.as_view(), name='Registrar-parqueadero'),
    path('lista/', lista_parqueaderos, name='lista_parqueaderos'),
    path('modificar/<uuid:id_parqueadero>/', ModificarParqueaderoView.as_view(), name='modificar_parqueadero'),
    path('Espacios-disponibles/<uuid:id_parqueadero>/', ListaEspaciosDisponiblesView.as_view(), name='lista_espacios_disponibles'),
    path('Guardar_espacios/<uuid:id_parqueadero>/', GuardarEspaciosDisponiblesView.as_view(), name='Guardar_espacios'),
    path('modificar_espacios/', ModificarEspaciosParqueaderoView.as_view(), name='modificar_espacios_parqueadero'),
    path('ver_espacios/', VerEspaciosParqueaderoView.as_view(), name='ver_espacios'),
    
]
