from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from math import radians, cos, sin, asin, sqrt
from .models import Parqueadero
from .serializers import ParqueaderoSerializer  # Crea este si no existe

def calcular_distancia(lat1, lon1, lat2, lon2):
    # Fórmula Haversine
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

class ParqueaderosCercanosView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lat = request.data.get("lat")
        lng = request.data.get("lng")

        if lat is None or lng is None:
            return Response({"error": "Se requieren lat y lng"}, status=400)

        parqueaderos = Parqueadero.objects.all()
        parqueaderos_dist = []

        for parqueadero in parqueaderos:
            distancia = calcular_distancia(
                float(lat), float(lng),
                float(parqueadero.latitud), float(parqueadero.longitud)
            )
            parqueaderos_dist.append((distancia, parqueadero))

        parqueaderos_dist.sort(key=lambda x: x[0])  # ordenar por distancia
        parqueaderos_cercanos = [p[1] for p in parqueaderos_dist[:10]]  # los 10 más cercanos

        serializer = ParqueaderoSerializer(parqueaderos_cercanos, many=True)
        return Response(serializer.data)



from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from usuarios.models import Parqueadero
from .serializers import ParqueaderoSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from usuarios.models import Parqueadero
from .serializers import ParqueaderoSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUser

class CrearParqueaderoView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ParqueaderoSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            parqueadero = serializer.save()
            parqueadero_data = ParqueaderoSerializer(parqueadero, context={'request': request}).data
            return Response({
                "message": "Parqueadero creado exitosamente.",
                "parqueadero": parqueadero_data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@login_required
def lista_parqueaderos(request):
    # Solo usuarios que NO sean staff o superuser pueden entrar
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para acceder a esta vista")

    parqueaderos = Parqueadero.objects.all()
    data = [{
        'id': str(p.id_parqueadero),
        'nombre': p.nombre,
        'direccion': p.direccion,
        'ciudad': p.ciudad,
        'latitud': float(p.latitud),
        'longitud': float(p.longitud),
        'capacidad_total': p.capacidad_total,
        'capacidad_disponible': p.capacidad_disponible,
        'precio_hora': float(p.precio_hora),
    } for p in parqueaderos]

    return JsonResponse({'parqueaderos': data})
