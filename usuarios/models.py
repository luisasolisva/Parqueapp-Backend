from django.db import models
import uuid
# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

TIPO_USUARIO_CHOICES = [
    #Quien Reserva
    ('Cliente', 'Cliente'),
    #Quien Admin Del Parqueadero
    ('Admin', 'Admin'),
    #Quien Encargado Del Parqueadero
    ('Operario', 'Operario'),
    #Quien Maneja La Plataforma ParqueApp
    ('Root', 'Root'),
]

class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    codigo_restauracion = models.CharField(max_length=4, null=True, blank=True)  # Campo para el código de restauración
    codigo_creado = models.DateTimeField(null=True, blank=True)  # Fecha de creación del código
    codigo_validado = models.BooleanField(default=False) # Estado de validación del código

    password = models.CharField(max_length=255)  # ¡Agrega este campo!

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuarios_usuario_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuarios_usuario_set',
        blank=True
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'telefono', 'tipo_usuario']

    def __str__(self):
        return f'{self.nombre} {self.apellido}'
    

from cloudinary.models import CloudinaryField
class Parqueadero(models.Model):
    id_parqueadero = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    latitud = models.DecimalField(max_digits=9, decimal_places=7)
    longitud = models.DecimalField(max_digits=9, decimal_places=7)
    precio_hora = models.IntegerField()
    nombre_propietario = models.CharField(max_length=200) 
    propietario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    descripcion = models.TextField(blank=True, null=True) 
    imagenes = models.ManyToManyField('ImagenParqueadero', blank=True, related_name="lista_de_imagenes")  # ✅ Usa comillas para evitar NameError    

    def __str__(self):
        return self.nombre

class MapaParqueadero(models.Model):
    parqueadero = models.OneToOneField(Parqueadero, on_delete=models.CASCADE, related_name='mapa')
    filas = models.IntegerField()
    columnas = models.IntegerField()
    nomenclatura = models.CharField(max_length=20, choices=[('Numerica', 'Numerica'), ('Alfanumerica', 'Alfanumerica')])

    def __str__(self):
        return f'Mapa de {self.parqueadero.nombre}'

class EspacioParqueadero(models.Model):
    ESTADO_CHOICES = [
        ('Disponible', 'Disponible'),
        ('Deshabilitado', 'Deshabilitado'),
    ]

    id_espacio = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mapa = models.ForeignKey(MapaParqueadero, on_delete=models.CASCADE, related_name='espacios')
    espacio = models.CharField(max_length=50)  # nombre/etiqueta del espacio, como "A1" o "01"
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    fila = models.IntegerField(null=False) 
    columna = models.IntegerField(null=False)

    def __str__(self):
        return f'Espacio {self.espacio} en {self.mapa.parqueadero.nombre}'


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Confirmada', 'Confirmada'),
        ('Cancelada', 'Cancelada'),
        ('Finalizada', 'Finalizada'),
    ]
    TIPO_VEHICULO_CHOICES = [
        ('Carro', 'Carro'),
        ('Moto', 'Moto'),
        ('Bicicleta', 'Bicicleta'),
    ]

    id_reserva = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="cliente_id")
    id_parqueadero = models.ForeignKey(Parqueadero, on_delete=models.CASCADE, db_column="parqueadero_id")
    id_espacio = models.ForeignKey(EspacioParqueadero, on_delete=models.CASCADE, db_column="espacio_id")
    fecha_inicio = models.DateField()
    hora_inicio = models.TimeField()
    fecha_fin = models.DateField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # ✅ Asegura un valor por defecto
    placa = models.CharField(max_length=10)
    color = models.CharField(max_length=20)
    modelo = models.CharField(max_length=50)
    tipo_vehiculo = models.CharField(max_length=20, choices=TIPO_VEHICULO_CHOICES)
    codigo_qr_texto = models.TextField(blank=True, null=True)  # ✅ Nuevo campo para almacenar el QR en texto


    def __str__(self):
        return f'Reserva {self.id_reserva} de {self.cliente}'


class Pago(models.Model):
    METODO_PAGO_CHOICES = [
        ('Tarjeta', 'Tarjeta'),
        ('Efectivo', 'Efectivo'),
        ('PayPal', 'PayPal'),
    ]

    ESTADO_PAGO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Rechazado', 'Rechazado'),
    ]

    id_pago = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES)
    fecha_pago = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pago {self.id_pago} para {self.id_reserva}'


class Reseña(models.Model):
    id_reseña = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    id_parqueadero = models.ForeignKey(Parqueadero, on_delete=models.CASCADE)
    calificacion = models.IntegerField()
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Reseña de {self.id_usuario} para {self.id_parqueadero}'


class Vehiculo(models.Model):
    id_vehiculo = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    placa = models.CharField(max_length=10)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    color = models.CharField(max_length=50)

    def __str__(self):
        return self.placa


class Cancelacion(models.Model):
    id_cancelacion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    motivo = models.TextField()
    fecha_cancelacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Cancelación {self.id_cancelacion} de {self.id_reserva}'

class ImagenParqueadero(models.Model):
    id_imagen = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parqueadero = models.ForeignKey('Parqueadero', on_delete=models.CASCADE, related_name="imagenes_del_parqueadero")  # ✅ Evita NameError
    imagen = CloudinaryField("imagen") 