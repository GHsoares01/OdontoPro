from datetime import datetime

from django import forms
from .models import (
    Paciente,
    Procedimento,
    Consulta,
    ArquivoPaciente,
    OdontogramaItem,
    Dentista,
    Sala,
)


def gerar_horarios_consulta():
    horarios = []

    # manhã: 08:00 até 11:30
    for hora in range(8, 12):
        horarios.append((f"{hora:02d}:00", f"{hora:02d}:00"))
        horarios.append((f"{hora:02d}:30", f"{hora:02d}:30"))

    # tarde: 13:00 até 17:30
    for hora in range(13, 18):
        horarios.append((f"{hora:02d}:00", f"{hora:02d}:00"))
        horarios.append((f"{hora:02d}:30", f"{hora:02d}:30"))

    # último horário
    horarios.append(("18:00", "18:00"))

    return horarios


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = "__all__"
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
        }


class DentistaForm(forms.ModelForm):
    class Meta:
        model = Dentista
        fields = "__all__"


class ProcedimentoForm(forms.ModelForm):
    class Meta:
        model = Procedimento
        fields = [
            "dentista",
            "descricao",
            "valor",
            "data",
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
        }


class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = [
        "paciente",
        "dentista",
        "sala",
        "data",
        "hora",
        "duracao_minutos",
        "valor",
        "status",
        "observacoes",
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "hora": forms.Select(),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
            "valor": forms.NumberInput(attrs={
            "step": "0.01",
            "placeholder": "Ex: 120.00"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        horarios_base = [
            ("07:00", "07:00"),
            ("07:30", "07:30"),
            ("08:00", "08:00"),
            ("08:30", "08:30"),
            ("09:00", "09:00"),
            ("09:30", "09:30"),
            ("10:00", "10:00"),
            ("10:30", "10:30"),
            ("11:00", "11:00"),
            ("11:30", "11:30"),
            ("12:00", "12:00"),
            ("12:30", "12:30"),
            ("13:00", "13:00"),
            ("13:30", "13:30"),
            ("14:00", "14:00"),
            ("14:30", "14:30"),
            ("15:00", "15:00"),
            ("15:30", "15:30"),
            ("16:00", "16:00"),
            ("16:30", "16:30"),
            ("17:00", "17:00"),
            ("17:30", "17:30"),
            ("18:00", "18:00"),
        ]

        self.fields["hora"].choices = horarios_base

        if self.instance and self.instance.pk and self.instance.hora:
            hora_atual = self.instance.hora.strftime("%H:%M")
            if (hora_atual, hora_atual) not in self.fields["hora"].choices:
                self.fields["hora"].choices = [(hora_atual, hora_atual)] + list(self.fields["hora"].choices)

    def _hora_para_minutos(self, hora):
        return hora.hour * 60 + hora.minute

    def _tem_conflito_intervalo(self, inicio_a, fim_a, inicio_b, fim_b):
        return inicio_a < fim_b and inicio_b < fim_a

    def clean(self):
        cleaned_data = super().clean()

        dentista = cleaned_data.get("dentista")
        sala = cleaned_data.get("sala")
        data = cleaned_data.get("data")
        hora = cleaned_data.get("hora")
        duracao = cleaned_data.get("duracao_minutos")

        if not data or not hora or not duracao:
            return cleaned_data

        inicio_novo = self._hora_para_minutos(hora)
        fim_novo = inicio_novo + int(duracao)

        consultas_mesmo_dia = Consulta.objects.filter(data=data)

        if self.instance and self.instance.pk:
            consultas_mesmo_dia = consultas_mesmo_dia.exclude(pk=self.instance.pk)

        for consulta in consultas_mesmo_dia:
            inicio_existente = self._hora_para_minutos(consulta.hora)
            fim_existente = inicio_existente + int(consulta.duracao_minutos)

            if dentista and consulta.dentista_id == dentista.id:
                if self._tem_conflito_intervalo(inicio_novo, fim_novo, inicio_existente, fim_existente):
                    self.add_error(
                        "hora",
                        "Este dentista já possui uma consulta nesse intervalo de horário."
                    )
                    break

        for consulta in consultas_mesmo_dia:
            inicio_existente = self._hora_para_minutos(consulta.hora)
            fim_existente = inicio_existente + int(consulta.duracao_minutos)

            if sala and consulta.sala_id == sala.id:
                if self._tem_conflito_intervalo(inicio_novo, fim_novo, inicio_existente, fim_existente):
                    self.add_error(
                        "sala",
                        "Esta sala já está ocupada nesse intervalo de horário."
                    )
                    break

        return cleaned_data

class ArquivoPacienteForm(forms.ModelForm):
    class Meta:
        model = ArquivoPaciente
        fields = [
            "titulo",
            "tipo",
            "arquivo",
            "descricao",
        ]


class OdontogramaItemForm(forms.ModelForm):
    class Meta:
        model = OdontogramaItem
        fields = [
            "dente",
            "status",
            "observacoes",
        ]