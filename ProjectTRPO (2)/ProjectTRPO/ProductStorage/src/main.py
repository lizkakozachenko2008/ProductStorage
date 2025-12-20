from fastapi import APIRouter, FastAPI, HTTPException, Depends, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
from src.setup_db import setup_db
from src.settings import settings
from typing import List, Optional

# Импорт DTO
from src.schemas import (
    UserDTO, UserCreateDTO, UserBaseDTO,
    AdminDTO, AdminCreateDTO,
    CategoryDTO, CategoryCreateDTO, CategoryBaseDTO,
    StockDTO,
    ProductDTO, ProductCreateDTO, ProductBaseDTO,
    OverflowBinDTO, OverflowBinCreateDTO, OverflowBinBaseDTO,
    PurchaseOrderDTO, PurchaseOrderCreateDTO, PurchaseOrderBaseDTO,
    ShelfDTO, ShelfCreateDTO, ShelfBaseDTO,
    MovementHistoryDTO, MovementHistoryCreateDTO, MovementHistoryBaseDTO,
    NotificationDTO, NotificationCreateDTO, NotificationBaseDTO,
    ProductPlacementDTO, ProductPlacementCreateDTO, ProductPlacementBaseDTO,
    SupplyDTO, SupplyCreateDTO, SupplyBaseDTO,
    ShipmentDTO, ShipmentCreateDTO, ShipmentBaseDTO,
    ProductPlaceRequestDTO, ShipmentRequestDTO,
    PlacementReportDTO, MonthlyReportDTO, InventoryReportDTO,
    FreeSpaceNotificationDTO, LowStockNotificationDTO,
    PlacementResponseDTO, ShipmentResponseDTO, SupplyResponseDTO,
    StockStatisticsDTO
)

# Импорт сервисов и фабричных функций
from src.service import (
    UserService, AdminService, CategoryService, 
    StockService, ProductService, OverflowBinService, 
    PurchaseOrderService, ShelfService, MovementHistoryService, 
    NotificationService, ProductPlacementService, SupplyService,
    ShipmentService, WarehouseService,
    user_service, admin_service, category_service,
    stock_service, product_service, overflow_bin_service,
    purchase_order_service, shelf_service, movement_history_service,
    notification_service, product_placement_service, supply_service,
    shipment_service, warehouse_service
)

setup_db()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== СОЗДАНИЕ РОУТЕРОВ =====
user_router = APIRouter(prefix="/users", tags=["Users"])
admin_router = APIRouter(prefix="/admins", tags=["Administrators"])
category_router = APIRouter(prefix="/categories", tags=["Categories"])
stock_router = APIRouter(prefix="/stocks", tags=["Stocks"])
product_router = APIRouter(prefix="/products", tags=["Products"])
overflow_bin_router = APIRouter(prefix="/overflow-bins", tags=["Overflow Bins"])
purchase_order_router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])
shelf_router = APIRouter(prefix="/shelves", tags=["Shelves"])
movement_history_router = APIRouter(prefix="/movement-history", tags=["Movement History"])
notification_router = APIRouter(prefix="/notifications", tags=["Notifications"])
product_placement_router = APIRouter(prefix="/product-placements", tags=["Product Placements"])
supply_router = APIRouter(prefix="/supplies", tags=["Supplies"])
shipment_router = APIRouter(prefix="/shipments", tags=["Shipments"])
warehouse_router = APIRouter(prefix="/warehouse", tags=["Warehouse Operations"])
reports_router = APIRouter(prefix="/reports", tags=["Reports"])
system_notifications_router = APIRouter(prefix="/system-notifications", tags=["System Notifications"])

# ===== ПОЛЬЗОВАТЕЛИ =====
@user_router.get("", response_model=List[UserDTO])
def get_users(user_service: UserService = Depends(user_service)):
    return user_service.get_all_users()

@user_router.get("/{user_id}", response_model=UserDTO)
def get_user(user_id: int, user_service: UserService = Depends(user_service)):
    try:
        return user_service.get_one_user(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

@user_router.post("", response_model=UserDTO)
def create_user(user: UserCreateDTO, user_service: UserService = Depends(user_service)):
    return user_service.add_one_user(user)

@user_router.put("/{user_id}", response_model=UserDTO)
def update_user(user_id: int, user: UserBaseDTO, user_service: UserService = Depends(user_service)):
    return user_service.update_user(user_id, user)

@user_router.delete("/{user_id}", response_model=UserDTO)
def delete_user(user_id: int, user_service: UserService = Depends(user_service)):
    try:
        return user_service.delete_user(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

# ===== АДМИНИСТРАТОРЫ =====
@admin_router.get("", response_model=List[AdminDTO])
def get_admins(admin_service: AdminService = Depends(admin_service)):
    return admin_service.get_all_admins()

@admin_router.get("/{login}", response_model=AdminDTO)
def get_admin(login: str, admin_service: AdminService = Depends(admin_service)):
    try:
        return admin_service.get_one_admin(login)
    except Exception:
        raise HTTPException(status_code=404, detail="Администратор не найден")

@admin_router.post("", response_model=AdminDTO)
def create_admin(admin: AdminCreateDTO, admin_service: AdminService = Depends(admin_service)):
    return admin_service.add_one_admin(admin)

@admin_router.delete("/{login}", response_model=AdminDTO)
def delete_admin(login: str, admin_service: AdminService = Depends(admin_service)):
    try:
        return admin_service.delete_admin(login)
    except Exception:
        raise HTTPException(status_code=404, detail="Администратор не найден")

# ===== КАТЕГОРИИ =====
@category_router.get("", response_model=List[CategoryDTO])
def get_categories(category_service: CategoryService = Depends(category_service)):
    return category_service.get_all_categories()

@category_router.get("/{category_id}", response_model=CategoryDTO)
def get_category(category_id: int, category_service: CategoryService = Depends(category_service)):
    try:
        return category_service.get_one_category(category_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Категория не найдена")

@category_router.post("", response_model=CategoryDTO)
def create_category(category: CategoryCreateDTO, category_service: CategoryService = Depends(category_service)):
    return category_service.add_one_category(category)

@category_router.put("/{category_id}", response_model=CategoryDTO)
def update_category(category_id: int, category: CategoryBaseDTO, category_service: CategoryService = Depends(category_service)):
    try:
        return category_service.update_category(category_id, category)
    except Exception:
        raise HTTPException(status_code=404, detail="Категория не найдена")

@category_router.delete("/{category_id}", response_model=CategoryDTO)
def delete_category(category_id: int, category_service: CategoryService = Depends(category_service)):
    try:
        return category_service.delete_category(category_id)
    except ValueError as e:
        if "продукт" in str(e).lower():
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=404, detail="Категория не найдена")
    except Exception as e:
        raise HTTPException(status_code=404, detail="Категория не найдена")

# ===== ЗАПАСЫ =====
@stock_router.get("/product/{product_id}", response_model=StockDTO)
def get_product_stock(product_id: int, stock_service: StockService = Depends(stock_service)):
    stock = stock_service.get_stock_by_product(product_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Запасы товара не найдены")
    return stock

@stock_router.get("/summary", response_model=StockStatisticsDTO)
def get_stock_summary(stock_service: StockService = Depends(stock_service)):
    return stock_service.get_stock_statistics()

@stock_router.post("/reserve/{product_id}")
def reserve_product_stock(
    product_id: int,
    quantity: int = Query(gt=0, description="Количество для резервирования"),
    stock_service: StockService = Depends(stock_service)
):
    try:
        stock = stock_service.reserve_stock(product_id, quantity)
        return {
            "message": f"Успешно зарезервировано {quantity} единиц товара",
            "stock": stock
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stock_router.post("/release/{product_id}")
def release_product_stock(
    product_id: int,
    quantity: int = Query(gt=0, description="Количество для освобождения"),
    stock_service: StockService = Depends(stock_service)
):
    try:
        stock = stock_service.release_stock(product_id, quantity)
        return {
            "message": f"Успешно освобождено {quantity} единиц товара",
            "stock": stock
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stock_router.get("/low-stock")
def get_low_stock_report(stock_service: StockService = Depends(stock_service)):
    return stock_service.get_low_stock_products()

# ===== ТОВАРЫ =====
@product_router.get("", response_model=List[ProductDTO])
def get_products(product_service: ProductService = Depends(product_service)):
    return product_service.get_all_products()

@product_router.get("/{product_id}", response_model=ProductDTO)
def get_product(product_id: int, product_service: ProductService = Depends(product_service)):
    try:
        return product_service.get_one_product(product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

@product_router.post("", response_model=ProductDTO)
def create_product(product: ProductCreateDTO, product_service: ProductService = Depends(product_service)):
    return product_service.add_one_product(product)

@product_router.put("/{product_id}", response_model=ProductDTO)
def update_product(product_id: int, product: ProductBaseDTO, product_service: ProductService = Depends(product_service)):
    try:
        return product_service.update_product(product_id, product)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

@product_router.delete("/{product_id}", response_model=ProductDTO)
def delete_product(product_id: int, product_service: ProductService = Depends(product_service)):
    try:
        return product_service.delete_product(product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

@product_router.get("/low-stock", response_model=List[ProductDTO])
def get_low_stock_products(product_service: ProductService = Depends(product_service)):
    return product_service.get_low_stock_products()

# ===== ОТСТОЙНИКИ =====
@overflow_bin_router.get("", response_model=List[OverflowBinDTO])
def get_overflow_bins(overflow_bin_service: OverflowBinService = Depends(overflow_bin_service)):
    return overflow_bin_service.get_all_overflow_bins()

@overflow_bin_router.get("/{bin_id}", response_model=OverflowBinDTO)
def get_overflow_bin(bin_id: int, overflow_bin_service: OverflowBinService = Depends(overflow_bin_service)):
    try:
        return overflow_bin_service.get_one_overflow_bin(bin_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Отстойник не найден")

@overflow_bin_router.post("", response_model=OverflowBinDTO)
def create_overflow_bin(overflow_bin: OverflowBinCreateDTO, overflow_bin_service: OverflowBinService = Depends(overflow_bin_service)):
    return overflow_bin_service.add_one_overflow_bin(overflow_bin)

@overflow_bin_router.put("/{bin_id}", response_model=OverflowBinDTO)
def update_overflow_bin(bin_id: int, overflow_bin: OverflowBinBaseDTO, overflow_bin_service: OverflowBinService = Depends(overflow_bin_service)):
    try:
        return overflow_bin_service.update_overflow_bin(bin_id, overflow_bin)
    except Exception:
        raise HTTPException(status_code=404, detail="Отстойник не найден")

@overflow_bin_router.delete("/{bin_id}", response_model=OverflowBinDTO)
def delete_overflow_bin(bin_id: int, overflow_bin_service: OverflowBinService = Depends(overflow_bin_service)):
    try:
        return overflow_bin_service.delete_overflow_bin(bin_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Отстойник не найден")

# ===== ЗАКАЗЫ НА ПОКУПКУ =====
@purchase_order_router.get("", response_model=List[PurchaseOrderDTO])
def get_purchase_orders(purchase_order_service: PurchaseOrderService = Depends(purchase_order_service)):
    return purchase_order_service.get_all_purchase_orders()

@purchase_order_router.get("/{order_id}", response_model=PurchaseOrderDTO)
def get_purchase_order(order_id: int, purchase_order_service: PurchaseOrderService = Depends(purchase_order_service)):
    try:
        return purchase_order_service.get_one_purchase_order(order_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Заказ на покупку не найден")

@purchase_order_router.post("", response_model=PurchaseOrderDTO)
def create_purchase_order(purchase_order: PurchaseOrderCreateDTO, purchase_order_service: PurchaseOrderService = Depends(purchase_order_service)):
    return purchase_order_service.add_one_purchase_order(purchase_order)

@purchase_order_router.put("/{order_id}", response_model=PurchaseOrderDTO)
def update_purchase_order(order_id: int, purchase_order: PurchaseOrderBaseDTO, purchase_order_service: PurchaseOrderService = Depends(purchase_order_service)):
    try:
        return purchase_order_service.update_purchase_order(order_id, purchase_order)
    except Exception:
        raise HTTPException(status_code=404, detail="Заказ на покупку не найден")

@purchase_order_router.delete("/{order_id}", response_model=PurchaseOrderDTO)
def delete_purchase_order(order_id: int, purchase_order_service: PurchaseOrderService = Depends(purchase_order_service)):
    try:
        return purchase_order_service.delete_purchase_order(order_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Заказ на покупку не найден")

# ===== СТЕЛЛАЖИ =====
@shelf_router.get("", response_model=List[ShelfDTO])
def get_shelves(shelf_service: ShelfService = Depends(shelf_service)):
    return shelf_service.get_all_shelves()

@shelf_router.get("/{shelf_id}", response_model=ShelfDTO)
def get_shelf(shelf_id: int, shelf_service: ShelfService = Depends(shelf_service)):
    try:
        return shelf_service.get_one_shelf(shelf_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

@shelf_router.post("", response_model=ShelfDTO)
def create_shelf(shelf: ShelfCreateDTO, shelf_service: ShelfService = Depends(shelf_service)):
    return shelf_service.add_one_shelf(shelf)

@shelf_router.put("/{shelf_id}", response_model=ShelfDTO)
def update_shelf(shelf_id: int, shelf: ShelfBaseDTO, shelf_service: ShelfService = Depends(shelf_service)):
    try:
        return shelf_service.update_shelf(shelf_id, shelf)
    except Exception:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

@shelf_router.delete("/{shelf_id}", response_model=ShelfDTO)
def delete_shelf(shelf_id: int, shelf_service: ShelfService = Depends(shelf_service)):
    try:
        return shelf_service.delete_shelf(shelf_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

# ===== ИСТОРИЯ ПЕРЕМЕЩЕНИЙ =====
@movement_history_router.get("", response_model=List[MovementHistoryDTO])
def get_movement_history(movement_history_service: MovementHistoryService = Depends(movement_history_service)):
    return movement_history_service.get_all_movement_history()

@movement_history_router.get("/{history_id}", response_model=MovementHistoryDTO)
def get_movement_history_record(history_id: int, movement_history_service: MovementHistoryService = Depends(movement_history_service)):
    try:
        return movement_history_service.get_one_movement_history(history_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Запись истории перемещений не найдена")

@movement_history_router.post("", response_model=MovementHistoryDTO)
def create_movement_history(movement_history: MovementHistoryCreateDTO, movement_history_service: MovementHistoryService = Depends(movement_history_service)):
    return movement_history_service.add_one_movement_history(movement_history)

@movement_history_router.get("/recent/{days}")
def get_recent_movements(
    days: int = Path(..., ge=1, le=365, description="Количество дней"),
    movement_history_service: MovementHistoryService = Depends(movement_history_service)
):
    return movement_history_service.get_recent_movements(days)

# ===== УВЕДОМЛЕНИЯ =====
@notification_router.get("", response_model=List[NotificationDTO])
def get_notifications(notification_service: NotificationService = Depends(notification_service)):
    return notification_service.get_all_notifications()

@notification_router.get("/{notification_id}", response_model=NotificationDTO)
def get_notification(notification_id: int, notification_service: NotificationService = Depends(notification_service)):
    try:
        return notification_service.get_one_notification(notification_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

@notification_router.post("", response_model=NotificationDTO)
def create_notification(notification: NotificationCreateDTO, notification_service: NotificationService = Depends(notification_service)):
    return notification_service.add_one_notification(notification)

@notification_router.put("/{notification_id}", response_model=NotificationDTO)
def update_notification(notification_id: int, notification: NotificationBaseDTO, notification_service: NotificationService = Depends(notification_service)):
    try:
        return notification_service.update_notification(notification_id, notification)
    except Exception:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

@notification_router.delete("/{notification_id}", response_model=NotificationDTO)
def delete_notification(notification_id: int, notification_service: NotificationService = Depends(notification_service)):
    try:
        return notification_service.delete_notification(notification_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

# ===== РАЗМЕЩЕНИЕ ТОВАРОВ =====
@product_placement_router.get("", response_model=List[ProductPlacementDTO])
def get_product_placements(product_placement_service: ProductPlacementService = Depends(product_placement_service)):
    return product_placement_service.get_all_product_placements()

@product_placement_router.get("/{placement_id}", response_model=ProductPlacementDTO)
def get_product_placement(placement_id: int, product_placement_service: ProductPlacementService = Depends(product_placement_service)):
    try:
        return product_placement_service.get_one_product_placement(placement_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Размещение товара не найдено")

@product_placement_router.post("", response_model=ProductPlacementDTO)
def create_product_placement(product_placement: ProductPlacementCreateDTO, product_placement_service: ProductPlacementService = Depends(product_placement_service)):
    return product_placement_service.add_one_product_placement(product_placement)

@product_placement_router.put("/{placement_id}", response_model=ProductPlacementDTO)
def update_product_placement(placement_id: int, product_placement: ProductPlacementBaseDTO, product_placement_service: ProductPlacementService = Depends(product_placement_service)):
    try:
        return product_placement_service.update_product_placement(placement_id, product_placement)
    except Exception:
        raise HTTPException(status_code=404, detail="Размещение товара не найдено")

@product_placement_router.delete("/{placement_id}", response_model=ProductPlacementDTO)
def delete_product_placement(placement_id: int, product_placement_service: ProductPlacementService = Depends(product_placement_service)):
    try:
        return product_placement_service.delete_product_placement(placement_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Размещение товара не найдено")

# ===== ПОСТАВКИ =====
@supply_router.get("", response_model=List[SupplyDTO])
def get_supplies(supply_service: SupplyService = Depends(supply_service)):
    return supply_service.get_all_supplies()

@supply_router.get("/{supply_id}", response_model=SupplyDTO)
def get_supply(supply_id: int, supply_service: SupplyService = Depends(supply_service)):
    try:
        return supply_service.get_one_supply(supply_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Поставка не найдена")

@supply_router.post("", response_model=SupplyResponseDTO)
def create_supply(supply: SupplyCreateDTO, supply_service: SupplyService = Depends(supply_service)):
    return supply_service.add_one_supply(supply)

@supply_router.put("/{supply_id}", response_model=SupplyDTO)
def update_supply(supply_id: int, supply: SupplyBaseDTO, supply_service: SupplyService = Depends(supply_service)):
    try:
        return supply_service.update_supply(supply_id, supply)
    except Exception:
        raise HTTPException(status_code=404, detail="Поставка не найдена")

@supply_router.delete("/{supply_id}", response_model=SupplyDTO)
def delete_supply(supply_id: int, supply_service: SupplyService = Depends(supply_service)):
    try:
        return supply_service.delete_supply(supply_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Поставка не найдена")

# ===== ОТГРУЗКИ =====
@shipment_router.get("", response_model=List[ShipmentDTO])
def get_shipments(shipment_service: ShipmentService = Depends(shipment_service)):
    return shipment_service.get_all_shipments()

@shipment_router.get("/{shipment_id}", response_model=ShipmentDTO)
def get_shipment(shipment_id: int, shipment_service: ShipmentService = Depends(shipment_service)):
    try:
        return shipment_service.get_one_shipment(shipment_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Отгрузка не найдена")

@shipment_router.post("", response_model=ShipmentResponseDTO)
def create_shipment(shipment: ShipmentCreateDTO, shipment_service: ShipmentService = Depends(shipment_service)):
    return shipment_service.create_shipment(shipment)

@shipment_router.put("/{shipment_id}", response_model=ShipmentDTO)
def update_shipment(shipment_id: int, shipment: ShipmentBaseDTO, shipment_service: ShipmentService = Depends(shipment_service)):
    try:
        return shipment_service.update_shipment(shipment_id, shipment)
    except Exception:
        raise HTTPException(status_code=404, detail="Отгрузка не найдена")

@shipment_router.delete("/{shipment_id}", response_model=ShipmentDTO)
def delete_shipment(shipment_id: int, shipment_service: ShipmentService = Depends(shipment_service)):
    try:
        return shipment_service.delete_shipment(shipment_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Отгрузка не найдена")

# ===== ОПЕРАЦИИ СО СКЛАДОМ =====
@warehouse_router.post("/place-product", response_model=PlacementResponseDTO)
def place_product_on_warehouse(
    placement: ProductPlaceRequestDTO,
    product_service: ProductService = Depends(product_service)
):
    return product_service.place_product(placement)

@warehouse_router.post("/ship-product", response_model=ShipmentResponseDTO)
def ship_product_from_warehouse(
    shipment_request: ShipmentRequestDTO,
    shipment_service: ShipmentService = Depends(shipment_service)
):
    shipment_data = ShipmentCreateDTO(**shipment_request.model_dump())
    return shipment_service.create_shipment(shipment_data)

@warehouse_router.post("/move-from-overflow/{overflow_bin_id}/to-shelf/{shelf_id}")
def move_product_from_overflow_to_shelf(
    overflow_bin_id: int = Path(..., description="ID отстойника"),
    shelf_id: int = Path(..., description="ID стеллажа"),
    overflow_bin_service: OverflowBinService = Depends(overflow_bin_service),
    product_service: ProductService = Depends(product_service)
):
    overflow_bin = overflow_bin_service.get_one_overflow_bin(overflow_bin_id)
    if not overflow_bin:
        raise HTTPException(status_code=404, detail="Отстойник не найден")
    
    if overflow_bin.quantity <= 0:
        raise HTTPException(status_code=400, detail="В отстойнике нет товара")
    
    placement_data = ProductPlaceRequestDTO(
        product_id=overflow_bin.product_id,
        shelf_id=shelf_id,
        quantity=overflow_bin.quantity
    )
    
    try:
        result = product_service.place_product(placement_data)
        overflow_bin_service.delete_overflow_bin(overflow_bin_id)
        
        return {
            "message": "Товар успешно перемещен из отстойника на стеллаж",
            "placement": result.placement,
            "overflow_bin_deleted": True
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ОТЧЕТЫ =====
@reports_router.get("/placement", response_model=PlacementReportDTO)
def get_product_placement_report(product_service: ProductService = Depends(product_service)):
    return product_service.get_placement_report()

@reports_router.get("/inventory", response_model=InventoryReportDTO)
def get_inventory_report(warehouse_service: WarehouseService = Depends(warehouse_service)):
    return warehouse_service.get_inventory_report()

@reports_router.get("/monthly/{year}/{month}", response_model=MonthlyReportDTO)
def get_monthly_supply_shipment_report(
    year: int = Path(..., ge=2000, le=2100, description="Год"),
    month: int = Path(..., ge=1, le=12, description="Месяц (1-12)"),
    supply_service: SupplyService = Depends(supply_service)
):
    return supply_service.get_monthly_supply_shipment_report(year, month)

@reports_router.get("/stock-statistics", response_model=StockStatisticsDTO)
def get_stock_statistics_report(stock_service: StockService = Depends(stock_service)):
    return stock_service.get_stock_statistics()

# ===== СИСТЕМНЫЕ УВЕДОМЛЕНИЯ =====
@system_notifications_router.get("/overflow-opportunities", response_model=List[FreeSpaceNotificationDTO])
def get_overflow_placement_opportunities(overflow_bin_service: OverflowBinService = Depends(overflow_bin_service)):
    return overflow_bin_service.check_overflow_for_free_shelves()

@system_notifications_router.get("/low-stock", response_model=List[LowStockNotificationDTO])
def get_low_stock_notifications(stock_service: StockService = Depends(stock_service)):
    low_stock = stock_service.get_low_stock_products()
    
    notifications = []
    for item in low_stock:
        notification = LowStockNotificationDTO(
            product_id=item['product_id'],
            product_name=item['product_name'],
            current_quantity=item['available'],
            min_quantity=item['min_required'],
            deficit=item['deficit'],
            unit=item['unit'],
            is_critical=item['is_critical'],
            message=f"Товар '{item['product_name']}': запас {item['available']}, минимум {item['min_required']}"
        )
        notifications.append(notification)
    
    return notifications

@system_notifications_router.get("/shelf-utilization")
def get_shelf_utilization_notifications(shelf_service: ShelfService = Depends(shelf_service)):
    utilization = shelf_service.get_shelf_utilization()
    
    warnings = []
    for shelf in utilization:
        if shelf['utilization_percent'] >= 90:
            warnings.append({
                "shelf_id": shelf['id'],
                "shelf_name": shelf['name'],
                "utilization": round(shelf['utilization_percent'], 2),
                "message": f"Стеллаж '{shelf['name']}' заполнен на {round(shelf['utilization_percent'], 2)}%"
            })
        elif shelf['utilization_percent'] <= 10:
            warnings.append({
                "shelf_id": shelf['id'],
                "shelf_name": shelf['name'],
                "utilization": round(shelf['utilization_percent'], 2),
                "message": f"Стеллаж '{shelf['name']}' почти пуст ({round(shelf['utilization_percent'], 2)}% заполнения)"
            })
    
    return {
        "count": len(warnings),
        "warnings": warnings
    }

# ===== КОРНЕВОЙ ЭНДПОИНТ =====
@app.get('/')
def root():
    return RedirectResponse('/docs')

# ===== ПОДКЛЮЧЕНИЕ РОУТЕРОВ =====
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(category_router)
app.include_router(stock_router)
app.include_router(product_router)
app.include_router(overflow_bin_router)
app.include_router(purchase_order_router)
app.include_router(shelf_router)
app.include_router(movement_history_router)
app.include_router(notification_router)
app.include_router(product_placement_router)
app.include_router(supply_router)
app.include_router(shipment_router)
app.include_router(warehouse_router)
app.include_router(reports_router)
app.include_router(system_notifications_router)

# ===== ЗАПУСК =====
if __name__ == '__main__':
    uvicorn.run(app)