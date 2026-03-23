from django.urls import path
from . import views
from .views import CustomLoginView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # HOME PÚBLICA + DASHBOARD
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # RELATÓRIOS
    path("relatorios/financeiro/", views.relatorio_financeiro, name="relatorio_financeiro"),
    path("relatorios/dentistas/", views.relatorio_dentistas, name="relatorio_dentistas"),

    # PACIENTES
    path("pacientes/", views.lista_pacientes, name="lista_pacientes"),
    path("pacientes/novo/", views.cadastrar_paciente, name="cadastrar_paciente"),
    path("pacientes/<int:pk>/", views.detalhes_paciente, name="detalhes_paciente"),
    path("pacientes/<int:pk>/editar/", views.editar_paciente, name="editar_paciente"),
    path("pacientes/<int:pk>/deletar/", views.deletar_paciente, name="deletar_paciente"),
    path("pacientes/<int:pk>/pdf/", views.gerar_pdf_paciente, name="gerar_pdf_paciente"),

    # DENTISTAS
    path("dentistas/", views.lista_dentistas, name="lista_dentistas"),
    path("dentistas/novo/", views.cadastrar_dentista, name="cadastrar_dentista"),
    path("dentistas/<int:pk>/editar/", views.editar_dentista, name="editar_dentista"),
    path("dentistas/<int:pk>/deletar/", views.deletar_dentista, name="deletar_dentista"),

    # PROCEDIMENTOS
    path("pacientes/<int:pk>/procedimentos/novo/", views.adicionar_procedimento, name="adicionar_procedimento"),
    path("procedimentos/<int:pk>/editar/", views.editar_procedimento, name="editar_procedimento"),
    path("procedimentos/<int:pk>/deletar/", views.deletar_procedimento, name="deletar_procedimento"),

    # ARQUIVOS
    path("pacientes/<int:pk>/arquivo/adicionar/", views.adicionar_arquivo_paciente, name="adicionar_arquivo_paciente"),
    path("arquivo/<int:pk>/deletar/", views.deletar_arquivo_paciente, name="deletar_arquivo_paciente"),

    # ODONTOGRAMA
    path("pacientes/<int:pk>/odontograma/adicionar/", views.adicionar_odontograma_item, name="adicionar_odontograma_item"),
    path("odontograma/<int:pk>/editar/", views.editar_odontograma_item, name="editar_odontograma_item"),
    path("odontograma/<int:pk>/deletar/", views.deletar_odontograma_item, name="deletar_odontograma_item"),
    path("pacientes/<int:paciente_pk>/odontograma/ajax/salvar/", views.salvar_odontograma_ajax, name="salvar_odontograma_ajax"),

    # CONSULTAS
    path("consultas/", views.lista_consultas, name="lista_consultas"),
    path("consultas/calendario/", views.calendario_consultas, name="calendario_consultas"),
    path("consultas/nova/", views.cadastrar_consulta, name="cadastrar_consulta"),
    path("consultas/<int:pk>/editar/", views.editar_consulta, name="editar_consulta"),
    path("consultas/<int:pk>/deletar/", views.deletar_consulta, name="deletar_consulta"),
    path("consultas/hoje/", views.consultas_hoje, name="consultas_hoje"),
    path("consultas/<int:pk>/status/<str:novo_status>/", views.atualizar_status_consulta, name="atualizar_status_consulta"),
    path("consultas/horarios-disponiveis/", views.horarios_disponiveis, name="horarios_disponiveis"),
    path("consultas/<int:pk>/mover/", views.mover_consulta_semana, name="mover_consulta_semana"),

    # AGENDA
    path("agenda/", views.agenda_completa, name="agenda_completa"),
    path("consultas/semana/", views.agenda_semanal, name="agenda_semanal"),

    # LOGIN / LOGOUT
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]