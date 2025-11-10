from typing import List, Type, TypeVar

from sqlalchemy import update, delete, select, ClauseElement

from src.database import db
from src.models import AdminORM, Base, UserORM


ModelType = TypeVar('ModelType', bound=Base)


class SqlAlchemyRepository[ModelType]:
    def __init__(self, model: Type[ModelType]):
        self.model: Type[ModelType] = model

    def create(self, data: dict) -> ModelType:
        with db.session as session:
            model = self.model(**data)
            session.add(model)
            session.commit()
            session.refresh(model)

            return model

    def create_multiple(self, data: List[dict]) -> List[ModelType]:
        with db.session as session:
            list_models: list[ModelType] = []
            for row in data:
                model = self.model(**row)
                list_models.append(model)

            session.add_all(list_models)
            session.commit()
            session.refresh(list_models)

            return list_models

    def update(
        self,
        data: dict,
        conditions: List[ClauseElement] = None,
        **filters
    ) -> ModelType:
        with db.session as session:
            query = session.query(self.model).filter(*conditions or [], **filters)
            obj = query.one_or_none()

            if obj:
                for key, value in data.items():
                    setattr(obj, key, value)
                session.commit()

            return obj

    def delete(self,
        conditions: List[ClauseElement] = None,
        **filters
    ) -> ModelType:
        with db.session as session:
            obj = session.query(self.model).filter_by(**filters).first()
            if obj:
                session.delete(obj)
                session.commit()
            
            return obj

    def find(
            self,
            conditions: List[ClauseElement] = None,
            **filters
    ) -> ModelType:
        with db.session as session:
            query = (
                select(self.model)
                .where(*(conditions or []))
                .filter_by(**filters)
            )

            result = session.execute(query)
            return result.scalars().first()

    def find_all(
            self,
            conditions: List[ClauseElement] = None,
            **filters,
    ) -> List[ModelType]:
        with db.session as session:
            query = (
                select(self.model)
                .where(*(conditions or []))
                .filter_by(**filters)
            )

            result = session.execute(query)

            return result.unique().scalars().all()


class RepoFactory:
    @staticmethod
    def user_repo() -> SqlAlchemyRepository[UserORM]:
        return SqlAlchemyRepository(UserORM)

    @staticmethod
    def admin_repo() -> SqlAlchemyRepository[AdminORM]:
        return SqlAlchemyRepository(AdminORM)
