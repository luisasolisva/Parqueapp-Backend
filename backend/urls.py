from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import path , include
from django.contrib import admin

def home(request):
    if request.user.is_authenticated:
        return HttpResponse("¡Bienvenido, al backend!")
    return redirect('/accounts/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('usuarios.urls')),
    path('accounts/', include('allauth.urls')),
    path('', home),
]
