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
