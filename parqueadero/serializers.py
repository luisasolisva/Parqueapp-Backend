from rest_framework import serializers
from usuarios.models import Reserva


class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = '__all__'  # o define los campos uno a uno si prefieres

    def validate(self, data):
        # Validar que fecha/hora de inicio sea menor a la de fin
        fecha_inicio = data.get('fecha_inicio')
        hora_inicio = data.get('hora_inicio')
        fecha_fin = data.get('fecha_fin')
        hora_fin = data.get('hora_fin')

        if (fecha_inicio, hora_inicio) >= (fecha_fin, hora_fin):
            raise serializers.ValidationError("La fecha y hora de inicio deben ser anteriores a la de fin.")
        return data
