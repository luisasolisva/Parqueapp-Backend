from django.urls import path
from .views import ParqueaderosCercanosView
from .views import CrearParqueaderoView, lista_parqueaderos
from .views import ModificarParqueaderoView
from .views import VerMatrizParqueaderoView, ModificarMatrizParqueaderoView
from . import views




urlpatterns = [
    path('cercanos/', ParqueaderosCercanosView.as_view(), name='parqueaderos_cercanos'),
    path('crear-parqueadero/', CrearParqueaderoView.as_view(), name='crear-parqueadero'),
    path('lista/', lista_parqueaderos, name='lista_parqueaderos'),
    path('modificar-matriz/<uuid:id_parqueadero>/', ModificarMatrizParqueaderoView.as_view(), name='modificar-matriz'),
    path('ver-matriz/<uuid:id_parqueadero>/', VerMatrizParqueaderoView.as_view(), name='ver_matriz'),
    path('modificar/<uuid:id_parqueadero>/', ModificarParqueaderoView.as_view(), name='modificar_parqueadero'),

]
