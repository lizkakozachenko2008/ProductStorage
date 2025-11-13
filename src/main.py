from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
from src.setup_db import setup_db
from src.schemas import (
    UserBaseDTO, UserCreateDTO, UserDTO,
    AdminCreateDTO, AdminDTO,
    CategoryBaseDTO, CategoryCreateDTO, CategoryDTO,
    ProductBaseDTO, ProductCreateDTO, ProductDTO,
    OverflowBinBaseDTO, OverflowBinCreateDTO, OverflowBinDTO,
    PurchaseOrderBaseDTO, PurchaseOrderCreateDTO, PurchaseOrderDTO,
    ShelfBaseDTO, ShelfCreateDTO, ShelfDTO,
    MovementHistoryCreateDTO, MovementHistoryDTO,
    NotificationBaseDTO, NotificationCreateDTO, NotificationDTO,
    ProductPlacementBaseDTO, ProductPlacementCreateDTO, ProductPlacementDTO,
    SupplyBaseDTO, SupplyCreateDTO, SupplyDTO
)
from src.service import (
    UserServiceType, AdminServiceType, CategoryServiceType, ProductServiceType,
    OverflowBinServiceType, PurchaseOrderServiceType, ShelfServiceType,
    MovementHistoryServiceType, NotificationServiceType, ProductPlacementServiceType,
    SupplyServiceType
)
from src.settings import settings

setup_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
@app.get("/users", response_model=list[UserDTO])
def get_users(user_service: UserServiceType):
    return user_service.get_all_users()

@app.get("/users/{user_id}", response_model=UserDTO)
def get_user(user_id: int, user_service: UserServiceType):
    try:
        return user_service.get_one_user(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

@app.post("/users", response_model=UserDTO)
def create_user(user: UserCreateDTO, user_service: UserServiceType):
    return user_service.add_one_user(user)

@app.put("/users/{user_id}", response_model=UserDTO)
def update_user(user_id: int, user: UserBaseDTO, user_service: UserServiceType):
    try:
        return user_service.update_user(user_id, user)
    except Exception:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

@app.delete("/users/{user_id}", response_model=UserDTO)
def delete_user(user_id: int, user_service: UserServiceType):
    try:
        return user_service.delete_user(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

# ДЛЯ АДМИНИСТРАТОРОВ 
@app.get("/admins", response_model=list[AdminDTO])
def get_admins(admin_service: AdminServiceType):
    return admin_service.get_all_admins()

@app.get("/admins/{login}", response_model=AdminDTO)
def get_admin(login: str, admin_service: AdminServiceType):
    try:
        return admin_service.get_one_admin(login)
    except Exception:
        raise HTTPException(status_code=404, detail="Администратор не найден")

@app.post("/admins", response_model=AdminDTO)
def create_admin(admin: AdminCreateDTO, admin_service: AdminServiceType):
    return admin_service.add_one_admin(admin)

@app.delete("/admins/{login}", response_model=AdminDTO)
def delete_admin(login: str, admin_service: AdminServiceType):
    try:
        return admin_service.delete_admin(login)
    except Exception:
        raise HTTPException(status_code=404, detail="Администратор не найден")

# ДЛЯ КАТЕГОРИЙ
@app.get("/categories", response_model=list[CategoryDTO])
def get_categories(category_service: CategoryServiceType):
    return category_service.get_all_categories()

@app.get("/categories/{category_id}", response_model=CategoryDTO)
def get_category(category_id: int, category_service: CategoryServiceType):
    try:
        return category_service.get_one_category(category_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Категория не найдена")

@app.post("/categories", response_model=CategoryDTO)
def create_category(category: CategoryCreateDTO, category_service: CategoryServiceType):
    return category_service.add_one_category(category)

@app.put("/categories/{category_id}", response_model=CategoryDTO)
def update_category(category_id: int, category: CategoryBaseDTO, category_service: CategoryServiceType):
    try:
        return category_service.update_category(category_id, category)
    except Exception:
        raise HTTPException(status_code=404, detail="Категория не найдена")

@app.delete("/categories/{category_id}", response_model=CategoryDTO)
def delete_category(category_id: int, category_service: CategoryServiceType):
    try:
        return category_service.delete_category(category_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Категория не найдена")

#  ДЛЯ ТОВАРОВ 
@app.get("/products", response_model=list[ProductDTO])
def get_products(product_service: ProductServiceType):
    return product_service.get_all_products()

@app.get("/products/{product_id}", response_model=ProductDTO)
def get_product(product_id: int, product_service: ProductServiceType):
    try:
        return product_service.get_one_product(product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

@app.post("/products", response_model=ProductDTO)
def create_product(product: ProductCreateDTO, product_service: ProductServiceType):
    return product_service.add_one_product(product)

@app.put("/products/{product_id}", response_model=ProductDTO)
def update_product(product_id: int, product: ProductBaseDTO, product_service: ProductServiceType):
    try:
        return product_service.update_product(product_id, product)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

@app.delete("/products/{product_id}", response_model=ProductDTO)
def delete_product(product_id: int, product_service: ProductServiceType):
    try:
        return product_service.delete_product(product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")

#  ДЛЯ ОТСТОЙНИКОВ
@app.get("/overflow-bins", response_model=list[OverflowBinDTO])
def get_overflow_bins(overflow_bin_service: OverflowBinServiceType):
    return overflow_bin_service.get_all_overflow_bins()

@app.get("/overflow-bins/{bin_id}", response_model=OverflowBinDTO)
def get_overflow_bin(bin_id: int, overflow_bin_service: OverflowBinServiceType):
    try:
        return overflow_bin_service.get_one_overflow_bin(bin_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Отстойник не найден")

@app.post("/overflow-bins", response_model=OverflowBinDTO)
def create_overflow_bin(overflow_bin: OverflowBinCreateDTO, overflow_bin_service: OverflowBinServiceType):
    return overflow_bin_service.add_one_overflow_bin(overflow_bin)

@app.put("/overflow-bins/{bin_id}", response_model=OverflowBinDTO)
def update_overflow_bin(bin_id: int, overflow_bin: OverflowBinBaseDTO, overflow_bin_service: OverflowBinServiceType):
    try:
        return overflow_bin_service.update_overflow_bin(bin_id, overflow_bin)
    except Exception:
        raise HTTPException(status_code=404, detail="Отстойник не найден")

@app.delete("/overflow-bins/{bin_id}", response_model=OverflowBinDTO)
def delete_overflow_bin(bin_id: int, overflow_bin_service: OverflowBinServiceType):
    try:
        return overflow_bin_service.delete_overflow_bin(bin_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Отстойник не найден")

# ДЛЯ ЗАКАЗОВ НА ПОКУПКУ 
@app.get("/purchase-orders", response_model=list[PurchaseOrderDTO])
def get_purchase_orders(purchase_order_service: PurchaseOrderServiceType):
    return purchase_order_service.get_all_purchase_orders()

@app.get("/purchase-orders/{order_id}", response_model=PurchaseOrderDTO)
def get_purchase_order(order_id: int, purchase_order_service: PurchaseOrderServiceType):
    try:
        return purchase_order_service.get_one_purchase_order(order_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Заказ на покупку не найден")

@app.post("/purchase-orders", response_model=PurchaseOrderDTO)
def create_purchase_order(purchase_order: PurchaseOrderCreateDTO, purchase_order_service: PurchaseOrderServiceType):
    return purchase_order_service.add_one_purchase_order(purchase_order)

@app.put("/purchase-orders/{order_id}", response_model=PurchaseOrderDTO)
def update_purchase_order(order_id: int, purchase_order: PurchaseOrderBaseDTO, purchase_order_service: PurchaseOrderServiceType):
    try:
        return purchase_order_service.update_purchase_order(order_id, purchase_order)
    except Exception:
        raise HTTPException(status_code=404, detail="Заказ на покупку не найден")

@app.delete("/purchase-orders/{order_id}", response_model=PurchaseOrderDTO)
def delete_purchase_order(order_id: int, purchase_order_service: PurchaseOrderServiceType):
    try:
        return purchase_order_service.delete_purchase_order(order_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Заказ на покупку не найден")

# ДЛЯ СТЕЛЛАЖЕЙ 
@app.get("/shelves", response_model=list[ShelfDTO])
def get_shelves(shelf_service: ShelfServiceType):
    return shelf_service.get_all_shelves()

@app.get("/shelves/{shelf_id}", response_model=ShelfDTO)
def get_shelf(shelf_id: int, shelf_service: ShelfServiceType):
    try:
        return shelf_service.get_one_shelf(shelf_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

@app.post("/shelves", response_model=ShelfDTO)
def create_shelf(shelf: ShelfCreateDTO, shelf_service: ShelfServiceType):
    return shelf_service.add_one_shelf(shelf)

@app.put("/shelves/{shelf_id}", response_model=ShelfDTO)
def update_shelf(shelf_id: int, shelf: ShelfBaseDTO, shelf_service: ShelfServiceType):
    try:
        return shelf_service.update_shelf(shelf_id, shelf)
    except Exception:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

@app.delete("/shelves/{shelf_id}", response_model=ShelfDTO)
def delete_shelf(shelf_id: int, shelf_service: ShelfServiceType):
    try:
        return shelf_service.delete_shelf(shelf_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

# ДЛЯ ИСТОРИИ ПЕРЕМЕЩЕНИЙ
@app.get("/movement-history", response_model=list[MovementHistoryDTO])
def get_movement_history(movement_history_service: MovementHistoryServiceType):
    return movement_history_service.get_all_movement_history()

@app.get("/movement-history/{history_id}", response_model=MovementHistoryDTO)
def get_movement_history_record(history_id: int, movement_history_service: MovementHistoryServiceType):
    try:
        return movement_history_service.get_one_movement_history(history_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Запись истории перемещений не найдена")

@app.post("/movement-history", response_model=MovementHistoryDTO)
def create_movement_history(movement_history: MovementHistoryCreateDTO, movement_history_service: MovementHistoryServiceType):
    return movement_history_service.add_one_movement_history(movement_history)

# ДЛЯ УВЕДОМЛЕНИЙ
@app.get("/notifications", response_model=list[NotificationDTO])
def get_notifications(notification_service: NotificationServiceType):
    return notification_service.get_all_notifications()

@app.get("/notifications/{notification_id}", response_model=NotificationDTO)
def get_notification(notification_id: int, notification_service: NotificationServiceType):
    try:
        return notification_service.get_one_notification(notification_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

@app.post("/notifications", response_model=NotificationDTO)
def create_notification(notification: NotificationCreateDTO, notification_service: NotificationServiceType):
    return notification_service.add_one_notification(notification)

@app.put("/notifications/{notification_id}", response_model=NotificationDTO)
def update_notification(notification_id: int, notification: NotificationBaseDTO, notification_service: NotificationServiceType):
    try:
        return notification_service.update_notification(notification_id, notification)
    except Exception:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

@app.delete("/notifications/{notification_id}", response_model=NotificationDTO)
def delete_notification(notification_id: int, notification_service: NotificationServiceType):
    try:
        return notification_service.delete_notification(notification_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

# ДЛЯ РАЗМЕЩЕНИЯ ТОВАРОВ 
@app.get("/product-placements", response_model=list[ProductPlacementDTO])
def get_product_placements(product_placement_service: ProductPlacementServiceType):
    return product_placement_service.get_all_product_placements()

@app.get("/product-placements/{placement_id}", response_model=ProductPlacementDTO)
def get_product_placement(placement_id: int, product_placement_service: ProductPlacementServiceType):
    try:
        return product_placement_service.get_one_product_placement(placement_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Размещение товара не найдено")

@app.post("/product-placements", response_model=ProductPlacementDTO)
def create_product_placement(product_placement: ProductPlacementCreateDTO, product_placement_service: ProductPlacementServiceType):
    return product_placement_service.add_one_product_placement(product_placement)

@app.put("/product-placements/{placement_id}", response_model=ProductPlacementDTO)
def update_product_placement(placement_id: int, product_placement: ProductPlacementBaseDTO, product_placement_service: ProductPlacementServiceType):
    try:
        return product_placement_service.update_product_placement(placement_id, product_placement)
    except Exception:
        raise HTTPException(status_code=404, detail="Размещение товара не найдено")

@app.delete("/product-placements/{placement_id}", response_model=ProductPlacementDTO)
def delete_product_placement(placement_id: int, product_placement_service: ProductPlacementServiceType):
    try:
        return product_placement_service.delete_product_placement(placement_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Размещение товара не найдено")

# ДЛЯ ПОСТАВОК 
@app.get("/supplies", response_model=list[SupplyDTO])
def get_supplies(supply_service: SupplyServiceType):
    return supply_service.get_all_supplies()

@app.get("/supplies/{supply_id}", response_model=SupplyDTO)
def get_supply(supply_id: int, supply_service: SupplyServiceType):
    try:
        return supply_service.get_one_supply(supply_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Поставка не найдена")

@app.post("/supplies", response_model=SupplyDTO)
def create_supply(supply: SupplyCreateDTO, supply_service: SupplyServiceType):
    return supply_service.add_one_supply(supply)

@app.put("/supplies/{supply_id}", response_model=SupplyDTO)
def update_supply(supply_id: int, supply: SupplyBaseDTO, supply_service: SupplyServiceType):
    try:
        return supply_service.update_supply(supply_id, supply)
    except Exception:
        raise HTTPException(status_code=404, detail="Поставка не найдена")

@app.delete("/supplies/{supply_id}", response_model=SupplyDTO)
def delete_supply(supply_id: int, supply_service: SupplyServiceType):
    try:
        return supply_service.delete_supply(supply_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Поставка не найдена")

# ЗАПРОСЫ 
@app.get("/products/low-stock", response_model=list[ProductDTO])
def get_low_stock_products(product_service: ProductServiceType):
    """Товары с низким запасом (текущее количество <= минимальное)"""
    return product_service.get_low_stock_products()

@app.get("/movements/recent")
def get_recent_movements(
    movement_service: MovementHistoryServiceType,
    days: int = 7 
):
    """Последние перемещения за указанное количество дней (по умолчанию 7)"""
    return movement_service.get_recent_movements(days)
@app.get('/')
def root():
    return RedirectResponse('/docs')

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)