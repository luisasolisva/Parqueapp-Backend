from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# Redirigir la raíz a la página de inicio de sesión
def home(request):
    return redirect('/accounts/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('usuarios.urls')),  # Rutas para tu API
    path('accounts/', include('allauth.urls')),  # Rutas de allauth para login
    path('', home),  # Redirige la raíz a la página de login
]
