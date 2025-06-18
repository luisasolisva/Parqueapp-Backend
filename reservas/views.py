from django.shortcuts import render

# Create your views here.

    
    
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

        # ✅ Ajuste: Filtrar por `mapa__parqueadero_id` en lugar de `id_parqueadero`
        espacios_disponibles = EspacioParqueadero.objects.filter(mapa__parqueadero=id_parqueadero, estado="Disponible")

        # Serializar los datos correctamente
        data = [{
            "id_espacio": str(espacio.id_espacio),
            "fila": espacio.fila,
            "columna": espacio.columna,
            "espacio": espacio.espacio,
            "estado": espacio.estado
        } for espacio in espacios_disponibles]

        return Response({"espacios_disponibles": data}, status=status.HTTP_200_OK)




from datetime import datetime
import qrcode
import base64
from email.mime.image import MIMEImage
from django.core.mail import EmailMultiAlternatives
from io import BytesIO
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from usuarios.models import Reserva, EspacioParqueadero, Parqueadero, Vehiculo, ImagenParqueadero
from .serializers import ReservaSerializer


def generar_qr(url):
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return buffer.getvalue()


class CrearReservaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id_parqueadero, id_espacio):
        if request.user.tipo_usuario != "Cliente":
            return Response({"error": "Solo los clientes pueden hacer reservas."}, status=status.HTTP_403_FORBIDDEN)

        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
        espacio = get_object_or_404(EspacioParqueadero, id_espacio=id_espacio, mapa__parqueadero=parqueadero)

        if espacio.estado != "Disponible":
            return Response({"error": "El espacio seleccionado no está disponible."}, status=status.HTTP_400_BAD_REQUEST)

        errores = {}
        datos_requeridos = ["placa", "marca", "modelo", "color", "tipo_vehiculo", "fecha_inicio", "fecha_fin", "hora_inicio", "hora_fin"]
        for campo in datos_requeridos:
            if not request.data.get(campo):
                errores[campo] = f"El campo '{campo}' es obligatorio."
        if errores:
            return Response({"error": "Faltan datos obligatorios en la reserva.", "detalles": errores}, status=status.HTTP_400_BAD_REQUEST)

        try:
            hora_inicio = datetime.strptime(request.data.get("hora_inicio"), "%I:%M %p").time()
            hora_fin = datetime.strptime(request.data.get("hora_fin"), "%I:%M %p").time()
        except ValueError:
            return Response({"error": "Formato de hora incorrecto. Usa 'HH:MM AM/PM'."}, status=status.HTTP_400_BAD_REQUEST)

        confirmar_reserva = request.data.get("confirmar", False)

        fecha_inicio = datetime.strptime(request.data.get("fecha_inicio"), "%Y-%m-%d")
        fecha_fin = datetime.strptime(request.data.get("fecha_fin"), "%Y-%m-%d")

        fecha_hora_inicio = datetime.combine(fecha_inicio, hora_inicio)
        fecha_hora_fin = datetime.combine(fecha_fin, hora_fin)

        reservas_cruzadas = Reserva.objects.filter(
            cliente=request.user,
            estado__in=["Pendiente", "Confirmada"],
            fecha_inicio__lte=fecha_fin,
            fecha_fin__gte=fecha_inicio
        ).exclude(
            hora_inicio__gte=hora_fin
        ).exclude(
            hora_fin__lte=hora_inicio
        )

        if reservas_cruzadas.exists():
            return Response({
                "error": "Ya tienes una reserva que se cruza en horario con la que estás intentando hacer.",
                "reservas_cruzadas": list(reservas_cruzadas.values(
                    "id_reserva", "fecha_inicio", "fecha_fin", "hora_inicio", "hora_fin", "id_parqueadero__nombre"
                ))
            }, status=status.HTTP_400_BAD_REQUEST)

        duracion_horas = (fecha_hora_fin - fecha_hora_inicio).total_seconds() / 3600
        monto_total_calculado = round(duracion_horas * float(parqueadero.precio_hora), 2)

        imagenes = [
            request.build_absolute_uri(imagen.imagen.url)
            for imagen in ImagenParqueadero.objects.filter(parqueadero=parqueadero)
            if imagen.imagen
        ]

        if not confirmar_reserva:
            return Response({
                "mensaje": "Detalles de la reserva antes de confirmar.",
                "fecha_inicio": request.data.get("fecha_inicio"),
                "fecha_fin": request.data.get("fecha_fin"),
                "hora_inicio": request.data.get("hora_inicio"),
                "hora_fin": request.data.get("hora_fin"),
                "parqueadero": parqueadero.nombre,
                "direccion": parqueadero.direccion,
                "imagen": imagenes,
                "plaza": espacio.espacio,
                "monto_total": monto_total_calculado,
                "confirmar": False
            }, status=status.HTTP_200_OK)

        vehiculo = Vehiculo.objects.create(
            id_usuario=request.user,
            placa=request.data.get("placa"),
            marca=request.data.get("marca"),
            modelo=request.data.get("modelo"),
            color=request.data.get("color"),
            tipo_vehiculo=request.data.get("tipo_vehiculo")
        )

        data = request.data.copy()
        data["cliente"] = request.user.id
        data["monto_total"] = monto_total_calculado
        data["vehiculo"] = vehiculo.id_vehiculo
        data["id_parqueadero"] = id_parqueadero
        data["id_espacio"] = id_espacio
        data["hora_inicio"] = hora_inicio
        data["hora_fin"] = hora_fin

        serializer = ReservaSerializer(data=data)
        if serializer.is_valid():
            reserva = serializer.save(estado="Confirmada")
            reserva.monto_total = monto_total_calculado
            reserva.save(update_fields=["monto_total"])

            url_qr = f"http://127.0.0.1:8000/api/reservas/validar-qr/{reserva.token_qr}/"
            qr_image = generar_qr(url_qr)
            qr_buffer = BytesIO(qr_image)

            subject = "Confirmación de Reserva - ParqueApp"
            message_html = render_to_string("reserva_confirmada.html", {
                "usuario": request.user,
                "reserva": reserva,
                "parqueadero": parqueadero,
                "espacio": reserva.id_espacio,
                "monto_total": reserva.monto_total
            })

            email = EmailMultiAlternatives(
                subject=subject,
                body='',
                from_email="parqueappreservas@gmail.com",
                to=[request.user.email]
            )
            email.attach_alternative(message_html, "text/html")
            qr_image = MIMEImage(qr_buffer.getvalue(), _subtype="png")
            qr_image.add_header("Content-ID", "<qr_code>")
            qr_image.add_header("Content-Disposition", "inline", filename="qr_code.png")
            email.mixed_subtype = 'related'
            email.attach(qr_image)
            email.send(fail_silently=False)

            espacio.estado = "Reservado"
            espacio.save()

            return Response({"mensaje": "Reserva creada exitosamente"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from usuarios.models import Reserva, EspacioParqueadero, Cancelacion

class CancelarReservaView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id_reserva):
        reserva = get_object_or_404(Reserva, id_reserva=id_reserva)

        if reserva.cliente != request.user:
            return Response({"error": "Solo el dueño de la reserva puede cancelarla."}, status=status.HTTP_403_FORBIDDEN)

        ahora = timezone.now()
        hora_inicio_reserva = timezone.make_aware(datetime.combine(reserva.fecha_inicio, reserva.hora_inicio))

        if ahora >= hora_inicio_reserva:
            return Response({"error": "No puedes cancelar una reserva después de la hora de inicio."}, status=status.HTTP_400_BAD_REQUEST)

        # Validar que el usuario haya enviado un motivo de cancelación
        motivo = request.data.get("motivo", "").strip()
        if not motivo:
            return Response({"error": "Debes proporcionar un motivo para la cancelación."}, status=status.HTTP_400_BAD_REQUEST)

        # Registrar la cancelación en el modelo Cancelacion
        Cancelacion.objects.create(
            id_reserva=reserva,
            id_usuario=request.user,
            motivo=motivo
        )

        # Cancelar reserva y liberar espacio
        reserva.estado = "Cancelada"
        reserva.save(update_fields=["estado"])
        EspacioParqueadero.objects.filter(id_espacio=reserva.id_espacio.id_espacio).update(estado="Disponible")

        # ✅ Mover el envío de correo antes del `return Response()`
        try:
            email_html = render_to_string("correo_cancelacion.html", {
                "nombre_usuario": request.user.nombre,
                "numero_reserva": reserva.numero_reserva,  # ✅ Ahora usa el número de reserva
                "espacio": reserva.id_espacio.espacio,
                "fecha_inicio": reserva.fecha_inicio.strftime("%d de %B de %Y"),  # ✅ Formato más claro
                "hora_inicio": reserva.hora_inicio.strftime("%I:%M %p"), 
                "motivo": motivo
            })
            email_plaintext = strip_tags(email_html)  # ✅ Convertir HTML a texto plano

            send_mail(
                "Cancelación de reserva",
                email_plaintext,
                "parqueappreservas@gmail.com",
                [request.user.email],
                html_message=email_html,
                fail_silently=False,
            )
        except Exception as e:
            return Response({"error": f"No se pudo enviar el correo de cancelación: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "mensaje": "Reserva cancelada exitosamente.",
            "id_reserva": str(reserva.id_reserva),
            "espacio_liberado": reserva.id_espacio.espacio,
            "motivo": motivo
        }, status=status.HTTP_200_OK)




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from usuarios.models import Reserva, ImagenParqueadero

class DetalleReservaView(APIView):
    def get(self, request, id_reserva):
        reserva = get_object_or_404(Reserva, id_reserva=id_reserva)
        parqueadero = reserva.id_parqueadero

        imagenes = [
            request.build_absolute_uri(imagen.imagen.url)
            for imagen in ImagenParqueadero.objects.filter(parqueadero=parqueadero)
            if imagen.imagen
        ]

        datos = {
            "fecha_inicio": reserva.fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_fin": reserva.fecha_fin.strftime("%Y-%m-%d"),
            "hora_inicio": reserva.hora_inicio.strftime("%I:%M %p"),
            "hora_fin": reserva.hora_fin.strftime("%I:%M %p"),
            "plaza": reserva.id_espacio.espacio,
            "monto_total": float(reserva.monto_total),
            "parqueadero": parqueadero.nombre,
            "direccion": parqueadero.direccion,
            "imagen": imagenes
        }

        return Response(datos, status=status.HTTP_200_OK)


from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from usuarios.models import Reserva, Parqueadero
from .serializers import ReservaDetalleSerializer

class ReservasParqueaderoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_parqueadero):
        # Obtener el parqueadero
        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)

        # Verificar que el usuario es dueño o un operario del parqueadero
        es_admin = request.user.is_superuser  # Si es admin global
        es_propietario = parqueadero.propietario == request.user  # Si es el dueño
        es_operario = request.user.tipo_usuario == "Operario" and request.user.parqueadero_asignado == parqueadero

        if not (es_admin or es_propietario or es_operario):
            return Response({"error": "No tienes permisos para ver reservas de este parqueadero."}, status=status.HTTP_403_FORBIDDEN)

        # Obtener reservas del parqueadero
        reservas = Reserva.objects.filter(id_parqueadero=parqueadero)
        serializer = ReservaDetalleSerializer(reservas, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)





from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from usuarios.models import Reserva
from reservas.utils import extraer_codigo_qr  # ✅ Importa la función de lectura QR

class ValidarReservaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # ✅ Recibir la imagen del QR
        imagen_qr = request.FILES.get("qr_imagen")

        if not imagen_qr:
            return Response({"error": "Imagen del código QR no proporcionada."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Convertir imagen en texto
        codigo_qr_texto = extraer_codigo_qr(imagen_qr)

        if not codigo_qr_texto:
            return Response({"error": "No se pudo leer el código QR."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Buscar la reserva asociada al código QR
        reserva = get_object_or_404(Reserva, codigo_qr_texto=codigo_qr_texto)

        # ✅ Validar si la reserva está activa
        if reserva.estado != "Confirmada":
            return Response({"error": f"La reserva no es válida para el acceso. Estado: {reserva.estado}"}, status=status.HTTP_403_FORBIDDEN)

        # ✅ Permitir el acceso
        return Response({
            "mensaje": "Acceso permitido.",
            "id_reserva": str(reserva.id_reserva),
            "cliente": reserva.cliente.email,
            "fecha_inicio": reserva.fecha_inicio,
            "hora_inicio": reserva.hora_inicio,
            "estado": reserva.estado
        }, status=status.HTTP_200_OK)









from django.template.loader import render_to_string
from django.utils.html import strip_tags

class ModificarReservaView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id_reserva):
        reserva = get_object_or_404(Reserva, id_reserva=id_reserva)

        if reserva.cliente != request.user:
            return Response({"error": "Solo el dueño de la reserva puede modificarla."}, status=status.HTTP_403_FORBIDDEN)

        ahora = timezone.now()
        hora_inicio_reserva = timezone.make_aware(datetime.combine(reserva.fecha_inicio, reserva.hora_inicio))
        if ahora >= hora_inicio_reserva:
            return Response({"error": "No puedes modificar una reserva después de la hora de inicio."}, status=status.HTTP_400_BAD_REQUEST)

        nueva_fecha = request.data.get("fecha_inicio")
        nueva_hora = request.data.get("hora_inicio")
        nuevo_espacio_id = request.data.get("nuevo_espacio")

        if nuevo_espacio_id:
            nuevo_espacio = get_object_or_404(EspacioParqueadero, id_espacio=nuevo_espacio_id)
            if nuevo_espacio.estado != "Disponible":
                return Response({"error": f"El espacio {nuevo_espacio.numero_espacio} no está disponible."}, status=status.HTTP_400_BAD_REQUEST)

            reserva.id_espacio.estado = "Disponible"
            reserva.id_espacio.save()
            reserva.id_espacio = nuevo_espacio
            reserva.id_espacio.estado = "Ocupado"
            reserva.id_espacio.save()

        if nueva_fecha:
            reserva.fecha_inicio = nueva_fecha
        if nueva_hora:
            reserva.hora_inicio = nueva_hora

        reserva.save()

        # Renderizar el correo HTML
        email_html = render_to_string("correo_modificacion.html", {
            "username": request.user.username,
            "id_reserva": reserva.id_reserva,
            "nuevo_espacio": reserva.id_espacio.numero_espacio,
            "nueva_fecha": reserva.fecha_inicio,
            "nueva_hora": reserva.hora_inicio,
        })
        email_plaintext = strip_tags(email_html)  

        send_mail(
            "Modificación de reserva",
            email_plaintext,  
            "parqueappreservas@gmail.com",
            [request.user.email],
            html_message=email_html,  
            fail_silently=False,
        )

        return Response({
            "mensaje": "Reserva modificada exitosamente.",
            "id_reserva": str(reserva.id_reserva),
            "nuevo_espacio": reserva.id_espacio.numero_espacio,
            "nueva_fecha": reserva.fecha_inicio,
            "nueva_hora": reserva.hora_inicio
        }, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from usuarios.models import Parqueadero, MapaParqueadero, EspacioParqueadero, Reserva
from datetime import datetime
from django.utils import timezone

# ✅ Parser universal de horas
def parse_hora(hora_str):
    formatos = ["%H:%M", "%I:%M %p", "%H:%M:%S"]
    for formato in formatos:
        try:
            return datetime.strptime(hora_str, formato).time()
        except ValueError:
            continue
    raise ValueError("Formato de hora inválido")

class MapaDisponibilidadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_parqueadero):
        ROLES_PERMITIDOS = ["Cliente", "Operario"]
        if request.user.tipo_usuario not in ROLES_PERMITIDOS:
            return Response({"error": "No tienes permisos para consultar los espacios."}, status=status.HTTP_403_FORBIDDEN)

        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
        mapa = get_object_or_404(MapaParqueadero, parqueadero=parqueadero)

        fecha_str = request.query_params.get("fecha")
        hora_str = request.query_params.get("hora")

        if not fecha_str or not hora_str:
            return Response({"error": "Debes enviar fecha y hora."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            hora = parse_hora(hora_str)
            fecha_hora_consulta = timezone.make_aware(datetime.combine(fecha, hora))
        except ValueError:
            return Response({"error": "Formato de fecha u hora inválido."}, status=status.HTTP_400_BAD_REQUEST)

        espacios = EspacioParqueadero.objects.filter(mapa=mapa)

        resultado = []
        for espacio in espacios:
            estado_actual = "disponible"

            if espacio.estado == "Deshabilitado":
                estado_actual = "deshabilitado"
            else:
                # Buscamos reservas activas de ese espacio para ese día
                reservas = Reserva.objects.filter(
                    id_espacio=espacio,
                    estado__in=["Pendiente", "Confirmada"],
                    fecha_inicio__lte=fecha,
                    fecha_fin__gte=fecha
                )

                conflicto = False
                for reserva in reservas:
                    inicio = timezone.make_aware(datetime.combine(reserva.fecha_inicio, reserva.hora_inicio))
                    fin = timezone.make_aware(datetime.combine(reserva.fecha_fin, reserva.hora_fin))
                    if inicio <= fecha_hora_consulta <= fin:
                        conflicto = True
                        break

                if conflicto:
                    estado_actual = "ocupado"

            resultado.append({
                "id_espacio": str(espacio.id_espacio),
                "fila": espacio.fila,
                "columna": espacio.columna,
                "espacio": espacio.espacio,
                "estado": estado_actual
            })

        return Response({
            "mapaParqueadero": {
                "mapaSize": {"filas": mapa.filas, "columnas": mapa.columnas},
                "nomenclatura": mapa.nomenclatura,
                "espacios": resultado
            }
        }, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from usuarios.models import Reserva, Parqueadero, ImagenParqueadero
from django.shortcuts import get_object_or_404

class ReservasClienteView(APIView):
    def get(self, request, id_cliente):
        reservas = Reserva.objects.filter(
            cliente__id=id_cliente,
            estado__in=["Confirmada", "Finalizada"]
        ).select_related("id_parqueadero")

        resultado = []

        for reserva in reservas:
            parqueadero = reserva.id_parqueadero

            # Obtener todas las URLs absolutas de las imágenes asociadas al parqueadero
            imagenes = [
                request.build_absolute_uri(imagen.imagen.url)
                for imagen in ImagenParqueadero.objects.filter(parqueadero=parqueadero)
                if imagen.imagen
            ]

            resultado.append({
                "id_reserva": str(reserva.id_reserva),
                #"id_parqueadero": str(parqueadero.id_parqueadero),
                "nombre_parqueadero": parqueadero.nombre,
                "direccion": parqueadero.direccion,
                "imagen": imagenes,  # Lista de URLs absolutas
                "fecha_reserva": reserva.fecha_inicio.strftime("%Y-%m-%d"),
                "estado": "Activa" if reserva.estado == "Confirmada" else "Pasada"
            })

        return Response(resultado, status=status.HTTP_200_OK)
    

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from usuarios.models import Reserva
from django.shortcuts import get_object_or_404
from django.utils import timezone

class ValidarQRView(APIView):
    def get(self, request, token_qr):
        reserva = get_object_or_404(Reserva, token_qr=token_qr)

        if not reserva.qr_usado_entrada:
            reserva.qr_usado_entrada = True
            reserva.estado = "En Curso"
            reserva.save(update_fields=["qr_usado_entrada", "estado"])
            return Response({
                "mensaje": "QR validado para entrada. La reserva está en curso.",
                "redirigir_a": "https://tusitio.com/frontend/reserva/entrada"  # cambia esta URL
            }, status=status.HTTP_200_OK)

        elif not reserva.qr_usado_salida:
            reserva.qr_usado_salida = True
            reserva.estado = "Finalizada"
            reserva.save(update_fields=["qr_usado_salida", "estado"])
            return Response({
                "mensaje": "QR validado para salida. La reserva ha finalizado.",
                "redirigir_a": "https://tusitio.com/frontend/reserva/salida"  # cambia esta URL
            }, status=status.HTTP_200_OK)

        else:
            return Response({
                "mensaje": "Este QR ya fue utilizado para entrada y salida.",
                "estado": reserva.estado
            }, status=status.HTTP_400_BAD_REQUEST)


class QRReservaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_reserva):
        reserva = get_object_or_404(Reserva, id_reserva=id_reserva, cliente=request.user)
        url_qr = f"https://tusitio.com/api/reservas/validar-qr/{reserva.token_qr}/"
        return Response({
            "url_qr": url_qr
        })


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime
import pytz

from usuarios.models import Parqueadero, MapaParqueadero, EspacioParqueadero, Reserva, Usuario

# ... (importaciones y clase sin cambios hasta aquí)

class MapaDisponibilidadOperarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.tipo_usuario != "Operario":
            return Response({"error": "Solo los operarios pueden consultar este recurso."}, status=status.HTTP_403_FORBIDDEN)

        operario = request.user
        parqueadero = operario.parqueadero_asignado

        if not parqueadero:
            return Response({"error": "El operario no tiene un parqueadero asignado."}, status=status.HTTP_400_BAD_REQUEST)

        mapa = get_object_or_404(MapaParqueadero, parqueadero=parqueadero)

        colombia_tz = pytz.timezone("America/Bogota")
        ahora_colombia = timezone.now().astimezone(colombia_tz)
        fecha = ahora_colombia.date()
        hora = ahora_colombia.time()
        fecha_hora_consulta = ahora_colombia

        espacios = EspacioParqueadero.objects.filter(mapa=mapa)
        resultado = []

        # 👉 Inicializamos contadores
        disponibles = 0
        ocupados = 0
        deshabilitados = 0

        for espacio in espacios:
            estado_actual = "disponible"

            if espacio.estado == "Deshabilitado":
                estado_actual = "deshabilitado"
                deshabilitados += 1
            else:
                reservas = Reserva.objects.filter(
                    id_espacio=espacio,
                    estado__in=["Pendiente", "Confirmada"],
                    fecha_inicio__lte=fecha,
                    fecha_fin__gte=fecha
                )

                conflicto = any(
                    timezone.make_aware(datetime.combine(r.fecha_inicio, r.hora_inicio)) <= fecha_hora_consulta <=
                    timezone.make_aware(datetime.combine(r.fecha_fin, r.hora_fin))
                    for r in reservas
                )

                if conflicto:
                    estado_actual = "ocupado"
                    ocupados += 1
                else:
                    disponibles += 1

            resultado.append({
                "id_espacio": str(espacio.id_espacio),
                "fila": espacio.fila,
                "columna": espacio.columna,
                "espacio": espacio.espacio,
                "estado": estado_actual
            })

        return Response({
            "mapaParqueadero": {
                "mapaSize": {"filas": mapa.filas, "columnas": mapa.columnas},
                "nomenclatura": mapa.nomenclatura,
                "espacios": resultado
            },
            "fecha_actual": fecha.isoformat(),
            "hora_actual": hora.strftime("%H:%M"),
            "estadisticas": {
                "disponibles": disponibles,
                "ocupados": ocupados,
                "deshabilitados": deshabilitados
            }
        }, status=status.HTTP_200_OK)
