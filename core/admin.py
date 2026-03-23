from django.contrib import admin
from .models import (
    Paciente,
    Dentista,
    Sala,
    Procedimento,
    Consulta,
    ArquivoPaciente,
    OdontogramaItem,
)

admin.site.register(Paciente)
admin.site.register(Dentista)
admin.site.register(Sala)
admin.site.register(Procedimento)
admin.site.register(Consulta)
admin.site.register(ArquivoPaciente)
admin.site.register(OdontogramaItem)