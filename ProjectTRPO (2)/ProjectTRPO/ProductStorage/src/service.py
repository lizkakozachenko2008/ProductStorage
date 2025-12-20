from typing import Annotated, List, Optional, Dict
from fastapi import Depends, HTTPException
from starlette import status
from sqlalchemy import exc
from datetime import datetime, date, timedelta
from decimal import Decimal

from src.repository import RepoFactory, SqlAlchemyRepository
from src.schemas import (
    # User
    UserDTO, UserCreateDTO, UserBaseDTO,
    # Admin
    AdminDTO, AdminCreateDTO,
    # Category
    CategoryDTO, CategoryCreateDTO, CategoryBaseDTO,
    # Stock
    StockDTO, StockCreateDTO, StockBaseDTO,
    # Product
    ProductDTO, ProductCreateDTO, ProductBaseDTO,
    # OverflowBin
    OverflowBinDTO, OverflowBinCreateDTO, OverflowBinBaseDTO,
    # PurchaseOrder
    PurchaseOrderDTO, PurchaseOrderCreateDTO, PurchaseOrderBaseDTO,
    # Shelf
    ShelfDTO, ShelfCreateDTO, ShelfBaseDTO,
    # MovementHistory
    MonthlyReportItemDTO,
    MovementHistoryDTO, MovementHistoryCreateDTO, MovementHistoryBaseDTO,
    # Notification
    NotificationDTO, NotificationCreateDTO, NotificationBaseDTO,
    # ProductPlacement
    ProductPlacementDTO, ProductPlacementCreateDTO, ProductPlacementBaseDTO,
    # Supply
    SupplyDTO, SupplyCreateDTO, SupplyBaseDTO,
    # Shipment
    ShipmentDTO, ShipmentCreateDTO, ShipmentBaseDTO,
    # Warehouse Operations
    ProductPlaceRequestDTO, ShipmentRequestDTO,
    # Reports
    PlacementReportItemDTO,
    PlacementReportDTO, MonthlyReportDTO, InventoryReportDTO,
    # Notifications
    FreeSpaceNotificationDTO, LowStockNotificationDTO,
    # Responses
    PlacementResponseDTO, ShipmentResponseDTO, SupplyResponseDTO,
    # Statistics
    StockStatisticsDTO, InventoryStatusDTO
)


# Кастомные исключения
class CategoryNotFoundError(Exception):
    pass

class CategoryHasProductsError(Exception):
    def __init__(self, products_count: int):
        self.products_count = products_count
        super().__init__(f"Невозможно удалить категорию. В ней находится {products_count} продукт(ов)")

class InsufficientStockError(Exception):
    def __init__(self, product_id: int, available: int, requested: int):
        self.product_id = product_id
        self.available = available
        self.requested = requested
        super().__init__(f"Недостаточно товара (ID: {product_id}). Доступно: {available}, требуется: {requested}")

class ShelfCapacityExceededError(Exception):
    def __init__(self, shelf_id: int, free_space: int, requested: int):
        self.shelf_id = shelf_id
        self.free_space = free_space
        self.requested = requested
        super().__init__(f"Недостаточно места на стеллаже (ID: {shelf_id}). Свободно: {free_space}, требуется: {requested}")


# User Service
class UserService:
    def __init__(self, user_repo: SqlAlchemyRepository):
        self.user_repo: SqlAlchemyRepository = user_repo

    def get_all_users(self) -> List[UserDTO]:
        users = self.user_repo.find_all()
        return [UserDTO.model_validate(row) for row in users]

    def get_one_user(self, user_id: int) -> UserDTO:
        user = self.user_repo.find(id=user_id)
        return UserDTO.model_validate(user)
    
    def add_one_user(self, user: UserCreateDTO) -> UserDTO:
        user_dict = user.model_dump()
        db_user = self.user_repo.create(user_dict)
        return UserDTO.model_validate(db_user)
    
    def update_user(self, user_id: int, user: UserBaseDTO) -> UserDTO:
        user_dict = user.model_dump()
        db_user = self.user_repo.update(data=user_dict, id=user_id)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserDTO.model_validate(db_user)
    
    def delete_user(self, user_id: int) -> UserDTO:
        user = self.user_repo.delete(id=user_id)
        return UserDTO.model_validate(user)

def user_service():
    return UserService(user_repo=RepoFactory.user_repo())

UserServiceType = Annotated[UserService, Depends(user_service)]


# Admin Service
class AdminService:
    def __init__(self, admin_repo: SqlAlchemyRepository):
        self.admin_repo: SqlAlchemyRepository = admin_repo

    def get_all_admins(self) -> List[AdminDTO]:
        admins = self.admin_repo.find_all()
        return [AdminDTO.model_validate(row) for row in admins]

    def get_one_admin(self, login: str) -> AdminDTO:
        admin = self.admin_repo.find(login=login)
        return AdminDTO.model_validate(admin)
    
    def add_one_admin(self, admin: AdminCreateDTO) -> AdminDTO:
        try:
            admin_dict = admin.model_dump()
            db_admin = self.admin_repo.create(admin_dict)
            return AdminDTO.model_validate(db_admin)
        except exc.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This login is already used"
            )
    
    def delete_admin(self, login: str) -> AdminDTO:
        admin = self.admin_repo.delete(login=login)
        return AdminDTO.model_validate(admin)

def admin_service():
    return AdminService(admin_repo=RepoFactory.admin_repo())

AdminServiceType = Annotated[AdminService, Depends(admin_service)]


# Category Service
class CategoryService:
    def __init__(self, category_repo: SqlAlchemyRepository):
        self.category_repo: SqlAlchemyRepository = category_repo

    def get_all_categories(self) -> List[CategoryDTO]:
        categories = self.category_repo.find_all()
        return [CategoryDTO.model_validate(row) for row in categories]

    def get_one_category(self, category_id: int) -> CategoryDTO:
        category = self.category_repo.find(id=category_id)
        return CategoryDTO.model_validate(category)
    
    def add_one_category(self, category: CategoryCreateDTO) -> CategoryDTO:
        category_dict = category.model_dump()
        db_category = self.category_repo.create(category_dict)
        return CategoryDTO.model_validate(db_category)
    
    def update_category(self, category_id: int, category: CategoryBaseDTO) -> CategoryDTO:
        category_dict = category.model_dump()
        db_category = self.category_repo.update(category_dict, id=category_id)
        return CategoryDTO.model_validate(db_category)
    
    # В CategoryService
def delete_category(self, category_id: int) -> CategoryDTO:
    # Проверяем есть ли продукты в категории
    product_count = self.product_repo.count_by_category(category_id)
    
    if product_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Невозможно удалить категорию. В ней есть {product_count} продуктов. "
                   f"Сначала удалите или переместите продукты."
        )
    
    category = self.repo.delete(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    return CategoryDTO.model_validate(category)

def category_service():
    return CategoryService(category_repo=RepoFactory.category_repo())

CategoryServiceType = Annotated[CategoryService, Depends(category_service)]


# Stock Service
class StockService:
    def __init__(self, stock_repo: SqlAlchemyRepository):
        self.stock_repo: SqlAlchemyRepository = stock_repo

    def get_stock_by_product(self, product_id: int) -> Optional[StockDTO]:
        stock = self.stock_repo.find(product_id=product_id)
        if stock:
            return StockDTO.model_validate(stock)
        return None

    def update_stock(self, product_id: int, quantity_change: int, 
                     is_reservation: bool = False) -> StockDTO:
        stock = self.stock_repo.update_stock_quantity(
            product_id=product_id,
            quantity_change=quantity_change,
            is_reservation=is_reservation
        )
        return StockDTO.model_validate(stock)

    def reserve_stock(self, product_id: int, quantity: int) -> StockDTO:
        available = self.stock_repo.get_available_quantity(product_id)
        if available < quantity:
            raise InsufficientStockError(product_id, available, quantity)
        
        return self.update_stock(product_id, quantity, is_reservation=True)

    def release_stock(self, product_id: int, quantity: int) -> StockDTO:
        return self.update_stock(product_id, -quantity, is_reservation=True)

    def get_available_quantity(self, product_id: int) -> int:
        return self.stock_repo.get_available_quantity(product_id)

    def get_low_stock_products(self) -> List[dict]:
        product_repo = RepoFactory.product_repo()
        products = product_repo.find_low_stock()
        
        low_stock = []
        for product in products:
            stock = self.stock_repo.find(product_id=product.id)
            if stock:
                low_stock.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'category_id': product.category_id,
                    'available': stock.available_quantity,
                    'min_required': product.min_quantity,
                    'deficit': product.min_quantity - stock.available_quantity,
                    'unit': product.unit,
                    'is_critical': stock.available_quantity <= product.min_quantity * 0.5
                })
        
        return low_stock

    def get_stock_summary(self) -> dict:
        stats = self.stock_repo.get_stock_statistics()
        
        # Добавляем расчет стоимости
        product_repo = RepoFactory.product_repo()
        total_value = product_repo.get_inventory_value()
        
        stats['total_value'] = float(total_value)
        stats['average_stock_level'] = round(
            stats['total_quantity'] / max(stats['total_products'], 1), 2
        )
        
        # Рассчитываем оборот запасов (упрощенный)
        movement_repo = RepoFactory.movement_history_repo()
        recent_movements = movement_repo.find_recent_movements(30)
        total_moved = sum(m.quantity for m in recent_movements)
        
        stats['stock_turnover_rate'] = round(
            (total_moved / max(stats['total_quantity'], 1)) * 30, 2
        )
        
        return stats

    def get_stock_statistics(self) -> StockStatisticsDTO:
        summary = self.get_stock_summary()
        return StockStatisticsDTO(**summary)

def stock_service():
    return StockService(stock_repo=RepoFactory.stock_repo())

StockServiceType = Annotated[StockService, Depends(stock_service)]


# Product Service
class ProductService:
    def __init__(self, product_repo: SqlAlchemyRepository, stock_service: StockServiceType):
        self.product_repo: SqlAlchemyRepository = product_repo
        self.stock_service = stock_service

    def get_all_products(self) -> List[ProductDTO]:
        products = self.product_repo.find_all()
        result = []
        for product in products:
            product_dict = ProductDTO.model_validate(product).model_dump()
            stock = self.stock_service.get_stock_by_product(product.id)
            if stock:
                product_dict['stock'] = stock
                product_dict['current_quantity'] = stock.available_quantity
            result.append(ProductDTO(**product_dict))
        return result

    def get_one_product(self, product_id: int) -> ProductDTO:
        product = self.product_repo.find(id=product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )
        
        product_dict = ProductDTO.model_validate(product).model_dump()
        stock = self.stock_service.get_stock_by_product(product_id)
        if stock:
            product_dict['stock'] = stock
            product_dict['current_quantity'] = stock.available_quantity
        
        return ProductDTO(**product_dict)
    
    def add_one_product(self, product: ProductCreateDTO) -> ProductDTO:
        product_dict = product.model_dump()
        db_product = self.product_repo.create(product_dict)
        
        # Создаем запись запасов для нового товара
        stock_service = stock_service()
        stock_service.update_stock(db_product.id, 0)
        
        return self.get_one_product(db_product.id)
    
    def update_product(self, product_id: int, product: ProductBaseDTO) -> ProductDTO:
        product_dict = product.model_dump()
        db_product = self.product_repo.update(product_dict, id=product_id)
        return self.get_one_product(product_id)
    
    def delete_product(self, product_id: int) -> ProductDTO:
        product = self.get_one_product(product_id)
        self.product_repo.delete(id=product_id)
        return product
    
    def get_low_stock_products(self) -> List[ProductDTO]:
        low_stock = self.stock_service.get_low_stock_products()
        result = []
        
        for item in low_stock:
            product = self.get_one_product(item['product_id'])
            result.append(product)
        
        return result

    def place_product(self, placement_data: ProductPlaceRequestDTO) -> PlacementResponseDTO:
        from src.repository import RepoFactory
        
        # Проверяем товар
        product = self.product_repo.find(id=placement_data.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с ID {placement_data.product_id} не найден"
            )
        
        # Проверяем доступное количество
        available = self.stock_service.get_available_quantity(placement_data.product_id)
        if available < placement_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно товара. Доступно: {available}, требуется: {placement_data.quantity}"
            )
        
        shelf_updated = None
        
        # Если размещаем на стеллаже
        if placement_data.shelf_id:
            shelf_repo = RepoFactory.shelf_repo()
            shelf = shelf_repo.find(id=placement_data.shelf_id)
            if not shelf:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Стеллаж с ID {placement_data.shelf_id} не найден"
                )
            
            # Проверяем место
            free_space = shelf.max_capacity - shelf.current_quantity
            if free_space < placement_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Недостаточно места на стеллаже '{shelf.name}'. "
                           f"Свободно: {free_space}, требуется: {placement_data.quantity}"
                )
            
            # Обновляем стеллаж
            updated_shelf = shelf_repo.update(
                data={"current_quantity": shelf.current_quantity + placement_data.quantity},
                id=shelf.id
            )
            shelf_updated = ShelfDTO.model_validate(updated_shelf)
        
        # Создаем размещение
        placement_repo = RepoFactory.product_placement_repo()
        placement_dict = placement_data.model_dump()
        placement = placement_repo.create(placement_dict)
        
        # Резервируем товар
        stock_updated = self.stock_service.reserve_stock(
            placement_data.product_id, 
            placement_data.quantity
        )
        
        # Создаем запись в истории
        movement_repo = RepoFactory.movement_history_repo()
        movement_data = {
            "product_id": product.id,
            "quantity": placement_data.quantity,
            "to_shelf_id": placement_data.shelf_id,
            "to_overflow": placement_data.overflow_id is not None,
            "movement_type": "placement"
        }
        movement_repo.create(movement_data)
        
        # Освобождаем резерв при размещении
        if placement_data.operation_type == "place":
            self.stock_service.release_stock(placement_data.product_id, placement_data.quantity)
        
        return PlacementResponseDTO(
            placement=ProductPlacementDTO.model_validate(placement),
            stock_updated=stock_updated,
            shelf_updated=shelf_updated,
            message=f"Товар '{product.name}' успешно размещен"
        )

    def get_placement_report(self) -> PlacementReportDTO:
        from src.repository import RepoFactory
        
        placement_repo = RepoFactory.product_placement_repo()
        product_repo = RepoFactory.product_repo()
        shelf_repo = RepoFactory.shelf_repo()
        
        placements = placement_repo.find_all()
        products = product_repo.find_all()
        shelves = shelf_repo.find_all()
        
        product_dict = {p.id: p for p in products}
        shelf_dict = {s.id: s for s in shelves}
        
        items = []
        total_quantity = 0
        used_shelves = set()
        used_overflows = set()
        low_stock_count = 0
        
        for placement in placements:
            product = product_dict.get(placement.product_id)
            shelf = shelf_dict.get(placement.shelf_id) if placement.shelf_id else None
            
            if product:
                # Проверяем низкий запас
                stock = self.stock_service.get_stock_by_product(product.id)
                is_low_stock = stock.available_quantity <= product.min_quantity if stock else False
                
                if is_low_stock:
                    low_stock_count += 1
                
                item = PlacementReportItemDTO(
                    product_id=product.id,
                    product_name=product.name,
                    shelf_id=placement.shelf_id,
                    shelf_name=shelf.name if shelf else None,
                    overflow_id=placement.overflow_id,
                    quantity=placement.quantity,
                    total_quantity=stock.available_quantity if stock else 0,
                    unit=product.unit,
                    is_low_stock=is_low_stock
                )
                items.append(item)
                total_quantity += placement.quantity
                
                if placement.shelf_id:
                    used_shelves.add(placement.shelf_id)
                if placement.overflow_id:
                    used_overflows.add(placement.overflow_id)
        
        return PlacementReportDTO(
            items=items,
            total_products=len(set(p.product_id for p in placements)),
            total_quantity=total_quantity,
            shelves_used=len(used_shelves),
            overflow_used=len(used_overflows),
            low_stock_count=low_stock_count
        )

def product_service():
    return ProductService(
        product_repo=RepoFactory.product_repo(),
        stock_service=stock_service()
    )


ProductServiceType = Annotated[ProductService, Depends(product_service)]


# Supply Service
class SupplyService:
    def __init__(self, supply_repo: SqlAlchemyRepository, stock_service: StockServiceType):
        self.supply_repo: SqlAlchemyRepository = supply_repo
        self.stock_service = stock_service

    def get_all_supplies(self) -> List[SupplyDTO]:
        supplies = self.supply_repo.find_all()
        return [SupplyDTO.model_validate(row) for row in supplies]

    def get_one_supply(self, supply_id: int) -> SupplyDTO:
        supply = self.supply_repo.find(id=supply_id)
        return SupplyDTO.model_validate(supply)
    
    def add_one_supply(self, supply: SupplyCreateDTO) -> SupplyResponseDTO:
        # Создаем поставку
        supply_dict = supply.model_dump()
        db_supply = self.supply_repo.create(supply_dict)
        
        # Увеличиваем запасы
        stock_updated = self.stock_service.update_stock(
            supply.product_id,
            supply.quantity,
            is_reservation=False
        )
        
        # Создаем уведомление о низком запасе (если было критично)
        product_repo = RepoFactory.product_repo()
        product = product_repo.find(id=supply.product_id)
        
        if product:
            stock = self.stock_service.get_stock_by_product(supply.product_id)
            if stock and stock.available_quantity <= product.min_quantity:
                # Создаем уведомление
                notification_repo = RepoFactory.notification_repo()
                notification_data = {
                    "product_id": supply.product_id,
                    "message": f"Товар '{product.name}' все еще имеет низкий запас после поставки. "
                               f"Текущее количество: {stock.available_quantity}, минимальное: {product.min_quantity}",
                    "priority": "medium",
                    "notification_type": "warning"
                }
                notification_repo.create(notification_data)
        
        return SupplyResponseDTO(
            supply=SupplyDTO.model_validate(db_supply),
            stock_updated=stock_updated,
            message=f"Поставка товара ID {supply.product_id} на {supply.quantity} единиц успешно зарегистрирована"
        )
    
    def update_supply(self, supply_id: int, supply: SupplyBaseDTO) -> SupplyDTO:
        supply_dict = supply.model_dump()
        db_supply = self.supply_repo.update(supply_dict, id=supply_id)
        return SupplyDTO.model_validate(db_supply)
    
    def delete_supply(self, supply_id: int) -> SupplyDTO:
        supply = self.supply_repo.delete(id=supply_id)
        return SupplyDTO.model_validate(supply)

    def get_monthly_supply_shipment_report(self, year: int, month: int) -> MonthlyReportDTO:
        from src.repository import RepoFactory
        
        # Получаем поставки
        supplies = self.supply_repo.get_monthly_supplies(year, month)
        
        # Получаем отгрузки
        shipment_repo = RepoFactory.shipment_repo()
        shipments = shipment_repo.get_monthly_shipments(year, month)
        
        # Информация о товарах
        product_repo = RepoFactory.product_repo()
        products = product_repo.find_all()
        product_dict = {p.id: p for p in products}
        
        items = []
        total_supplied = 0
        total_shipped = 0
        
        # Добавляем поставки
        for supply in supplies:
            product = product_dict.get(supply.product_id)
            item = MonthlyReportItemDTO(
                date=supply.supply_date,
                product_id=supply.product_id,
                product_name=product.name if product else "Неизвестный товар",
                type="supply",
                quantity=supply.quantity,
                reference_id=supply.id,
                details=f"Поставка от {supply.supplier}" if supply.supplier else None
            )
            items.append(item)
            total_supplied += supply.quantity
        
        # Добавляем отгрузки
        for shipment in shipments:
            product = product_dict.get(shipment.product_id)
            item = MonthlyReportItemDTO(
                date=shipment.shipment_date,
                product_id=shipment.product_id,
                product_name=product.name if product else "Неизвестный товар",
                type="shipment",
                quantity=shipment.quantity,
                reference_id=shipment.id,
                details=f"Отгрузка для {shipment.customer}" if shipment.customer else None
            )
            items.append(item)
            total_shipped += shipment.quantity
        
        # Сортируем по дате
        items.sort(key=lambda x: x.date)
        
        return MonthlyReportDTO(
            year=year,
            month=month,
            items=items,
            total_supplied=total_supplied,
            total_shipped=total_shipped,
            net_change=total_supplied - total_shipped,
            total_transactions=len(items)
        )

def supply_service():
    return SupplyService(
        supply_repo=RepoFactory.supply_repo(),
        stock_service=stock_service()
    )

SupplyServiceType = Annotated[SupplyService, Depends(supply_service)]


# Shipment Service
class ShipmentService:
    def __init__(self, shipment_repo: SqlAlchemyRepository, 
                 stock_service: StockServiceType,
                 product_service: ProductServiceType):
        self.shipment_repo: SqlAlchemyRepository = shipment_repo
        self.stock_service = stock_service
        self.product_service = product_service

    def get_all_shipments(self) -> List[ShipmentDTO]:
        shipments = self.shipment_repo.find_all()
        return [ShipmentDTO.model_validate(row) for row in shipments]

    def get_one_shipment(self, shipment_id: int) -> ShipmentDTO:
        shipment = self.shipment_repo.find(id=shipment_id)
        return ShipmentDTO.model_validate(shipment)
    
    def create_shipment(self, shipment: ShipmentCreateDTO) -> ShipmentResponseDTO:
        # Проверяем доступное количество
        available = self.stock_service.get_available_quantity(shipment.product_id)
        if available < shipment.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно товара для отгрузки. Доступно: {available}, требуется: {shipment.quantity}"
            )
        
        # Создаем отгрузку
        shipment_dict = shipment.model_dump()
        db_shipment = self.shipment_repo.create(shipment_dict)
        
        # Уменьшаем запасы
        stock_updated = self.stock_service.update_stock(
            shipment.product_id,
            -shipment.quantity,
            is_reservation=False
        )
        
        # Проверяем не стал ли запас низким
        product = self.product_service.get_one_product(shipment.product_id)
        if product.min_quantity > 0 and stock_updated.available_quantity <= product.min_quantity:
            # Создаем уведомление
            notification_repo = RepoFactory.notification_repo()
            notification_data = {
                "product_id": shipment.product_id,
                "message": f"Товар '{product.name}' имеет низкий запас после отгрузки. "
                           f"Текущее количество: {stock_updated.available_quantity}, минимальное: {product.min_quantity}",
                "priority": "high" if stock_updated.available_quantity <= product.min_quantity * 0.5 else "medium",
                "notification_type": "warning"
            }
            notification_repo.create(notification_data)
        
        return ShipmentResponseDTO(
            shipment=ShipmentDTO.model_validate(db_shipment),
            stock_updated=stock_updated,
            message=f"Отгрузка товара ID {shipment.product_id} на {shipment.quantity} единиц успешно зарегистрирована"
        )
    
    def update_shipment(self, shipment_id: int, shipment: ShipmentBaseDTO) -> ShipmentDTO:
        shipment_dict = shipment.model_dump()
        db_shipment = self.shipment_repo.update(shipment_dict, id=shipment_id)
        return ShipmentDTO.model_validate(db_shipment)
    
    def delete_shipment(self, shipment_id: int) -> ShipmentDTO:
        shipment = self.shipment_repo.delete(id=shipment_id)
        return ShipmentDTO.model_validate(shipment)

def shipment_service():
    return ShipmentService(
        shipment_repo=RepoFactory.shipment_repo(),
        stock_service=stock_service(),
        product_service=product_service()
    )

ShipmentServiceType = Annotated[ShipmentService, Depends(shipment_service)]


# OverflowBin Service
class OverflowBinService:
    def __init__(self, overflow_bin_repo: SqlAlchemyRepository):
        self.overflow_bin_repo: SqlAlchemyRepository = overflow_bin_repo

    def get_all_overflow_bins(self) -> List[OverflowBinDTO]:
        bins = self.overflow_bin_repo.find_all()
        return [OverflowBinDTO.model_validate(row) for row in bins]

    def get_one_overflow_bin(self, bin_id: int) -> OverflowBinDTO:
        bin = self.overflow_bin_repo.find(id=bin_id)
        return OverflowBinDTO.model_validate(bin)
    
    def add_one_overflow_bin(self, overflow_bin: OverflowBinCreateDTO) -> OverflowBinDTO:
        bin_dict = overflow_bin.model_dump()
        db_bin = self.overflow_bin_repo.create(bin_dict)
        return OverflowBinDTO.model_validate(db_bin)
    
    def update_overflow_bin(self, bin_id: int, overflow_bin: OverflowBinBaseDTO) -> OverflowBinDTO:
        bin_dict = overflow_bin.model_dump()
        db_bin = self.overflow_bin_repo.update(bin_dict, id=bin_id)
        return OverflowBinDTO.model_validate(db_bin)
    
    def delete_overflow_bin(self, bin_id: int) -> OverflowBinDTO:
        bin = self.overflow_bin_repo.delete(id=bin_id)
        return OverflowBinDTO.model_validate(bin)

    def check_overflow_for_free_shelves(self) -> List[FreeSpaceNotificationDTO]:
        from src.repository import RepoFactory
        
        notifications = []
        
        # Товары в отстойнике
        overflow_items = self.overflow_bin_repo.get_overflow_with_stock()
        if not overflow_items:
            return notifications
        
        # Стеллажи
        shelf_repo = RepoFactory.shelf_repo()
        shelves = shelf_repo.find_all()
        
        # Товары
        product_repo = RepoFactory.product_repo()
        products = product_repo.find_all()
        product_dict = {p.id: p for p in products}
        
        for overflow in overflow_items:
            product = product_dict.get(overflow.product_id)
            if not product:
                continue
            
            for shelf in shelves:
                free_space = shelf.max_capacity - shelf.current_quantity
                can_fit = free_space >= overflow.quantity
                
                if free_space > 0:  # Если есть хоть какое-то свободное место
                    notification = FreeSpaceNotificationDTO(
                        shelf_id=shelf.id,
                        shelf_name=shelf.name,
                        product_id=product.id,
                        product_name=product.name,
                        overflow_bin_id=overflow.id,
                        available_quantity=overflow.quantity,
                        shelf_capacity=shelf.max_capacity,
                        shelf_current=shelf.current_quantity,
                        free_space=free_space,
                        can_fit=can_fit,
                        fit_percentage=round((overflow.quantity / free_space * 100) if free_space > 0 else 0, 2)
                    )
                    notifications.append(notification)
        
        return notifications

def overflow_bin_service():
    return OverflowBinService(overflow_bin_repo=RepoFactory.overflow_bin_repo())

OverflowBinServiceType = Annotated[OverflowBinService, Depends(overflow_bin_service)]


# PurchaseOrder Service
class PurchaseOrderService:
    def __init__(self, purchase_order_repo: SqlAlchemyRepository):
        self.purchase_order_repo: SqlAlchemyRepository = purchase_order_repo

    def get_all_purchase_orders(self) -> List[PurchaseOrderDTO]:
        orders = self.purchase_order_repo.find_all()
        return [PurchaseOrderDTO.model_validate(row) for row in orders]

    def get_one_purchase_order(self, order_id: int) -> PurchaseOrderDTO:
        order = self.purchase_order_repo.find(id=order_id)
        return PurchaseOrderDTO.model_validate(order)
    
    def add_one_purchase_order(self, purchase_order: PurchaseOrderCreateDTO) -> PurchaseOrderDTO:
        order_dict = purchase_order.model_dump()
        db_order = self.purchase_order_repo.create(order_dict)
        return PurchaseOrderDTO.model_validate(db_order)
    
    def update_purchase_order(self, order_id: int, purchase_order: PurchaseOrderBaseDTO) -> PurchaseOrderDTO:
        order_dict = purchase_order.model_dump()
        db_order = self.purchase_order_repo.update(order_dict, id=order_id)
        return PurchaseOrderDTO.model_validate(db_order)
    
    def delete_purchase_order(self, order_id: int) -> PurchaseOrderDTO:
        order = self.purchase_order_repo.delete(id=order_id)
        return PurchaseOrderDTO.model_validate(order)

def purchase_order_service():
    return PurchaseOrderService(purchase_order_repo=RepoFactory.purchase_order_repo())

PurchaseOrderServiceType = Annotated[PurchaseOrderService, Depends(purchase_order_service)]


# Shelf Service
class ShelfService:
    def __init__(self, shelf_repo: SqlAlchemyRepository):
        self.shelf_repo: SqlAlchemyRepository = shelf_repo

    def get_all_shelves(self) -> List[ShelfDTO]:
        shelves = self.shelf_repo.find_all()
        return [ShelfDTO.model_validate(row) for row in shelves]

    def get_one_shelf(self, shelf_id: int) -> ShelfDTO:
        shelf = self.shelf_repo.find(id=shelf_id)
        return ShelfDTO.model_validate(shelf)
    
    def add_one_shelf(self, shelf: ShelfCreateDTO) -> ShelfDTO:
        shelf_dict = shelf.model_dump()
        db_shelf = self.shelf_repo.create(shelf_dict)
        return ShelfDTO.model_validate(db_shelf)
    
    def update_shelf(self, shelf_id: int, shelf: ShelfBaseDTO) -> ShelfDTO:
        shelf_dict = shelf.model_dump()
        db_shelf = self.shelf_repo.update(shelf_dict, id=shelf_id)
        return ShelfDTO.model_validate(db_shelf)
    
    def delete_shelf(self, shelf_id: int) -> ShelfDTO:
        shelf = self.shelf_repo.delete(id=shelf_id)
        return ShelfDTO.model_validate(shelf)
    
    def get_shelf_utilization(self) -> List[dict]:
        return self.shelf_repo.get_shelf_utilization()

def shelf_service():
    return ShelfService(shelf_repo=RepoFactory.shelf_repo())

ShelfServiceType = Annotated[ShelfService, Depends(shelf_service)]


# MovementHistory Service
class MovementHistoryService:
    def __init__(self, movement_history_repo: SqlAlchemyRepository):
        self.movement_history_repo: SqlAlchemyRepository = movement_history_repo

    def get_all_movement_history(self) -> List[MovementHistoryDTO]:
        history = self.movement_history_repo.find_all()
        return [MovementHistoryDTO.model_validate(row) for row in history]

    def get_one_movement_history(self, history_id: int) -> MovementHistoryDTO:
        history = self.movement_history_repo.find(id=history_id)
        return MovementHistoryDTO.model_validate(history)
    
    def add_one_movement_history(self, movement_history: MovementHistoryCreateDTO) -> MovementHistoryDTO:
        history_dict = movement_history.model_dump()
        db_history = self.movement_history_repo.create(history_dict)
        return MovementHistoryDTO.model_validate(db_history)
    
    def get_recent_movements(self, days: int = 7) -> List[MovementHistoryDTO]:
        movements = self.movement_history_repo.find_recent_movements(days)
        return [MovementHistoryDTO.model_validate(row) for row in movements]

def movement_history_service():
    return MovementHistoryService(movement_history_repo=RepoFactory.movement_history_repo())

MovementHistoryServiceType = Annotated[MovementHistoryService, Depends(movement_history_service)]


# Notification Service
class NotificationService:
    def __init__(self, notification_repo: SqlAlchemyRepository):
        self.notification_repo: SqlAlchemyRepository = notification_repo

    def get_all_notifications(self) -> List[NotificationDTO]:
        notifications = self.notification_repo.find_all()
        return [NotificationDTO.model_validate(row) for row in notifications]

    def get_one_notification(self, notification_id: int) -> NotificationDTO:
        notification = self.notification_repo.find(id=notification_id)
        return NotificationDTO.model_validate(notification)
    
    def add_one_notification(self, notification: NotificationCreateDTO) -> NotificationDTO:
        notification_dict = notification.model_dump()
        db_notification = self.notification_repo.create(notification_dict)
        return NotificationDTO.model_validate(db_notification)
    
    def update_notification(self, notification_id: int, notification: NotificationBaseDTO) -> NotificationDTO:
        notification_dict = notification.model_dump()
        db_notification = self.notification_repo.update(notification_dict, id=notification_id)
        return NotificationDTO.model_validate(db_notification)
    
    def delete_notification(self, notification_id: int) -> NotificationDTO:
        notification = self.notification_repo.delete(id=notification_id)
        return NotificationDTO.model_validate(notification)
    
    def create_low_stock_notification(self, product_id: int, message: str, 
                                      priority: str = "medium") -> NotificationDTO:
        notification_data = {
            "product_id": product_id,
            "message": message,
            "priority": priority,
            "notification_type": "warning"
        }
        return self.add_one_notification(NotificationCreateDTO(**notification_data))

def notification_service():
    return NotificationService(notification_repo=RepoFactory.notification_repo())

NotificationServiceType = Annotated[NotificationService, Depends(notification_service)]


# ProductPlacement Service
class ProductPlacementService:
    def __init__(self, product_placement_repo: SqlAlchemyRepository):
        self.product_placement_repo: SqlAlchemyRepository = product_placement_repo

    def get_all_product_placements(self) -> List[ProductPlacementDTO]:
        placements = self.product_placement_repo.find_all()
        return [ProductPlacementDTO.model_validate(row) for row in placements]

    def get_one_product_placement(self, placement_id: int) -> ProductPlacementDTO:
        placement = self.product_placement_repo.find(id=placement_id)
        return ProductPlacementDTO.model_validate(placement)
    
    def add_one_product_placement(self, product_placement: ProductPlacementCreateDTO) -> ProductPlacementDTO:
        placement_dict = product_placement.model_dump()
        db_placement = self.product_placement_repo.create(placement_dict)
        return ProductPlacementDTO.model_validate(db_placement)
    
    def update_product_placement(self, placement_id: int, product_placement: ProductPlacementBaseDTO) -> ProductPlacementDTO:
        placement_dict = product_placement.model_dump()
        db_placement = self.product_placement_repo.update(placement_dict, id=placement_id)
        return ProductPlacementDTO.model_validate(db_placement)
    
    def delete_product_placement(self, placement_id: int) -> ProductPlacementDTO:
        placement = self.product_placement_repo.delete(id=placement_id)
        return ProductPlacementDTO.model_validate(placement)

def product_placement_service():
    return ProductPlacementService(product_placement_repo=RepoFactory.product_placement_repo())

ProductPlacementServiceType = Annotated[ProductPlacementService, Depends(product_placement_service)]


# Warehouse Service (комбинированный)
class WarehouseService:
    def __init__(self,
                 product_service: ProductServiceType,
                 stock_service: StockServiceType,
                 shipment_service: ShipmentServiceType,
                 overflow_bin_service: OverflowBinServiceType):
        self.product_service = product_service
        self.stock_service = stock_service
        self.shipment_service = shipment_service
        self.overflow_bin_service = overflow_bin_service

    def get_inventory_report(self) -> InventoryReportDTO:
        from src.repository import RepoFactory
        
        product_repo = RepoFactory.product_repo()
        category_repo = RepoFactory.category_repo()
        overflow_repo = RepoFactory.overflow_bin_repo()
        
        products = product_repo.find_all()
        categories = category_repo.find_all()
        overflow_items = overflow_repo.get_overflow_with_stock()
        
        category_dict = {c.id: c for c in categories}
        overflow_dict = {o.product_id: o for o in overflow_items}
        
        inventory_items = []
        low_stock_items = []
        overflow_items_list = []
        
        total_value = 0
        total_quantity = 0
        low_stock_count = 0
        
        for product in products:
            stock = self.stock_service.get_stock_by_product(product.id)
            if not stock:
                continue
            
            category = category_dict.get(product.category_id)
            overflow = overflow_dict.get(product.id)
            
            is_low_stock = stock.available_quantity <= product.min_quantity
            if is_low_stock:
                low_stock_count += 1
                low_stock_items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "current_quantity": stock.available_quantity,
                    "min_quantity": product.min_quantity,
                    "deficit": product.min_quantity - stock.available_quantity,
                    "unit": product.unit
                })
            
            if overflow:
                overflow_items_list.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": overflow.quantity,
                    "date_added": overflow.date_added
                })
            
            # Считаем стоимость
            item_value = product.price * stock.available_quantity if product.price else 0
            total_value += item_value
            total_quantity += stock.available_quantity
            
            # Считаем размещения
            placement_repo = RepoFactory.product_placement_repo()
            placement_count = len(placement_repo.find_all(product_id=product.id))
            
            item = InventoryStatusDTO(
                product_id=product.id,
                product_name=product.name,
                category_id=product.category_id,
                category_name=category.name if category else "Без категории",
                current_quantity=stock.available_quantity,
                min_quantity=product.min_quantity,
                unit=product.unit,
                is_low_stock=is_low_stock,
                in_overflow=overflow is not None,
                overflow_quantity=overflow.quantity if overflow else None,
                placement_count=placement_count,
                total_value=item_value
            )
            inventory_items.append(item)
        
        summary = {
            "total_products": len(inventory_items),
            "total_quantity": total_quantity,
            "total_value": total_value,
            "low_stock_count": low_stock_count,
            "overflow_items_count": len(overflow_items_list),
            "average_stock_value": round(total_value / max(len(inventory_items), 1), 2)
        }
        
        return InventoryReportDTO(
            summary=summary,
            products=inventory_items,
            low_stock_items=low_stock_items,
            overflow_items=overflow_items_list
        )

def warehouse_service():
    return WarehouseService(
        product_service=product_service(),
        stock_service=stock_service(),
        shipment_service=shipment_service(),
        overflow_bin_service=overflow_bin_service()
    )

WarehouseServiceType = Annotated[WarehouseService, Depends(warehouse_service)]