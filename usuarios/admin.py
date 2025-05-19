from django.contrib import admin
from .models import Usuario, Parqueadero, EspacioParqueadero, Reserva, Pago, Reseña, Vehiculo, Cancelacion

admin.site.register(Usuario)
admin.site.register(Parqueadero)
admin.site.register(EspacioParqueadero)
admin.site.register(Reserva)
admin.site.register(Pago)
admin.site.register(Reseña)
admin.site.register(Vehiculo)
admin.site.register(Cancelacion)
