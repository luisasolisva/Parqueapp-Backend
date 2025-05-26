from django.db import models
from django.utils import timezone

class CambioMatriz(models.Model):
    parqueadero = models.ForeignKey('usuarios.Parqueadero', on_delete=models.CASCADE)
    fila = models.IntegerField()
    columna = models.IntegerField()
    tipo_anterior = models.CharField(max_length=20)
    tipo_nuevo = models.CharField(max_length=20)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"Cambio en {self.parqueadero.nombre} - Fila {self.fila}, Columna {self.columna}"

