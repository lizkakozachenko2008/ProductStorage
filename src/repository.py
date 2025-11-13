from typing import List, Type, TypeVar

from sqlalchemy import update, delete, select, ClauseElement

from src.database import db
from src.models import (
    AdminORM, Base, UserORM, CategoryORM, ProductORM, 
    OverflowBinORM, PurchaseOrderORM, ShelfORM, MovementHistoryORM,
    NotificationORM, ProductPlacementORM, SupplyORM
)


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

    # МЕТОДЫ ДЛЯ ЗАПРОСОВ
    def find_low_stock(self):
        """Найти товары с текущим количеством <= минимальному"""
        from src.models import ProductORM
        
        if self.model != ProductORM:
            raise ValueError("Этот метод доступен только для ProductORM")
            
        stmt = select(ProductORM).where(
            ProductORM.current_quantity <= ProductORM.min_quantity
        )
        with db.session as session:
            result = session.execute(stmt)
            return result.scalars().all()

    def find_recent_movements(self, days: int = 7):
        """Найти перемещения за последние N дней"""
        from src.models import MovementHistoryORM
        from datetime import datetime, timedelta
        
        if self.model != MovementHistoryORM:
            raise ValueError("Этот метод доступен только для MovementHistoryORM")
        
        since_date = datetime.now() - timedelta(days=days)
        stmt = select(MovementHistoryORM).where(
            MovementHistoryORM.movement_date >= since_date
        ).order_by(MovementHistoryORM.movement_date.desc())
        
        with db.session as session:
            result = session.execute(stmt)
            return result.scalars().all()


class RepoFactory:
    @staticmethod
    def user_repo() -> SqlAlchemyRepository[UserORM]:
        return SqlAlchemyRepository(UserORM)

    @staticmethod
    def admin_repo() -> SqlAlchemyRepository[AdminORM]:
        return SqlAlchemyRepository(AdminORM)

    @staticmethod
    def category_repo() -> SqlAlchemyRepository[CategoryORM]:
        return SqlAlchemyRepository(CategoryORM)

    @staticmethod
    def product_repo() -> SqlAlchemyRepository[ProductORM]:
        return SqlAlchemyRepository(ProductORM)

    @staticmethod
    def overflow_bin_repo() -> SqlAlchemyRepository[OverflowBinORM]:
        return SqlAlchemyRepository(OverflowBinORM)

    @staticmethod
    def purchase_order_repo() -> SqlAlchemyRepository[PurchaseOrderORM]:
        return SqlAlchemyRepository(PurchaseOrderORM)

    @staticmethod
    def shelf_repo() -> SqlAlchemyRepository[ShelfORM]:
        return SqlAlchemyRepository(ShelfORM)

    @staticmethod
    def movement_history_repo() -> SqlAlchemyRepository[MovementHistoryORM]:
        return SqlAlchemyRepository(MovementHistoryORM)

    @staticmethod
    def notification_repo() -> SqlAlchemyRepository[NotificationORM]:
        return SqlAlchemyRepository(NotificationORM)

    @staticmethod
    def product_placement_repo() -> SqlAlchemyRepository[ProductPlacementORM]:
        return SqlAlchemyRepository(ProductPlacementORM)

    @staticmethod
    def supply_repo() -> SqlAlchemyRepository[SupplyORM]:
        return SqlAlchemyRepository(SupplyORM)