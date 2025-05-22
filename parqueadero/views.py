from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from math import radians, cos, sin, asin, sqrt
from .serializers import ParqueaderoSerializer
from usuarios.models import Parqueadero

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
        'nombre_propietario': p.nombre_propietario,  # Eliminado el espacio y paréntesis extra
        'descripcion': p.descripcion,  # Eliminado el paréntesis extra
    } for p in parqueaderos]

    return JsonResponse({'parqueaderos': data})










from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsAdminUser
from usuarios.models import Parqueadero

class ModificarMatrizParqueaderoView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
        
        # Bloquear si el usuario no es admin
        if request.user.tipo_usuario != "Admin":
            return Response({"error": "Solo administradores pueden acceder"}, status=status.HTTP_403_FORBIDDEN)

        # Bloquear si el usuario no es el propietario del parqueadero
        if request.user != parqueadero.id_propietario:
            return Response({"error": "Solo el administrador propietario puede modificar esta matriz"}, status=status.HTTP_403_FORBIDDEN)

        return Response({"matriz": parqueadero.matriz}, status=status.HTTP_200_OK)

    def post(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        # Bloquear si el usuario no es admin
        if request.user.tipo_usuario != "Admin":
            return Response({"error": "Solo administradores pueden modificar esta matriz"}, status=status.HTTP_403_FORBIDDEN)

        # Bloquear si el usuario no es el propietario del parqueadero
        if request.user != parqueadero.id_propietario:
            return Response({"error": "Solo el administrador propietario puede modificar esta matriz"}, status=status.HTTP_403_FORBIDDEN)

        # Asegurar que los datos vienen en `request.data`
        matriz = request.data.get("matriz")
        if not matriz:
            return Response({"error": "La matriz es requerida"}, status=status.HTTP_400_BAD_REQUEST)

        # Validar que los estados sean correctos
        for fila in matriz:
            for celda in fila:
                if celda.get("estado") not in ["Disponible", "Ocupado", "Fuera_de_servicio"]:
                    return Response({"error": "Estado inválido. Solo se permite Disponible, Ocupado o Fuera de servicio"}, status=status.HTTP_400_BAD_REQUEST)

        # Guardar cambios en la base de datos
        parqueadero.matriz = matriz
        parqueadero.save()

        return Response({"message": "Matriz actualizada correctamente", "matriz": parqueadero.matriz}, status=status.HTTP_200_OK)






from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from usuarios.models import Parqueadero
from django.http import HttpResponse


@method_decorator(login_required, name='dispatch')
class VerMatrizParqueaderoView(View):
    def get(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        # Validación de permisos
        if request.user != parqueadero.id_propietario and getattr(request.user, 'tipo_usuario', '') != 'Admin':
            return render(request, 'no_autorizado.html', {'mensaje': 'No tienes permiso para ver la matriz.'})

        return render(request, 'matriz.html', {'matriz': parqueadero.matriz, 'parqueadero': parqueadero})







class ModificarParqueaderoView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ParqueaderoSerializer
    queryset = Parqueadero.objects.all()

    def get_object(self):
        return get_object_or_404(Parqueadero, id_parqueadero=self.kwargs['id_parqueadero'])

    def get(self, request, id_parqueadero):
        parqueadero = self.get_object()
        serializer = self.get_serializer(parqueadero, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id_parqueadero):
        parqueadero = self.get_object()
        serializer = self.get_serializer(parqueadero, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            parqueadero = serializer.save()
            parqueadero_data = ParqueaderoSerializer(parqueadero, context={'request': request}).data
            return Response({
                "message": "Parqueadero modificado exitosamente.",
                "parqueadero": parqueadero_data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)