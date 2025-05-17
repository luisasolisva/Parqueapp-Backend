from django.urls import path
from .views import ParqueaderosCercanosView
from .views import CrearParqueaderoView, lista_parqueaderos
from .views import modificar_matriz_parqueadero
from .views import VerMatrizParqueaderoView
from . import views




urlpatterns = [
    path('cercanos/', ParqueaderosCercanosView.as_view(), name='parqueaderos_cercanos'),
    path('crear-parqueadero/', CrearParqueaderoView.as_view(), name='crear-parqueadero'),
    path('parqueaderos/', lista_parqueaderos, name='lista_parqueaderos'),
    path('parqueadero/<uuid:id_parqueadero>/modificar/', views.modificar_matriz_parqueadero, name='modificar-matriz'),
    path('parqueaderos/<uuid:id_parqueadero>/ver-matriz/', VerMatrizParqueaderoView.as_view(), name='ver_matriz'),
]
