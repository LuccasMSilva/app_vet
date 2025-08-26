# Sistema de Gerenciamento de Clínica Veterinária

Este é um sistema web simples desenvolvido em Flask para gerenciar o cadastro de animais, clínicas e agendamentos de procedimentos. A aplicação utiliza SQLAlchemy para interagir com um banco de dados SQLite.

## Funcionalidades Principais

O sistema possui três perfis de usuários com diferentes níveis de acesso:

1.  **Administrador:**
    *   Visão completa de todos os animais e agendamentos.
    *   Gerenciamento completo de clínicas (criar, editar, remover).
    *   Pode agendar procedimentos para qualquer clínica.

2.  **Clínica:**
    *   Vê os animais que já estão agendados para sua clínica.
    *   Vê uma lista de animais que aguardam atendimento e pode agendá-los para si.
    *   O agendamento é restrito à sua própria clínica.

3.  **Usuário (Dono do Pet):**
    *   Pode se cadastrar e fazer login.
    *   Cadastra seus próprios animais.
    *   Vê o status de agendamento dos seus animais.

## Tecnologias Utilizadas

*   **Backend:** Python com Flask
*   **Banco de Dados:** SQLAlchemy com SQLite
*   **Frontend:** HTML renderizado diretamente no Flask com `render_template_string`

## Como Executar o Projeto

1.  **Pré-requisitos:**
    *   Python 3
    *   Flask (`pip install Flask`)
    *   Flask-SQLAlchemy (`pip install Flask-SQLAlchemy`)
    *   Werkzeug (`pip install Werkzeug`)

2.  **Execução:**
    *   Clone o repositório.
    *   Execute o arquivo `M Cadastro vet2.py`:
      ```bash
      python "M Cadastro vet2.py"
      ```
    *   Acesse a aplicação no seu navegador em `http://127.0.0.1:5000`.

3.  **Banco de Dados:**
    *   O arquivo do banco de dados (`pets.db`) será criado automaticamente na pasta `instance`.
    *   Se você fizer alterações nos modelos (tabelas), apague o arquivo `pets.db` para que ele seja recriado com a nova estrutura na próxima execução.

## Credenciais de Acesso Padrão

Ao iniciar a aplicação pela primeira vez, os seguintes usuários são criados:

*   **Administrador:**
    *   **Usuário:** `admin`
    *   **Senha:** `admin`

*   **Clínica (associado à 'Clínica Vet 1'):**
    *   **Usuário:** `clinic_user`
    *   **Senha:** `clinic`

Você pode cadastrar novos usuários (donos de pets) através da página de registro.