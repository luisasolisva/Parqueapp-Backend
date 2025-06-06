

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

import cloudinary
import cloudinary.uploader

from rest_framework import serializers
from usuarios.models import Parqueadero
from parqueadero.utils import validar_imagen
from django.db import IntegrityError

class RegistrarParqueaderoSerializer(serializers.ModelSerializer):
    imagenes = serializers.ImageField(required=True)  # ✅ Ahora la imagen es obligatoria

    class Meta:
        model = Parqueadero
        fields = ['nombre', 'direccion', 'ciudad', 'latitud', 'longitud', 'precio_hora', 'nombre_propietario', 'descripcion', 'imagenes']

    def validate(self, data):
        """Validar que todos los campos obligatorios estén presentes y que el admin no registre más de un parqueadero."""
        request = self.context.get('request')  
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Debes estar autenticado para registrar un parqueadero.")

        if Parqueadero.objects.filter(propietario=request.user).exists():
            raise serializers.ValidationError("El administrador ya tiene un parqueadero registrado y no puede crear otro.")

        # ✅ Validar que ningún campo obligatorio esté vacío
        for campo in ['nombre', 'direccion', 'ciudad', 'latitud', 'longitud', 'precio_hora', 'nombre_propietario', 'descripcion', 'imagenes']:
            if not data.get(campo):
                raise serializers.ValidationError({campo: f"El campo {campo} es obligatorio."})

        return data

    def create(self, validated_data):
        request = self.context.get('request')  
        imagen = validated_data.pop("imagenes", None)

        try:
            parqueadero = Parqueadero.objects.create(propietario=request.user, **validated_data)

            # ✅ Subir imagen solo si se proporciona
            resultado = cloudinary.uploader.upload(imagen)
            ImagenParqueadero.objects.create(parqueadero=parqueadero, imagen=resultado["url"])

            return parqueadero

        except Exception as e:
            raise serializers.ValidationError(f"Error en la base de datos: {str(e)}")
        
class EstadisticasAdminSerializer(serializers.Serializer):
    total_clientes = serializers.IntegerField()
    total_reservas = serializers.IntegerField()
    reservas_confirmadas = serializers.IntegerField()
    reservas_canceladas = serializers.IntegerField()
    ingresos_totales = serializers.DecimalField(max_digits=10, decimal_places=2)


from rest_framework import serializers
from usuarios.models import ImagenParqueadero

class ImagenParqueaderoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenParqueadero
        fields = ["id_imagen", "imagen"]




class ParqueaderoDetailSerializer(serializers.ModelSerializer):
    imagenes = serializers.SerializerMethodField()  # ✅ Convertir imágenes en URLs serializables

    class Meta:
        model = Parqueadero
        fields = ['id_parqueadero', 'nombre', 'direccion', 'ciudad', 'latitud', 'longitud', 'precio_hora', 'nombre_propietario', 'descripcion', 'imagenes']

    def get_imagenes(self, obj):
        return [str(imagen.imagen) for imagen in ImagenParqueadero.objects.filter(parqueadero=obj) if imagen.imagen]  # ✅ Convertir a string y filtrar valores vacíos



class EliminarParqueaderoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parqueadero
        fields = ['id_parqueadero', 'nombre', 'direccion', 'ciudad']  # ✅ Mostrar algunos detalles antes de eliminar

