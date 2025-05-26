from django.urls import path
from .views import (
    ParqueaderosCercanosView,
    CrearParqueaderoView,
    lista_parqueaderos,
    ModificarParqueaderoView,
    VerMatrizParqueaderoView,
    ModificarMatrizParqueaderoView,
    ListaEspaciosDisponiblesView,
    CargarMatrizBaseView,
    ModificarMatrizView,
    ValidarEstructuraMatrizView,
    AplicarPatronMatrizView,
    RellenarAreaMatrizView,
    GuardarMatrizCompletaView
)

urlpatterns = [
    path('cercanos/', ParqueaderosCercanosView.as_view(), name='parqueaderos_cercanos'),
    path('crear-parqueadero/', CrearParqueaderoView.as_view(), name='crear-parqueadero'),
    path('lista/', lista_parqueaderos, name='lista_parqueaderos'),
    path('modificar-matriz/<uuid:id_parqueadero>/', ModificarMatrizParqueaderoView.as_view(), name='modificar-matriz'),
    path('ver-matriz/<uuid:id_parqueadero>/', VerMatrizParqueaderoView.as_view(), name='ver_matriz'),
    path('modificar/<uuid:id_parqueadero>/', ModificarParqueaderoView.as_view(), name='modificar_parqueadero'),
    path('Espacios-disponibles/<uuid:id_parqueadero>/', ListaEspaciosDisponiblesView.as_view(), name='lista_espacios_disponibles'),
    path('parqueadero/<uuid:id_parqueadero>/matriz/', CargarMatrizBaseView.as_view(), name='cargar-matriz'),
    path('parqueadero/<uuid:id_parqueadero>/modificar-matriz/', ModificarMatrizView.as_view(), name='modificar-matriz'),
    path('parqueadero/<uuid:id_parqueadero>/validar-estructura/', ValidarEstructuraMatrizView.as_view(), name='validar-estructura'),
    path('parqueadero/<uuid:id_parqueadero>/aplicar-patron/', AplicarPatronMatrizView.as_view(), name='aplicar-patron'),
    path('parqueadero/<uuid:id_parqueadero>/rellenar-area/', RellenarAreaMatrizView.as_view(), name='rellenar-area'),
    path('parqueadero/<uuid:id_parqueadero>/guardar-matriz/', GuardarMatrizCompletaView.as_view(), name='guardar-matriz'),
]
