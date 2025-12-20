from typing import Any, List, Optional, Type, TypeVar, Sequence, Dict
from sqlalchemy import select, func, extract, and_, or_, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date

from src.database import db
from src.models import *

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
            return list_models

    def update(self, data: dict[str, Any], **filters) -> Optional[ModelType]:
        with db.session as session:
            query = session.query(self.model).filter_by(**filters)
            obj = query.one_or_none()

            if obj:
                for key, value in data.items():
                    setattr(obj, key, value)
                session.commit()
                session.refresh(obj)

            return obj

    def delete(self, **filters) -> Optional[ModelType]:
        with db.session as session:
            obj = session.query(self.model).filter_by(**filters).first()
            if obj:
                session.delete(obj)
                session.commit()
            
            return obj

    def find(self, **filters) -> Optional[ModelType]:
        with db.session as session:
            query = (
                select(self.model)
                .filter_by(**filters)
                .options(*self.model.get_loads()) # type: ignore
            )
            result = session.execute(query)
            return result.scalar_one_or_none()

    def find_all(self, **filters) -> Sequence[ModelType]:
        with db.session as session:
            query = (
                select(self.model)
                .filter_by(**filters)
                .options(*self.model.get_loads()) # type: ignore
            )
            result = session.execute(query)
            return result.scalars().all()

    # Специальные методы для StockORM
    def update_stock_quantity(self, product_id: int, quantity_change: int,
                            is_reservation: bool = False) -> Optional[ModelType]:
        """Обновить количество запасов товара"""
        if self.model != StockORM:
            raise ValueError("Этот метод доступен только для StockORM")
        
        with db.session as session:
            stock = session.query(StockORM).filter_by(product_id=product_id).first()
            
            if not stock:
                # Создаем запись запасов, если ее нет
                stock = StockORM(
                    product_id=product_id,
                    total_quantity=max(quantity_change, 0) if not is_reservation else 0,
                    reserved_quantity=max(quantity_change, 0) if is_reservation else 0
                )
                stock.calculate_available()
                session.add(stock)
            else:
                if is_reservation:
                    # Изменяем резерв
                    stock.reserved_quantity += quantity_change
                    if stock.reserved_quantity < 0:
                        stock.reserved_quantity = 0
                else:
                    # Изменяем общее количество
                    stock.total_quantity += quantity_change
                    if stock.total_quantity < 0:
                        stock.total_quantity = 0
                
                # Пересчитываем доступное количество
                stock.calculate_available()
                stock.last_updated = datetime.now(timezone.utc)
            
            session.commit()
            session.refresh(stock)
            return stock

    def get_available_quantity(self, product_id: int) -> int:
        """Получить доступное количество товара"""
        if self.model != StockORM:
            raise ValueError("Этот метод доступен только для StockORM")
        
        stock = self.find(product_id=product_id)
        if stock:
            return stock.available_quantity
        return 0

    def reserve_stock(self, product_id: int, quantity: int) -> Optional[ModelType]:
        """Зарезервировать количество товара"""
        return self.update_stock_quantity(product_id, quantity, is_reservation=True)

    def release_stock(self, product_id: int, quantity: int) -> Optional[ModelType]:
        """Освободить зарезервированное количество товара"""
        return self.update_stock_quantity(product_id, -quantity, is_reservation=True)

    # Методы для поиска низких запасов
    def find_low_stock(self) -> List[ProductORM]:
        """Найти товары с текущим количеством <= минимальному"""
        from src.models import ProductORM
        
        if self.model != ProductORM:
            raise ValueError("Этот метод доступен только для ProductORM")
            
        with db.session as session:
            stmt = (
                select(ProductORM)
                .join(StockORM, ProductORM.id == StockORM.product_id)
                .where(StockORM.available_quantity <= ProductORM.min_quantity)
            )
            result = session.execute(stmt)
            return result.scalars().all()

    # Методы для отчетов
    def get_product_placements_summary(self) -> List[Dict]:
        """Получить сводку по размещению товаров"""
        if self.model != ProductPlacementORM:
            raise ValueError("Этот метод доступен только для ProductPlacementORM")
        
        with db.session as session:
            stmt = (
                select(
                    ProductPlacementORM.product_id,
                    func.sum(ProductPlacementORM.quantity).label('total_placed'),
                    func.count(ProductPlacementORM.id).label('placement_count')
                )
                .group_by(ProductPlacementORM.product_id)
            )
            result = session.execute(stmt)
            return [dict(row._mapping) for row in result]

    def get_monthly_supplies(self, year: int, month: int) -> List[SupplyORM]:
        """Найти поставки за указанный месяц"""
        if self.model != SupplyORM:
            raise ValueError("Этот метод доступен только для SupplyORM")
        
        with db.session as session:
            stmt = (
                select(SupplyORM)
                .where(
                    extract('year', SupplyORM.supply_date) == year,
                    extract('month', SupplyORM.supply_date) == month
                )
                .order_by(SupplyORM.supply_date)
            )
            result = session.execute(stmt)
            return result.scalars().all()

    def get_monthly_shipments(self, year: int, month: int) -> List[ShipmentORM]:
        """Найти отгрузки за указанный месяц"""
        if self.model != ShipmentORM:
            raise ValueError("Этот метод доступен только для ShipmentORM")
        
        with db.session as session:
            stmt = (
                select(ShipmentORM)
                .where(
                    extract('year', ShipmentORM.shipment_date) == year,
                    extract('month', ShipmentORM.shipment_date) == month
                )
                .order_by(ShipmentORM.shipment_date)
            )
            result = session.execute(stmt)
            return result.scalars().all()

    def get_overflow_with_stock(self) -> List[OverflowBinORM]:
        """Найти товары в отстойнике с положительным количеством"""
        if self.model != OverflowBinORM:
            raise ValueError("Этот метод доступен только для OverflowBinORM")
        
        with db.session as session:
            stmt = select(OverflowBinORM).where(OverflowBinORM.quantity > 0)
            result = session.execute(stmt)
            return result.scalars().all()

    def find_recent_movements(self, days: int = 7) -> List[MovementHistoryORM]:
        """Найти перемещения за последние N дней"""
        if self.model != MovementHistoryORM:
            raise ValueError("Этот метод доступен только для MovementHistoryORM")
        
        since_date = datetime.now() - timedelta(days=days)
        with db.session as session:
            stmt = (
                select(MovementHistoryORM)
                .where(MovementHistoryORM.movement_date >= since_date)
                .order_by(MovementHistoryORM.movement_date.desc())
            )
            result = session.execute(stmt)
            return result.scalars().all()

    def count_by_category(self, category_id: int) -> int:
        """Подсчитать количество продуктов в категории"""
        if self.model != ProductORM:
            raise ValueError("Этот метод доступен только для ProductORM")
        
        with db.session as session:
            stmt = select(func.count(ProductORM.id)).where(ProductORM.category_id == category_id)
            result = session.execute(stmt)
            return result.scalar() or 0

    def get_stock_statistics(self) -> Dict:
        """Получить статистику по запасам"""
        if self.model != StockORM:
            raise ValueError("Этот метод доступен только для StockORM")
        
        with db.session as session:
            # Общая статистика
            total_stats = session.execute(
                select(
                    func.count(StockORM.id).label('total_products'),
                    func.sum(StockORM.total_quantity).label('total_quantity'),
                    func.sum(StockORM.reserved_quantity).label('total_reserved'),
                    func.sum(StockORM.available_quantity).label('total_available')
                )
            ).first()
            
            # Товары с низким запасом
            low_stock_count = session.execute(
                select(func.count(ProductORM.id))
                .join(StockORM, ProductORM.id == StockORM.product_id)
                .where(StockORM.available_quantity <= ProductORM.min_quantity)
            ).scalar() or 0
            
            # Товары с нулевым запасом
            out_of_stock_count = session.execute(
                select(func.count(StockORM.id))
                .where(StockORM.available_quantity <= 0)
            ).scalar() or 0
            
            return {
                'total_products': total_stats.total_products or 0,
                'total_quantity': total_stats.total_quantity or 0,
                'total_reserved': total_stats.total_reserved or 0,
                'total_available': total_stats.total_available or 0,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count
            }

    def get_inventory_value(self) -> float:
        """Рассчитать общую стоимость инвентаря"""
        if self.model != ProductORM:
            raise ValueError("Этот метод доступен только для ProductORM")
        
        with db.session as session:
            stmt = (
                select(func.sum(ProductORM.price * StockORM.available_quantity))
                .join(StockORM, ProductORM.id == StockORM.product_id)
                .where(ProductORM.price.is_not(None))
            )
            result = session.execute(stmt)
            return result.scalar() or 0.0

    def get_shelf_utilization(self) -> List[Dict]:
        """Получить статистику использования стеллажей"""
        if self.model != ShelfORM:
            raise ValueError("Этот метод доступен только для ShelfORM")
        
        with db.session as session:
            stmt = (
                select(
                    ShelfORM.id,
                    ShelfORM.name,
                    ShelfORM.max_capacity,
                    ShelfORM.current_quantity,
                    ((ShelfORM.current_quantity * 100.0) / ShelfORM.max_capacity).label('utilization_percent'),
                    (ShelfORM.max_capacity - ShelfORM.current_quantity).label('free_space')
                )
                .order_by(ShelfORM.current_quantity.desc())
            )
            result = session.execute(stmt)
            return [dict(row._mapping) for row in result]


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
    def stock_repo() -> SqlAlchemyRepository[StockORM]:
        return SqlAlchemyRepository(StockORM)

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

    @staticmethod
    def shipment_repo() -> SqlAlchemyRepository[ShipmentORM]:
        return SqlAlchemyRepository(ShipmentORM)