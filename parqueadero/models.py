from django.db import models

class Parqueadero(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    latitud = models.FloatField()
    longitud = models.FloatField()

    def __str__(self):
        return self.nombre



