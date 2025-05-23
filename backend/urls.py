from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('usuarios.urls')),
    path('api/parqueadero/', include('parqueadero.urls')),
    path('parqueaderos/', include('parqueadero.urls'))
]
