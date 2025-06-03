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

from django.db.models import Q

class ParqueaderosCercanosView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lat = request.data.get("lat")
        lng = request.data.get("lng")
        busqueda = request.data.get("busqueda")  # Texto ingresado manualmente

        if lat and lng:
            parqueaderos = Parqueadero.objects.all()
            parqueaderos_dist = []

            for parqueadero in parqueaderos:
                distancia = calcular_distancia(
                    float(lat), float(lng),
                    float(parqueadero.latitud), float(parqueadero.longitud)
                )
                parqueaderos_dist.append((distancia, parqueadero))

            parqueaderos_dist.sort(key=lambda x: x[0])
            parqueaderos_cercanos = parqueaderos_dist[:10]

            resultado = []
            for distancia, parqueadero in parqueaderos_cercanos:
                data = ParqueaderoSerializer(parqueadero).data
                data['distancia_km'] = round(distancia, 2)
                resultado.append(data)

            return Response(resultado)

        elif busqueda:
            parqueaderos = Parqueadero.objects.filter(
                Q(nombre__icontains=busqueda) |
                Q(ciudad__icontains=busqueda)
            )

            serializer = ParqueaderoSerializer(parqueaderos, many=True)
            return Response(serializer.data)

        else:
            return Response({
                "error": "Se requieren coordenadas o un término de búsqueda por nombre o ciudad."
            }, status=400)

    



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
import cloudinary
import cloudinary.uploader
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from parqueadero.utils import validar_imagen  

class RegistrarParqueaderoView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = RegistrarParqueaderoSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})  # ✅ Pasar el usuario en el contexto
        if serializer.is_valid():
            parqueadero = serializer.save()
            return Response({"message": "Parqueadero registrado exitosamente.", "parqueadero": serializer.data}, status=status.HTTP_201_CREATED)

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

        # ✅ Validar permisos: solo administradores pueden modificar los espacios
        if request.user.tipo_usuario != "Admin":
            return Response({"error": "Solo administradores pueden modificar los espacios."}, status=status.HTTP_403_FORBIDDEN)

        espacios_modificados = request.data.get("espacios_disponibles", [])

        if not espacios_modificados:
            return Response({"error": "Debes proporcionar al menos un espacio a modificar."}, status=status.HTTP_400_BAD_REQUEST)

        estados_permitidos = ["Disponible", "Ocupado", "Fuera de servicio"]  # ✅ Definir estados válidos
        espacios_actuales = EspacioParqueadero.objects.filter(id_parqueadero=parqueadero)

        # ✅ Validar cada espacio antes de modificarlo
        for modificado in espacios_modificados:
            espacio_db = espacios_actuales.filter(numero_espacio=modificado.get("espacio")).first()

            if not espacio_db:
                return Response({"error": f"El espacio '{modificado.get('espacio')}' no existe en el parqueadero."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Validar que el estado sea válido
            if "estado" in modificado and modificado["estado"] not in estados_permitidos:
                return Response({"error": f"Estado '{modificado['estado']}' no es válido. Solo se permiten: {', '.join(estados_permitidos)}"}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Solo modificar el estado y número de espacio
            if "estado" in modificado:
                espacio_db.estado = modificado["estado"]
            if "nuevo_numero_espacio" in modificado:
                espacio_db.numero_espacio = modificado["nuevo_numero_espacio"]

            espacio_db.save()

        return Response({
            "message": "Espacios modificados correctamente.",
            "espacios_modificados": list(espacios_actuales.values("numero_espacio", "estado"))
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
            return Response({"error": "Solo administradores pueden modificar los espacios."}, status=status.HTTP_403_FORBIDDEN)

        nuevos_espacios = request.data.get("espacios_disponibles", [])

        if not nuevos_espacios:
            return Response({"error": "Debes proporcionar al menos un espacio."}, status=status.HTTP_400_BAD_REQUEST)

        estados_permitidos = ["Disponible", "Ocupado", "Fuera de servicio"]  # ✅ Definir estados válidos
        espacios_creados = []

        for espacio in nuevos_espacios:
            print("Espacio recibido:", espacio)  # 👀 Verifica qué datos llegan a la API

            # ✅ Validar que los campos requeridos estén presentes
            if not all(key in espacio for key in ["fila", "columna", "espacio", "estado"]):
                return Response({"error": "Cada espacio debe incluir fila, columna, número de espacio y estado."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Validar que el estado sea válido
            if espacio["estado"] not in estados_permitidos:
                return Response({"error": f"Estado '{espacio['estado']}' no es válido. Solo se permiten: {', '.join(estados_permitidos)}"}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Validar que fila y columna sean números
            try:
                fila = int(espacio["fila"])
                columna = int(espacio["columna"])
            except ValueError:
                return Response({"error": "Los valores de fila y columna deben ser números."}, status=status.HTTP_400_BAD_REQUEST)

            espacio_obj = EspacioParqueadero.objects.create(
                id_parqueadero=parqueadero,
                numero_espacio=espacio["espacio"],
                fila=fila,
                columna=columna,
                estado=espacio["estado"]
            )
            espacios_creados.append({
                "numero_espacio": espacio_obj.numero_espacio,
                "fila": espacio_obj.fila,
                "columna": espacio_obj.columna,
                "estado": espacio_obj.estado
            })

        return Response({
            "message": "Espacios guardados correctamente.",
            "id_parqueadero": str(parqueadero.id_parqueadero),
            "espacios_creados": espacios_creados
        }, status=status.HTTP_200_OK)




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from usuarios.models import Parqueadero
from usuarios.models import Usuario
from usuarios.models import Reserva
from parqueadero.serializers import EstadisticasAdminSerializer

class EstadisticasAdminView(APIView):
    def get(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        total_clientes = Usuario.objects.filter(reserva__id_parqueadero=parqueadero).distinct().count()  # ✅ Corregida la consulta
        total_reservas = Reserva.objects.filter(id_parqueadero=parqueadero).count()
        reservas_confirmadas = Reserva.objects.filter(id_parqueadero=parqueadero, estado="Confirmada").count()
        reservas_canceladas = Reserva.objects.filter(id_parqueadero=parqueadero, estado="Cancelada").count()
        ingresos_totales = Reserva.objects.filter(id_parqueadero=parqueadero, estado="Confirmada").aggregate(Sum("monto_total"))["monto_total__sum"] or 0

        data = {
            "total_clientes": total_clientes,
            "total_reservas": total_reservas,
            "reservas_confirmadas": reservas_confirmadas,
            "reservas_canceladas": reservas_canceladas,
            "ingresos_totales": ingresos_totales
        }

        serializer = EstadisticasAdminSerializer(data)  # ✅ Se asegura que reciba un diccionario
        return Response(serializer.data, status=status.HTTP_200_OK)

from .serializers import ParqueaderoDetailSerializer


class ParqueaderoDetailView(APIView):
    permission_classes = [IsAuthenticated]  # ✅ Solo usuarios autenticados pueden ver detalles

    def get(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
        serializer = ParqueaderoDetailSerializer(parqueadero)
        return Response(serializer.data, status=status.HTTP_200_OK)



class EliminarParqueaderoView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]  # ✅ Solo admins autenticados pueden eliminar

    def delete(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        # ✅ Verificar que el usuario autenticado sea el propietario real
        if parqueadero.propietario != request.user:  # 🔥 Comparar por ForeignKey, no por texto
            return Response({"error": "No puedes eliminar un parqueadero que no te pertenece."}, status=status.HTTP_403_FORBIDDEN)

        parqueadero.delete()
        return Response({"message": "Parqueadero eliminado correctamente."}, status=status.HTTP_200_OK)


from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from usuarios.models import Reserva, EspacioParqueadero, Parqueadero
from .serializers import ReservaSerializer
class CrearReservaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id_parqueadero, id_espacio):
        # Validamos que el usuario sea Cliente
        if request.user.tipo_usuario != "Cliente":
            return Response({"error": "Solo los clientes pueden hacer reservas"}, status=status.HTTP_403_FORBIDDEN)

        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
        espacio = get_object_or_404(EspacioParqueadero, id_espacio=id_espacio, id_parqueadero=parqueadero)

        # Verificar que el espacio esté disponible
        if espacio.estado != "Disponible":
            return Response({"error": "El espacio seleccionado no está disponible"}, status=status.HTTP_400_BAD_REQUEST)

        # Capturar datos del vehículo
        data = request.data.copy()  # Creamos una copia para modificarlo
        data["id_usuario"] = request.user.id
        data["id_parqueadero"] = parqueadero.id_parqueadero
        data["id_espacio"] = espacio.id_espacio

        # Convertir fechas a formato adecuado
        try:
            data["fecha_inicio"] = datetime.strptime(data["fecha_inicio"], "%Y-%m-%d").date()
            data["fecha_fin"] = datetime.strptime(data["fecha_fin"], "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Formato de fecha incorrecto. Usa YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Serializar y validar los datos
        serializer = ReservaSerializer(data=data)
        if serializer.is_valid():
            reserva = serializer.save(estado="Pendiente")

            # Marcar el espacio como ocupado
            espacio.estado = "Ocupado"
            espacio.save()

            return Response({"mensaje": "Reserva creada exitosamente", "id_reserva": str(reserva.id_reserva)}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
