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
from io import BytesIO
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from email.mime.image import MIMEImage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from usuarios.models import Reserva, EspacioParqueadero, Parqueadero, Vehiculo
from .serializers import ReservaSerializer

def generar_qr(texto):
    """Genera un código QR en formato de imagen."""
    qr = qrcode.make(texto)
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

        # ✅ Corrección 1: Validar que el espacio esté disponible antes de cualquier otro proceso
        if espacio.estado != "Disponible":
            return Response({"error": "El espacio seleccionado no está disponible."}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener datos del vehículo
        placa = request.data.get("placa")
        marca = request.data.get("marca")
        modelo = request.data.get("modelo")
        color = request.data.get("color")
        tipo_vehiculo = request.data.get("tipo_vehiculo")

        if not all([placa, marca, modelo, color, tipo_vehiculo]):
            return Response({"error": "Debes proporcionar todos los datos del vehículo."}, status=status.HTTP_400_BAD_REQUEST)

        vehiculo = Vehiculo.objects.create(
            id_usuario=request.user,
            placa=placa,
            marca=marca,
            modelo=modelo,
            color=color,
            tipo_vehiculo=tipo_vehiculo
        )

        # Validar formato de hora (AM/PM)
        try:
            fecha_inicio = request.data.get("fecha_inicio")
            fecha_fin = request.data.get("fecha_fin")

            # ✅ Corrección 2: Ahora el usuario ingresa la hora en AM/PM
            hora_inicio = datetime.strptime(request.data.get("hora_inicio"), "%I:%M %p").time()
            hora_fin = datetime.strptime(request.data.get("hora_fin"), "%I:%M %p").time()
        except ValueError:
            return Response({"error": "Formato de hora incorrecto. Usa 'HH:MM AM/PM'."}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar disponibilidad en fecha y hora
        reservas_existentes = Reserva.objects.filter(id_espacio=espacio, fecha_inicio=fecha_inicio, hora_inicio=hora_inicio)
        if reservas_existentes.exists():
            return Response({"error": "Este espacio ya está reservado para la fecha y hora seleccionadas."}, status=status.HTTP_400_BAD_REQUEST)

        # Calcular monto total
        horas_reservadas = (datetime.combine(datetime.today(), hora_fin) - datetime.combine(datetime.today(), hora_inicio)).seconds / 3600
        monto_total = round(horas_reservadas * float(parqueadero.precio_hora), 2)

        # Mostrar detalles antes de confirmar
        if not request.data.get("confirmar"):
            return Response({
                "mensaje": "Detalles de la reserva antes de confirmar.",
                "placa": vehiculo.placa,
                "marca": vehiculo.marca,
                "modelo": vehiculo.modelo,
                "color": vehiculo.color,
                "tipo_vehiculo": vehiculo.tipo_vehiculo,
                "fecha_inicio": fecha_inicio,
                "hora_inicio": request.data.get("hora_inicio"),  # ✅ Se mantiene como ingresó el usuario
                "fecha_fin": fecha_fin,
                "hora_fin": request.data.get("hora_fin"),  # ✅ Se mantiene como ingresó el usuario
                "monto_total": monto_total,
                "confirmar": False
            }, status=status.HTTP_200_OK)

        # Crear reserva
        data = request.data.copy()
        data["cliente"] = request.user.id
        data["monto_total"] = monto_total
        data["vehiculo"] = vehiculo.id_vehiculo
        data["id_parqueadero"] = id_parqueadero  # ✅ Se toma de la URL
        data["id_espacio"] = id_espacio  # ✅ Se toma de la URL
        data["hora_inicio"] = hora_inicio  # ✅ Se almacena correctamente
        data["hora_fin"] = hora_fin  # ✅ Se almacena correctamente

        serializer = ReservaSerializer(data=data)
        if serializer.is_valid():
            reserva = serializer.save(estado="Confirmada")

            # Marcar espacio como reservado
            espacio.estado = "Reservado"
            espacio.save()

            # Generar código QR
            reserva.codigo_qr_texto = f"Reserva {reserva.id_reserva}"
            reserva.save(update_fields=["codigo_qr_texto"])
            qr_image = generar_qr(f"Reserva {reserva.id_reserva}")

            # Enviar correo de confirmación
            email_html = render_to_string("correo_confirmacion.html", {
                "id_reserva": reserva.id_reserva,
                "monto_total": reserva.monto_total,
                "fecha_inicio": reserva.fecha_inicio,
                "hora_inicio": request.data.get("hora_inicio"),  # ✅ Se usa el valor ingresado por el usuario
                "nombre_parqueadero": parqueadero.nombre,
            })

            email = EmailMessage(
                "Confirmación de reserva",
                email_html,
                "parqueappreservas@gmail.com",
                [request.user.email],
            )
            email.content_subtype = "html"
            image_attachment = MIMEImage(qr_image)
            image_attachment.add_header("Content-ID", "<qr_reserva>")
            email.attach(image_attachment)
            email.send()

            return Response({
                "mensaje": "Reserva creada exitosamente",
                "id_reserva": str(reserva.id_reserva),
                "estado": reserva.estado
            }, status=status.HTTP_201_CREATED)

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

        # Renderizar el correo HTML
        email_html = render_to_string("correo_cancelacion.html", {
            "nombre_usuario": request.user.nombre,  # ✅ Usa `nombre` en lugar de `username`
            "id_reserva": reserva.id_reserva,
            "espacio": reserva.id_espacio.espacio,  # ✅ Usa el campo correcto
            "fecha_inicio": reserva.fecha_inicio,
            "hora_inicio": reserva.hora_inicio,
            "motivo": motivo
        })
        

        return Response({
            "mensaje": "Reserva cancelada exitosamente.",
            "id_reserva": str(reserva.id_reserva),
            "espacio_liberado": reserva.id_espacio.espacio,  # ✅ Usa `espacio`, no `numero_espacio`
            "motivo": motivo
        }, status=status.HTTP_200_OK)
        email_plaintext = strip_tags(email_html)  

        send_mail(
            "Cancelación de reserva",
            email_plaintext,  
            "parqueappreservas@gmail.com",
            [request.user.email],
            html_message=email_html,  
            fail_silently=False,
        )

        return Response({
            "mensaje": "Reserva cancelada exitosamente.",
            "id_reserva": str(reserva.id_reserva),
            "espacio_liberado": reserva.id_espacio.numero_espacio,
            "motivo": motivo
        }, status=status.HTTP_200_OK)





class DetalleReservaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_reserva) :   # Obtener la reserva del usuario autenticado
        reserva = get_object_or_404(Reserva, id_reserva=id_reserva, cliente=request.user)

        # Serializar los datos
        serializer = ReservaSerializer(reserva)

        return Response(serializer.data, status=status.HTTP_200_OK)





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