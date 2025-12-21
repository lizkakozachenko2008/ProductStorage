from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = 'sqlite:///mydb.db'

class Database:
    def __init__(self) -> None:
        self.engine: Engine = create_engine(
            url=DATABASE_URL,
            echo=True
        )

        self.session_factory: sessionmaker = (
            sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False
        ))

    @property
    def session(self) -> Session:
        return self.session_factory()

db = Database()