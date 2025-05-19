from rest_framework import serializers
from .models import Parqueadero

class ParqueaderoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parqueadero
        fields = ['id', 'nombre', 'direccion', 'latitud', 'longitud']
