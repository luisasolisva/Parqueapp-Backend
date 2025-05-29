from django.urls import path
from .views import (
    ParqueaderosCercanosView,)

urlpatterns = [
    path('cercanos/', ParqueaderosCercanosView.as_view(), name='parqueaderos_cercanos'),
    
]
