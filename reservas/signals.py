from django.db.models.signals import post_save
from django.dispatch import receiver
from usuarios.models import Reserva
from usuarios.models import Reseña

@receiver(post_save, sender=Reserva)
def crear_reseña_automatica(sender, instance, **kwargs):
    if instance.estado == "Finalizada":
        Reseña.objects.create(
            id_usuario=instance.cliente,
            id_parqueadero=instance.id_parqueadero,
            calificacion=5,
            comentario="¡Gracias por reservar con ParqueApp!"
        )
