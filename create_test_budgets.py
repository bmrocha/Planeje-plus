from app import app, db
from models import Budget, Company
from datetime import datetime

def create_test_budgets():
    # Lista de orçamentos para teste
    test_budgets = [
        {
            'title': 'Campanha Marketing Digital Q4',
            'description': 'Campanha de marketing digital para o último trimestre do ano',
            'solicitado': 'Maria Silva',
            'sector': 'Marketing',
            'companies': [
                {'name': 'Digital Ads Agency'},
                {'name': 'Social Media Pro'}
            ]
        },
        {
            'title': 'Atualização Equipamentos TI',
            'description': 'Renovação de computadores e equipamentos do setor de TI',
            'solicitado': 'João Santos',
            'sector': 'TI',
            'companies': [
                {'name': 'Tech Solutions Inc'},
                {'name': 'Hardware Express'}
            ]
        },
        {
            'title': 'Treinamento Equipe Vendas',
            'description': 'Programa de capacitação para equipe de vendas',
            'solicitado': 'Ana Oliveira',
            'sector': 'Comercial',
            'companies': [
                {'name': 'Sales Training Co'},
                {'name': 'Professional Development Ltd'}
            ]
        },
        {
            'title': 'Reforma Escritório',
            'description': 'Reforma e modernização do espaço de trabalho',
            'solicitado': 'Pedro Costa',
            'sector': 'Administrativo',
            'companies': [
                {'name': 'Construction Corp'},
                {'name': 'Office Design Solutions'}
            ]
        },
        {
            'title': 'Material Promocional',
            'description': 'Produção de material promocional para eventos',
            'solicitado': 'Carla Mendes',
            'sector': 'Marketing',
            'companies': [
                {'name': 'Print Solutions'},
                {'name': 'Promo Items Co'}
            ]
        }
    ]

    with app.app_context():
        # Buscar um aprovador e um solicitante para associar aos orçamentos
        from models import User
        aprovador = User.query.filter_by(role='aprovador', is_active=True).first()
        solicitante = User.query.filter_by(role='solicitante', is_active=True).first()

        if not aprovador or not solicitante:
            print("Erro: Necessário ter pelo menos um aprovador e um solicitante cadastrados")
            return

        # Criar os orçamentos
        for budget_data in test_budgets:
            budget = Budget(
                title=budget_data['title'],
                description=budget_data['description'],
                solicitado=budget_data['solicitado'],
                requested_name=solicitante.name,
                sector=budget_data['sector'],
                solicitante_id=solicitante.id,
                aprovador_id=aprovador.id,
                status='pendente',
                request_date=datetime.utcnow()
            )

            # Adicionar empresas ao orçamento
            for company_data in budget_data['companies']:
                company = Company(name=company_data['name'])
                budget.companies.append(company)

            db.session.add(budget)

        # Commit das alterações
        try:
            db.session.commit()
            print("Orçamentos de teste criados com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar orçamentos: {str(e)}")

if __name__ == '__main__':
    create_test_budgets()
