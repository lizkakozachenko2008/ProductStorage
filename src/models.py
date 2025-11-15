from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, Boolean, Float
from datetime import datetime, timezone
from typing import Optional

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


class UserORM(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(String(15))


class AdminORM(Base):
    __tablename__ = 'admins'

    login: Mapped[str] = mapped_column(primary_key=True)
    password: Mapped[str] = mapped_column (String(15))

class CategoryORM(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class ProductORM(Base):
    __tablename__ = 'products'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    min_quantity: Mapped[int] = mapped_column(default=0)
    unit: Mapped[str] = mapped_column(String(50)) 
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_quantity: Mapped[int] = mapped_column(default=0)
    price: Mapped[float] = mapped_column(Float,nullable=True)

    category: Mapped['CategoryORM'] = relationship(back_populates='products')

class OverflowBinORM(Base):  # Отстойник
    __tablename__ = 'overflow_bins'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] = mapped_column(default=0)
    date_added: Mapped[datetime] = mapped_column(default= lambda: datetime.now(timezone.utc))

    product: Mapped['ProductORM'] = relationship()

class PurchaseOrderORM(Base):  # Заказ на покупку
    __tablename__ = 'purchase_orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] = mapped_column(default=0)
    order_date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, completed, cancelled
    created_date: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))

    product: Mapped['ProductORM'] = relationship()

class ShelfORM(Base):  # Стеллаж
    __tablename__ = 'shelves'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey('categories.id'), nullable=True)
    max_capacity: Mapped[int] = mapped_column()
    current_quantity: Mapped[int] = mapped_column(default=0)

    category: Mapped[Optional['CategoryORM']] = relationship()

class MovementHistoryORM(Base):  # История перемещений
    __tablename__ = 'movement_history'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    from_shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey('shelves.id'), nullable=True)
    to_shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey('shelves.id'), nullable=True)
    from_overflow: Mapped[bool] = mapped_column(default=False)
    to_overflow: Mapped[bool] = mapped_column(default=False)
    quantity: Mapped[int] = mapped_column(default=0)
    movement_date: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))

    product: Mapped['ProductORM'] = relationship()
    from_shelf: Mapped[Optional['ShelfORM']] = relationship(foreign_keys=[from_shelf_id])
    to_shelf: Mapped[Optional['ShelfORM']] = relationship(foreign_keys=[to_shelf_id])

class NotificationORM(Base):  # Уведомления
    __tablename__ = 'notifications'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey('shelves.id'), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean,default=False)
    created_date: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))
    priority: Mapped[str] = mapped_column(String(20), default='medium')  # low, medium, high

    product: Mapped['ProductORM'] = relationship()
    shelf: Mapped[Optional['ShelfORM']] = relationship()

class ProductPlacementORM(Base):  # Размещение товара
    __tablename__ = 'product_placements'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey('shelves.id'), nullable=True)
    overflow_id: Mapped[Optional[int]] = mapped_column(ForeignKey('overflow_bins.id'), nullable=True)
    quantity: Mapped[int] = mapped_column(default=0)
    placement_date: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))
    last_updated: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc), onupdate=lambda:datetime.now(timezone.utc))

    product: Mapped['ProductORM'] = relationship()
    shelf: Mapped[Optional['ShelfORM']] = relationship()
    overflow: Mapped[Optional['OverflowBinORM']] = relationship()

class SupplyORM(Base):  # Поставка
    __tablename__ = 'supplies'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] = mapped_column()
    supply_date: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), default='delivered')  # delivered, pending, cancelled

    product: Mapped['ProductORM'] = relationship()

CategoryORM.products = relationship('ProductORM', back_populates='category')