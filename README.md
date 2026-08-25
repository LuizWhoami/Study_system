# Study System - Plataforma de Estudos para Concursos

Sistema completo para organização de estudos, com foco em produtividade, revisões e acompanhamento de desempenho.

## Estrutura
- Django + PostgreSQL
- Bootstrap 5, Chart.js, EasyMDE
- Apps modulares

## Configuração
1. Crie um ambiente virtual: `python -m venv venv`
2. Ative: `source venv/bin/activate` (Linux/Mac) ou `venv\Scripts\activate` (Windows)
3. Instale as dependências: `pip install -r requirements.txt`
4. Configure o banco de dados no arquivo `.env`
5. Execute as migrações: `python manage.py migrate`
6. Crie um superusuário: `python manage.py createsuperuser`
7. Inicie o servidor: `python manage.py runserver`
 
#### tem algumas dependecias
