from src.models import Base, AdminORM, UserORM, ProductORM, StockORM
from src.database import db

def setup_db():
    # Создаем все таблицы
    Base.metadata.create_all(
        bind=db.engine
    )
    
    # Создаем администратора по умолчанию
    with db.session as session:
        admin = session.query(AdminORM).filter_by(login="admin").first()

        if not admin:
            mock_admin = AdminORM(
                login="adminok",
                password="123456789"
            )
            session.add(mock_admin)
            session.commit()

    # Создаем тестовых пользователей
    with db.session as session:
        users = session.query(UserORM).all()
        if not users:
            mock_users = [
                UserORM(
                    login='user1',
                    email='user1@example.com',
                    password='password123'
                ),
                UserORM(
                    login='user2',
                    email='user2@example.com',
                    password='password123'
                ),
                UserORM(
                    login='manager1',
                    email='manager@example.com',
                    password='password123'
                ),
            ]
            session.add_all(mock_users)
            session.commit()

    # Создаем начальные запасы для существующих товаров
    with db.session as session:
        # Получаем все товары без записей запасов
        products = session.query(ProductORM).all()
        
        for product in products:
            existing_stock = session.query(StockORM).filter_by(product_id=product.id).first()
            
            if not existing_stock:
                # Создаем начальные запасы
                stock = StockORM(
                    product_id=product.id,
                    total_quantity=0,
                    reserved_quantity=0
                )
                stock.calculate_available()
                session.add(stock)
        
        session.commit()