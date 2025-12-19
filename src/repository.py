from typing import Any, List, Optional, Type, TypeVar, Sequence

from sqlalchemy import select

from src.database import db
from src.models import * 
# (
#     AdminORM, Base, UserORM, CategoryORM, ProductORM, 
#     OverflowBinORM, PurchaseOrderORM, ShelfORM, MovementHistoryORM,
#     NotificationORM, ProductPlacementORM, SupplyORM
# )


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
        data: dict[str, Any],
        **filters
    ) -> Optional[ModelType]:
        with db.session as session:
            query = session.query(self.model).filter_by(**filters)
            obj = query.one_or_none()

            if obj:
                for key, value in data.items():
                    setattr(obj, key, value)
                session.commit()

            print(obj)

            return obj

    def delete(self,
        **filters
    ) -> Optional[ModelType]:
        with db.session as session:
            obj = session.query(self.model).filter_by(**filters).first()
            if obj:
                session.delete(obj)
                session.commit()
            
            return obj

    def find(
            self,
            **filters
    ) -> Optional[ModelType]:
        with db.session as session:
            query = (
                select(self.model)
                .filter_by(**filters)
            )

            result = session.execute(query)
            return result.scalar_one_or_none()

    def find_all(
            self,
            **filters,
    ) -> Sequence[ModelType]:
        with db.session as session:
            query = (
                select(self.model)
                .filter_by(**filters)
            )

            result = session.execute(query)

            return result.scalars().all()

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
        
    # МЕТОД ДЛЯ ПОДСЧЕТА КОЛИЧЕСТВА ПРОДУКТОВ В КАТЕГОРИИ
    def count_by_category(self, category_id: int) -> int:
        """Подсчитать количество продуктов в категории"""
        from src.models import ProductORM
        
        if self.model != ProductORM:
            raise ValueError("Этот метод доступен только для ProductORM")
            
        stmt = select(ProductORM).where(ProductORM.category_id == category_id)
        with db.session as session:
            result = session.execute(stmt)
            return len(result.scalars().all())

    # МЕТОД ДЛЯ ПОИСКА ТОВАРОВ В ОТСТОЙНИКЕ (с количеством > 0)
    def find_overflow_with_stock(self):
        """Найти товары в отстойнике с положительным количеством"""
        from src.models import OverflowBinORM
        
        if self.model != OverflowBinORM:
            raise ValueError("Этот метод доступен только для OverflowBinORM")
            
        stmt = select(OverflowBinORM).where(OverflowBinORM.quantity > 0)
        with db.session as session:
            result = session.execute(stmt)
            return result.scalars().all()

    # МЕТОД ДЛЯ ПОИСКА РАЗМЕЩЕНИЙ НА КОНКРЕТНОМ СТЕЛЛАЖЕ
    def find_placements_on_shelf(self, shelf_id: int):
        """Найти размещения на конкретном стеллаже"""
        from src.models import ProductPlacementORM
        
        if self.model != ProductPlacementORM:
            raise ValueError("Этот метод доступен только для ProductPlacementORM")
            
        stmt = select(ProductPlacementORM).where(
            ProductPlacementORM.shelf_id == shelf_id,
            ProductPlacementORM.quantity > 0
        )
        with db.session as session:
            result = session.execute(stmt)
            return result.scalars().all()

    # МЕТОД ДЛЯ ОТЧЕТА О ПОСТАВКАХ ЗА МЕСЯЦ
    def find_supplies_by_month(self, year: int, month: int):
        """Найти поставки за указанный месяц"""
        from src.models import SupplyORM
        from sqlalchemy import extract
        
        if self.model != SupplyORM:
            raise ValueError("Этот метод доступен только для SupplyORM")
            
        stmt = select(SupplyORM).where(
            extract('year', SupplyORM.supply_date) == year,
            extract('month', SupplyORM.supply_date) == month
        ).order_by(SupplyORM.supply_date)
        
        with db.session as session:
            result = session.execute(stmt)
            return result.scalars().all()

    # МЕТОД ДЛЯ ПОИСКА ПЕРЕМЕЩЕНИЙ С ОТГРУЗКОЙ (со склада наружу)
    def find_shipments_by_month(self, year: int, month: int):
        """Найти отгрузки (перемещения со склада наружу) за месяц"""
        from src.models import MovementHistoryORM
        from sqlalchemy import extract
        
        if self.model != MovementHistoryORM:
            raise ValueError("Этот метод доступен только для MovementHistoryORM")
            
        # Отгрузки: from_shelf есть, to_shelf нет, и не в отстойник
        stmt = select(MovementHistoryORM).where(
            extract('year', MovementHistoryORM.movement_date) == year,
            extract('month', MovementHistoryORM.movement_date) == month,
            MovementHistoryORM.from_shelf_id.is_not(None),
            MovementHistoryORM.to_shelf_id.is_(None),
            MovementHistoryORM.to_overflow == False
        ).order_by(MovementHistoryORM.movement_date)
        
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