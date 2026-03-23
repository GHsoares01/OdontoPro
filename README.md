# 🦷 OdontoPro

> Sistema SaaS odontológico moderno para gestão completa de clínicas.

O **OdontoPro** é uma plataforma desenvolvida para clínicas odontológicas que desejam organizar, automatizar e escalar seus atendimentos, oferecendo uma experiência profissional tanto para gestores quanto para pacientes.

---

## 🚀 Sobre o Projeto

O OdontoPro é um sistema web que permite o gerenciamento completo de uma clínica odontológica, incluindo:

- Gestão de pacientes
- Agendamento de consultas
- Odontograma interativo
- Controle financeiro
- Dashboard com métricas
- Sistema multi-clínica (em desenvolvimento)

---

## 🧠 Objetivo

Criar uma plataforma SaaS moderna, escalável e acessível, capaz de competir com sistemas profissionais do mercado.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python + Django
- **Frontend:** HTML, CSS, JavaScript
- **Banco de Dados:** SQLite (atual) → PostgreSQL (futuro)
- **Controle de versão:** Git + GitHub

---

## 💻 Funcionalidades

### ✅ Já implementadas
- Sistema de login
- Dashboard
- Estrutura base do sistema
- Layout moderno (UI/UX melhorado)
- Base para odontograma
- Área administrativa

### 🚧 Em desenvolvimento
- Multi-clínica
- Financeiro completo
- Relatórios avançados
- Integração com WhatsApp
- Sistema de permissões (níveis de acesso)

---

## 📸 Preview

> Radm.png  la voçe vai ver o preview

---

## ⚙️ Como rodar o projeto

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/odontopro.git

# Entrar na pasta
cd odontopro

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar migrações
python manage.py migrate

# Iniciar servidor
python manage.py runserver
