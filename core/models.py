from django.db import models
from django.utils import timezone


class Paciente(models.Model):
    nome = models.CharField(max_length=120)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Dentista(models.Model):
    nome = models.CharField(max_length=120)
    cro = models.CharField(max_length=20, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Sala(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class Procedimento(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="procedimentos"
    )
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="procedimentos"
    )
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data = models.DateField()

    def __str__(self):
        return f"{self.paciente.nome} - {self.descricao}"


class Consulta(models.Model):
    STATUS_CHOICES = [
        ("agendado", "Agendado"),
        ("confirmado", "Confirmado"),
        ("concluido", "Concluído"),
        ("cancelado", "Cancelado"),
    ]

    DURACAO_CHOICES = [
        (30, "30 minutos"),
        (60, "60 minutos"),
        (90, "90 minutos"),
        (120, "120 minutos"),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="consultas"
    )
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultas"
    )
    sala = models.ForeignKey(
        Sala,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultas"
    )
    data = models.DateField()
    hora = models.TimeField()
    duracao_minutos = models.PositiveIntegerField(
        choices=DURACAO_CHOICES,
        default=60
    )
    observacoes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="agendado"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Valor cobrado pela consulta/procedimento"
    )

    def __str__(self):
        return f"{self.paciente.nome} - {self.data} {self.hora}"


class ArquivoPaciente(models.Model):
    TIPO_CHOICES = [
        ("raiox", "Raio-X"),
        ("foto", "Foto"),
        ("pdf", "PDF"),
        ("documento", "Documento"),
        ("outro", "Outro"),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="arquivos"
    )
    titulo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="outro")
    arquivo = models.FileField(upload_to="pacientes/arquivos/")
    descricao = models.TextField(blank=True, null=True)
    enviado_em = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.paciente.nome} - {self.titulo}"


class OdontogramaItem(models.Model):
    STATUS_CHOICES = [
        ("saudavel", "Saudável"),
        ("carie", "Cárie"),
        ("restauracao", "Restauração"),
        ("canal", "Canal"),
        ("extracao", "Extração"),
        ("implante", "Implante"),
        ("ausente", "Ausente"),
        ("outro", "Outro"),
    ]

    DENTE_CHOICES = [
        ("18", "18"), ("17", "17"), ("16", "16"), ("15", "15"),
        ("14", "14"), ("13", "13"), ("12", "12"), ("11", "11"),
        ("21", "21"), ("22", "22"), ("23", "23"), ("24", "24"),
        ("25", "25"), ("26", "26"), ("27", "27"), ("28", "28"),
        ("48", "48"), ("47", "47"), ("46", "46"), ("45", "45"),
        ("44", "44"), ("43", "43"), ("42", "42"), ("41", "41"),
        ("31", "31"), ("32", "32"), ("33", "33"), ("34", "34"),
        ("35", "35"), ("36", "36"), ("37", "37"), ("38", "38"),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="odontograma"
    )
    dente = models.CharField(max_length=2, choices=DENTE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="saudavel"
    )
    observacoes = models.TextField(blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("paciente", "dente")
        ordering = ["dente"]

    def __str__(self):
        return f"{self.paciente.nome} - Dente {self.dente} - {self.status}"


class OdontogramaHistorico(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="historico_odontograma"
    )
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historico_odontograma"
    )
    dente = models.CharField(
        max_length=2,
        choices=OdontogramaItem.DENTE_CHOICES
    )
    status = models.CharField(
        max_length=20,
        choices=OdontogramaItem.STATUS_CHOICES,
        default="saudavel"
    )
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.paciente.nome} - Dente {self.dente} - {self.status} - {self.criado_em:%d/%m/%Y %H:%M}"