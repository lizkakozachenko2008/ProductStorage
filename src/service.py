from typing import Annotated
from fastapi import Depends
from src.repository import RepoFactory, SqlAlchemyRepository
from src.schemas import (
    UserBaseDTO, UserCreateDTO, UserDTO,
    AdminBaseDTO, AdminCreateDTO, AdminDTO,
    CategoryBaseDTO, CategoryCreateDTO, CategoryDTO,
    ProductBaseDTO, ProductCreateDTO, ProductDTO,
    OverflowBinBaseDTO, OverflowBinCreateDTO, OverflowBinDTO,
    PurchaseOrderBaseDTO, PurchaseOrderCreateDTO, PurchaseOrderDTO,
    ShelfBaseDTO, ShelfCreateDTO, ShelfDTO,
    MovementHistoryBaseDTO, MovementHistoryCreateDTO, MovementHistoryDTO,
    NotificationBaseDTO, NotificationCreateDTO, NotificationDTO,
    ProductPlacementBaseDTO, ProductPlacementCreateDTO, ProductPlacementDTO,
    SupplyBaseDTO, SupplyCreateDTO, SupplyDTO
)

# Сервис для пользователей
class UserService:
    def __init__(self, user_repo: SqlAlchemyRepository):
        self.user_repo: SqlAlchemyRepository = user_repo

    def get_all_users(self) -> list[UserDTO]:
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
        db_user = self.user_repo.update(user_dict, id=user_id)
        return UserDTO.model_validate(db_user)
    
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

    def get_all_admins(self) -> list[AdminDTO]:
        admins = self.admin_repo.find_all()
        return [AdminDTO.model_validate(row) for row in admins]

    def get_one_admin(self, login: str) -> AdminDTO:
        admin = self.admin_repo.find(login=login)
        return AdminDTO.model_validate(admin)
    
    def add_one_admin(self, admin: AdminCreateDTO) -> AdminDTO:
        admin_dict = admin.model_dump()
        db_admin = self.admin_repo.create(admin_dict)
        return AdminDTO.model_validate(db_admin)
    
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

    def get_all_categories(self) -> list[CategoryDTO]:
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
        category = self.category_repo.delete(id=category_id)
        return CategoryDTO.model_validate(category)

def category_service():
    return CategoryService(category_repo=RepoFactory.category_repo())

CategoryServiceType = Annotated[CategoryService, Depends(category_service)]

# Сервис для товаров
class ProductService:
    def __init__(self, product_repo: SqlAlchemyRepository):
        self.product_repo: SqlAlchemyRepository = product_repo

    def get_all_products(self) -> list[ProductDTO]:
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

def product_service():
    return ProductService(product_repo=RepoFactory.product_repo())

def get_low_stock_products(self) -> list[ProductDTO]:
        """Товары с низким запасом (текущее количество <= минимальное)"""
        products = self.product_repo.find_low_stock()
        return [ProductDTO.model_validate(row) for row in products]

ProductServiceType = Annotated[ProductService, Depends(product_service)]

# Сервис для отстойников (overflow bins)
class OverflowBinService:
    def __init__(self, overflow_bin_repo: SqlAlchemyRepository):
        self.overflow_bin_repo: SqlAlchemyRepository = overflow_bin_repo

    def get_all_overflow_bins(self) -> list[OverflowBinDTO]:
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

def overflow_bin_service():
    return OverflowBinService(overflow_bin_repo=RepoFactory.overflow_bin_repo())

OverflowBinServiceType = Annotated[OverflowBinService, Depends(overflow_bin_service)]

# Сервис для заказов на покупку
class PurchaseOrderService:
    def __init__(self, purchase_order_repo: SqlAlchemyRepository):
        self.purchase_order_repo: SqlAlchemyRepository = purchase_order_repo

    def get_all_purchase_orders(self) -> list[PurchaseOrderDTO]:
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

    def get_all_shelves(self) -> list[ShelfDTO]:
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

    def get_all_movement_history(self) -> list[MovementHistoryDTO]:
        history = self.movement_history_repo.find_all()
        return [MovementHistoryDTO.model_validate(row) for row in history]

    def get_one_movement_history(self, history_id: int) -> MovementHistoryDTO:
        history = self.movement_history_repo.find(id=history_id)
        return MovementHistoryDTO.model_validate(history)
    
    def add_one_movement_history(self, movement_history: MovementHistoryCreateDTO) -> MovementHistoryDTO:
        history_dict = movement_history.model_dump()
        db_history = self.movement_history_repo.create(history_dict)
        return MovementHistoryDTO.model_validate(db_history)
    
    def get_recent_movements(self, days: int = 7) -> list[MovementHistoryDTO]:
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

    def get_all_notifications(self) -> list[NotificationDTO]:
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

    def get_all_product_placements(self) -> list[ProductPlacementDTO]:
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

    def get_all_supplies(self) -> list[SupplyDTO]:
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

def supply_service():
    return SupplyService(supply_repo=RepoFactory.supply_repo())

SupplyServiceType = Annotated[SupplyService, Depends(supply_service)]