

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
    class Meta:
        model = Parqueadero
        exclude = ['matriz']  # Ocultamos la matriz en el formulario

    def validate(self, data):
        user = self.context['request'].user
        if user.tipo_usuario != 'Admin':
            raise serializers.ValidationError("Solo los administradores pueden crear parqueaderos.")

        # Validación de nombre_propietario
        nombre_propietario = data.get("nombre_propietario", "").strip()
        if not nombre_propietario:
            raise serializers.ValidationError({"nombre_propietario": "El nombre del propietario no puede estar vacío."})

        return data
    
def create(self, validated_data):
    filas = validated_data.get('filas')
    columnas = validated_data.get('columnas')

    if filas is None or columnas is None:
        raise serializers.ValidationError({"filas": "El número de filas es obligatorio.", "columnas": "El número de columnas es obligatorio."})

    # Se genera la matriz automáticamente
    matriz = [[{"nombre": "", "estado": ""} for _ in range(columnas)] for _ in range(filas)]
    validated_data['matriz'] = matriz

    return Parqueadero.objects.create(**validated_data)
