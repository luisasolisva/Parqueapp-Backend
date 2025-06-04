
from rest_framework import serializers
from usuarios.models import Reserva

class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = [
            "id_reserva", "cliente", "id_parqueadero", "id_espacio",
            "fecha_inicio", "hora_inicio", "fecha_fin", "hora_fin",
            "estado", "placa", "color", "modelo", "tipo_vehiculo",
            "monto_total"
        ]
        read_only_fields = ["id_reserva", "estado", "monto_total"]




class ReservaDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = "__all__"  # ✅ Incluye todos los datos de la reserva



class EspacioDisponibleSerializer(serializers.Serializer):
    fila = serializers.IntegerField()
    columna = serializers.IntegerField()
    espacio = serializers.CharField(max_length=50)  # Nombre del espacio
    estado = serializers.ChoiceField(choices=["Disponible", "Ocupado", "Fuera_de_servicio"])

