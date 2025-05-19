from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# Redirigir la raíz a la página de inicio de sesión
def home(request):
    return redirect('/accounts/login/')

urlpatterns = [
    path('', home, name='home'),  # Redirección para la raíz
    path('admin/', admin.site.urls),
    path('api/', include('usuarios.urls')),
    path('accounts/', include('allauth.urls')),
    path('api/parqueadero/', include('parqueadero.urls')),
    path('parqueaderos/', include('parqueadero.urls'))
]
