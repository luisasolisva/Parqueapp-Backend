

from rest_framework import serializers
from usuarios.models import Parqueadero, MapaParqueadero, EspacioParqueadero


from rest_framework import serializers
from usuarios.models import Parqueadero, ImagenParqueadero

class ParqueaderoSerializer(serializers.ModelSerializer):
    imagenes = serializers.SerializerMethodField()

    class Meta:
        model = Parqueadero
        fields = [
            'id_parqueadero',
            'nombre',
            'direccion',
            'ciudad',
            'precio_hora',
            'imagenes'
        ]

    def get_imagenes(self, obj):
        return [
            str(imagen.imagen.url) 
            for imagen in ImagenParqueadero.objects.filter(parqueadero=obj) 
            if imagen.imagen
        ]


class EspacioParqueaderoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EspacioParqueadero
        fields = ['fila', 'columna', 'espacio', 'estado']

class EspacioEstadoUpdateSerializer(serializers.Serializer):
    fila = serializers.IntegerField(min_value=0)
    columna = serializers.IntegerField(min_value=0)
    estado = serializers.ChoiceField(choices=["Disponible", "Deshabilitado"])


class MapaSizeSerializer(serializers.Serializer):
    filas = serializers.IntegerField(min_value=1)
    columnas = serializers.IntegerField(min_value=1)

class MapaParqueaderoSerializer(serializers.Serializer):
    mapaSize = MapaSizeSerializer()
    nomenclatura = serializers.ChoiceField(choices=["Numerica", "Alfanumerica"])
    espacios = EspacioParqueaderoSerializer(many=True)


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


class ModificarParqueaderoSerializer(serializers.ModelSerializer):
    imagenes = serializers.ImageField(required=False, allow_null=True)  # ✅ Imagen opcional en modificación

    class Meta:
        model = Parqueadero
        fields = ['nombre', 'direccion', 'ciudad', 'latitud', 'longitud', 'precio_hora', 'nombre_propietario', 'descripcion', 'imagenes']

    def update(self, instance, validated_data):
        """Actualizar los datos del parqueadero sin restricciones de registro duplicado."""
        imagen = validated_data.pop("imagenes", None)

        instance.nombre = validated_data.get("nombre", instance.nombre)
        instance.direccion = validated_data.get("direccion", instance.direccion)
        instance.ciudad = validated_data.get("ciudad", instance.ciudad)
        instance.latitud = validated_data.get("latitud", instance.latitud)
        instance.longitud = validated_data.get("longitud", instance.longitud)
        instance.precio_hora = validated_data.get("precio_hora", instance.precio_hora)
        instance.nombre_propietario = validated_data.get("nombre_propietario", instance.nombre_propietario)
        instance.descripcion = validated_data.get("descripcion", instance.descripcion)
        instance.save()

        if imagen:
            ImagenParqueadero.objects.filter(parqueadero=instance).delete()  # ✅ Eliminar imagen anterior
            resultado = cloudinary.uploader.upload(imagen)
            ImagenParqueadero.objects.create(parqueadero=instance, imagen=resultado["url"])

        return instance
