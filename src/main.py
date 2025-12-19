from fastapi import APIRouter, FastAPI, HTTPException, Depends, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
from src.setup_db import setup_db
from src.settings import settings
from typing import List

# Импортируем только необходимые DTO
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
    FreeSpaceNotificationDTO, PlacementResponseDTO
)

# Импортируем только типы сервисов и функции зависимостей
from src.service import (
    UserServiceType, AdminServiceType, CategoryServiceType, ProductServiceType,
    OverflowBinServiceType, PurchaseOrderServiceType, ShelfServiceType,
    MovementHistoryServiceType, NotificationServiceType, ProductPlacementServiceType,
    SupplyServiceType
)

setup_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== СОЗДАНИЕ РОУТЕРОВ ДЛЯ КАЖДОГО РАЗДЕЛА =====

user_router = APIRouter(prefix="/users", tags=["Users"])
admin_router = APIRouter(prefix="/admins", tags=["Administrators"])
category_router = APIRouter(prefix="/categories", tags=["Categories"])
product_router = APIRouter(prefix="/products", tags=["Products"])
overflow_bin_router = APIRouter(prefix="/overflow-bins", tags=["Overflow Bins"])
purchase_order_router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])
shelf_router = APIRouter(prefix="/shelves", tags=["Shelves"])
movement_history_router = APIRouter(prefix="/movement-history", tags=["Movement History"])
notification_router = APIRouter(prefix="/notifications", tags=["Notifications"])
product_placement_router = APIRouter(prefix="/product-placements", tags=["Product Placements"])
supply_router = APIRouter(prefix="/supplies", tags=["Supplies"])
warehouse_router = APIRouter(prefix="/warehouse", tags=["Warehouse Operations"])
reports_router = APIRouter(prefix="/reports", tags=["Reports"])
system_notifications_router = APIRouter(prefix="/system-notifications", tags=["System Notifications"])

# ===== ЭНДПОИНТЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ =====
@user_router.get("", response_model=List[UserDTO])
def get_users(user_service: UserServiceType):
    return user_service.get_all_users()

@user_router.get("/{user_id}", response_model=UserDTO)
def get_user(user_id: int, user_service: UserServiceType):
    try:
        return user_service.get_one_user(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

@user_router.post("", response_model=UserDTO)
def create_user(user: UserCreateDTO, user_service: UserServiceType):
    user_db = user_service.add_one_user(user)
    return user_db

@user_router.put("/{user_id}", response_model=UserDTO)
def update_user(user_id: int, user: UserBaseDTO, user_service: UserServiceType):
    return user_service.update_user(user_id, user)

@user_router.delete("/{user_id}", response_model=UserDTO)
def delete_user(user_id: int, user_service: UserServiceType):
    try:
        return user_service.delete_user(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

# ===== ЭНДПОИНТЫ ДЛЯ АДМИНИСТРАТОРОВ =====
@admin_router.get("", response_model=List[AdminDTO])
def get_admins(admin_service: AdminServiceType):
    return admin_service.get_all_admins()

@admin_router.get("/{login}", response_model=AdminDTO)
def get_admin(login: str, admin_service: AdminServiceType):
    try:
        return admin_service.get_one_admin(login)
    except Exception:
        raise HTTPException(status_code=404, detail="Администратор не найден")

@admin_router.post("", response_model=AdminDTO)
def create_admin(admin: AdminCreateDTO, admin_service: AdminServiceType):
    return admin_service.add_one_admin(admin)

@admin_router.delete("/{login}", response_model=AdminDTO)
def delete_admin(login: str, admin_service: AdminServiceType):
    try:
        return admin_service.delete_admin(login)
    except Exception:
        raise HTTPException(status_code=404, detail="Администратор не найден")

# ===== ЭНДПОИНТЫ ДЛЯ КАТЕГОРИЙ =====
@category_router.get("", response_model=List[CategoryDTO])
def get_categories(category_service: CategoryServiceType):
    return category_service.get_all_categories()

@category_router.get("/{category_id}", response_model=CategoryDTO)
def get_category(category_id: int, category_service: CategoryServiceType):
    try:
        return category_service.get_one_category(category_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Категория не найдена")

@category_router.post("", response_model=CategoryDTO)
def create_category(category: CategoryCreateDTO, category_service: CategoryServiceType):
    return category_service.add_one_category(category)

@category_router.put("/{category_id}", response_model=CategoryDTO)
def update_category(category_id: int, category: CategoryBaseDTO, category_service: CategoryServiceType):
    try:
        return category_service.update_category(category_id, category)
    except Exception:
        raise HTTPException(status_code=404, detail="Категория не найдена")

@category_router.delete("/{category_id}", response_model=CategoryDTO)
def delete_category(category_id: int, category_service: CategoryServiceType):
    try:
        return category_service.delete_category(category_id)
    except ValueError as e:
        if "продукт" in str(e).lower():
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=404, detail="Категория не найдена")
    except Exception as e:
        raise HTTPException(status_code=404, detail="Категория не найдена")

# ===== ЭНДПОИНТЫ ДЛЯ ТОВАРОВ =====
@product_router.get("", response_model=List[ProductDTO])
def get_products(product_service: ProductServiceType):
    return product_service.get_all_products()

@product_router.get("/{product_id}", response_model=ProductDTO)
def get_product(product_id: int, product_service: ProductServiceType):
    try:
        return product_service.get_one_product(product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

@product_router.post("", response_model=ProductDTO)
def create_product(product: ProductCreateDTO, product_service: ProductServiceType):
    return product_service.add_one_product(product)

@product_router.put("/{product_id}", response_model=ProductDTO)
def update_product(product_id: int, product: ProductBaseDTO, product_service: ProductServiceType):
    try:
        return product_service.update_product(product_id, product)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

@product_router.delete("/{product_id}", response_model=ProductDTO)
def delete_product(product_id: int, product_service: ProductServiceType):
    try:
        return product_service.delete_product(product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

@product_router.get("/low-stock", response_model=List[ProductDTO])
def get_low_stock_products(product_service: ProductServiceType):
    """Товары с низким запасом (текущее количество <= минимальное)"""
    return product_service.get_low_stock_products()

# ===== ЭНДПОИНТЫ ДЛЯ ОТСТОЙНИКОВ =====
@overflow_bin_router.get("", response_model=List[OverflowBinDTO])
def get_overflow_bins(overflow_bin_service: OverflowBinServiceType):
    return overflow_bin_service.get_all_overflow_bins()

@overflow_bin_router.get("/{bin_id}", response_model=OverflowBinDTO)
def get_overflow_bin(bin_id: int, overflow_bin_service: OverflowBinServiceType):
    try:
        return overflow_bin_service.get_one_overflow_bin(bin_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Отстойник не найден")

@overflow_bin_router.post("", response_model=OverflowBinDTO)
def create_overflow_bin(overflow_bin: OverflowBinCreateDTO, overflow_bin_service: OverflowBinServiceType):
    return overflow_bin_service.add_one_overflow_bin(overflow_bin)

@overflow_bin_router.put("/{bin_id}", response_model=OverflowBinDTO)
def update_overflow_bin(bin_id: int, overflow_bin: OverflowBinBaseDTO, overflow_bin_service: OverflowBinServiceType):
    try:
        return overflow_bin_service.update_overflow_bin(bin_id, overflow_bin)
    except Exception:
        raise HTTPException(status_code=404, detail="Отстойник не найден")

@overflow_bin_router.delete("/{bin_id}", response_model=OverflowBinDTO)
def delete_overflow_bin(bin_id: int, overflow_bin_service: OverflowBinServiceType):
    try:
        return overflow_bin_service.delete_overflow_bin(bin_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Отстойник не найден")

# ===== ЭНДПОИНТЫ ДЛЯ ЗАКАЗОВ НА ПОКУПКУ =====
@purchase_order_router.get("", response_model=List[PurchaseOrderDTO])
def get_purchase_orders(purchase_order_service: PurchaseOrderServiceType):
    return purchase_order_service.get_all_purchase_orders()

@purchase_order_router.get("/{order_id}", response_model=PurchaseOrderDTO)
def get_purchase_order(order_id: int, purchase_order_service: PurchaseOrderServiceType):
    try:
        return purchase_order_service.get_one_purchase_order(order_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Заказ на покупку не найден")

@purchase_order_router.post("", response_model=PurchaseOrderDTO)
def create_purchase_order(purchase_order: PurchaseOrderCreateDTO, purchase_order_service: PurchaseOrderServiceType):
    return purchase_order_service.add_one_purchase_order(purchase_order)

@purchase_order_router.put("/{order_id}", response_model=PurchaseOrderDTO)
def update_purchase_order(order_id: int, purchase_order: PurchaseOrderBaseDTO, purchase_order_service: PurchaseOrderServiceType):
    try:
        return purchase_order_service.update_purchase_order(order_id, purchase_order)
    except Exception:
        raise HTTPException(status_code=404, detail="Заказ на покупку не найден")

@purchase_order_router.delete("/{order_id}", response_model=PurchaseOrderDTO)
def delete_purchase_order(order_id: int, purchase_order_service: PurchaseOrderServiceType):
    try:
        return purchase_order_service.delete_purchase_order(order_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Заказ на покупку не найден")

# ===== ЭНДПОИНТЫ ДЛЯ СТЕЛЛАЖЕЙ =====
@shelf_router.get("", response_model=List[ShelfDTO])
def get_shelves(shelf_service: ShelfServiceType):
    return shelf_service.get_all_shelves()

@shelf_router.get("/{shelf_id}", response_model=ShelfDTO)
def get_shelf(shelf_id: int, shelf_service: ShelfServiceType):
    try:
        return shelf_service.get_one_shelf(shelf_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

@shelf_router.post("", response_model=ShelfDTO)
def create_shelf(shelf: ShelfCreateDTO, shelf_service: ShelfServiceType):
    return shelf_service.add_one_shelf(shelf)

@shelf_router.put("/{shelf_id}", response_model=ShelfDTO)
def update_shelf(shelf_id: int, shelf: ShelfBaseDTO, shelf_service: ShelfServiceType):
    try:
        return shelf_service.update_shelf(shelf_id, shelf)
    except Exception:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

@shelf_router.delete("/{shelf_id}", response_model=ShelfDTO)
def delete_shelf(shelf_id: int, shelf_service: ShelfServiceType):
    try:
        return shelf_service.delete_shelf(shelf_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

# ===== ЭНДПОИНТЫ ДЛЯ ИСТОРИИ ПЕРЕМЕЩЕНИЙ =====
@movement_history_router.get("", response_model=List[MovementHistoryDTO])
def get_movement_history(movement_history_service: MovementHistoryServiceType):
    return movement_history_service.get_all_movement_history()

@movement_history_router.get("/{history_id}", response_model=MovementHistoryDTO)
def get_movement_history_record(history_id: int, movement_history_service: MovementHistoryServiceType):
    try:
        return movement_history_service.get_one_movement_history(history_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Запись истории перемещений не найдена")

@movement_history_router.post("", response_model=MovementHistoryDTO)
def create_movement_history(movement_history: MovementHistoryCreateDTO, movement_history_service: MovementHistoryServiceType):
    return movement_history_service.add_one_movement_history(movement_history)

@movement_history_router.get("/recent/{days}")
def get_recent_movements(
    days: int = Path(..., ge=1, le=365, description="Количество дней"),
    movement_history_service: MovementHistoryServiceType = None
):
    """Последние перемещения за указанное количество дней"""
    return movement_history_service.get_recent_movements(days)

# ===== ЭНДПОИНТЫ ДЛЯ УВЕДОМЛЕНИЙ =====
@notification_router.get("", response_model=List[NotificationDTO])
def get_notifications(notification_service: NotificationServiceType):
    return notification_service.get_all_notifications()

@notification_router.get("/{notification_id}", response_model=NotificationDTO)
def get_notification(notification_id: int, notification_service: NotificationServiceType):
    try:
        return notification_service.get_one_notification(notification_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

@notification_router.post("", response_model=NotificationDTO)
def create_notification(notification: NotificationCreateDTO, notification_service: NotificationServiceType):
    return notification_service.add_one_notification(notification)

@notification_router.put("/{notification_id}", response_model=NotificationDTO)
def update_notification(notification_id: int, notification: NotificationBaseDTO, notification_service: NotificationServiceType):
    try:
        return notification_service.update_notification(notification_id, notification)
    except Exception:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

@notification_router.delete("/{notification_id}", response_model=NotificationDTO)
def delete_notification(notification_id: int, notification_service: NotificationServiceType):
    try:
        return notification_service.delete_notification(notification_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

# ===== ЭНДПОИНТЫ ДЛЯ РАЗМЕЩЕНИЯ ТОВАРОВ =====
@product_placement_router.get("", response_model=List[ProductPlacementDTO])
def get_product_placements(product_placement_service: ProductPlacementServiceType):
    return product_placement_service.get_all_product_placements()

@product_placement_router.get("/{placement_id}", response_model=ProductPlacementDTO)
def get_product_placement(placement_id: int, product_placement_service: ProductPlacementServiceType):
    try:
        return product_placement_service.get_one_product_placement(placement_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Размещение товара не найдено")

@product_placement_router.post("", response_model=ProductPlacementDTO)
def create_product_placement(product_placement: ProductPlacementCreateDTO, product_placement_service: ProductPlacementServiceType):
    return product_placement_service.add_one_product_placement(product_placement)

@product_placement_router.put("/{placement_id}", response_model=ProductPlacementDTO)
def update_product_placement(placement_id: int, product_placement: ProductPlacementBaseDTO, product_placement_service: ProductPlacementServiceType):
    try:
        return product_placement_service.update_product_placement(placement_id, product_placement)
    except Exception:
        raise HTTPException(status_code=404, detail="Размещение товара не найдено")

@product_placement_router.delete("/{placement_id}", response_model=ProductPlacementDTO)
def delete_product_placement(placement_id: int, product_placement_service: ProductPlacementServiceType):
    try:
        return product_placement_service.delete_product_placement(placement_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Размещение товара не найдено")

# ===== ЭНДПОИНТЫ ДЛЯ ПОСТАВОК =====
@supply_router.get("", response_model=List[SupplyDTO])
def get_supplies(supply_service: SupplyServiceType):
    return supply_service.get_all_supplies()

@supply_router.get("/{supply_id}", response_model=SupplyDTO)
def get_supply(supply_id: int, supply_service: SupplyServiceType):
    try:
        return supply_service.get_one_supply(supply_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Поставка не найдена")

@supply_router.post("", response_model=SupplyDTO)
def create_supply(supply: SupplyCreateDTO, supply_service: SupplyServiceType):
    return supply_service.add_one_supply(supply)

@supply_router.put("/{supply_id}", response_model=SupplyDTO)
def update_supply(supply_id: int, supply: SupplyBaseDTO, supply_service: SupplyServiceType):
    try:
        return supply_service.update_supply(supply_id, supply)
    except Exception:
        raise HTTPException(status_code=404, detail="Поставка не найдена")

@supply_router.delete("/{supply_id}", response_model=SupplyDTO)
def delete_supply(supply_id: int, supply_service: SupplyServiceType):
    try:
        return supply_service.delete_supply(supply_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Поставка не найдена")

# ===== ЭНДПОИНТЫ ДЛЯ ОПЕРАЦИЙ СО СКЛАДОМ =====
@warehouse_router.post("/place-product", response_model=PlacementResponseDTO)
def place_product_on_warehouse(
    placement: ProductPlaceRequestDTO,
    product_service: ProductServiceType
):
    """
    Разместить товар на складе.
    
    - Если указан shelf_id: разместить на стеллаже
    - Если указан overflow_id: разместить в отстойник
    """
    return product_service.place_product(placement)

@warehouse_router.post("/move-from-overflow/{overflow_bin_id}/to-shelf/{shelf_id}")
def move_product_from_overflow_to_shelf(
    overflow_bin_id: int = Path(..., description="ID отстойника"),
    shelf_id: int = Path(..., description="ID стеллажа"),
    overflow_bin_service: OverflowBinServiceType = None,
    product_service: ProductServiceType = None
):
    """Переместить товар из отстойника на стеллаж"""
    # Получаем информацию об отстойнике
    overflow_bin = overflow_bin_service.get_one_overflow_bin(overflow_bin_id)
    if not overflow_bin:
        raise HTTPException(status_code=404, detail="Отстойник не найден")
    
    # Проверяем, есть ли товар в отстойнике
    if overflow_bin.quantity <= 0:
        raise HTTPException(status_code=400, detail="В отстойнике нет товара")
    
    # Создаем запрос на размещение
    placement_data = ProductPlaceRequestDTO(
        product_id=overflow_bin.product_id,
        shelf_id=shelf_id,
        quantity=overflow_bin.quantity
    )
    
    try:
        # Размещаем товар на стеллаже
        result = product_service.place_product(placement_data)
        
        # Удаляем товар из отстойника
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

# ===== ЭНДПОИНТЫ ДЛЯ ОТЧЕТОВ =====
@reports_router.get("/placement", response_model=PlacementReportDTO)
def get_product_placement_report(
    product_service: ProductServiceType = None
):
    """Получить отчет по размещению товаров на складе"""
    return product_service.get_placement_report()

@reports_router.get("/monthly/{year}/{month}", response_model=MonthlyReportDTO)
def get_monthly_supply_shipment_report(
    year: int = Path(..., ge=2000, le=2100, description="Год"),
    month: int = Path(..., ge=1, le=12, description="Месяц (1-12)"),
    supply_service: SupplyServiceType = None
):
    """Получить отчет по поставкам и отгрузкам за указанный месяц"""
    return supply_service.get_monthly_supply_shipment_report(year, month)

@reports_router.get("/inventory-status")
def get_inventory_status_report(
    product_service: ProductServiceType = None
):
    """Получить сводный отчет по состоянию инвентаря"""
    # Товары с низким запасом
    low_stock = product_service.get_low_stock_products()
    
    # Все товары
    all_products = product_service.get_all_products()
    
    # Статистика
    total_products = len(all_products)
    total_quantity = sum(p.current_quantity for p in all_products)
    low_stock_count = len(low_stock)
    
    # Группировка по категориям
    from collections import defaultdict
    category_stats = defaultdict(lambda: {"total": 0, "low_stock": 0, "quantity": 0})
    
    for product in all_products:
        category_stats[product.category_id]["total"] += 1
        category_stats[product.category_id]["quantity"] += product.current_quantity
        
        # Проверяем, находится ли товар в списке low_stock
        if any(p.id == product.id for p in low_stock):
            category_stats[product.category_id]["low_stock"] += 1
    
    return {
        "summary": {
            "total_products": total_products,
            "total_quantity": total_quantity,
            "low_stock_products": low_stock_count,
            "low_stock_percentage": round((low_stock_count / total_products * 100) if total_products > 0 else 0, 2)
        },
        "by_category": [
            {
                "category_id": cat_id,
                **stats
            } for cat_id, stats in category_stats.items()
        ],
        "low_stock_details": [
            {
                "id": p.id,
                "name": p.name,
                "category_id": p.category_id,
                "current_quantity": p.current_quantity,
                "min_quantity": p.min_quantity,
                "difference": p.min_quantity - p.current_quantity
            } for p in low_stock
        ]
    }

# ===== ЭНДПОИНТЫ ДЛЯ СИСТЕМНЫХ УВЕДОМЛЕНИЙ =====
@system_notifications_router.get("/overflow-opportunities", response_model=List[FreeSpaceNotificationDTO])
def get_overflow_placement_opportunities(
    overflow_bin_service: OverflowBinServiceType = None
):
    """
    Получить уведомления о возможности размещения товаров из отстойника.
    
    Система проверяет, есть ли свободное место на стеллажах для товаров,
    которые находятся в отстойнике.
    """
    return overflow_bin_service.check_overflow_for_free_shelves()

@system_notifications_router.get("/low-stock")
def get_low_stock_notifications(
    product_service: ProductServiceType = None
):
    """Получить уведомления о товарах с низким запасом"""
    low_stock = product_service.get_low_stock_products()
    
    return {
        "count": len(low_stock),
        "notifications": [
            {
                "product_id": p.id,
                "product_name": p.name,
                "current_quantity": p.current_quantity,
                "min_quantity": p.min_quantity,
                "urgent": p.current_quantity <= p.min_quantity * 0.5,  # Критически низкий запас
                "message": f"Товар '{p.name}': текущий запас {p.current_quantity}, минимальный {p.min_quantity}"
            } for p in low_stock
        ]
    }

# ===== КОРНЕВОЙ ЭНДПОИНТ =====
@app.get('/')
def root():
    return RedirectResponse('/docs')

# ===== ПОДКЛЮЧЕНИЕ ВСЕХ РОУТЕРОВ =====
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(overflow_bin_router)
app.include_router(purchase_order_router)
app.include_router(shelf_router)
app.include_router(movement_history_router)
app.include_router(notification_router)
app.include_router(product_placement_router)
app.include_router(supply_router)
app.include_router(warehouse_router)
app.include_router(reports_router)
app.include_router(system_notifications_router)

# ===== ЗАПУСК ПРИЛОЖЕНИЯ =====
if __name__ == '__main__':
    uvicorn.run(app)