from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import path , include
from django.contrib import admin


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('usuarios.urls')),
]
