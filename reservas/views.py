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

        # Obtener los espacios disponibles desde el modelo `EspacioParqueadero`
        espacios_disponibles = EspacioParqueadero.objects.filter(id_parqueadero=parqueadero, estado="Disponible")

        # Serializar los datos para enviarlos como respuesta
        data = [{
            "id_espacio": str(espacio.id_espacio),
            "numero_espacio": espacio.numero_espacio,
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
from usuarios.models import Reserva, EspacioParqueadero, Parqueadero
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
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.tipo_usuario != "Cliente":
            return Response({"error": "Solo los clientes pueden crear reservas."}, status=status.HTTP_403_FORBIDDEN)

        parqueadero = get_object_or_404(Parqueadero, id_parqueadero=id_parqueadero)
        espacio = get_object_or_404(EspacioParqueadero, id_espacio=id_espacio, id_parqueadero=parqueadero)

        if espacio.estado != "Disponible":
            return Response({"error": "El espacio seleccionado no está disponible."}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar disponibilidad en fecha y hora
        fecha_inicio = request.data.get("fecha_inicio")
        hora_inicio = request.data.get("hora_inicio")
        reservas_existentes = Reserva.objects.filter(id_espacio=espacio, fecha_inicio=fecha_inicio, hora_inicio=hora_inicio)

        if reservas_existentes.exists():
            return Response({"error": "Este espacio ya está reservado para la fecha y hora seleccionadas."}, status=status.HTTP_400_BAD_REQUEST)

        # Calcular el monto si no está presente
        horas_reservadas = (datetime.strptime(request.data["hora_fin"], "%H:%M:%S") - datetime.strptime(request.data["hora_inicio"], "%H:%M:%S")).seconds / 3600
        monto_total = round(horas_reservadas * float(parqueadero.precio_hora), 2)

        # Paso 1: Mostrar los detalles antes de la confirmación
        if not request.data.get("confirmar"):
            return Response({
                "mensaje": "Detalles de la reserva antes de confirmar.",
                "id_parqueadero": str(parqueadero.id_parqueadero),
                "nombre_parqueadero": parqueadero.nombre,
                "id_espacio": str(espacio.id_espacio),
                "fecha_inicio": fecha_inicio,
                "hora_inicio": hora_inicio,
                "fecha_fin": request.data["fecha_fin"],
                "hora_fin": request.data["hora_fin"],
                "monto_total": monto_total,
                "confirmar": False
            }, status=status.HTTP_200_OK)

        # Paso 2: Si el usuario confirma, se crea la reserva
        data = request.data.copy()
        data["cliente"] = request.user.id
        data["monto_total"] = monto_total

        serializer = ReservaSerializer(data=data)
        if serializer.is_valid():
            reserva = serializer.save(estado="Pendiente", monto_total=data["monto_total"])
            
            # ✅ Cambiamos el estado a "Confirmada" si el usuario confirmó la reserva
            if request.data.get("confirmar"):
                reserva.estado = "Confirmada"
                reserva.save(update_fields=["estado"])

            # ✅ Asignamos correctamente el QR en texto
            reserva.codigo_qr_texto = f"Reserva {reserva.id_reserva}"
            reserva.save(update_fields=["codigo_qr_texto"])  # ✅ Guardamos solo el código QR en la BD

            # Generar código QR como imagen
            qr_image = generar_qr(f"Reserva {reserva.id_reserva}")

            # Marcar el espacio como reservado
            espacio.estado = "Reservado"
            espacio.save()

            # Renderizar el correo HTML con los detalles
            email_html = render_to_string("correo_confirmacion.html", {
                "id_reserva": reserva.id_reserva,
                "monto_total": reserva.monto_total,
                "fecha_inicio": reserva.fecha_inicio,
                "hora_inicio": reserva.hora_inicio,
                "nombre_parqueadero": parqueadero.nombre,
            })

            # Crear correo con HTML
            email = EmailMessage(
                "Confirmación de reserva",
                email_html,
                "parqueappreservas@gmail.com",
                [request.user.email],
            )
            email.content_subtype = "html"

            # Adjuntar la imagen QR
            image_attachment = MIMEImage(qr_image)
            image_attachment.add_header("Content-ID", "<qr_reserva>")
            email.attach(image_attachment)

            email.send()

            return Response({
                "mensaje": "Reserva creada exitosamente",
                "id_reserva": str(reserva.id_reserva),
                "estado": reserva.estado  # ✅ Confirmamos el estado de la reserva en la respuesta
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from datetime import datetime
from django.core.mail import send_mail

class CancelarReservaView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id_reserva):
        reserva = get_object_or_404(Reserva, id_reserva=id_reserva)

        if reserva.cliente != request.user:
            return Response({"error": "Solo el dueño de la reserva puede cancelarla."}, status=status.HTTP_403_FORBIDDEN)

        # Obtener fecha y hora actual
        ahora = datetime.now()

        # Combinar fecha y hora de la reserva
        hora_inicio_reserva = datetime.combine(reserva.fecha_inicio, reserva.hora_inicio)

        # Comparar fecha y hora completas
        if ahora >= hora_inicio_reserva:
            return Response({"error": "No puedes cancelar una reserva después de la hora de inicio."}, status=status.HTTP_400_BAD_REQUEST)

        # Lógica de cancelación
        reserva.id_espacio.estado = "Disponible"
        reserva.id_espacio.save()
        reserva.estado = "Cancelada"
        reserva.save()

        # Enviar correo de cancelación
        send_mail(
            "Cancelación de reserva",
            f"Tu reserva ha sido cancelada.\nID: {reserva.id_reserva}",
            "parqueappreservas@gmail.com",
            [request.user.email],
            fail_silently=False,
        )

        return Response({"mensaje": "Reserva cancelada exitosamente."}, status=status.HTTP_200_OK)











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
