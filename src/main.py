from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import APIRouter, FastAPI, HTTPException, Depends, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
import uvicorn
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel
import json
from fastapi import HTTPException, Path, Query

DATABASE_URL = 'sqlite:///mydb.db'

class Database:
    def __init__(self) -> None:
        self.engine: Engine = create_engine(
            url=DATABASE_URL,
            echo=True
        )

        self.session_factory: sessionmaker = (
            sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False
        ))

    @property
    def session(self) -> Session:
        return self.session_factory()

db = Database()

app = FastAPI(title="Продуктовый склад API", version="1.0.0")

# ВАЖНО: ИСПРАВЛЕННЫЕ CORS НАСТРОЙКИ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Модели данных для API
class ProductBase(BaseModel):
    name: str
    category_id: int
    min_quantity: int = 0
    unit: str = "шт"
    description: Optional[str] = None
    price: Optional[float] = None
    current_quantity: int = 0

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    category_name: Optional[str] = None

class PurchaseOrderBase(BaseModel):
    product_id: int
    quantity: int
    supplier: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    order_date: datetime
    status: str = "pending"
    created_date: datetime

class SupplyBase(BaseModel):
    purchase_order_id: Optional[int] = None
    product_id: int
    quantity: int
    supplier: str  
    delivery_date: Optional[date] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    status: str = "delivered"

class SupplyCreate(SupplyBase):
    pass

class SupplyResponse(SupplyBase):
    id: int
    supply_date: datetime
    status: str = "delivered"
    product_name: Optional[str] = None
    purchase_order_status: Optional[str] = None

class StockUpdate(BaseModel):
    product_id: int
    quantity_change: int
    reason: str = "supply"
    notes: Optional[str] = None

# Модели для размещения товаров
class ProductPlacementBase(BaseModel):
    product_id: int
    shelf_id: Optional[int] = None
    overflow_id: Optional[int] = None
    quantity: int
    placement_date: Optional[datetime] = None
    notes: Optional[str] = None

class ProductPlacementCreate(ProductPlacementBase):
    pass

class ProductPlacementResponse(ProductPlacementBase):
    id: int
    placement_date: datetime
    product_name: Optional[str] = None
    shelf_name: Optional[str] = None

# Модели для стеллажей
class ShelfBase(BaseModel):
    name: str
    max_capacity: int
    current_quantity: int = 0
    location: Optional[str] = None
    description: Optional[str] = None

class ShelfCreate(ShelfBase):
    pass

class ShelfResponse(ShelfBase):
    id: int
    free_space: Optional[int] = None

# Модели для отстойника
class OverflowBinBase(BaseModel):
    name: str
    max_capacity: int = 1000
    current_quantity: int = 0
    location: Optional[str] = None

class OverflowBinCreate(OverflowBinBase):
    pass

class OverflowBinResponse(OverflowBinBase):
    id: int
    free_space: Optional[int] = None

# Модель для товаров в отстойнике (согласно вашей модели OverflowBinORM)
class OverflowItemBase(BaseModel):
    product_id: int
    quantity: int
    notes: Optional[str] = None

class OverflowItemCreate(OverflowItemBase):
    pass

class OverflowItemResponse(OverflowItemBase):
    id: int
    date_added: datetime
    product_name: Optional[str] = None

# Специальный обработчик для OPTIONS запросов
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.options("/{rest_of_path:path}")
async def options_handler():
    return JSONResponse(
        content={"status": "ok"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Тестовый эндпоинт
@app.get("/")
def root():
    return RedirectResponse("/docs")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Продуктовый склад API", "timestamp": datetime.now().isoformat()}

# ===== ТОВАРЫ =====
products_router = APIRouter(prefix="/products", tags=["Товары"])

# Тестовые данные продуктовых товаров
PRODUCTS_DATA = [
    {
        "id": 1,
        "name": "Молоко 3.2% 1л",
        "category_id": 1,
        "category_name": "Молочные продукты",
        "current_quantity": 150,
        "min_quantity": 50,
        "unit": "шт",
        "price": 85.50,
        "description": "Пастеризованное молоко"
    },
    {
        "id": 2,
        "name": "Хлеб Бородинский",
        "category_id": 2,
        "category_name": "Хлебобулочные изделия",
        "current_quantity": 80,
        "min_quantity": 30,
        "unit": "шт",
        "price": 65.00,
        "description": "Ржаной хлеб"
    },
    {
        "id": 3,
        "name": "Яйца куриные С0",
        "category_id": 3,
        "category_name": "Яйца",
        "current_quantity": 200,
        "min_quantity": 100,
        "unit": "упак",
        "price": 120.00,
        "description": "10 штук в упаковке"
    },
    {
        "id": 4,
        "name": "Картофель",
        "category_id": 4,
        "category_name": "Овощи",
        "current_quantity": 500,
        "min_quantity": 200,
        "unit": "кг",
        "price": 45.00,
        "description": "Свежий картофель"
    },
    {
        "id": 5,
        "name": "Яблоки Голден",
        "category_id": 5,
        "category_name": "Фрукты",
        "current_quantity": 300,
        "min_quantity": 100,
        "unit": "кг",
        "price": 110.00,
        "description": "Сладкие яблоки"
    },
    {
        "id": 6,
        "name": "Сахар 1кг",
        "category_id": 6,
        "category_name": "Бакалея",
        "current_quantity": 120,
        "min_quantity": 40,
        "unit": "шт",
        "price": 75.00,
        "description": "Сахарный песок"
    },
    {
        "id": 7,
        "name": "Масло подсолнечное",
        "category_id": 6,
        "category_name": "Бакалея",
        "current_quantity": 90,
        "min_quantity": 30,
        "unit": "шт",
        "price": 140.00,
        "description": "Рафинированное масло 1л"
    },
    {
        "id": 8,
        "name": "Курица охлажденная",
        "category_id": 7,
        "category_name": "Мясо и птица",
        "current_quantity": 70,
        "min_quantity": 25,
        "unit": "кг",
        "price": 250.00,
        "description": "Куриные тушки"
    }
]

@products_router.get("", response_model=List[ProductResponse])
def get_products(
    category_id: Optional[int] = Query(None, description="Фильтр по категории"),
    low_stock: Optional[bool] = Query(None, description="Только товары с низким запасом")
):
    filtered_products = PRODUCTS_DATA.copy()
    
    if category_id:
        filtered_products = [p for p in filtered_products if p["category_id"] == category_id]
    
    if low_stock:
        filtered_products = [p for p in filtered_products if p["current_quantity"] <= p["min_quantity"]]
    
    return filtered_products

@products_router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    product = next((p for p in PRODUCTS_DATA if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product

@products_router.post("", response_model=ProductResponse)
def create_product(product: ProductCreate):
    new_id = max(p["id"] for p in PRODUCTS_DATA) + 1
    new_product = {
        "id": new_id,
        **product.dict(),
        "category_name": "Новая категория"  # В реальности получаем из БД
    }
    PRODUCTS_DATA.append(new_product)
    return new_product

@products_router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_update: ProductCreate):
    product = next((p for p in PRODUCTS_DATA if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    for key, value in product_update.dict().items():
        if value is not None:
            product[key] = value
    
    return product

@products_router.delete("/{product_id}", response_model=dict)
def delete_product(product_id: int):
    global PRODUCTS_DATA
    product = next((p for p in PRODUCTS_DATA if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    PRODUCTS_DATA = [p for p in PRODUCTS_DATA if p["id"] != product_id]
    
    return {
        "message": "Товар удален",
        "deleted_id": product_id,
        "product_name": product["name"]
    }

# ===== СТЕЛЛАЖИ =====
shelves_router = APIRouter(prefix="/shelves", tags=["Стеллажи"])

# Тестовые данные стеллажей
SHELVES_DATA = [
    {
        "id": 1,
        "name": "Стеллаж А1",
        "max_capacity": 200,
        "current_quantity": 150,
        "location": "Зона А, Ряд 1",
        "description": "Для молочных продуктов",
        "free_space": 50
    },
    {
        "id": 2,
        "name": "Стеллаж А2",
        "max_capacity": 150,
        "current_quantity": 80,
        "location": "Зона А, Ряд 2",
        "description": "Для хлебобулочных изделий",
        "free_space": 70
    },
    {
        "id": 3,
        "name": "Стеллаж Б1",
        "max_capacity": 300,
        "current_quantity": 200,
        "location": "Зона Б, Ряд 1",
        "description": "Для овощей и фруктов",
        "free_space": 100
    },
    {
        "id": 4,
        "name": "Стеллаж Б2",
        "max_capacity": 250,
        "current_quantity": 120,
        "location": "Зона Б, Ряд 2",
        "description": "Для бакалеи",
        "free_space": 130
    },
    {
        "id": 5,
        "name": "Стеллаж В1",
        "max_capacity": 100,
        "current_quantity": 70,
        "location": "Зона В, Ряд 1",
        "description": "Для мяса и птицы",
        "free_space": 30
    }
]

@shelves_router.get("", response_model=List[ShelfResponse])
def get_shelves():
    return SHELVES_DATA

@shelves_router.get("/{shelf_id}", response_model=ShelfResponse)
def get_shelf(shelf_id: int):
    shelf = next((s for s in SHELVES_DATA if s["id"] == shelf_id), None)
    if not shelf:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")
    return shelf

@shelves_router.post("", response_model=ShelfResponse)
def create_shelf(shelf: ShelfCreate):
    new_id = max(s["id"] for s in SHELVES_DATA) + 1 if SHELVES_DATA else 1
    new_shelf = {
        "id": new_id,
        **shelf.dict(),
        "free_space": shelf.max_capacity - shelf.current_quantity
    }
    SHELVES_DATA.append(new_shelf)
    return new_shelf

@shelves_router.put("/{shelf_id}", response_model=ShelfResponse)
def update_shelf(shelf_id: int, shelf_update: ShelfCreate):
    shelf = next((s for s in SHELVES_DATA if s["id"] == shelf_id), None)
    if not shelf:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")
    
    for key, value in shelf_update.dict().items():
        if value is not None:
            shelf[key] = value
    
    # Обновляем свободное место
    shelf["free_space"] = shelf["max_capacity"] - shelf["current_quantity"]
    
    return shelf

@shelves_router.delete("/{shelf_id}", response_model=dict)
def delete_shelf(shelf_id: int):
    global SHELVES_DATA
    shelf = next((s for s in SHELVES_DATA if s["id"] == shelf_id), None)
    if not shelf:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")
    
    SHELVES_DATA = [s for s in SHELVES_DATA if s["id"] != shelf_id]
    
    return {
        "message": "Стеллаж удален",
        "deleted_id": shelf_id,
        "shelf_name": shelf["name"]
    }

# ===== РАЗМЕЩЕНИЕ ТОВАРОВ =====
product_placements_router = APIRouter(prefix="/product-placements", tags=["Размещение товаров"])

# Тестовые данные размещения товаров
PRODUCT_PLACEMENTS_DATA = [
    {
        "id": 1,
        "product_id": 1,
        "product_name": "Молоко 3.2% 1л",
        "shelf_id": 1,
        "shelf_name": "Стеллаж А1",
        "overflow_id": None,
        "quantity": 100,
        "placement_date": "2024-01-12T11:30:00",
        "notes": "Основное размещение"
    },
    {
        "id": 2,
        "product_id": 2,
        "product_name": "Хлеб Бородинский",
        "shelf_id": 2,
        "shelf_name": "Стеллаж А2",
        "overflow_id": None,
        "quantity": 50,
        "placement_date": "2024-01-13T08:45:00",
        "notes": "Ежедневная поставка"
    },
    {
        "id": 3,
        "product_id": 3,
        "product_name": "Яйца куриные С0",
        "shelf_id": 4,
        "shelf_name": "Стеллаж Б2",
        "overflow_id": None,
        "quantity": 150,
        "placement_date": "2024-01-14T10:15:00",
        "notes": "Новая поставка"
    },
    {
        "id": 4,
        "product_id": 6,
        "product_name": "Сахар 1кг",
        "shelf_id": None,
        "shelf_name": None,
        "overflow_id": 1,
        "quantity": 20,
        "placement_date": "2024-01-15T14:20:00",
        "notes": "Временное хранение в отстойнике"
    }
]

@product_placements_router.get("", response_model=List[ProductPlacementResponse])
def get_product_placements(
    product_id: Optional[int] = Query(None, description="Фильтр по товару"),
    shelf_id: Optional[int] = Query(None, description="Фильтр по стеллажу"),
    overflow_id: Optional[int] = Query(None, description="Фильтр по отстойнику")
):
    filtered_placements = PRODUCT_PLACEMENTS_DATA.copy()
    
    if product_id:
        filtered_placements = [p for p in filtered_placements if p["product_id"] == product_id]
    
    if shelf_id:
        filtered_placements = [p for p in filtered_placements if p["shelf_id"] == shelf_id]
    
    if overflow_id:
        filtered_placements = [p for p in filtered_placements if p["overflow_id"] == overflow_id]
    
    return filtered_placements

@product_placements_router.get("/{placement_id}", response_model=ProductPlacementResponse)
def get_product_placement(placement_id: int):
    placement = next((p for p in PRODUCT_PLACEMENTS_DATA if p["id"] == placement_id), None)
    if not placement:
        raise HTTPException(status_code=404, detail="Размещение не найдено")
    return placement

@product_placements_router.post("", response_model=ProductPlacementResponse)
def create_product_placement(placement: ProductPlacementCreate):
    # Проверяем существование товара
    product = next((p for p in PRODUCTS_DATA if p["id"] == placement.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Проверяем доступное количество товара
    if placement.quantity > product["current_quantity"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Недостаточно товара. Доступно: {product['current_quantity']}, запрошено: {placement.quantity}"
        )
    
    # Если размещение на стеллаж, проверяем свободное место
    if placement.shelf_id:
        shelf = next((s for s in SHELVES_DATA if s["id"] == placement.shelf_id), None)
        if not shelf:
            raise HTTPException(status_code=404, detail="Стеллаж не найден")
        
        if placement.quantity > shelf["free_space"]:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно места на стеллаже. Свободно: {shelf['free_space']}, требуется: {placement.quantity}"
            )
        
        # Обновляем занятое место на стеллаже
        shelf["current_quantity"] += placement.quantity
        shelf["free_space"] = shelf["max_capacity"] - shelf["current_quantity"]
        shelf_name = shelf["name"]
    else:
        shelf_name = None
    
    # Если размещение в отстойник (пока используем тестовый отстойник)
    if placement.overflow_id:
        shelf_name = None
    
    new_id = max(p["id"] for p in PRODUCT_PLACEMENTS_DATA) + 1 if PRODUCT_PLACEMENTS_DATA else 1
    new_placement = {
        "id": new_id,
        **placement.dict(),
        "product_name": product["name"],
        "shelf_name": shelf_name,
        "placement_date": datetime.now()
    }
    PRODUCT_PLACEMENTS_DATA.append(new_placement)
    
    # Уменьшаем количество товара на складе
    product["current_quantity"] -= placement.quantity
    
    return new_placement

@product_placements_router.put("/{placement_id}", response_model=ProductPlacementResponse)
def update_product_placement(placement_id: int, placement_update: ProductPlacementCreate):
    placement = next((p for p in PRODUCT_PLACEMENTS_DATA if p["id"] == placement_id), None)
    if not placement:
        raise HTTPException(status_code=404, detail="Размещение не найдено")
    
    # Сохраняем старое количество для корректировки
    old_quantity = placement["quantity"]
    
    # Обновляем данные размещения
    for key, value in placement_update.dict().items():
        if value is not None:
            placement[key] = value
    
    # Обновляем количество товара на складе
    product = next((p for p in PRODUCTS_DATA if p["id"] == placement["product_id"]), None)
    if product:
        quantity_difference = old_quantity - placement_update.quantity
        product["current_quantity"] += quantity_difference
    
    return placement

@product_placements_router.delete("/{placement_id}", response_model=dict)
def delete_product_placement(placement_id: int):
    global PRODUCT_PLACEMENTS_DATA
    placement = next((p for p in PRODUCT_PLACEMENTS_DATA if p["id"] == placement_id), None)
    if not placement:
        raise HTTPException(status_code=404, detail="Размещение не найдено")
    
    # Возвращаем товар на склад
    product = next((p for p in PRODUCTS_DATA if p["id"] == placement["product_id"]), None)
    if product:
        product["current_quantity"] += placement["quantity"]
    
    # Освобождаем место на стеллаже
    if placement["shelf_id"]:
        shelf = next((s for s in SHELVES_DATA if s["id"] == placement["shelf_id"]), None)
        if shelf:
            shelf["current_quantity"] = max(0, shelf["current_quantity"] - placement["quantity"])
            shelf["free_space"] = shelf["max_capacity"] - shelf["current_quantity"]
    
    PRODUCT_PLACEMENTS_DATA = [p for p in PRODUCT_PLACEMENTS_DATA if p["id"] != placement_id]
    
    return {
        "message": "Размещение удалено",
        "deleted_id": placement_id,
        "product_id": placement["product_id"],
        "quantity_returned": placement["quantity"]
    }

# ===== ОТСТОЙНИКИ (товары в отстойнике) =====
overflow_bins_router = APIRouter(prefix="/overflow-bins", tags=["Отстойники"])

# Тестовые данные товаров в отстойнике (согласно модели OverflowBinORM)
OVERFLOW_ITEMS_DATA = [
    {
        "id": 1,
        "product_id": 6,
        "product_name": "Сахар 1кг",
        "quantity": 20,
        "date_added": "2024-01-15T14:20:00",
        "notes": "Временное хранение"
    },
    {
        "id": 2,
        "product_id": 7,
        "product_name": "Масло подсолнечное",
        "quantity": 15,
        "date_added": "2024-01-16T10:30:00",
        "notes": "Ждет размещения"
    },
    {
        "id": 3,
        "product_id": 5,
        "product_name": "Яблоки Голден",
        "quantity": 50,
        "date_added": "2024-01-17T09:15:00",
        "notes": "Сезонное переполнение"
    }
]

@overflow_bins_router.get("", response_model=List[dict])
def get_overflow_items():
    """Получить все товары в отстойнике"""
    return OVERFLOW_ITEMS_DATA

@overflow_bins_router.get("/{item_id}", response_model=dict)
def get_overflow_item(item_id: int):
    """Получить товар в отстойнике по ID"""
    item = next((b for b in OVERFLOW_ITEMS_DATA if b["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Товар в отстойнике не найден")
    return item

@overflow_bins_router.post("", response_model=dict)
def add_to_overflow(item: dict):
    """Добавить товар в отстойник"""
    # Проверяем существование товара
    product = next((p for p in PRODUCTS_DATA if p["id"] == item.get("product_id")), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Проверяем доступное количество
    if item.get("quantity", 0) > product["current_quantity"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Недостаточно товара. Доступно: {product['current_quantity']}, запрошено: {item.get('quantity', 0)}"
        )
    
    new_id = max(b["id"] for b in OVERFLOW_ITEMS_DATA) + 1 if OVERFLOW_ITEMS_DATA else 1
    new_item = {
        "id": new_id,
        "product_id": item["product_id"],
        "product_name": product["name"],
        "quantity": item["quantity"],
        "date_added": datetime.now().isoformat(),
        "notes": item.get("notes", "")
    }
    OVERFLOW_ITEMS_DATA.append(new_item)
    
    # Уменьшаем количество товара на складе
    product["current_quantity"] -= item["quantity"]
    
    return new_item

@overflow_bins_router.put("/{item_id}", response_model=dict)
def update_overflow_item(item_id: int, item_update: dict):
    """Обновить товар в отстойнике"""
    item = next((b for b in OVERFLOW_ITEMS_DATA if b["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Товар в отстойнике не найден")
    
    # Если меняем количество, корректируем остатки
    if "quantity" in item_update and item_update["quantity"] != item["quantity"]:
        product = next((p for p in PRODUCTS_DATA if p["id"] == item["product_id"]), None)
        if product:
            difference = item_update["quantity"] - item["quantity"]
            product["current_quantity"] -= difference
    
    # Обновляем данные
    for key, value in item_update.items():
        if value is not None:
            item[key] = value
    
    return item

@overflow_bins_router.delete("/{item_id}", response_model=dict)
def delete_overflow_item(item_id: int):
    """Удалить товар из отстойника"""
    global OVERFLOW_ITEMS_DATA 
    
    item = next((b for b in OVERFLOW_ITEMS_DATA if b["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Товар в отстойнике не найден")
    
    # Возвращаем товар на склад
    product = next((p for p in PRODUCTS_DATA if p["id"] == item["product_id"]), None)
    if product:
        product["current_quantity"] += item["quantity"]
    
    OVERFLOW_ITEMS_DATA = [b for b in OVERFLOW_ITEMS_DATA if b["id"] != item_id]
    
    return {
        "message": "Товар удален из отстойника",
        "deleted_id": item_id,
        "product_id": item["product_id"],
        "product_name": item["product_name"],
        "quantity_returned": item["quantity"]
    }

@overflow_bins_router.post("/{item_id}/move-to-shelf")
def move_from_overflow_to_shelf(
    
    item_id: int,
    shelf_id: int,
    quantity: Optional[int] = None,
    notes: Optional[str] = None
):
    global OVERFLOW_ITEMS_DATA
    """Переместить товар из отстойника на стеллаж"""
    item = next((b for b in OVERFLOW_ITEMS_DATA if b["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Товар в отстойнике не найден")
    
    shelf = next((s for s in SHELVES_DATA if s["id"] == shelf_id), None)
    if not shelf:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")
    
    # Определяем количество для перемещения
    move_quantity = quantity if quantity is not None else item["quantity"]
    
    if move_quantity > item["quantity"]:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно товара в отстойнике. Доступно: {item['quantity']}, запрошено: {move_quantity}"
        )
    
    # Проверяем место на стеллаже
    if move_quantity > shelf["free_space"]:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно места на стеллаже '{shelf['name']}'. Свободно: {shelf['free_space']}, требуется: {move_quantity}"
        )
    
    # Обновляем стеллаж
    shelf["current_quantity"] += move_quantity
    shelf["free_space"] = shelf["max_capacity"] - shelf["current_quantity"]
    
    # Обновляем отстойник
    if move_quantity == item["quantity"]:
        # Если весь товар перемещен, удаляем запись
        OVERFLOW_ITEMS_DATA = [b for b in OVERFLOW_ITEMS_DATA if b["id"] != item_id]
        overflow_removed = True
    else:
        # Если часть товара, уменьшаем количество
        item["quantity"] -= move_quantity
        overflow_removed = False
    
    # Создаем размещение
    new_placement_id = max(p["id"] for p in PRODUCT_PLACEMENTS_DATA) + 1 if PRODUCT_PLACEMENTS_DATA else 1
    placement = {
        "id": new_placement_id,
        "product_id": item["product_id"],
        "product_name": item["product_name"],
        "shelf_id": shelf_id,
        "shelf_name": shelf["name"],
        "overflow_id": None,
        "quantity": move_quantity,
        "placement_date": datetime.now().isoformat(),
        "notes": notes or f"Перемещено из отстойника (ID: {item_id})"
    }
    PRODUCT_PLACEMENTS_DATA.append(placement)
    
    return {
        "success": True,
        "message": f"Товар '{item['product_name']}' перемещен из отстойника на стеллаж '{shelf['name']}'",
        "quantity_moved": move_quantity,
        "overflow_removed": overflow_removed,
        "overflow_remaining": 0 if overflow_removed else item.get("quantity", 0),
        "placement": placement
    }

@overflow_bins_router.delete("/{item_id}/return-to-stock")
def return_overflow_to_stock(item_id: int):
    global OVERFLOW_ITEMS_DATA
    """Вернуть товар из отстойника на склад"""
    item = next((b for b in OVERFLOW_ITEMS_DATA if b["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Товар в отстойнике не найден")
    
    # Возвращаем товар на склад
    product = next((p for p in PRODUCTS_DATA if p["id"] == item["product_id"]), None)
    if product:
        product["current_quantity"] += item["quantity"]
    
    # Удаляем из отстойника
    OVERFLOW_ITEMS_DATA = [b for b in OVERFLOW_ITEMS_DATA if b["id"] != item_id]
    
    return {
        "success": True,
        "message": f"Товар '{item['product_name']}' возвращен на склад",
        "quantity_returned": item["quantity"],
        "product": {
            "id": product["id"],
            "name": product["name"],
            "new_quantity": product["current_quantity"]
        }
    }

@overflow_bins_router.get("/product/{product_id}")
def get_product_overflow(product_id: int):
    """Получить информацию о товаре в отстойнике по ID товара"""
    items = [b for b in OVERFLOW_ITEMS_DATA if b["product_id"] == product_id]
    if not items:
        return {"found": False, "message": "Товар не найден в отстойнике"}
    
    return {
        "found": True,
        "items": items,
        "total_quantity": sum(item["quantity"] for item in items)
    }

@overflow_bins_router.get("/with-details/")
def get_overflow_with_details():
    """Получить все товары в отстойнике с деталями"""
    result = []
    for item in OVERFLOW_ITEMS_DATA:
        product = next((p for p in PRODUCTS_DATA if p["id"] == item["product_id"]), None)
        if product:
            result.append({
                **item,
                "category_id": product["category_id"],
                "category_name": product["category_name"],
                "unit": product["unit"],
                "price": product["price"],
                "description": product["description"],
                "product_current_quantity": product["current_quantity"],
                "product_min_quantity": product["min_quantity"]
            })
    
    return result

# ===== ЗАКАЗЫ НА ЗАКУПКУ =====
purchase_orders_router = APIRouter(prefix="/purchase-orders", tags=["Заказы на закупку"])

# Тестовые данные заказов
PURCHASE_ORDERS_DATA = [
    {
        "id": 1,
        "product_id": 1,
        "product_name": "Молоко 3.2% 1л",
        "quantity": 100,
        "supplier": "Молочный комбинат",
        "order_date": "2024-01-10T09:00:00",
        "expected_delivery_date": "2024-01-12",
        "status": "delivered",
        "notes": "Срочный заказ",
        "created_date": "2024-01-10T09:00:00"
    },
    {
        "id": 2,
        "product_id": 2,
        "product_name": "Хлеб Бородинский",
        "quantity": 50,
        "supplier": "Хлебозавод №1",
        "order_date": "2024-01-11T10:30:00",
        "expected_delivery_date": "2024-01-13",
        "status": "in_progress",
        "notes": "Ежедневная поставка",
        "created_date": "2024-01-11T10:30:00"
    },
    {
        "id": 3,
        "product_id": 3,
        "product_name": "Яйца куриные С0",
        "quantity": 150,
        "supplier": "Птицефабрика",
        "order_date": "2024-01-12T14:15:00",
        "expected_delivery_date": "2024-01-15",
        "status": "pending",
        "notes": None,
        "created_date": "2024-01-12T14:15:00"
    }
]
@purchase_orders_router.patch("/{order_id}", response_model=PurchaseOrderResponse)
def partial_update_purchase_order(
    order_id: int,
    order_update: PurchaseOrderBase
):
    """Частичное обновление заказа"""
    order = next((o for o in PURCHASE_ORDERS_DATA if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    
    # Обновляем только переданные поля
    update_data = order_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            order[key] = value
    
    # Если обновлен product_id, обновляем имя товара
    if 'product_id' in update_data:
        product = next((p for p in PRODUCTS_DATA if p["id"] == order_update.product_id), None)
        if product:
            order["product_name"] = product["name"]
    
    return order

@purchase_orders_router.get("", response_model=List[PurchaseOrderResponse])
def get_purchase_orders(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    product_id: Optional[int] = Query(None, description="Фильтр по товару")
):
    filtered_orders = PURCHASE_ORDERS_DATA.copy()
    
    if status:
        filtered_orders = [o for o in filtered_orders if o["status"] == status]
    
    if product_id:
        filtered_orders = [o for o in filtered_orders if o["product_id"] == product_id]
    
    return filtered_orders

@purchase_orders_router.get("/{order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(order_id: int):
    order = next((o for o in PURCHASE_ORDERS_DATA if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    return order

@purchase_orders_router.post("", response_model=PurchaseOrderResponse)
def create_purchase_order(order: PurchaseOrderCreate):
    # Находим товар
    product = next((p for p in PRODUCTS_DATA if p["id"] == order.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    new_id = max(o["id"] for o in PURCHASE_ORDERS_DATA) + 1
    new_order = {
        "id": new_id,
        **order.dict(),
        "product_name": product["name"],
        "order_date": datetime.now(),
        "created_date": datetime.now(),
        "status": "pending"
    }
    PURCHASE_ORDERS_DATA.append(new_order)
    
    # Создаем уведомление о низком запасе, если нужно
    if product["current_quantity"] <= product["min_quantity"]:
        print(f"⚠️ Создан заказ на товар с низким запасом: {product['name']}")
    
    return new_order

@purchase_orders_router.put("/{order_id}/status", response_model=PurchaseOrderResponse)
def update_order_status(
    order_id: int,
    status: str = Query(..., description="Новый статус заказа")
):
    order = next((o for o in PURCHASE_ORDERS_DATA if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    
    order["status"] = status
    return order

# ===== ПОСТАВКИ =====
supplies_router = APIRouter(prefix="/supplies", tags=["Поставки"])

# Тестовые данные поставок
SUPPLIES_DATA = [
    {
        "id": 1,
        "purchase_order_id": 1,
        "product_id": 1,
        "product_name": "Молоко 3.2% 1л",
        "quantity": 100,
        "supplier": "Молочный комбинат",
        "supply_date": "2024-01-12T11:30:00",
        "delivery_date": "2024-01-12",
        "status": "delivered",
        "invoice_number": "INV-2024-001",
        "notes": "Поставка выполнена вовремя",
        "purchase_order_status": "delivered"
    },
    {
        "id": 2,
        "purchase_order_id": 2,
        "product_id": 2,
        "product_name": "Хлеб Бородинский",
        "quantity": 50,
        "supplier": "Хлебозавод №1",
        "supply_date": "2024-01-13T08:45:00",
        "delivery_date": "2024-01-13",
        "status": "in_transit",
        "invoice_number": "INV-2024-002",
        "notes": "В пути",
        "purchase_order_status": "in_progress"
    }
]

# ===== ЗАКАЗЫ НА ЗАКУПКУ =====

@purchase_orders_router.put("/{order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(order_id: int, order_update: PurchaseOrderBase):
    """Обновление заказа на закупку"""
    order = next((o for o in PURCHASE_ORDERS_DATA if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    
    # Проверяем существование товара
    product = next((p for p in PRODUCTS_DATA if p["id"] == order_update.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Обновляем данные заказа
    for key, value in order_update.dict(exclude_unset=True).items():
        if value is not None:
            order[key] = value
    
    # Обновляем имя товара
    order["product_name"] = product["name"]
    
    return order

# Обновление только статуса
@purchase_orders_router.put("/{order_id}/status", response_model=PurchaseOrderResponse)
def update_order_status(
    order_id: int,
    status: str = Query(..., description="Новый статус заказа")
):
    """Обновление статуса заказа"""
    order = next((o for o in PURCHASE_ORDERS_DATA if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    
    order["status"] = status
    return order

# Удаление заказа
@purchase_orders_router.delete("/{order_id}", response_model=dict)
def delete_purchase_order(order_id: int):
    """Удаление заказа на закупку"""
    global PURCHASE_ORDERS_DATA
    order = next((o for o in PURCHASE_ORDERS_DATA if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    
    PURCHASE_ORDERS_DATA = [o for o in PURCHASE_ORDERS_DATA if o["id"] != order_id]
    
    return {
        "message": "Заказ удален",
        "deleted_id": order_id,
        "product_name": order.get("product_name", "")
    }

@supplies_router.get("", response_model=List[SupplyResponse])
def get_supplies(
    purchase_order_id: Optional[int] = Query(None, description="Фильтр по заказу на закупку"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    start_date: Optional[date] = Query(None, description="Начальная дата"),
    end_date: Optional[date] = Query(None, description="Конечная дата")
):
    filtered_supplies = SUPPLIES_DATA.copy()
    
    if purchase_order_id:
        filtered_supplies = [s for s in filtered_supplies if s.get("purchase_order_id") == purchase_order_id]
    
    if status:
        filtered_supplies = [s for s in filtered_supplies if s["status"] == status]
    
    if start_date:
        filtered_supplies = [s for s in filtered_supplies if datetime.fromisoformat(s["supply_date"].replace("Z", "")).date() >= start_date]
    
    if end_date:
        filtered_supplies = [s for s in filtered_supplies if datetime.fromisoformat(s["supply_date"].replace("Z", "")).date() <= end_date]
    
    return filtered_supplies

@supplies_router.get("/{supply_id}", response_model=SupplyResponse)
def get_supply(supply_id: int):
    supply = next((s for s in SUPPLIES_DATA if s["id"] == supply_id), None)
    if not supply:
        raise HTTPException(status_code=404, detail="Поставка не найдена")
    return supply

@supplies_router.post("", response_model=SupplyResponse)
def create_supply(supply: SupplyCreate):
    # Находим товар
    product = next((p for p in PRODUCTS_DATA if p["id"] == supply.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Если указан purchase_order_id, проверяем заказ
    purchase_order_status = None
    if supply.purchase_order_id:
        order = next((o for o in PURCHASE_ORDERS_DATA if o["id"] == supply.purchase_order_id), None)
        if order:
            purchase_order_status = order["status"]
            # Обновляем статус заказа
            order["status"] = "delivered"
    
    new_id = max(s["id"] for s in SUPPLIES_DATA) + 1 if SUPPLIES_DATA else 1
    new_supply = {
        "id": new_id,
        **supply.dict(),
        "product_name": product["name"],
        "supply_date": datetime.now(),
        "status": "delivered",
        "purchase_order_status": purchase_order_status
    }
    SUPPLIES_DATA.append(new_supply)
    
    # Обновляем количество товара на складе
    product["current_quantity"] += supply.quantity
    
    # Проверяем, был ли низкий запас
    was_low_stock = product["current_quantity"] - supply.quantity <= product["min_quantity"]
    now_adequate = product["current_quantity"] > product["min_quantity"]
    
    if was_low_stock and now_adequate:
        print(f"✅ Запас товара '{product['name']}' восстановлен до нормального уровня")
    
    return new_supply

@supplies_router.put("/{supply_id}", response_model=SupplyResponse)
def update_supply(supply_id: int, supply_update: SupplyBase):
    """Обновление поставки"""
    supply = next((s for s in SUPPLIES_DATA if s["id"] == supply_id), None)
    if not supply:
        raise HTTPException(status_code=404, detail="Поставка не найдена")
    
    # Обновляем данные
    for key, value in supply_update.dict(exclude_unset=True).items():
        if value is not None:
            supply[key] = value
    
    return supply

@supplies_router.delete("/{supply_id}", response_model=dict)
def delete_supply(supply_id: int):
    global SUPPLIES_DATA
    supply = next((s for s in SUPPLIES_DATA if s["id"] == supply_id), None)
    if not supply:
        raise HTTPException(status_code=404, detail="Поставка не найдена")
    
    # Уменьшаем количество товара на складе
    product = next((p for p in PRODUCTS_DATA if p["id"] == supply["product_id"]), None)
    if product:
        product["current_quantity"] = max(0, product["current_quantity"] - supply["quantity"])
    
    SUPPLIES_DATA = [s for s in SUPPLIES_DATA if s["id"] != supply_id]
    
    return {
        "message": "Поставка удалена",
        "deleted_id": supply_id,
        "product_id": supply["product_id"],
        "quantity_returned": supply["quantity"]
    }

# ===== ОТЧЕТЫ =====
reports_router = APIRouter(prefix="/reports", tags=["Отчеты"])

@reports_router.get("/stock-summary")
def get_stock_summary():
    total_products = len(PRODUCTS_DATA)
    total_quantity = sum(p["current_quantity"] for p in PRODUCTS_DATA)
    total_value = sum(p["current_quantity"] * (p["price"] or 0) for p in PRODUCTS_DATA)
    
    low_stock_products = [
        {
            "product_id": p["id"],
            "product_name": p["name"],
            "current_quantity": p["current_quantity"],
            "min_quantity": p["min_quantity"],
            "deficit": p["min_quantity"] - p["current_quantity"],
            "unit": p["unit"],
            "is_critical": p["current_quantity"] <= p["min_quantity"] * 0.5
        }
        for p in PRODUCTS_DATA if p["current_quantity"] <= p["min_quantity"]
    ]
    
    # Товары в отстойнике
    overflow_summary = [
        {
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "quantity": item["quantity"],
            "date_added": item["date_added"]
        }
        for item in OVERFLOW_ITEMS_DATA
    ]
    
    return {
        "total_products": total_products,
        "total_quantity": total_quantity,
        "total_value": round(total_value, 2),
        "low_stock_count": len(low_stock_products),
        "critical_stock_count": len([p for p in low_stock_products if p["is_critical"]]),
        "overflow_count": len(OVERFLOW_ITEMS_DATA),
        "overflow_total_quantity": sum(item["quantity"] for item in OVERFLOW_ITEMS_DATA),
        "low_stock_products": low_stock_products,
        "overflow_items": overflow_summary
    }

@reports_router.get("/supply-statistics")
def get_supply_statistics():
    total_supplies = len(SUPPLIES_DATA)
    total_quantity = sum(s["quantity"] for s in SUPPLIES_DATA)
    
    # Группировка по товарам
    product_stats = {}
    for supply in SUPPLIES_DATA:
        product_id = supply["product_id"]
        if product_id not in product_stats:
            product = next((p for p in PRODUCTS_DATA if p["id"] == product_id), None)
            product_stats[product_id] = {
                "product_id": product_id,
                "product_name": product["name"] if product else "Неизвестный товар",
                "total_supplied": 0,
                "supply_count": 0
            }
        product_stats[product_id]["total_supplied"] += supply["quantity"]
        product_stats[product_id]["supply_count"] += 1
    
    return {
        "total_supplies": total_supplies,
        "total_quantity_supplied": total_quantity,
        "average_supply_quantity": round(total_quantity / max(total_supplies, 1), 2),
        "by_product": list(product_stats.values())
    }

@reports_router.get("/overflow-report")
def get_overflow_report():
    """Отчет по отстойнику"""
    overflow_items = []
    for item in OVERFLOW_ITEMS_DATA:
        product = next((p for p in PRODUCTS_DATA if p["id"] == item["product_id"]), None)
        if product:
            overflow_items.append({
                **item,
                "category_name": product["category_name"],
                "unit": product["unit"],
                "days_in_overflow": (datetime.now() - datetime.fromisoformat(item["date_added"].replace("Z", ""))).days
            })
    
    return {
        "total_items": len(OVERFLOW_ITEMS_DATA),
        "total_quantity": sum(item["quantity"] for item in OVERFLOW_ITEMS_DATA),
        "items": sorted(overflow_items, key=lambda x: x["days_in_overflow"], reverse=True),
        "oldest_item": min(OVERFLOW_ITEMS_DATA, key=lambda x: x["date_added"]) if OVERFLOW_ITEMS_DATA else None,
        "largest_quantity_item": max(OVERFLOW_ITEMS_DATA, key=lambda x: x["quantity"]) if OVERFLOW_ITEMS_DATA else None
    }

# Подключаем ВСЕ роутеры
app.include_router(products_router)
app.include_router(shelves_router)
app.include_router(product_placements_router)
app.include_router(overflow_bins_router)
app.include_router(purchase_orders_router)
app.include_router(supplies_router)
app.include_router(reports_router)

if __name__ == "__main__":
    uvicorn.run(app)