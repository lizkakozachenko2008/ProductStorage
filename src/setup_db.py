from src.models import Base, UserORM
from src.database import db

def setup_db():
    Base.metadata.create_all(
        bind=db.engine
    )
    
    with db.session as session:
        users = session.query(UserORM)
        if not users:
            mock_users = [
                UserORM(
                    login='1',
                    email='1@example.com',
                    password='12341234'
                ),
                UserORM(
                    login='12',
                    email='12@example.com',
                    password='12341234'
                ),
                UserORM(
                    login='123',
                    email='123@example.com',
                    password='12341234'
                ),
                UserORM(
                    login='1234',
                    email='1234@example.com',
                    password='12341234'
                ),
                UserORM(
                    login='12345',
                    email='12345@example.com',
                    password='12341234'
                ),
            ]

            session.add_all(mock_users)
            session.commit()