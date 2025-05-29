

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

class EspacioDisponibleSerializer(serializers.Serializer):
    fila = serializers.IntegerField()
    columna = serializers.IntegerField()
    espacio = serializers.CharField(max_length=50)  # Nombre del espacio
    estado = serializers.ChoiceField(choices=["Disponible", "Ocupado", "Fuera_de_servicio"])



from rest_framework import serializers
from usuarios.models import Parqueadero

class RegistrarParqueaderoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parqueadero
        fields = ['id_parqueadero', 'nombre', 'direccion', 'ciudad', 'latitud', 'longitud', 'precio_hora', 'capacidad_total','nombre_propietario', 'descripcion']

    def validate(self, data):
        user = self.context['request'].user
        if user.tipo_usuario != 'Admin':
            raise serializers.ValidationError("Solo los administradores pueden registrar parqueaderos.")
        return data

    def create(self, validated_data):
        return Parqueadero.objects.create(**validated_data)




class EstadisticasAdminSerializer(serializers.Serializer):
    total_clientes = serializers.IntegerField()
    total_reservas = serializers.IntegerField()
    reservas_confirmadas = serializers.IntegerField()
    reservas_canceladas = serializers.IntegerField()
    ingresos_totales = serializers.DecimalField(max_digits=10, decimal_places=2)
