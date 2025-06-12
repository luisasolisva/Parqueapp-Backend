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
    
class RegistrarParqueaderoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RegistrarParqueaderoSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                parqueadero = serializer.save()
                return Response({"message": "Parqueadero registrado exitosamente.", "id": parqueadero.id_parqueadero}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

from datetime import datetime
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .permissions import IsAdminUser
from usuarios.models import Parqueadero, EspacioParqueadero, Reserva

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

        estados_permitidos = ["Disponible", "Ocupado", "Deshabilitado"]
        espacios_actuales = EspacioParqueadero.objects.filter(id_parqueadero=parqueadero)

        reservas_canceladas = []

        for modificado in espacios_modificados:
            espacio_db = espacios_actuales.filter(numero_espacio=modificado.get("espacio")).first()

            if not espacio_db:
                return Response({"error": f"El espacio '{modificado.get('espacio')}' no existe en el parqueadero."}, status=status.HTTP_400_BAD_REQUEST)

            if "estado" in modificado and modificado["estado"] not in estados_permitidos:
                return Response({"error": f"Estado '{modificado['estado']}' no es válido. Solo se permiten: {', '.join(estados_permitidos)}"}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Verificar si el espacio tenía una reserva activa
            reserva_activa = Reserva.objects.filter(id_espacio=espacio_db, estado="Pendiente").first()
            if reserva_activa:
                # ✅ Cambiar el estado de la reserva a Cancelada
                reserva_activa.estado = "Cancelada"
                reserva_activa.save()

                # ✅ Notificar al cliente
                send_mail(
                    "Cancelación de reserva - Modificación de espacio",
                    f"Estimado usuario,\n\nTu reserva en el espacio {espacio_db.numero_espacio} ha sido cancelada porque el espacio ha sido modificado por el administrador.\n\nDisculpa las molestias.",
                    "parqueappreservas@gmail.com",
                    [reserva_activa.cliente.email],
                    fail_silently=False,
                )

                reservas_canceladas.append({
                    "id_reserva": str(reserva_activa.id_reserva),
                    "cliente": reserva_activa.cliente.email,
                    "numero_espacio": espacio_db.numero_espacio
                })

            # ✅ Modificar el estado del espacio
            if "estado" in modificado:
                espacio_db.estado = modificado["estado"]
            if "nuevo_numero_espacio" in modificado:
                espacio_db.numero_espacio = modificado["nuevo_numero_espacio"]

            espacio_db.save()

        return Response({
            "message": "Espacios modificados correctamente.",
            "reservas_canceladas": reservas_canceladas,
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

from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from usuarios.models import Parqueadero, EspacioParqueadero, ImagenParqueadero
import cloudinary.uploader
from .serializers import ModificarParqueaderoSerializer


class ModificarParqueaderoView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        serializer = ModificarParqueaderoSerializer(parqueadero, data=request.data, partial=True)
        if serializer.is_valid():
            parqueadero = serializer.save()
            imagen_existente = ImagenParqueadero.objects.filter(parqueadero=parqueadero).first()
            imagen_url = str(imagen_existente.imagen) if imagen_existente else None  # ✅ Convertimos la imagen a su URL


            return Response({
                "message": "Parqueadero modificado exitosamente.",
                "parqueadero": ModificarParqueaderoSerializer(parqueadero).data,
                "imagen": imagen_url
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from usuarios.models import Parqueadero, MapaParqueadero, EspacioParqueadero
from .serializers import MapaParqueaderoSerializer  

class CrearMapaParqueaderoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        if request.user.tipo_usuario != "Admin":
            return Response({"error": "Solo administradores pueden modificar los espacios."}, status=status.HTTP_403_FORBIDDEN)

        # Verificar si ya existe un mapa para el parqueadero
        if MapaParqueadero.objects.filter(parqueadero=parqueadero).exists():
            return Response(
                {"error": "Este parqueadero ya tiene un mapa registrado. No se puede crear otro."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valida el serializer con los datos recibidos
        serializer = MapaParqueaderoSerializer(data=request.data.get("mapaParqueadero"))
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        filas = data["mapaSize"]["filas"]
        columnas = data["mapaSize"]["columnas"]
        nomenclatura = data["nomenclatura"]
        espacios_data = data["espacios"]

        # Validaciones adicionales
        if filas <= 0 or columnas <= 0:
            return Response({"error": "Filas y columnas deben ser mayores a cero."}, status=status.HTTP_400_BAD_REQUEST)

        estados_permitidos = ["Disponible", "Deshabilitado"]
        errores_espacios = []

        for idx, espacio in enumerate(espacios_data):
            if espacio["estado"] not in estados_permitidos:
                errores_espacios.append(f"Espacio '{espacio['espacio']}': estado inválido '{espacio['estado']}'.")
            if espacio["fila"] < 0 or espacio["columna"] < 0:
                errores_espacios.append(f"Espacio '{espacio['espacio']}': fila y columna deben ser >= 0.")
            if espacio["fila"] >= filas or espacio["columna"] >= columnas:
                errores_espacios.append(
                    f"Espacio '{espacio['espacio']}': fuera de los límites del mapa ({filas}x{columnas})."
                )

        if errores_espacios:
            return Response({"error": "Errores en los espacios:", "detalles": errores_espacios}, status=status.HTTP_400_BAD_REQUEST)

        # Crear nuevo mapa
        mapa = MapaParqueadero.objects.create(
            parqueadero=parqueadero,
            filas=filas,
            columnas=columnas,
            nomenclatura=nomenclatura
        )

        for espacio in espacios_data:
            EspacioParqueadero.objects.create(
                mapa=mapa,
                espacio=espacio["espacio"],
                fila=espacio["fila"],
                columna=espacio["columna"],
                estado=espacio["estado"]
            )

        return Response({
            "mensaje": "Mapa creado exitosamente."
        }, status=status.HTTP_201_CREATED)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction  # transacción atómica

class ModificarMapaParqueaderoView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        if request.user.tipo_usuario != "Admin":
            return Response({"error": "Solo administradores pueden modificar el mapa."}, status=status.HTTP_403_FORBIDDEN)

        serializer = MapaParqueaderoSerializer(data=request.data.get("mapaParqueadero"))
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        filas = data['mapaSize']['filas']
        columnas = data['mapaSize']['columnas']
        nomenclatura = data['nomenclatura']
        espacios_data = data['espacios']

        # Validaciones adicionales de lógica de negocio
        errores_espacios = []
        for espacio in espacios_data:
            if espacio["fila"] >= filas or espacio["columna"] >= columnas:
                errores_espacios.append(f"Espacio '{espacio['espacio']}' está fuera de los límites del mapa ({filas}x{columnas}).")

        if errores_espacios:
            return Response({"errores": errores_espacios}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Borrar mapa anterior
                MapaParqueadero.objects.filter(parqueadero=parqueadero).delete()

                # Crear nuevo mapa
                mapa = MapaParqueadero.objects.create(
                    parqueadero=parqueadero,
                    filas=filas,
                    columnas=columnas,
                    nomenclatura=nomenclatura
                )

                # Crear nuevos espacios
                for espacio in espacios_data:
                    EspacioParqueadero.objects.create(
                        mapa=mapa,
                        espacio=espacio["espacio"],
                        fila=espacio["fila"],
                        columna=espacio["columna"],
                        estado=espacio["estado"]
                    )

            return Response({"mensaje": "Mapa modificado exitosamente."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Ocurrió un error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from usuarios.models import Parqueadero, MapaParqueadero, EspacioParqueadero

class ObtenerMapaParqueaderoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_parqueadero):
        try:
            parqueadero = Parqueadero.objects.get(id_parqueadero=id_parqueadero)
        except Parqueadero.DoesNotExist:
            return Response(
                {"error": "Parqueadero no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        mapa = MapaParqueadero.objects.filter(parqueadero=parqueadero).first()

        if not mapa:
            return Response(
                {"error": "Este parqueadero no tiene un mapa registrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        espacios = EspacioParqueadero.objects.filter(mapa=mapa)

        respuesta = {
            "mapaSize": {
                "filas": mapa.filas,
                "columnas": mapa.columnas
            },
            "nomenclatura": mapa.nomenclatura,
            "espacios": [
                {
                    "fila": espacio.fila,
                    "columna": espacio.columna,
                    "espacio": espacio.espacio,
                    "estado": espacio.estado
                } for espacio in espacios
            ]
        }

        return Response(respuesta, status=status.HTTP_200_OK)

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from usuarios.models import Parqueadero, MapaParqueadero, EspacioParqueadero
from .serializers import EspacioEstadoUpdateSerializer


class CambiarEstadoEspaciosView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id_parqueadero):
        if request.user.tipo_usuario != "Admin":
            return Response(
                {"error": "Solo administradores pueden modificar el estado de los espacios."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            parqueadero = Parqueadero.objects.get(id_parqueadero=id_parqueadero)
        except Parqueadero.DoesNotExist:
            return Response(
                {"error": "Parqueadero no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        mapa = MapaParqueadero.objects.filter(parqueadero=parqueadero).first()
        if not mapa:
            return Response(
                {"error": "Este parqueadero no tiene un mapa registrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data.get("espacios")
        if not data:
            return Response(
                {"error": "Debe enviar al menos un espacio a modificar bajo la clave 'espacios'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Aceptar lista o diccionario individual
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            return Response(
                {"error": "El campo 'espacios' debe ser un objeto o una lista de objetos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        errores = []
        actualizados = []

        for idx, espacio_data in enumerate(data):
            serializer = EspacioEstadoUpdateSerializer(data=espacio_data)
            if not serializer.is_valid():
                errores.append(f"Ítem {idx + 1}: {serializer.errors}")
                continue

            valid_data = serializer.validated_data
            fila = valid_data["fila"]
            columna = valid_data["columna"]
            estado = valid_data["estado"]

            try:
                espacio = EspacioParqueadero.objects.get(mapa=mapa, fila=fila, columna=columna)
                espacio.estado = estado
                espacio.save()
                actualizados.append(f"({fila},{columna}) → '{estado}'")
            except EspacioParqueadero.DoesNotExist:
                errores.append(f"Espacio en fila {fila}, columna {columna} no encontrado.")

        if errores:
            return Response(
                {
                    "mensaje": "Algunos espacios no se pudieron actualizar.",
                    "actualizados": actualizados,
                    "errores": errores
                },
                status=status.HTTP_207_MULTI_STATUS
            )

        return Response(
            {"mensaje": "Espacios actualizados correctamente.", "actualizados": actualizados},
            status=status.HTTP_200_OK
        )


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


# Vista con endpint dinámico que retorna los detalles del parqueadero validando el id_admin o id_parqueadero 
import uuid
from .serializers import ParqueaderoDetailSerializer

class ParqueaderoDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # GET /detalles-parqueadero/?id_admin=<uuid>
        id_admin = request.query_params.get('id_admin')
        # GET /detalles-parqueadero/?id_parqueadero=<uuid>
        id_parqueadero = request.query_params.get('id_parqueadero')

        try:
            # Consulta por id_admin (solo el mismo admin puede hacerla)
            if id_admin:
                if request.user.id != uuid.UUID(id_admin):
                    return Response({
                        "message": "No tienes permiso para ver esta información."
                    }, status=status.HTTP_403_FORBIDDEN)

                parqueadero = Parqueadero.objects.filter(propietario__id=id_admin).first()

                if parqueadero:
                    serializer = ParqueaderoDetailSerializer(parqueadero)
                    tiene_mapa = MapaParqueadero.objects.filter(parqueadero=parqueadero).exists()
                    return Response({
                        "tiene_parqueadero": True,
                        "tiene_mapa": tiene_mapa,
                        "data": serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "tiene_parqueadero": False,
                        "message": "No tienes parqueadero registrado."
                    }, status=status.HTTP_200_OK)

            # Consulta por id_parqueadero (pública, sin has_parqueadero)
            elif id_parqueadero:
                parqueadero = Parqueadero.objects.filter(id_parqueadero=id_parqueadero).first()

                if parqueadero:
                    serializer = ParqueaderoDetailSerializer(parqueadero)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "message": "Parqueadero no encontrado."
                    }, status=status.HTTP_404_NOT_FOUND)

            # Ningún parámetro recibido
            return Response({
                "message": "Debes proporcionar un parámetro: id_admin o id_parqueadero."
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "message": "Error inesperado en el servidor.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from cloudinary.uploader import destroy

class EliminarParqueaderoView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, id_parqueadero):
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        if parqueadero.propietario != request.user:
            return Response({"error": "No puedes eliminar un parqueadero que no te pertenece."}, status=status.HTTP_403_FORBIDDEN)

        # Eliminar imágenes de Cloudinary antes de eliminar los registros
        for imagen in parqueadero.imagenes_del_parqueadero.all():
            imagen.imagen.delete()  # ✅ Esto elimina el archivo en Cloudinary
            imagen.delete()         # ✅ Esto elimina el registro en la base de datos

        parqueadero.delete()

        return Response({"message": "Parqueadero eliminado correctamente."}, status=status.HTTP_200_OK)

