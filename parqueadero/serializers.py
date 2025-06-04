

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


import cloudinary
import cloudinary.uploader

from rest_framework import serializers
from usuarios.models import Parqueadero
from parqueadero.utils import validar_imagen

class RegistrarParqueaderoSerializer(serializers.ModelSerializer):
    imagenes = serializers.ImageField(required=False)  # ✅ Permitir una imagen opcional

    class Meta:
        model = Parqueadero
        fields = ['nombre', 'direccion', 'ciudad', 'latitud', 'longitud', 'precio_hora', 'nombre_propietario', 'descripcion', 'imagenes']

    def validate_imagenes(self, imagen):
        error = validar_imagen(imagen)  # ✅ Validación ANTES de procesar la creación
        if error:
            raise serializers.ValidationError(error)
        return imagen

    def create(self, validated_data):
        request = self.context.get('request')  # ✅ Obtener el usuario autenticado
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Debes estar autenticado para registrar un parqueadero.")

        imagen = validated_data.pop("imagenes", None)

        # ✅ Validar imagen antes de crear el parqueadero
        if imagen:
            error = validar_imagen(imagen)
            if error:
                raise serializers.ValidationError(error)  # ✅ Evita que el parqueadero se cree si la imagen falla

        # ✅ Crear el parqueadero asociándolo al Admin que lo registra
        parqueadero = Parqueadero.objects.create(propietario=request.user, **validated_data)

        # ✅ Subir imagen solo si pasó la validación
        imagen_url = None
        if imagen:
            resultado = cloudinary.uploader.upload(imagen)
            ImagenParqueadero.objects.create(parqueadero=parqueadero, imagen=resultado["url"])
            imagen_url = resultado["url"]

        # ✅ Retornar todos los datos junto con la imagen
        parqueadero_data = RegistrarParqueaderoSerializer(parqueadero).data
        parqueadero_data["imagenes"] = imagen_url  

        return parqueadero_data

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

