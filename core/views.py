from collections import defaultdict
from datetime import date
from io import BytesIO
import calendar
from datetime import date, timedelta
from django.http import JsonResponse
from datetime import datetime
from django.db.models import Sum
from .models import OdontogramaHistorico
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractDay, TruncMonth
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect


from .forms import (
    ArquivoPacienteForm,
    ConsultaForm,
    DentistaForm,
    OdontogramaItemForm,
    PacienteForm,
    ProcedimentoForm,
)
from .models import (
    ArquivoPaciente,
    Consulta,
    Dentista,
    OdontogramaHistorico,
    OdontogramaItem,
    Paciente,
    Procedimento,
)
from django.core.exceptions import PermissionDenied

def eh_admin(user):
    return user.is_authenticated and user.groups.filter(name="Administrador").exists()

def eh_recepcao(user):
    return user.is_authenticated and user.groups.filter(name="Recepcao").exists()

def eh_dentista(user):
    return user.is_authenticated and user.groups.filter(name="Dentista").exists()

def admin_ou_recepcao(user):
    return eh_admin(user) or eh_recepcao(user)
    

STATUS_CONSULTA_VALIDOS = {"agendado", "confirmado", "cancelado", "concluido"}

NOMES_MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


# CORES DOS DENTISTAS
CORES_DENTISTAS = [
    "#2563eb",  # azul
    "#16a34a",  # verde
    "#7c3aed",  # roxo
    "#ea580c",  # laranja
    "#dc2626",  # vermelho
    "#0891b2",  # ciano
]


def _get_cor_dentista(dentista):
    if not dentista:
        return "#94a3b8"
    return CORES_DENTISTAS[(dentista.id - 1) % len(CORES_DENTISTAS)]


def _aplicar_cor_dentista(consultas):
    for consulta in consultas:
        consulta.cor_dentista = _get_cor_dentista(consulta.dentista)
    return consultas

def _get_mes_ano(request):
    hoje = date.today()

    try:
        mes = int(request.GET.get("mes", hoje.month))
        ano = int(request.GET.get("ano", hoje.year))
    except (TypeError, ValueError):
        return hoje.month, hoje.year

    if mes < 1 or mes > 12:
        mes = hoje.month

    if ano < 1:
        ano = hoje.year

    return mes, ano


def _get_navegacao_mes(mes, ano):
    if mes == 1:
        mes_anterior = 12
        ano_anterior = ano - 1
    else:
        mes_anterior = mes - 1
        ano_anterior = ano

    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano

    return {
        "mes_anterior": mes_anterior,
        "ano_anterior": ano_anterior,
        "proximo_mes": proximo_mes,
        "proximo_ano": proximo_ano,
    }

@login_required
def dashboard(request):
    hoje = date.today()

    total_pacientes = Paciente.objects.count()
    total_procedimentos = Procedimento.objects.count()
    total_dentistas = Dentista.objects.filter(ativo=True).count()

    consultas_hoje = (
        Consulta.objects.select_related("paciente", "dentista", "sala")
        .filter(data=hoje)
        .order_by("hora")
    )

    total_consultas_hoje = consultas_hoje.count()

    consultas_confirmadas_hoje = consultas_hoje.filter(status="confirmado").count()
    consultas_canceladas_hoje = consultas_hoje.filter(status="cancelado").count()
    consultas_concluidas_hoje = consultas_hoje.filter(status="concluido").count()
    consultas_agendadas_hoje = consultas_hoje.filter(status="agendado").count()

    faturamento_hoje = (
        Consulta.objects.filter(data=hoje, status="concluido")
        .aggregate(total=Sum("valor"))["total"] or 0
    )

    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    consultas_semana = Consulta.objects.filter(
        data__range=[inicio_semana, fim_semana]
    ).count()

    faturamento_mes = (
        Consulta.objects.filter(
            data__year=hoje.year,
            data__month=hoje.month,
            status="concluido"
        ).aggregate(total=Sum("valor"))["total"] or 0
    )

    consultas_mes_concluidas = Consulta.objects.filter(
        data__year=hoje.year,
        data__month=hoje.month,
        status="concluido"
    )

    ultimo_dia_mes = calendar.monthrange(hoje.year, hoje.month)[1]

    labels_grafico = []
    valores_grafico = []

    for dia in range(1, ultimo_dia_mes + 1):
        total_dia = (
            consultas_mes_concluidas.filter(data__day=dia)
            .aggregate(total=Sum("valor"))["total"] or 0
        )
        labels_grafico.append(str(dia))
        valores_grafico.append(float(total_dia))

    proximas_consultas = (
        Consulta.objects.select_related("paciente", "dentista", "sala")
        .filter(data__gte=hoje)
        .order_by("data", "hora")[:5]
    )

    alertas = []

    if consultas_agendadas_hoje > 0:
        alertas.append(
            f"{consultas_agendadas_hoje} consulta(s) de hoje ainda estão como agendadas e podem precisar de confirmação."
        )

    if consultas_canceladas_hoje > 0:
        alertas.append(
            f"{consultas_canceladas_hoje} consulta(s) foram canceladas hoje."
        )

    if total_consultas_hoje == 0:
        alertas.append("Não há consultas marcadas para hoje.")

    return render(request, "core/dashboard.html", {
        "total_pacientes": total_pacientes,
        "total_procedimentos": total_procedimentos,
        "total_dentistas": total_dentistas,
        "total_consultas_hoje": total_consultas_hoje,
        "consultas_confirmadas_hoje": consultas_confirmadas_hoje,
        "consultas_canceladas_hoje": consultas_canceladas_hoje,
        "consultas_concluidas_hoje": consultas_concluidas_hoje,
        "consultas_agendadas_hoje": consultas_agendadas_hoje,
        "faturamento_hoje": faturamento_hoje,
        "consultas_semana": consultas_semana,
        "faturamento_mes": faturamento_mes,
        "consultas_hoje": consultas_hoje,
        "proximas_consultas": proximas_consultas,
        "labels_grafico": labels_grafico,
        "valores_grafico": valores_grafico,
        "alertas": alertas,
    })




@login_required
def relatorio_financeiro(request):
    if not eh_admin(request.user):
        raise PermissionDenied

    hoje = date.today()

    total_geral = Procedimento.objects.aggregate(total=Sum("valor"))["total"] or 0
    total_hoje = (
        Procedimento.objects.filter(data=hoje).aggregate(total=Sum("valor"))["total"] or 0
    )
    total_mes = (
        Procedimento.objects.filter(data__year=hoje.year, data__month=hoje.month)
        .aggregate(total=Sum("valor"))["total"] or 0
    )

    procedimentos_mais_feitos = (
        Procedimento.objects.values("descricao")
        .annotate(total=Count("id"), valor_total=Sum("valor"))
        .order_by("-total", "-valor_total")[:10]
    )

    pacientes_que_mais_gastaram = (
        Procedimento.objects.values("paciente__nome")
        .annotate(total_gasto=Sum("valor"), total_proc=Count("id"))
        .order_by("-total_gasto")[:10]
    )

    faturamento_mensal = (
        Procedimento.objects.annotate(mes=TruncMonth("data"))
        .values("mes")
        .annotate(total=Sum("valor"))
        .order_by("mes")
    )

    labels_meses = []
    valores_meses = []

    for item in faturamento_mensal:
        if item["mes"]:
            labels_meses.append(item["mes"].strftime("%m/%Y"))
            valores_meses.append(float(item["total"] or 0))

    return render(request, "core/relatorios/financeiro.html", {
        "total_geral": total_geral,
        "total_hoje": total_hoje,
        "total_mes": total_mes,
        "procedimentos_mais_feitos": procedimentos_mais_feitos,
        "pacientes_que_mais_gastaram": pacientes_que_mais_gastaram,
        "labels_meses": labels_meses,
        "valores_meses": valores_meses,
    })

@login_required
def relatorio_dentistas(request):
    dentistas = (
        Dentista.objects.annotate(
            total_consultas=Count("consultas", distinct=True),
            total_procedimentos=Count("procedimentos", distinct=True),
            faturamento=Sum("procedimentos__valor"),
        )
        .order_by("nome")
    )

    return render(request, "core/relatorios/dentistas.html", {
        "dentistas": dentistas,
    })

@login_required
def lista_pacientes(request):
    q = (request.GET.get("q") or "").strip()

    pacientes = Paciente.objects.all().order_by("nome")

    if q:
        pacientes = pacientes.filter(
            Q(nome__icontains=q) |
            Q(cpf__icontains=q) |
            Q(telefone__icontains=q)
        ).order_by("nome")

    return render(request, "core/pacientes/listar.html", {
        "pacientes": pacientes,
        "q": q,
    })

@login_required(login_url='login')
def cadastrar_paciente(request):
    if request.method == "POST":
        form = PacienteForm(request.POST)

        if form.is_valid():
             paciente = form.save()
             messages.success(request, "Paciente cadastrado com sucesso.")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "total_pacientes": Paciente.objects.count()
            })

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return redirect("detalhes_paciente", pk=paciente.pk)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return render(request, "core/pacientes/_form_modal.html", {"form": form})

        messages.error(request, "Corrija os erros do formulário.")
    else:
        form = PacienteForm()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "core/pacientes/_form_modal.html", {"form": form})

    return render(request, "core/pacientes/cadastrar.html", {"form": form})

@login_required
def detalhes_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    procedimentos = (
        Procedimento.objects.select_related("dentista")
        .filter(paciente=paciente)
        .order_by("-data", "-id")
    )

    arquivos = (
        ArquivoPaciente.objects.filter(paciente=paciente)
        .order_by("-enviado_em", "-id")
    )

    odontograma = (
        OdontogramaItem.objects.filter(paciente=paciente)
        .order_by("dente")
    )

    # NOVO: histórico do odontograma
    historico_odontograma = (
        OdontogramaHistorico.objects
        .filter(paciente=paciente)
        .select_related("dentista")
        .order_by("-criado_em")
    )

    odontograma_dict = {item.dente: item for item in odontograma}

    dentes_superiores = ["18", "17", "16", "15", "14", "13", "12", "11"]
    dentes_superiores2 = ["21", "22", "23", "24", "25", "26", "27", "28"]
    dentes_inferiores = ["48", "47", "46", "45", "44", "43", "42", "41"]
    dentes_inferiores2 = ["31", "32", "33", "34", "35", "36", "37", "38"]

    total_gasto = procedimentos.aggregate(total=Sum("valor"))["total"] or 0

    return render(request, "core/pacientes/detalhes.html", {
        "paciente": paciente,
        "procedimentos": procedimentos,
        "arquivos": arquivos,
        "odontograma": odontograma,
        "odontograma_dict": odontograma_dict,
        "historico_odontograma": historico_odontograma,  # NOVO
        "form_proc": ProcedimentoForm(),
        "form_arquivo": ArquivoPacienteForm(),
        "form_odontograma": OdontogramaItemForm(),
        "total_gasto": total_gasto,
        "dentes_superiores": dentes_superiores,
        "dentes_superiores2": dentes_superiores2,
        "dentes_inferiores": dentes_inferiores,
        "dentes_inferiores2": dentes_inferiores2,
    })


def gerar_pdf_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    procedimentos = (
        Procedimento.objects.select_related("dentista")
        .filter(paciente=paciente)
        .order_by("-data", "-id")
    )

    odontograma = (
        OdontogramaItem.objects.filter(paciente=paciente)
        .order_by("dente")
    )

    arquivos = (
        ArquivoPaciente.objects.filter(paciente=paciente)
        .order_by("-enviado_em", "-id")
    )

    total_gasto = procedimentos.aggregate(total=Sum("valor"))["total"] or 0

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    largura, altura = A4
    y = altura - 50

    pdf.setTitle(f"Prontuario_{paciente.nome}")

    def linha(texto, tamanho=10, negrito=False, espacamento=18):
        nonlocal y

        if y < 60:
            pdf.showPage()
            y = altura - 50

        fonte = "Helvetica-Bold" if negrito else "Helvetica"
        pdf.setFont(fonte, tamanho)
        pdf.drawString(50, y, str(texto))
        y -= espacamento

    linha("CLÍNICA ODONTOPRO", 16, True, 28)
    linha("PRONTUÁRIO DO PACIENTE", 13, True, 24)

    linha(f"Nome: {paciente.nome}", 11, True)
    linha(f"CPF: {paciente.cpf}")
    linha(f"Telefone: {paciente.telefone or '-'}")
    linha(f"Data de nascimento: {paciente.data_nascimento or '-'}")
    linha(f"Endereço: {paciente.endereco or '-'}")
    linha(f"Observações: {paciente.observacoes or '-'}", espacamento=24)

    linha("HISTÓRICO DE PROCEDIMENTOS", 12, True, 20)

    if procedimentos:
        for proc in procedimentos:
            dentista = proc.dentista.nome if proc.dentista else "-"
            data_proc = proc.data.strftime("%d/%m/%Y") if proc.data else "-"
            linha(f"{data_proc} | {proc.descricao} | Dentista: {dentista} | R$ {proc.valor}")
    else:
        linha("Nenhum procedimento registrado.")

    linha(f"Total gasto: R$ {total_gasto}", 11, True, 24)

    linha("ODONTOGRAMA", 12, True, 20)

    if odontograma:
        for item in odontograma:
            observacao = item.observacoes if item.observacoes else "-"
            linha(f"Dente {item.dente} - {item.get_status_display()} - Obs: {observacao}")
    else:
        linha("Nenhum registro no odontograma.")

    linha("", espacamento=10)
    linha("ARQUIVOS DO PACIENTE", 12, True, 20)

    if arquivos:
        for arq in arquivos:
            data_envio = arq.enviado_em.strftime("%d/%m/%Y %H:%M") if arq.enviado_em else "-"
            linha(f"{arq.titulo} | {arq.get_tipo_display()} | {data_envio}")
    else:
        linha("Nenhum arquivo enviado.")

    pdf.save()
    buffer.seek(0)

    nome_arquivo = f"prontuario_{paciente.nome.replace(' ', '_')}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)

@login_required
def lista_dentistas(request):
    if not eh_admin(request.user):
        raise PermissionDenied
    q = (request.GET.get("q") or "").strip()

    dentistas = Dentista.objects.all().order_by("nome")

    if q:
        dentistas = dentistas.filter(
            Q(nome__icontains=q) |
            Q(cro__icontains=q) |
            Q(telefone__icontains=q) |
            Q(email__icontains=q)
        ).order_by("nome")

    return render(request, "core/dentistas/listar.html", {
        "dentistas": dentistas,
        "q": q,
    })

@login_required
def cadastrar_dentista(request):
    if not eh_admin(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = DentistaForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Dentista cadastrado com sucesso.")
            return redirect("lista_dentistas")

        messages.error(request, "Corrija os erros do formulário.")
    else:
        form = DentistaForm()

    return render(request, "core/dentistas/cadastrar.html", {
        "form": form,
    })

@login_required
def editar_dentista(request, pk):
    if not eh_admin(request.user):
        raise PermissionDenied
    dentista = get_object_or_404(Dentista, pk=pk)

    if request.method == "POST":
        form = DentistaForm(request.POST, instance=dentista)

        if form.is_valid():
            form.save()
            messages.success(request, "Dentista atualizado com sucesso.")
            return redirect("lista_dentistas")

        messages.error(request, "Corrija os erros do formulário.")
    else:
        form = DentistaForm(instance=dentista)

    return render(request, "core/dentistas/editar.html", {
        "form": form,
        "dentista": dentista,
    })

@login_required
def deletar_dentista(request, pk):
    if not eh_admin(request.user):
        raise PermissionDenied
    dentista = get_object_or_404(Dentista, pk=pk)

    if request.method == "POST":
        dentista.delete()
        messages.success(request, "Dentista deletado com sucesso.")
        return redirect("lista_dentistas")

    return render(request, "core/dentistas/confirmar_delete.html", {
        "dentista": dentista,
    })

@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == "POST":
        form = PacienteForm(request.POST, instance=paciente)

        if form.is_valid():
            form.save()
            messages.success(request, "Paciente atualizado com sucesso.")
            return redirect("detalhes_paciente", pk=paciente.pk)

        messages.error(request, "Corrija os erros do formulário.")
    else:
        form = PacienteForm(instance=paciente)

    return render(request, "core/pacientes/editar.html", {
        "form": form,
        "paciente": paciente,
    })

@login_required
def deletar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == "POST":
        paciente.delete()
        messages.success(request, "Paciente deletado com sucesso.")
        return redirect("lista_pacientes")

    return render(request, "core/pacientes/confirmar_delete.html", {
        "paciente": paciente,
    })

@login_required
def adicionar_procedimento(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method != "POST":
        return redirect("detalhes_paciente", pk=paciente.pk)

    form = ProcedimentoForm(request.POST)

    if form.is_valid():
        procedimento = form.save(commit=False)
        procedimento.paciente = paciente
        procedimento.save()
        messages.success(request, "Procedimento registrado com sucesso.")
    else:
        messages.error(request, "Erro ao salvar procedimento. Verifique os campos.")

    return redirect("detalhes_paciente", pk=paciente.pk)

@login_required
def editar_procedimento(request, pk):
    procedimento = get_object_or_404(Procedimento, pk=pk)

    if request.method == "POST":
        form = ProcedimentoForm(request.POST, instance=procedimento)

        if form.is_valid():
            form.save()
            messages.success(request, "Procedimento atualizado com sucesso.")
            return redirect("detalhes_paciente", pk=procedimento.paciente.pk)

        messages.error(request, "Corrija os erros do formulário.")
    else:
        form = ProcedimentoForm(instance=procedimento)

    return render(request, "core/procedimentos/editar.html", {
        "form": form,
        "procedimento": procedimento,
    })

@login_required
def deletar_procedimento(request, pk):
    procedimento = get_object_or_404(Procedimento, pk=pk)

    if request.method == "POST":
        paciente_id = procedimento.paciente.pk
        procedimento.delete()
        messages.success(request, "Procedimento deletado com sucesso.")
        return redirect("detalhes_paciente", pk=paciente_id)

    return render(request, "core/procedimentos/confirmar_delete.html", {
        "procedimento": procedimento,
    })

@login_required
def adicionar_arquivo_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method != "POST":
        return redirect("detalhes_paciente", pk=paciente.pk)

    form = ArquivoPacienteForm(request.POST, request.FILES)

    if form.is_valid():
        arquivo = form.save(commit=False)
        arquivo.paciente = paciente
        arquivo.save()
        messages.success(request, "Arquivo enviado com sucesso.")
    else:
        messages.error(request, "Erro ao enviar arquivo. Verifique os campos.")

    return redirect("detalhes_paciente", pk=paciente.pk)

@login_required
def deletar_arquivo_paciente(request, pk):
    arquivo = get_object_or_404(ArquivoPaciente, pk=pk)
    paciente_id = arquivo.paciente.pk

    if request.method == "POST":
        arquivo.delete()
        messages.success(request, "Arquivo deletado com sucesso.")
        return redirect("detalhes_paciente", pk=paciente_id)

    return render(request, "core/pacientes/confirmar_delete_arquivo.html", {
        "arquivo": arquivo,
    })

@login_required
def adicionar_odontograma_item(request, paciente_pk):
    paciente = get_object_or_404(Paciente, pk=paciente_pk)

    if request.method == "POST":
        form = OdontogramaItemForm(request.POST)

        if form.is_valid():
            dente = form.cleaned_data["dente"]
            status = form.cleaned_data["status"]
            observacoes = form.cleaned_data.get("observacoes")

            item, created = OdontogramaItem.objects.update_or_create(
                paciente=paciente,
                dente=dente,
                defaults={
                    "status": status,
                    "observacoes": observacoes,
                }
            )

            OdontogramaHistorico.objects.create(
                paciente=paciente,
                dente=dente,
                status=status,
                observacoes=observacoes,
            )

            return redirect("detalhes_paciente", pk=paciente.pk)

    return redirect("detalhes_paciente", pk=paciente.pk)

@login_required
def editar_odontograma_item(request, pk):
    item = get_object_or_404(OdontogramaItem, pk=pk)

    if request.method == "POST":
        form = OdontogramaItemForm(request.POST, instance=item)

        if form.is_valid():
            item_atualizado = form.save()

            OdontogramaHistorico.objects.create(
                paciente=item_atualizado.paciente,
                dente=item_atualizado.dente,
                status=item_atualizado.status,
                observacoes=item_atualizado.observacoes,
            )

            messages.success(request, f"Dente {item_atualizado.dente} atualizado com sucesso.")
            return redirect("detalhes_paciente", pk=item_atualizado.paciente.pk)

        messages.error(request, "Corrija os erros do formulário.")
    else:
        form = OdontogramaItemForm(instance=item)

    return render(request, "core/pacientes/editar_odontograma.html", {
        "form": form,
        "item": item,
    })

@login_required
def deletar_odontograma_item(request, pk):
    item = get_object_or_404(OdontogramaItem, pk=pk)
    paciente_id = item.paciente.pk

    if request.method == "POST":
        item.delete()
        messages.success(request, "Registro do odontograma deletado.")
        return redirect("detalhes_paciente", pk=paciente_id)

    return render(request, "core/pacientes/confirmar_delete_odontograma.html", {
        "item": item,
    })

@login_required
@login_required
def lista_consultas(request):
    if not (eh_admin(request.user) or eh_recepcao(request.user) or eh_dentista(request.user)):
        raise PermissionDenied
    consultas = (
        Consulta.objects.select_related("paciente", "dentista", "sala")
        .order_by("data", "hora")
    )

    data_filtro = (request.GET.get("data") or "").strip()
    status = (request.GET.get("status") or "").strip()
    busca = (request.GET.get("busca") or "").strip()

    if data_filtro:
        consultas = consultas.filter(data=data_filtro)

    if status:
        consultas = consultas.filter(status=status)

    if busca:
        consultas = consultas.filter(
            Q(paciente__nome__icontains=busca) |
            Q(dentista__nome__icontains=busca) |
            Q(status__icontains=busca)
        )

    consultas = _aplicar_cor_dentista(consultas)

    return render(request, "core/consultas/listar.html", {
        "consultas": consultas,
        "data": data_filtro,
        "status": status,
        "busca": busca,
    })
@login_required
def cadastrar_consulta(request):
    data_inicial = request.GET.get("data")

    if request.method == "POST":
        form = ConsultaForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Consulta cadastrada com sucesso.")
            return redirect("lista_consultas")

        messages.error(request, "Corrija os erros do formulário.")
    else:
        initial = {}
        if data_inicial:
            initial["data"] = data_inicial
        form = ConsultaForm(initial=initial)

    return render(request, "core/consultas/cadastrar.html", {
        "form": form,
    })

@login_required
def editar_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)

    if request.method == "POST":
        form = ConsultaForm(request.POST, instance=consulta)

        if form.is_valid():
            form.save()
            messages.success(request, "Consulta atualizada com sucesso.")
            return redirect("lista_consultas")

        messages.error(request, "Corrija os erros do formulário.")
    else:
        form = ConsultaForm(instance=consulta)

    return render(request, "core/consultas/editar.html", {
        "form": form,
        "consulta": consulta,
    })
@login_required
def deletar_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)

    if request.method == "POST":
        consulta.delete()
        messages.success(request, "Consulta deletada com sucesso.")
        return redirect("lista_consultas")

    return render(request, "core/consultas/confirmar_delete.html", {
        "consulta": consulta,
    })

@login_required
def calendario_consultas(request):
    hoje = date.today()
    mes, ano = _get_mes_ano(request)

    dentista_id = request.GET.get("dentista")

    cal = calendar.Calendar(firstweekday=6)
    dias_do_mes = list(cal.monthdatescalendar(ano, mes))

    consultas_mes = (
        Consulta.objects.select_related("paciente", "dentista", "sala")
        .filter(data__year=ano, data__month=mes)
        .order_by("data", "hora")
    )

    dentista_selecionado = None
    if dentista_id:
        consultas_mes = consultas_mes.filter(dentista_id=dentista_id)
        dentista_selecionado = dentista_id

    consultas_mes = _aplicar_cor_dentista(consultas_mes)

    consultas_por_dia = defaultdict(list)
    for consulta in consultas_mes:
        consultas_por_dia[consulta.data].append(consulta)

    dentistas = Dentista.objects.all().order_by("nome")

    contexto = {
        "dias_do_mes": dias_do_mes,
        "consultas_por_dia": dict(consultas_por_dia),
        "mes": mes,
        "ano": ano,
        "nome_mes": NOMES_MESES[mes],
        "hoje": hoje,
        "dentistas": dentistas,
        "dentista_selecionado": dentista_selecionado,
    }
    contexto.update(_get_navegacao_mes(mes, ano))

    return render(request, "core/consultas/calendario.html", contexto)

@login_required
def agenda_semanal(request):
    hoje = date.today()

    try:
        deslocamento = int(request.GET.get("semana", 0))
    except (TypeError, ValueError):
        deslocamento = 0

    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_semana = inicio_semana + timedelta(weeks=deslocamento)
    fim_semana = inicio_semana + timedelta(days=6)

    dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]

    consultas = (
        Consulta.objects.select_related("paciente", "dentista", "sala")
        .filter(data__range=[inicio_semana, fim_semana])
        .order_by("data", "hora")
    )

    consultas = _aplicar_cor_dentista(consultas)

    consultas_formatadas = []
    for consulta in consultas:
        hora = consulta.hora.hour
        minuto = consulta.hora.minute

        top = ((hora - 7) * 80) + int((minuto / 60) * 80)
        altura = max(70, int((int(consulta.duracao_minutos) / 60) * 80) - 6)

        dia_index = (consulta.data - inicio_semana).days

        consultas_formatadas.append({
            "obj": consulta,
            "dia_index": dia_index,
            "top": top,
            "altura": altura,
        })

    horarios = [f"{h:02d}:00" for h in range(7, 20)]

    return render(request, "core/consultas/semana.html", {
        "hoje": hoje,
        "dias_semana": dias_semana,
        "inicio_semana": inicio_semana,
        "fim_semana": fim_semana,
        "semana_anterior": deslocamento - 1,
        "proxima_semana": deslocamento + 1,
        "consultas_formatadas": consultas_formatadas,
        "horarios": horarios,
    })
@login_required
def consultas_hoje(request):
    if not (eh_admin(request.user) or eh_recepcao(request.user) or eh_dentista(request.user)):
        raise PermissionDenied

    ...
    hoje = date.today()
    dentista_id = request.GET.get("dentista")

    consultas = (
        Consulta.objects.select_related("paciente", "dentista", "sala")
        .filter(data=hoje)
        .order_by("hora")
    )

    dentista_selecionado = None
    if dentista_id:
        consultas = consultas.filter(dentista_id=dentista_id)
        dentista_selecionado = dentista_id

    consultas = _aplicar_cor_dentista(consultas)

    dentistas = Dentista.objects.all().order_by("nome")

    return render(request, "core/consultas/hoje.html", {
        "consultas": consultas,
        "hoje": hoje,
        "dentistas": dentistas,
        "dentista_selecionado": dentista_selecionado,
    })

def atualizar_status_consulta(request, pk, novo_status):
    consulta = get_object_or_404(Consulta, pk=pk)

    if request.method == "POST":
        if novo_status in STATUS_CONSULTA_VALIDOS:
            consulta.status = novo_status
            consulta.save(update_fields=["status"])
            messages.success(request, f"Status da consulta alterado para {novo_status}.")
        else:
            messages.error(request, "Status inválido.")

    return redirect("consultas_hoje")

@login_required
def agenda_completa(request):
    if not (eh_admin(request.user) or eh_recepcao(request.user) or eh_dentista(request.user)):
        raise PermissionDenied
    consultas = (
        Consulta.objects.select_related("paciente", "dentista", "sala")
        .order_by("data", "hora")
    )

    consultas = _aplicar_cor_dentista(consultas)

    agenda = {}

    for consulta in consultas:
        chave = consulta.data.strftime("%d/%m/%Y")

        if chave not in agenda:
            agenda[chave] = []

        agenda[chave].append(consulta)

    return render(
        request,
        "core/consultas/agenda.html",
        {"agenda": agenda}
    )

def horarios_disponiveis(request):
    data = request.GET.get("data")
    dentista_id = request.GET.get("dentista")
    sala_id = request.GET.get("sala")
    consulta_id = request.GET.get("consulta_id")
    duracao = request.GET.get("duracao_minutos")

    horarios_base = [
        "07:00", "07:30", "08:00", "08:30", "09:00", "09:30",
        "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30", "18:00",
    ]

    def hora_para_minutos(texto):
        h, m = texto.split(":")
        return int(h) * 60 + int(m)

    def tem_conflito(inicio_a, fim_a, inicio_b, fim_b):
        return inicio_a < fim_b and inicio_b < fim_a

    try:
        duracao = int(duracao) if duracao else 60
    except (TypeError, ValueError):
        duracao = 60

    if not data:
        return JsonResponse({"horarios": horarios_base})

    consultas = Consulta.objects.filter(data=data)

    if consulta_id:
        consultas = consultas.exclude(pk=consulta_id)

    horarios_livres = []

    for horario in horarios_base:
        inicio_novo = hora_para_minutos(horario)
        fim_novo = inicio_novo + duracao

        conflito = False

        for consulta in consultas:
            inicio_existente = consulta.hora.hour * 60 + consulta.hora.minute
            fim_existente = inicio_existente + int(consulta.duracao_minutos)

            conflito_dentista = dentista_id and str(consulta.dentista_id) == str(dentista_id)
            conflito_sala = sala_id and str(consulta.sala_id) == str(sala_id)

            if conflito_dentista or conflito_sala:
                if tem_conflito(inicio_novo, fim_novo, inicio_existente, fim_existente):
                    conflito = True
                    break

        if not conflito:
            horarios_livres.append(horario)

    return JsonResponse({"horarios": horarios_livres})

def mover_consulta_semana(request, pk):
    if request.method != "POST":
        return JsonResponse({"ok": False, "erro": "Método inválido."}, status=405)

    consulta = get_object_or_404(Consulta, pk=pk)

    nova_data = request.POST.get("data")
    nova_hora = request.POST.get("hora")

    if not nova_data or not nova_hora:
        return JsonResponse({"ok": False, "erro": "Data e hora são obrigatórias."}, status=400)

    try:
        data_convertida = datetime.strptime(nova_data, "%Y-%m-%d").date()
        hora_convertida = datetime.strptime(nova_hora, "%H:%M").time()
    except ValueError:
        return JsonResponse({"ok": False, "erro": "Data ou hora inválida."}, status=400)

    def hora_para_minutos(hora_obj):
        return hora_obj.hour * 60 + hora_obj.minute

    def tem_conflito(inicio_a, fim_a, inicio_b, fim_b):
        return inicio_a < fim_b and inicio_b < fim_a

    inicio_novo = hora_para_minutos(hora_convertida)
    fim_novo = inicio_novo + int(consulta.duracao_minutos)

    consultas_mesmo_dia = Consulta.objects.filter(data=data_convertida).exclude(pk=consulta.pk)

    for outra in consultas_mesmo_dia:
        inicio_existente = hora_para_minutos(outra.hora)
        fim_existente = inicio_existente + int(outra.duracao_minutos)

        if consulta.dentista_id and outra.dentista_id == consulta.dentista_id:
            if tem_conflito(inicio_novo, fim_novo, inicio_existente, fim_existente):
                return JsonResponse({
                    "ok": False,
                    "erro": "Este dentista já possui consulta nesse horário."
                }, status=400)

        if consulta.sala_id and outra.sala_id == consulta.sala_id:
            if tem_conflito(inicio_novo, fim_novo, inicio_existente, fim_existente):
                return JsonResponse({
                    "ok": False,
                    "erro": "Esta sala já está ocupada nesse horário."
                }, status=400)

    consulta.data = data_convertida
    consulta.hora = hora_convertida
    consulta.save(update_fields=["data", "hora"])

    return JsonResponse({"ok": True})

def faturamento_dia(data):
    total = Consulta.objects.filter(
        data=data,
        status="concluido"
    ).aggregate(total=Sum("valor"))["total"]

    return total or 0

def salvar_odontograma_ajax(request, paciente_pk):
    paciente = get_object_or_404(Paciente, pk=paciente_pk)

    if request.method != "POST":
        return JsonResponse({"ok": False, "erro": "Método inválido."}, status=405)

    dente = request.POST.get("dente")
    status = request.POST.get("status")
    observacoes = request.POST.get("observacoes", "")

    if not dente or not status:
        return JsonResponse({"ok": False, "erro": "Dente e status são obrigatórios."}, status=400)

    item, created = OdontogramaItem.objects.update_or_create(
        paciente=paciente,
        dente=dente,
        defaults={
            "status": status,
            "observacoes": observacoes,
        }
    )

    OdontogramaHistorico.objects.create(
        paciente=paciente,
        dente=dente,
        status=status,
        observacoes=observacoes,
    )

    return JsonResponse({
        "ok": True,
        "dente": item.dente,
        "status": item.status,
        "status_label": item.get_status_display(),
        "observacoes": item.observacoes or "",
    })

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "Login realizado com sucesso.")
        return super().form_valid(form)
    
def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/home.html")