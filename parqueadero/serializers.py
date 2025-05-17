from rest_framework import serializers
from .models import Parqueadero

class ParqueaderoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parqueadero
        fields = ['id', 'nombre', 'direccion', 'latitud', 'longitud']


from usuarios.models import Parqueadero


class ParqueaderoSerializer(serializers.ModelSerializer):
    id_propietario = serializers.ReadOnlyField(source='id_propietario.email')  # Mostrar el email del propietario

    class Meta:
        model = Parqueadero
        fields = '__all__'

    def validate(self, data):
        user = self.context['request'].user
        if user.tipo_usuario != 'Admin':
            raise serializers.ValidationError("Solo los administradores pueden crear parqueaderos.")
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        filas = validated_data.get('filas')
        columnas = validated_data.get('columnas')

        # Crear matriz vacía según filas y columnas
        matriz = [[0 for _ in range(columnas)] for _ in range(filas)]
        validated_data['matriz'] = matriz
        validated_data['id_propietario'] = user

        parqueadero = Parqueadero.objects.create(**validated_data)
        parqueadero.save()
        
        # Aquí podrías agregar alguna lógica extra, notificaciones, etc.

        return parqueadero
