from django.urls import path
from .views import ParqueaderosCercanosView
from .views import CrearParqueaderoView, lista_parqueaderos

urlpatterns = [
    path('cercanos/', ParqueaderosCercanosView.as_view(), name='parqueaderos_cercanos'),
    path('crear-parqueadero/', CrearParqueaderoView.as_view(), name='crear-parqueadero'),
    path('parqueaderos/', lista_parqueaderos, name='lista_parqueaderos'),
]
