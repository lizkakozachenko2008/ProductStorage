from sqlalchemy.orm.interfaces import LoaderOption
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload
from sqlalchemy import ForeignKey, String, Text, Boolean, Float, CheckConstraint, inspect
from datetime import datetime, timezone
from typing import Any, List, Optional, Set, Type, Union
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer

class Base(DeclarativeBase):
    __abstract__ = True

    repr_cols_num: int = 10
    repr_cols: list[str] = []

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {", ".join(cols)}>"
    
    @classmethod
    def get_loads(cls, visited: Union[Set[Type], None] = None) -> List[LoaderOption]:
        if visited is None:
            visited = set()

        if cls in visited:
            return []

        visited.add(cls)

        loads = []
        mapper: Any = inspect(cls)

        for rel in mapper.relationships:
            attr = getattr(cls, rel.key)

            nested_loads = rel.mapper.class_.get_loads(visited)
            if nested_loads:
                loads.append(selectinload(attr).options(*nested_loads))
            else:
                loads.append(selectinload(attr))

        return loads


class UserORM(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(String(15))




class AdminORM(Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(15), nullable=False)


class CategoryORM(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    products: Mapped[list['ProductORM']] = relationship('ProductORM', back_populates='category')


class ProductORM(Base):
    __tablename__ = 'products'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    min_quantity: Mapped[int] = mapped_column(default=0)
    unit: Mapped[str] = mapped_column(String(50)) 
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_quantity: Mapped[int]

    category: Mapped['CategoryORM'] = relationship(back_populates='products')
    stock: Mapped['StockORM'] = relationship(
        back_populates='product',
        cascade='all, delete-orphan',
        uselist=False
    )
    supplies: Mapped[List['SupplyORM']] = relationship(back_populates='product') 
    shipments: Mapped[List['ShipmentORM']] = relationship(back_populates='product')
    purchase_orders: Mapped[List['PurchaseOrderORM']] = relationship(back_populates='product') 

class StockORM(Base):
    """Таблица запасов - централизованное управление количеством товаров"""
    __tablename__ = 'stocks'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), unique=True)
    total_quantity: Mapped[int] = mapped_column(default=0)  # Общее количество
    reserved_quantity: Mapped[int] = mapped_column(default=0)  # Зарезервировано
    available_quantity: Mapped[int] = mapped_column(default=0)  # Доступно для использования
    last_updated: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    
    product: Mapped['ProductORM'] = relationship(back_populates='stock')
    
    __table_args__ = (
        CheckConstraint('total_quantity >= 0', name='check_total_quantity_non_negative'),
        CheckConstraint('reserved_quantity >= 0', name='check_reserved_quantity_non_negative'),
        CheckConstraint('available_quantity >= 0', name='check_available_quantity_non_negative'),
        CheckConstraint('reserved_quantity <= total_quantity', name='check_reserved_not_exceed_total'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_available()

    def calculate_available(self):
        """Рассчитать доступное количество"""
        self.available_quantity = self.total_quantity - self.reserved_quantity


class OverflowBinORM(Base):
    __tablename__ = 'overflow_bins'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] = mapped_column(default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_added: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    product: Mapped['ProductORM'] = relationship()
    
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_overflow_quantity_non_negative'),
    )


class PurchaseOrderORM(Base):
    __tablename__ = 'purchase_orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] = mapped_column(default=0)
    order_date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    supplier: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='pending')
    created_date: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    product: Mapped['ProductORM'] = relationship(back_populates='purchase_orders')  
    supplies: Mapped[List['SupplyORM']] = relationship(back_populates='purchase_order')

class ShelfORM(Base):
    __tablename__ = 'shelves'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey('categories.id'), nullable=True)
    max_capacity: Mapped[int] = mapped_column()
    current_quantity: Mapped[int] = mapped_column(default=0)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) 
    
    category: Mapped[Optional['CategoryORM']] = relationship()
    
    __table_args__ = (
        CheckConstraint('current_quantity >= 0', name='check_shelf_current_non_negative'),
        CheckConstraint('current_quantity <= max_capacity', name='check_shelf_not_exceed_capacity'),
    )


class MovementHistoryORM(Base):
    __tablename__ = 'movement_history'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    from_shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey('shelves.id'), nullable=True)
    to_shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey('shelves.id'), nullable=True)
    from_overflow: Mapped[bool] = mapped_column(default=False)
    to_overflow: Mapped[bool] = mapped_column(default=False)
    quantity: Mapped[int] = mapped_column(default=0)
    movement_date: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))
    movement_type: Mapped[str] = mapped_column(String(50), default='placement')  # placement, relocation, shipping

    product: Mapped['ProductORM'] = relationship()
    from_shelf: Mapped[Optional['ShelfORM']] = relationship(foreign_keys=[from_shelf_id])
    to_shelf: Mapped[Optional['ShelfORM']] = relationship(foreign_keys=[to_shelf_id])


class NotificationORM(Base):
    __tablename__ = 'notifications'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey('shelves.id'), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean,default=False)
    created_date: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))
    priority: Mapped[str] = mapped_column(String(20), default='medium')
    notification_type: Mapped[str] = mapped_column(String(50), default='info')  # info, warning, alert

    product: Mapped['ProductORM'] = relationship()
    shelf: Mapped[Optional['ShelfORM']] = relationship()


class ProductPlacementORM(Base):
    __tablename__ = 'product_placements'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey('shelves.id'), nullable=True)
    overflow_id: Mapped[Optional[int]] = mapped_column(ForeignKey('overflow_bins.id'), nullable=True)
    quantity: Mapped[int] = mapped_column(default=0)
    placement_date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    last_updated: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    product: Mapped['ProductORM'] = relationship()
    shelf: Mapped[Optional['ShelfORM']] = relationship()
    overflow: Mapped[Optional['OverflowBinORM']] = relationship()
    
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_placement_quantity_non_negative'),
    )
    
class SupplyORM(Base):
    __tablename__ = 'supplies'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey('purchase_orders.id'), nullable=True)  
    quantity: Mapped[int] = mapped_column()
    supplier: Mapped[str] = mapped_column(String(200))  
    supply_date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    delivery_date: Mapped[Optional[datetime]] = mapped_column(nullable=True) 
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  
    status: Mapped[str] = mapped_column(default='delivered')

    product: Mapped['ProductORM'] = relationship(back_populates='supplies')
    purchase_order: Mapped[Optional['PurchaseOrderORM']] = relationship()  
    
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_supply_quantity_positive'),
    )


class ShipmentORM(Base):
    """Отгрузка товара со склада"""
    __tablename__ = 'shipments'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] = mapped_column()
    shipment_date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    destination: Mapped[str] = mapped_column(String(200))
    customer: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    order_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='completed')

    product: Mapped['ProductORM'] = relationship(back_populates='shipments')
    
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_shipment_quantity_positive'),
    )