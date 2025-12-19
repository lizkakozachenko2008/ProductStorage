from typing import Annotated, List  
from fastapi import Depends, HTTPException
from starlette import status
from sqlalchemy import exc
from src.repository import RepoFactory, SqlAlchemyRepository
from src.schemas import (
    UserDTO, UserCreateDTO, UserBaseDTO,
    AdminDTO, AdminCreateDTO,
    CategoryDTO, CategoryCreateDTO, CategoryBaseDTO,
    ProductDTO, ProductCreateDTO, ProductBaseDTO,
    OverflowBinDTO, OverflowBinCreateDTO, OverflowBinBaseDTO,
    PurchaseOrderDTO, PurchaseOrderCreateDTO, PurchaseOrderBaseDTO,
    ShelfDTO, ShelfCreateDTO, ShelfBaseDTO,
    MovementHistoryDTO, MovementHistoryCreateDTO, MovementHistoryBaseDTO,
    NotificationDTO, NotificationCreateDTO, NotificationBaseDTO,
    ProductPlacementDTO, ProductPlacementCreateDTO, ProductPlacementBaseDTO,
    SupplyDTO, SupplyCreateDTO, SupplyBaseDTO,
    ProductPlaceRequestDTO, PlacementReportDTO, MonthlyReportDTO,
    FreeSpaceNotificationDTO, PlacementResponseDTO,
    PlacementReportItemDTO, MonthlyReportItemDTO
)


# Кастомные исключения для категорий (ДОБАВЛЕНО)
class CategoryNotFoundError(Exception):
    pass

class CategoryHasProductsError(Exception):
    def __init__(self, products_count: int):
        self.products_count = products_count
        super().__init__(f"Невозможно удалить категорию. В ней находится {products_count} продукт(ов)")


# Сервис для пользователей
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
                detail="User is None"
            )
        user = UserDTO.model_validate(db_user)
        return user
    
    def delete_user(self, user_id: int) -> UserDTO:
        user = self.user_repo.delete(id=user_id)
        return UserDTO.model_validate(user)

def user_service():
    return UserService(user_repo=RepoFactory.user_repo())

UserServiceType = Annotated[UserService, Depends(user_service)]

# Сервис для администраторов
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

# Сервис для категорий
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
    
    def delete_category(self, category_id: int) -> CategoryDTO:
        # Сначала находим категорию
        category = self.category_repo.find(id=category_id)
        if not category:
            raise CategoryNotFoundError()
    
        # Проверяем есть ли продукты в категории
        from src.repository import RepoFactory
        product_repo = RepoFactory.product_repo()
        products_count = product_repo.count_by_category(category_id)
    
        if products_count > 0:
            raise CategoryHasProductsError(products_count)
    
        # Если проверки прошли - удаляем
        deleted_category = self.category_repo.delete(id=category_id)
        if not deleted_category:
            raise CategoryNotFoundError()
        
        return CategoryDTO.model_validate(deleted_category)

def category_service():
    return CategoryService(category_repo=RepoFactory.category_repo())

CategoryServiceType = Annotated[CategoryService, Depends(category_service)]

# Сервис для товаров
class ProductService:
    def __init__(self, product_repo: SqlAlchemyRepository):
        self.product_repo: SqlAlchemyRepository = product_repo

    def get_all_products(self) -> List[ProductDTO]:
        products = self.product_repo.find_all()
        return [ProductDTO.model_validate(row) for row in products]

    def get_one_product(self, product_id: int) -> ProductDTO:
        product = self.product_repo.find(id=product_id)
        return ProductDTO.model_validate(product)
    
    def add_one_product(self, product: ProductCreateDTO) -> ProductDTO:
        product_dict = product.model_dump()
        db_product = self.product_repo.create(product_dict)
        return ProductDTO.model_validate(db_product)
    
    def update_product(self, product_id: int, product: ProductBaseDTO) -> ProductDTO:
        product_dict = product.model_dump()
        db_product = self.product_repo.update(product_dict, id=product_id)
        return ProductDTO.model_validate(db_product)
    
    def delete_product(self, product_id: int) -> ProductDTO:
        product = self.product_repo.delete(id=product_id)
        return ProductDTO.model_validate(product)
    
    def get_low_stock_products(self) -> List[ProductDTO]:
        """Товары с низким запасом (текущее количество <= минимальное)"""
        products = self.product_repo.find_low_stock()
        return [ProductDTO.model_validate(row) for row in products]

    def place_product(self, placement_data: ProductPlaceRequestDTO) -> PlacementResponseDTO:
        """Разместить товар на складе (на стеллаж или в отстойник)"""
        from src.repository import RepoFactory
        
        # Проверяем существование товара
        product = self.product_repo.find(id=placement_data.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с ID {placement_data.product_id} не найден"
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
            
            # Проверяем достаточно ли места
            if shelf.current_quantity + placement_data.quantity > shelf.max_capacity:
                free_space = shelf.max_capacity - shelf.current_quantity
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
        
        # Если размещаем в отстойник
        elif placement_data.overflow_id:
            overflow_repo = RepoFactory.overflow_bin_repo()
            overflow_bin = overflow_repo.find(id=placement_data.overflow_id)
            if not overflow_bin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Отстойник с ID {placement_data.overflow_id} не найден"
                )
        
        # Создаем запись о размещении
        placement_repo = RepoFactory.product_placement_repo()
        placement_dict = placement_data.model_dump()
        placement = placement_repo.create(placement_dict)
        
        # Обновляем общее количество товара
        updated_product = self.product_repo.update(
            data={"current_quantity": product.current_quantity + placement_data.quantity},
            id=product.id
        )
        
        # Создаем запись в истории перемещений
        movement_repo = RepoFactory.movement_history_repo()
        movement_data = {
            "product_id": product.id,
            "quantity": placement_data.quantity,
            "to_shelf_id": placement_data.shelf_id,
            "to_overflow": placement_data.overflow_id is not None
        }
        movement_repo.create(movement_data)
        
        return PlacementResponseDTO(
            placement=ProductPlacementDTO.model_validate(placement),
            product_updated=ProductDTO.model_validate(updated_product),
            shelf_updated=shelf_updated,
            message=f"Товар '{product.name}' успешно размещен"
        )

    def get_placement_report(self) -> PlacementReportDTO:
        """Получить полный отчет по размещению товаров на складе"""
        from src.repository import RepoFactory
        
        # Получаем все размещения
        placement_repo = RepoFactory.product_placement_repo()
        placements = placement_repo.find_all()
        
        if not placements:
            return PlacementReportDTO(
                items=[],
                total_products=0,
                total_quantity=0,
                shelves_used=0,
                overflow_used=0
            )
        
        # Получаем дополнительные данные
        product_repo = RepoFactory.product_repo()
        shelf_repo = RepoFactory.shelf_repo()
        overflow_repo = RepoFactory.overflow_bin_repo()
        
        products = product_repo.find_all()
        shelves = shelf_repo.find_all()
        
        # Создаем словари для быстрого доступа
        product_dict = {p.id: p for p in products}
        shelf_dict = {s.id: s for s in shelves}
        
        # Формируем отчет
        items = []
        total_quantity = 0
        used_shelves = set()
        used_overflows = set()
        
        for placement in placements:
            product = product_dict.get(placement.product_id)
            shelf = shelf_dict.get(placement.shelf_id) if placement.shelf_id else None
            
            if product:
                item = PlacementReportItemDTO(
                    product_id=product.id,
                    product_name=product.name,
                    shelf_id=placement.shelf_id,
                    shelf_name=shelf.name if shelf else None,
                    overflow_id=placement.overflow_id,
                    quantity=placement.quantity,
                    total_quantity=product.current_quantity,
                    unit=product.unit
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
            overflow_used=len(used_overflows)
        )

def product_service():
    return ProductService(product_repo=RepoFactory.product_repo())

ProductServiceType = Annotated[ProductService, Depends(product_service)]

# Сервис для отстойников (overflow bins)
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
        """Проверить, можно ли разместить товары из отстойника на освободившихся стеллажах"""
        from src.repository import RepoFactory
        
        notifications = []
        
        # Получаем товары в отстойнике
        overflow_items = self.overflow_bin_repo.find_overflow_with_stock()
        if not overflow_items:
            return notifications
        
        # Получаем стеллажи
        shelf_repo = RepoFactory.shelf_repo()
        shelves = shelf_repo.find_all()
        
        # Получаем товары
        product_repo = RepoFactory.product_repo()
        products = product_repo.find_all()
        product_dict = {p.id: p for p in products}
        
        # Получаем текущие размещения на стеллажах
        placement_repo = RepoFactory.product_placement_repo()
        
        for overflow in overflow_items:
            product = product_dict.get(overflow.product_id)
            if not product:
                continue
            
            # Ищем подходящие стеллажи
            for shelf in shelves:
                # Проверяем свободное место
                free_space = shelf.max_capacity - shelf.current_quantity
                
                # Проверяем, может ли товар поместиться хотя бы частично
                can_fit = free_space > 0
                
                if can_fit:
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
                        can_fit=free_space >= overflow.quantity
                    )
                    notifications.append(notification)
                    # Не прерываем цикл, чтобы проверить все стеллажи
        
        return notifications

def overflow_bin_service():
    return OverflowBinService(overflow_bin_repo=RepoFactory.overflow_bin_repo())

OverflowBinServiceType = Annotated[OverflowBinService, Depends(overflow_bin_service)]

# Сервис для заказов на покупку
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

# Сервис для стеллажей
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

def shelf_service():
    return ShelfService(shelf_repo=RepoFactory.shelf_repo())

ShelfServiceType = Annotated[ShelfService, Depends(shelf_service)]

# Сервис для истории перемещений
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
        """Последние перемещения за указанное количество дней"""
        movements = self.movement_history_repo.find_recent_movements(days)
        return [MovementHistoryDTO.model_validate(row) for row in movements]

def movement_history_service():
    return MovementHistoryService(movement_history_repo=RepoFactory.movement_history_repo())

MovementHistoryServiceType = Annotated[MovementHistoryService, Depends(movement_history_service)]

# Сервис для уведомлений
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

def notification_service():
    return NotificationService(notification_repo=RepoFactory.notification_repo())

NotificationServiceType = Annotated[NotificationService, Depends(notification_service)]

# Сервис для размещения товаров
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

# Сервис для поставок
class SupplyService:
    def __init__(self, supply_repo: SqlAlchemyRepository):
        self.supply_repo: SqlAlchemyRepository = supply_repo

    def get_all_supplies(self) -> List[SupplyDTO]:
        supplies = self.supply_repo.find_all()
        return [SupplyDTO.model_validate(row) for row in supplies]

    def get_one_supply(self, supply_id: int) -> SupplyDTO:
        supply = self.supply_repo.find(id=supply_id)
        return SupplyDTO.model_validate(supply)
    
    def add_one_supply(self, supply: SupplyCreateDTO) -> SupplyDTO:
        supply_dict = supply.model_dump()
        db_supply = self.supply_repo.create(supply_dict)
        return SupplyDTO.model_validate(db_supply)
    
    def update_supply(self, supply_id: int, supply: SupplyBaseDTO) -> SupplyDTO:
        supply_dict = supply.model_dump()
        db_supply = self.supply_repo.update(supply_dict, id=supply_id)
        return SupplyDTO.model_validate(db_supply)
    
    def delete_supply(self, supply_id: int) -> SupplyDTO:
        supply = self.supply_repo.delete(id=supply_id)
        return SupplyDTO.model_validate(supply)

    def get_monthly_supply_shipment_report(self, year: int, month: int) -> MonthlyReportDTO:
        """Получить отчет по поставкам и отгрузкам за указанный месяц"""
        from src.repository import RepoFactory
        
        # Получаем поставки за месяц
        supplies = self.supply_repo.find_supplies_by_month(year, month)
        
        # Получаем отгрузки (перемещения со склада) за месяц
        movement_repo = RepoFactory.movement_history_repo()
        shipments = movement_repo.find_shipments_by_month(year, month)
        
        # Получаем информацию о товарах
        product_repo = RepoFactory.product_repo()
        products = product_repo.find_all()
        product_dict = {p.id: p for p in products}
        
        # Формируем общий список операций
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
                reference_id=supply.id
            )
            items.append(item)
            total_supplied += supply.quantity
        
        # Добавляем отгрузки
        for shipment in shipments:
            product = product_dict.get(shipment.product_id)
            item = MonthlyReportItemDTO(
                date=shipment.movement_date,
                product_id=shipment.product_id,
                product_name=product.name if product else "Неизвестный товар",
                type="shipment",
                quantity=shipment.quantity,
                reference_id=shipment.id
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
            net_change=total_supplied - total_shipped
        )

def supply_service():
    return SupplyService(supply_repo=RepoFactory.supply_repo())

SupplyServiceType = Annotated[SupplyService, Depends(supply_service)]