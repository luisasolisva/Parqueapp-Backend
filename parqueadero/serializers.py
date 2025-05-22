

from rest_framework import serializers
from usuarios.models import Parqueadero


class ParqueaderoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parqueadero
        fields = ['id_parqueadero', 'nombre', 'direccion', 'ciudad', 'latitud', 'longitud', 'precio_hora']






class CeldaSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=50, allow_blank=True)
    estado = serializers.ChoiceField(choices=["Disponible", "Ocupado", "Fuera_de_servicio"])

class MatrizSerializer(serializers.ModelSerializer):
    matriz = serializers.ListField(child=serializers.ListField(child=CeldaSerializer()))

    class Meta:
        model = Parqueadero
        fields = ['id_parqueadero', 'matriz']




class ParqueaderoSerializer(serializers.ModelSerializer):
    id_propietario = serializers.ReadOnlyField(source='id_propietario.email')  # Solo para mostrar

    class Meta:
        model = Parqueadero
        exclude = ['matriz']  # Excluir matriz del formulario

    def validate(self, data):
        user = self.context['request'].user
        if user.tipo_usuario != 'Admin':
            raise serializers.ValidationError("Solo los administradores pueden crear parqueaderos.")
        return data

    def create(self, validated_data):
        user = self.context['request'].user

        filas = validated_data.pop('filas', None)
        columnas = validated_data.pop('columnas', None)

        if filas is None or columnas is None:
            raise serializers.ValidationError("Los campos filas y columnas son obligatorios.")

        matriz = [
            [{"nombre": "", "estado": ""} for _ in range(columnas)]  # Estado y nombre vacíos
            for _ in range(filas)
        ]

        validated_data['matriz'] = matriz

        # Asignar propietario actual
        validated_data['id_propietario'] = user

        # Crear el parqueadero
        return Parqueadero.objects.create(filas=filas, columnas=columnas, **validated_data)
