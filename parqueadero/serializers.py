from rest_framework import serializers
from .models import Reserva

class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = '__all__'
        read_only_fields = ['id_usuario', 'estado', 'monto_total']  # Automáticamente se pone el usuario autenticado

    def validate(self, data):
        # Validaciones como fecha/hora de inicio menor a fin, etc.
        if data['fecha_inicio'] > data['fecha_fin']:
            raise serializers.ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")

        if data['fecha_inicio'] == data['fecha_fin'] and data['hora_inicio'] >= data['hora_fin']:
            raise serializers.ValidationError("La hora de inicio debe ser anterior a la hora de fin.")

        return data
