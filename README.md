# Sistema de Gerenciamento de Clínica Veterinária

Este é um sistema web desenvolvido em Flask para gerenciar o cadastro de animais, clínicas e agendamentos de procedimentos. A aplicação foi refatorada para uma arquitetura modular e inclui funcionalidades de segurança, como a verificação de agendamentos por token.

## Arquitetura

O projeto foi estruturado de forma modular para separar as responsabilidades e facilitar a manutenção:

- `M Cadastro vet2.py`: Ponto de entrada da aplicação, responsável por configurar e executar o servidor Flask.
- `__init__.py`: Inicializa o pacote da aplicação, importando os módulos necessários.
- `models.py`: Define os modelos de dados do SQLAlchemy (`User`, `Clinic`, `Animal`).
- `services.py`: Contém a lógica de negócios e as funções de acesso ao banco de dados.
- `extensions.py`: Configura e inicializa as extensões do Flask (SQLAlchemy, LoginManager).
- `instance/`: Diretório onde o banco de dados (`pets.db`) e os logs são armazenados.
- `scripts/`: Contém scripts de utilidade para manutenção e testes.

## Funcionalidades Principais

O sistema possui três perfis de usuários com diferentes níveis de acesso:

1.  **Administrador:**
    *   Visão completa de todos os animais e agendamentos.
    *   Gerenciamento completo de clínicas (criar, editar, remover).
    *   Pode agendar procedimentos para qualquer clínica.

2.  **Clínica:**
    *   Vê os animais agendados para sua clínica.
    *   Vê uma lista de animais aguardando atendimento e pode agendá-los.
    *   Após o agendamento, um token de verificação é gerado.

3.  **Usuário (Dono do Pet):**
    *   Pode se cadastrar e fazer login.
    *   Cadastra seus próprios animais.
    *   Recebe um token (simulado via log) para confirmar o agendamento.

### Fluxo de Verificação por Token

Para aumentar a segurança, o agendamento de um procedimento gera um token de 6 dígitos. O fluxo é o seguinte:

1.  A clínica realiza o agendamento de um animal.
2.  O sistema gera um token numérico e o associa ao agendamento.
3.  Uma notificação (simulada por um log em `instance/sms.log`) é enviada ao dono do pet com o token.
4.  A clínica deve usar esse token para validar e confirmar o procedimento, garantindo que o dono do pet está ciente.

## Tecnologias Utilizadas

- **Backend:** Python com Flask
- **Banco de Dados:** SQLAlchemy com SQLite
- **Autenticação:** Flask-Login
- **Frontend:** HTML renderizado no Flask com `render_template_string`

## Como Executar o Projeto

1.  **Pré-requisitos:**
    *   Python 3
    *   Dependências do Flask (instale com `pip install -r requirements.txt` se disponível, ou individualmente):
        - `Flask`
        - `Flask-SQLAlchemy`
        - `Flask-Login`
        - `Werkzeug`

2.  **Execução:**
    *   Clone o repositório.
    *   Execute o arquivo principal da aplicação:
      ```bash
      python "M Cadastro vet2.py"
      ```
    *   Acesse a aplicação em `http://127.0.0.1:5000`.

3.  **Banco de Dados:**
    *   O banco de dados (`pets.db`) será criado automaticamente na pasta `instance`.
    *   Se houver alterações nos modelos, apague o arquivo `pets.db` para recriá-lo.

## Credenciais de Acesso Padrão

Ao iniciar a aplicação pela primeira vez, os seguintes usuários são criados:

- **Administrador:**
    - **Usuário:** `admin`
    - **Senha:** `admin`

- **Clínica (associado à 'Clínica Vet 1'):**
    - **Usuário:** `clinic_user`
    - **Senha:** `clinic`

Novos usuários (donos de pets) podem se cadastrar através da página de registro.