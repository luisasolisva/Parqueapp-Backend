from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from math import radians, cos, sin, asin, sqrt
from .serializers import ParqueaderoSerializer
from usuarios.models import Parqueadero
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import CambioMatriz

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

        resultado = []
        for distancia, parqueadero in parqueaderos_cercanos:
            data = ParqueaderoSerializer(parqueadero).data
            data['distancia_km'] = round(distancia, 2)  # agregar campo calculado
            resultado.append(data)

        return Response(resultado)



from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from usuarios.models import Parqueadero
from .serializers import RegistrarParqueaderoSerializer
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

class RegistrarParqueaderoView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = RegistrarParqueaderoSerializer

    def get_queryset(self):
        return Parqueadero.objects.none()  # Evita error de queryset vacío

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            parqueadero = serializer.save()

            # Copiar los datos antes de enviar la respuesta, eliminando solo `id_parqueadero`
            parqueadero_data = RegistrarParqueaderoSerializer(parqueadero, context={'request': request}).data
            parqueadero_data.pop('id_parqueadero', None)  # Eliminar ID sin afectar otros datos

            return Response({
                "message": "Parqueadero registrado exitosamente.",
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

class ModificarEspaciosParqueaderoView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        # Validar permisos
        if request.user.tipo_usuario != "Admin":
            return Response({"error": "Solo administradores pueden modificar los espacios"}, status=status.HTTP_403_FORBIDDEN)

        espacios_modificados = request.data.get("espacios_disponibles", [])

        if not espacios_modificados:
            return Response({"error": "Debes proporcionar al menos un espacio a modificar"}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener los espacios actuales en la base de datos
        espacios_actuales = EspacioParqueadero.objects.filter(id_parqueadero=parqueadero)

        # Validar que el espacio realmente existe antes de modificarlo
        for modificado in espacios_modificados:
            espacio_db = espacios_actuales.filter(numero_espacio=modificado["espacio"]).first()

            if not espacio_db:
                return Response({"error": f"El espacio '{modificado['espacio']}' no existe en el parqueadero."}, status=status.HTTP_400_BAD_REQUEST)

            # Modificar estado del espacio
            espacio_db.estado = modificado["estado"]
            espacio_db.save()

        return Response({
            "message": "Espacios modificados correctamente.",
            "espacios_disponibles": list(espacios_actuales.values("numero_espacio", "estado"))
        }, status=status.HTTP_200_OK)







class VerEspaciosParqueaderoView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]  # Solo admins pueden acceder

    def get(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        # Validar permisos
        if request.user.tipo_usuario != "Admin":
            return Response({"error": "Solo administradores pueden ver los espacios."}, status=status.HTTP_403_FORBIDDEN)

        # Obtener los espacios del parqueadero
        espacios = EspacioParqueadero.objects.filter(id_parqueadero=parqueadero)

        if not espacios.exists():
            return Response({"error": "Este parqueadero no tiene espacios registrados."}, status=status.HTTP_404_NOT_FOUND)

        # Serializar los datos
        espacios_disponibles = [
            {
                "id_espacio": str(espacio.id_espacio),
                "numero_espacio": espacio.numero_espacio,
                "estado": espacio.estado
            }
            for espacio in espacios
        ]

        return Response({"espacios_parqueadero": espacios_disponibles}, status=status.HTTP_200_OK)




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
    
    
    
    
    
    
    
    
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from usuarios.models import EspacioParqueadero
class ListaEspaciosDisponiblesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_parqueadero):
        # Validar acceso solo para clientes
        if request.user.tipo_usuario != "Cliente":
            return Response({"error": "Solo los clientes pueden ver los espacios disponibles"}, status=status.HTTP_403_FORBIDDEN)

        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        # Obtener los espacios disponibles desde el modelo `EspacioParqueadero`
        espacios_disponibles = EspacioParqueadero.objects.filter(id_parqueadero=parqueadero, estado="Disponible")

        # Serializar los datos para enviarlos como respuesta
        data = [{
            "id_espacio": str(espacio.id_espacio),
            "numero_espacio": espacio.numero_espacio,
            "estado": espacio.estado
        } for espacio in espacios_disponibles]

        return Response({"espacios_disponibles": data}, status=status.HTTP_200_OK)







class GuardarEspaciosDisponiblesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        if request.user.tipo_usuario != "Admin":
            return Response({"error": "Solo administradores pueden modificar los espacios"}, status=status.HTTP_403_FORBIDDEN)

        nuevos_espacios = request.data.get("espacios_disponibles", [])

        if not nuevos_espacios:
            return Response({"error": "Debes proporcionar al menos un espacio"}, status=status.HTTP_400_BAD_REQUEST)

        for espacio in nuevos_espacios:
            print("Espacio recibido:", espacio)  # 👀 Verifica qué datos llegan a la API

            if not all(key in espacio for key in ["fila", "columna", "espacio", "estado"]):
                return Response({"error": "Cada espacio debe incluir fila, columna, espacio y estado"}, status=status.HTTP_400_BAD_REQUEST)

            EspacioParqueadero.objects.create(
                id_parqueadero=parqueadero,
                numero_espacio=espacio["espacio"],
                fila=espacio["fila"],
                columna=espacio["columna"],
                estado=espacio["estado"]
            )

        return Response({
            "message": "Espacios guardados correctamente.",
            "id_parqueadero": str(parqueadero.id_parqueadero),
            "espacios_disponibles": nuevos_espacios
        }, status=status.HTTP_200_OK)
