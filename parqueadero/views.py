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
        cambios = request.data.get("cambios")
        if not cambios:
            return Response({"error": "Los cambios son requeridos"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fila_idx = cambios.get("fila")
            columna_idx = cambios.get("columna")
            nuevo_nombre = cambios.get("nombre")
            nuevo_estado = cambios.get("estado")

            # Validar índices
            if fila_idx is None or columna_idx is None:
                return Response({"error": "Fila y columna son obligatorias"}, status=status.HTTP_400_BAD_REQUEST)

            if nuevo_estado not in ["Disponible", "Ocupado", "Fuera_de_servicio"]:
                return Response({"error": "Estado inválido. Solo se permite Disponible, Ocupado o Fuera de servicio"}, status=status.HTTP_400_BAD_REQUEST)

            # Modificar solo el espacio especificado
            parqueadero.matriz[fila_idx][columna_idx]["nombre"] = nuevo_nombre if nuevo_nombre is not None else ""
            parqueadero.matriz[fila_idx][columna_idx]["estado"] = nuevo_estado

            parqueadero.save()

            # Enviar actualización por WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "parqueadero_group",
                {
                    "type": "parqueadero_message",
                    "message": {
                        "id_parqueadero": str(parqueadero.id_parqueadero),
                        "matriz": parqueadero.matriz
                    }
                }
            )

            return Response({"message": "Matriz actualizada correctamente", "matriz": parqueadero.matriz}, status=status.HTTP_200_OK)

        except (IndexError, TypeError):
            return Response({"error": "Posición inválida en la matriz"}, status=status.HTTP_400_BAD_REQUEST)





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

        # Filtrar los datos para evitar la modificación de `filas` y `columnas`
        datos_modificables = {k: v for k, v in request.data.items() if k not in ['filas', 'columnas']}

        serializer = self.get_serializer(parqueadero, data=datos_modificables, context={'request': request}, partial=True)
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
from usuarios.models import Parqueadero

class ListaEspaciosDisponiblesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_parqueadero):
        # Bloquear acceso si el usuario no es un cliente
        if request.user.tipo_usuario != "Cliente":
            return Response({"error": "Solo los clientes pueden ver los espacios disponibles"}, status=status.HTTP_403_FORBIDDEN)

        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
        
        espacios_disponibles = []
        for fila_idx, fila in enumerate(parqueadero.matriz):
            for columna_idx, celda in enumerate(fila):
                if celda["estado"] == "Disponible":
                    espacios_disponibles.append({
                        "id_espacio": f"{parqueadero.id_parqueadero}-{fila_idx}-{columna_idx}",
                        "fila": fila_idx,
                        "columna": columna_idx,
                        "nombre": celda["nombre"]
                    })

        return Response({"espacios_disponibles": espacios_disponibles}, status=status.HTTP_200_OK)


class CargarMatrizBaseView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, id_parqueadero):
        try:
            parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
            
            # Verificar permisos
            if request.user != parqueadero.id_propietario:
                return Response(
                    {"error": "Solo el propietario puede cargar la matriz base"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Obtener la matriz actual
            matriz = parqueadero.matriz
            
            # Si la matriz está vacía, inicializarla
            if not matriz:
                matriz = [
                    [{
                        "nombre": f"P-{i+1}-{j+1}",
                        "tipo": "parqueo"  # Por defecto, todos los espacios son de parqueo
                    } for j in range(parqueadero.columnas)]
                    for i in range(parqueadero.filas)
                ]
                parqueadero.matriz = matriz
                parqueadero.save()

            return Response({
                "matriz": matriz,
                "filas": parqueadero.filas,
                "columnas": parqueadero.columnas
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error al cargar la matriz: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ModificarMatrizView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id_parqueadero):
        try:
            parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
            
            # Verificar que el usuario es propietario o admin
            if not (request.user.tipo_usuario == 'Admin' or 
                   request.user == parqueadero.propietario):
                return Response(
                    {'error': 'No tienes permiso para modificar este parqueadero'},
                    status=status.HTTP_403_FORBIDDEN
                )

            cambios = request.data.get('cambios', {})
            fila = cambios.get('fila')
            columna = cambios.get('columna')
            nuevo_tipo = cambios.get('tipo')

            if None in (fila, columna, nuevo_tipo):
                return Response(
                    {'error': 'Faltan datos requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar el tipo de espacio
            tipos_validos = ['parqueo', 'pasillo', 'obstruccion']
            if nuevo_tipo not in tipos_validos:
                return Response(
                    {'error': f'Tipo de espacio inválido. Debe ser uno de: {", ".join(tipos_validos)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Obtener la matriz actual
            matriz = parqueadero.matriz
            if not matriz or fila >= len(matriz) or columna >= len(matriz[0]):
                return Response(
                    {'error': 'Coordenadas de matriz inválidas'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Guardar el tipo anterior
            tipo_anterior = matriz[fila][columna]['tipo']

            # Actualizar el tipo de espacio
            matriz[fila][columna]['tipo'] = nuevo_tipo
            parqueadero.matriz = matriz
            
            # Guardar en la base de datos
            parqueadero.save()

            # Registrar el cambio en el historial
            CambioMatriz.objects.create(
                parqueadero=parqueadero,
                fila=fila,
                columna=columna,
                tipo_anterior=tipo_anterior,
                tipo_nuevo=nuevo_tipo,
                usuario=request.user
            )

            # Enviar actualización por WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "parqueadero_group",
                {
                    "type": "parqueadero_message",
                    "message": {
                        "id_parqueadero": str(parqueadero.id_parqueadero),
                        "matriz": parqueadero.matriz
                    }
                }
            )

            return Response({
                'mensaje': 'Tipo de espacio actualizado correctamente',
                'matriz': matriz,
                'ultima_actualizacion': parqueadero.updated_at if hasattr(parqueadero, 'updated_at') else None
            })

        except Parqueadero.DoesNotExist:
            return Response(
                {'error': 'Parqueadero no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, id_parqueadero):
        try:
            parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
            
            # Verificar que el usuario es propietario o admin
            if not (request.user.tipo_usuario == 'Admin' or 
                   request.user == parqueadero.propietario):
                return Response(
                    {'error': 'No tienes permiso para ver este parqueadero'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Obtener el historial de cambios
            cambios = CambioMatriz.objects.filter(parqueadero=parqueadero).order_by('-fecha_cambio')[:10]
            historial = [{
                'fila': cambio.fila,
                'columna': cambio.columna,
                'tipo_anterior': cambio.tipo_anterior,
                'tipo_nuevo': cambio.tipo_nuevo,
                'fecha': cambio.fecha_cambio,
                'usuario': cambio.usuario.email if cambio.usuario else None
            } for cambio in cambios]

            return Response({
                'matriz': parqueadero.matriz,
                'ultima_actualizacion': parqueadero.updated_at if hasattr(parqueadero, 'updated_at') else None,
                'historial_cambios': historial
            })

        except Parqueadero.DoesNotExist:
            return Response(
                {'error': 'Parqueadero no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ValidarEstructuraMatrizView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, id_parqueadero):
        try:
            parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
            
            # Verificar permisos
            if request.user != parqueadero.id_propietario:
                return Response(
                    {"error": "Solo el propietario puede validar la estructura"},
                    status=status.HTTP_403_FORBIDDEN
                )

            matriz = parqueadero.matriz
            errores = []
            espacios_invalidos = []

            def es_posicion_valida(fila, columna):
                return 0 <= fila < parqueadero.filas and 0 <= columna < parqueadero.columnas

            def obtener_tipo_espacio(fila, columna):
                if not es_posicion_valida(fila, columna):
                    return None
                return matriz[fila][columna].get('tipo')

            # Validar cada espacio de parqueo
            for i in range(parqueadero.filas):
                for j in range(parqueadero.columnas):
                    if matriz[i][j].get('tipo') == 'parqueo':
                        tiene_acceso = False
                        direcciones = [
                            (i-1, j), (i+1, j), (i, j-1), (i, j+1)
                        ]

                        # Verificar acceso a pasillos
                        for fila, columna in direcciones:
                            if (es_posicion_valida(fila, columna) and 
                                obtener_tipo_espacio(fila, columna) == 'pasillo'):
                                tiene_acceso = True
                                break

                        if not tiene_acceso:
                            errores.append({
                                'tipo': 'sin_acceso',
                                'mensaje': f'El espacio de parqueo en ({i+1},{j+1}) no tiene acceso a un pasillo',
                                'fila': i,
                                'columna': j
                            })
                            espacios_invalidos.append({'fila': i, 'columna': j})

            # Validar conectividad de pasillos
            pasillos = []
            for i in range(parqueadero.filas):
                for j in range(parqueadero.columnas):
                    if matriz[i][j].get('tipo') == 'pasillo':
                        pasillos.append((i, j))

            if pasillos:
                # Verificar que todos los pasillos estén conectados
                visitados = set()
                def dfs(fila, columna):
                    if not es_posicion_valida(fila, columna) or (fila, columna) in visitados:
                        return
                    if obtener_tipo_espacio(fila, columna) != 'pasillo':
                        return
                    visitados.add((fila, columna))
                    for df, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        dfs(fila + df, columna + dc)

                # Comenzar DFS desde el primer pasillo
                dfs(pasillos[0][0], pasillos[0][1])
                
                # Verificar si todos los pasillos fueron visitados
                if len(visitados) != len(pasillos):
                    errores.append({
                        'tipo': 'pasillos_desconectados',
                        'mensaje': 'Existen pasillos desconectados entre sí'
                    })

            return Response({
                'valido': len(errores) == 0,
                'errores': errores,
                'espacios_invalidos': espacios_invalidos
            })

        except Exception as e:
            return Response(
                {"error": f"Error al validar la estructura: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AplicarPatronMatrizView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, id_parqueadero):
        try:
            parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
            
            # Verificar permisos
            if request.user != parqueadero.id_propietario:
                return Response(
                    {"error": "Solo el propietario puede aplicar patrones"},
                    status=status.HTTP_403_FORBIDDEN
                )

            patron = request.data.get('patron')
            if not patron:
                return Response(
                    {"error": "El patrón es requerido"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Obtener la matriz actual
            matriz = parqueadero.matriz
            if not matriz:
                matriz = [[{"nombre": "", "tipo": "pasillo"} for _ in range(parqueadero.columnas)] 
                         for _ in range(parqueadero.filas)]

            # Aplicar el patrón seleccionado
            if patron == 'diagonal':
                for i in range(parqueadero.filas):
                    for j in range(parqueadero.columnas):
                        if (i + j) % 2 == 0:
                            matriz[i][j]['tipo'] = 'parqueo'
                        else:
                            matriz[i][j]['tipo'] = 'pasillo'

            elif patron == 'linea':
                for i in range(parqueadero.filas):
                    for j in range(parqueadero.columnas):
                        if j % 2 == 0:
                            matriz[i][j]['tipo'] = 'parqueo'
                        else:
                            matriz[i][j]['tipo'] = 'pasillo'

            elif patron == 'zigzag':
                for i in range(parqueadero.filas):
                    for j in range(parqueadero.columnas):
                        if (i + (j // 2)) % 2 == 0:
                            matriz[i][j]['tipo'] = 'parqueo'
                        else:
                            matriz[i][j]['tipo'] = 'pasillo'

            else:
                return Response(
                    {"error": "Patrón no válido. Use 'diagonal', 'linea' o 'zigzag'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Guardar la matriz actualizada
            parqueadero.matriz = matriz
            parqueadero.save()

            return Response({
                'mensaje': f'Patrón {patron} aplicado correctamente',
                'matriz': matriz
            })

        except Exception as e:
            return Response(
                {"error": f"Error al aplicar el patrón: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RellenarAreaMatrizView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, id_parqueadero):
        try:
            parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
            
            # Verificar permisos
            if request.user != parqueadero.id_propietario:
                return Response(
                    {"error": "Solo el propietario puede rellenar áreas"},
                    status=status.HTTP_403_FORBIDDEN
                )

            tipo = request.data.get('tipo')
            fila_inicio = request.data.get('fila_inicio')
            fila_fin = request.data.get('fila_fin')
            columna_inicio = request.data.get('columna_inicio')
            columna_fin = request.data.get('columna_fin')

            if None in (tipo, fila_inicio, fila_fin, columna_inicio, columna_fin):
                return Response(
                    {"error": "Todos los campos son requeridos"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar el tipo de espacio
            tipos_validos = ['parqueo', 'pasillo', 'obstruccion']
            if tipo not in tipos_validos:
                return Response(
                    {"error": f"Tipo inválido. Debe ser uno de: {', '.join(tipos_validos)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar rangos
            if not (0 <= fila_inicio <= fila_fin < parqueadero.filas and 
                    0 <= columna_inicio <= columna_fin < parqueadero.columnas):
                return Response(
                    {"error": "Rangos de filas o columnas inválidos"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Obtener la matriz actual
            matriz = parqueadero.matriz
            if not matriz:
                matriz = [[{"nombre": "", "tipo": "pasillo"} for _ in range(parqueadero.columnas)] 
                         for _ in range(parqueadero.filas)]

            # Rellenar el área seleccionada
            for i in range(fila_inicio, fila_fin + 1):
                for j in range(columna_inicio, columna_fin + 1):
                    matriz[i][j]['tipo'] = tipo

            # Guardar la matriz actualizada
            parqueadero.matriz = matriz
            parqueadero.save()

            return Response({
                'mensaje': 'Área rellenada correctamente',
                'matriz': matriz
            })

        except Exception as e:
            return Response(
                {"error": f"Error al rellenar el área: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GuardarMatrizCompletaView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, id_parqueadero):
        try:
            parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
            
            # Verificar permisos
            if request.user != parqueadero.id_propietario:
                return Response(
                    {"error": "Solo el propietario puede guardar la matriz completa"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Obtener la matriz del request
            matriz_completa = request.data.get('matriz')
            if not matriz_completa:
                return Response(
                    {"error": "La matriz es requerida"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar estructura de la matriz
            if not isinstance(matriz_completa, list) or len(matriz_completa) != parqueadero.filas:
                return Response(
                    {"error": "Estructura de matriz inválida"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for fila in matriz_completa:
                if not isinstance(fila, list) or len(fila) != parqueadero.columnas:
                    return Response(
                        {"error": "Estructura de matriz inválida"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                for celda in fila:
                    if not isinstance(celda, dict) or 'tipo' not in celda:
                        return Response(
                            {"error": "Formato de celda inválido"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    if celda['tipo'] not in ['parqueo', 'pasillo', 'obstruccion']:
                        return Response(
                            {"error": "Tipo de espacio inválido"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            # Guardar la matriz completa
            parqueadero.matriz = matriz_completa
            parqueadero.save()

            # Enviar actualización por WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "parqueadero_group",
                {
                    "type": "parqueadero_message",
                    "message": {
                        "id_parqueadero": str(parqueadero.id_parqueadero),
                        "matriz": parqueadero.matriz
                    }
                }
            )

            return Response({
                'mensaje': 'Matriz guardada correctamente',
                'redirect_url': f'/parqueadero/ver-matriz/{id_parqueadero}/'
            })

        except Exception as e:
            return Response(
                {"error": f"Error al guardar la matriz: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


