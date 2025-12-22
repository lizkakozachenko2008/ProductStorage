from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import APIRouter, FastAPI, HTTPException, Depends, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
import uvicorn
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel
import json
from fastapi.middleware.cors import CORSMiddleware
import traceback
from src.service import ProductServiceType
from .models import (
    Base, 
    UserORM, 
    AdminORM, 
    CategoryORM, 
    ProductORM, 
    StockORM, 
    OverflowBinORM, 
    PurchaseOrderORM, 
    ShelfORM, 
    MovementHistoryORM, 
    NotificationORM, 
    ProductPlacementORM, 
    SupplyORM, 
    ShipmentORM
)

DATABASE_URL = 'sqlite:///mydb.db'

class Database:
    def __init__(self) -> None:
        self.engine: Engine = create_engine(
            url=DATABASE_URL,
            echo=True
        )
        
        # Создаем все таблицы
        Base.metadata.create_all(bind=self.engine)
        
        self.session_factory: sessionmaker = (
            sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False
            )
        )

    @property
    def session(self) -> Session:
        return self.session_factory()

db = Database()

# Функция для получения сессии базы данных
def get_db():
    db_session = db.session
    try:
        yield db_session
    finally:
        db_session.close()

app = FastAPI(title="Продуктовый склад API", version="1.0.0")

# Добавим обработчик startup для создания администратора
@app.on_event("startup")
async def startup_event():
    """Создаем администратора по умолчанию при запуске сервера"""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК FASTAPI СЕРВЕРА")
    print("="*60)
    
    try:
        # Создаем администратора по умолчанию
        with db.session as session:
            admin = session.query(AdminORM).filter_by(login="admin").first()
            
            if not admin:
                print("🔧 Создаем администратора по умолчанию...")
                mock_admin = AdminORM(
                    login="admin",
                    password="12341234"
                )
                session.add(mock_admin)
                session.commit()
                print("✅ Администратор создан:")
                print("   Логин: admin")
                print("   Пароль: 12341234")
            else:
                print(f"✅ Администратор уже существует: {admin.login}")
                
            # Покажем всех администраторов
            admins = session.query(AdminORM).all()
            print(f"\n📊 Все администраторы в системе ({len(admins)}):")
            for a in admins:
                print(f"  - ID: {a.id}, Логин: '{a.login}', Пароль: '{a.password}'")
                
    except Exception as e:
        print(f"⚠️  Ошибка при создании администратора: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*60 + "\n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== PYDANTIC МОДЕЛИ ДЛЯ API =====

class UserBase(BaseModel):
    login: str
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    product_count: Optional[int] = 0

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
    product_name: Optional[str] = None
    purchase_order_status: Optional[str] = None

class ShelfBase(BaseModel):
    name: str
    max_capacity: int
    current_quantity: int = 0
    location: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None

class ShelfCreate(ShelfBase):
    pass

class ShelfResponse(ShelfBase):
    id: int
    free_space: Optional[int] = None
    
    class Config:
        from_attributes = True

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

class OverflowItemBase(BaseModel):
    product_id: int
    quantity: int
    notes: Optional[str] = None

class OverflowItemResponse(OverflowItemBase):
    id: int
    date_added: datetime
    product_name: Optional[str] = None

class ShipmentBase(BaseModel):
    product_id: int
    quantity: int
    destination: str
    customer: Optional[str] = None
    order_number: Optional[str] = None
    status: str = "completed"

class ShipmentResponse(ShipmentBase):
    id: int
    shipment_date: datetime
    product_name: Optional[str] = None

# ===== МОДЕЛИ ДЛЯ АДМИНИСТРАТОРОВ =====
class AdminBase(BaseModel):
    login: str

class AdminCreate(BaseModel):
    login: str
    password: str

class AdminResponse(AdminBase):
    id: int

class AdminLoginRequest(BaseModel):
    login: str
    password: str

class AdminLoginResponse(BaseModel):
    message: str
    login: str
    is_authenticated: bool

# Новые модели для специальных операций
class MoveFromOverflowRequest(BaseModel):
    product_id: int
    shelf_id: int
    quantity: int
    notes: Optional[str] = None
    from_overflow: bool = True

class MoveToOverflowRequest(BaseModel):
    product_id: int
    quantity: int
    placement_id: Optional[int] = None
    notes: Optional[str] = None

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

@app.get("/")
def root():
    return RedirectResponse("/docs")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Продуктовый склад API", "timestamp": datetime.now().isoformat()}

# ===== АДМИНИСТРАТОРЫ =====
admins_router = APIRouter(prefix="/admins", tags=["Администраторы"])

@admins_router.get("", response_model=List[AdminResponse])
def get_admins(db: Session = Depends(get_db)):
    """Получить всех администраторов"""
    admins = db.query(AdminORM).all()
    return [{"id": admin.id, "login": admin.login} for admin in admins]

@admins_router.get("/{login}", response_model=AdminResponse)
def get_admin_by_login(login: str, db: Session = Depends(get_db)):
    """Получить администратора по логину"""
    admin = db.query(AdminORM).filter(AdminORM.login == login).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Администратор не найден")
    
    return {"id": admin.id, "login": admin.login}

@admins_router.post("/login", response_model=AdminLoginResponse)
def admin_login(login_data: AdminLoginRequest, db: Session = Depends(get_db)):
    """Вход администратора - УЛУЧШЕННАЯ ВЕРСИЯ С ОТЛАДКОЙ"""
    print(f"\n🔐 ===== ПОПЫТКА ВХОДА АДМИНИСТРАТОРА =====")
    print(f"📤 Получены данные: login='{login_data.login}', password='{login_data.password}'")
    
    try:
        # 1. Покажем ВСЕХ администраторов в БД
        print(f"\n📊 СОДЕРЖИМОЕ БАЗЫ ДАННЫХ:")
        all_admins = db.query(AdminORM).all()
        print(f"   Всего администраторов: {len(all_admins)}")
        
        if not all_admins:
            print("   ❌ В БАЗЕ ДАННЫХ НЕТ НИ ОДНОГО АДМИНИСТРАТОРА!")
            print("   🔧 Создаем администратора по умолчанию...")
            
            # Создаем администратора
            new_admin = AdminORM(
                login="admin",
                password="12341234"
            )
            db.add(new_admin)
            db.commit()
            print("   ✅ Администратор 'admin' создан с паролем '12341234'")
            
            # Повторно получаем список
            all_admins = db.query(AdminORM).all()
            print(f"   Теперь администраторов: {len(all_admins)}")
        
        for idx, admin in enumerate(all_admins, 1):
            print(f"   {idx}. ID: {admin.id}, Логин: '{admin.login}', Пароль: '{admin.password}'")
        
        # 2. Ищем конкретного администратора
        print(f"\n🔎 Поиск администратора с login='{login_data.login}'...")
        admin = db.query(AdminORM).filter(AdminORM.login == login_data.login).first()
        
        if not admin:
            print(f"❌ Администратор с логином '{login_data.login}' НЕ НАЙДЕН!")
            print(f"   Доступные логины: {[a.login for a in all_admins]}")
            raise HTTPException(
                status_code=401, 
                detail=f"Неверный логин или пароль. Администратор '{login_data.login}' не существует."
            )
        
        print(f"✅ Администратор найден: ID={admin.id}")
        print(f"   Логин в БД: '{admin.login}'")
        print(f"   Пароль в БД: '{admin.password}'")
        print(f"   Введенный пароль: '{login_data.password}'")
        
        # 3. Проверяем пароль
        if admin.password != login_data.password:
            print(f"❌ ПАРОЛЬ НЕ СОВПАДАЕТ!")
            print(f"   Ожидалось: '{admin.password}'")
            print(f"   Получено: '{login_data.password}'")
            raise HTTPException(
                status_code=401, 
                detail="Неверный логин или пароль"
            )
        
        print(f"✅ ПАРОЛЬ СОВПАЛ!")
        print(f"🎉 УСПЕШНЫЙ ВХОД для администратора '{admin.login}'")
        print("=" * 50 + "\n")
        
        return {
            "message": "Успешный вход",
            "login": admin.login,
            "is_authenticated": True
        }
        
    except HTTPException as he:
        print(f"⛔ ОШИБКА АВТОРИЗАЦИИ: {he.detail}")
        print("=" * 50 + "\n")
        raise
    except Exception as e:
        print(f"💥 НЕИЗВЕСТНАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50 + "\n")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@admins_router.post("", response_model=AdminResponse)
def create_admin(admin_data: AdminCreate, db: Session = Depends(get_db)):
    """Создать нового администратора"""
    # Проверяем, существует ли уже администратор с таким логином
    existing_admin = db.query(AdminORM).filter(AdminORM.login == admin_data.login).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Администратор с таким логином уже существует")
    
    new_admin = AdminORM(
        login=admin_data.login,
        password=admin_data.password  # В реальном приложении нужно хэшировать пароль!
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return {"id": new_admin.id, "login": new_admin.login}

@admins_router.delete("/{login}", response_model=dict)
def delete_admin(login: str, db: Session = Depends(get_db)):
    """Удалить администратора"""
    admin = db.query(AdminORM).filter(AdminORM.login == login).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Администратор не найден")
    
    db.delete(admin)
    db.commit()
    
    return {
        "message": "Администратор удален",
        "deleted_login": login
    }

# ===== ПОЛЬЗОВАТЕЛИ =====
users_router = APIRouter(prefix="/users", tags=["Пользователи"])

@users_router.get("", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """Получить всех пользователей из базы данных"""
    users = db.query(UserORM).all()
    return [
        {"id": user.id, "login": user.login, "email": user.email}
        for user in users
    ]

@users_router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Получить пользователя по ID"""
    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return {"id": user.id, "login": user.login, "email": user.email}

@users_router.post("", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Создать нового пользователя"""
    # Проверяем уникальность логина и email
    existing_login = db.query(UserORM).filter(UserORM.login == user.login).first()
    if existing_login:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    
    existing_email = db.query(UserORM).filter(UserORM.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    new_user = UserORM(
        login=user.login,
        email=user.email,
        password=user.password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": new_user.id, "login": new_user.login, "email": new_user.email}

@users_router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserBase, db: Session = Depends(get_db)):
    """Обновить пользователя"""
    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    existing_login = db.query(UserORM).filter(
        UserORM.login == user_update.login, 
        UserORM.id != user_id
    ).first()
    if existing_login:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    
    existing_email = db.query(UserORM).filter(
        UserORM.email == user_update.email, 
        UserORM.id != user_id
    ).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    user.login = user_update.login
    user.email = user_update.email
    
    db.commit()
    db.refresh(user)
    
    return {"id": user.id, "login": user.login, "email": user.email}

@users_router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Удалить пользователя"""
    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    db.delete(user)
    db.commit()
    
    return {
        "message": "Пользователь удален",
        "deleted_id": user_id,
        "login": user.login
    }

# ===== КАТЕГОРИИ =====
categories_router = APIRouter(prefix="/categories", tags=["Категории"])

@categories_router.get("", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Получить все категории"""
    categories = db.query(CategoryORM).all()
    result = []
    for category in categories:
        product_count = db.query(ProductORM).filter(ProductORM.category_id == category.id).count()
        result.append({
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "product_count": product_count
        })
    return result

@categories_router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Получить категорию по ID"""
    category = db.query(CategoryORM).filter(CategoryORM.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    product_count = db.query(ProductORM).filter(ProductORM.category_id == category.id).count()
    
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "product_count": product_count
    }

@categories_router.post("", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Создать новую категорию"""
    new_category = CategoryORM(
        name=category.name,
        description=category.description
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return {
        "id": new_category.id,
        "name": new_category.name,
        "description": new_category.description,
        "product_count": 0
    }

@categories_router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category_update: CategoryCreate, db: Session = Depends(get_db)):
    """Обновить категорию"""
    category = db.query(CategoryORM).filter(CategoryORM.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    category.name = category_update.name
    category.description = category_update.description
    
    db.commit()
    db.refresh(category)
    
    product_count = db.query(ProductORM).filter(ProductORM.category_id == category.id).count()
    
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "product_count": product_count
    }

@categories_router.delete("/{category_id}", response_model=dict)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Удалить категорию"""
    category = db.query(CategoryORM).filter(CategoryORM.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    products = db.query(ProductORM).filter(ProductORM.category_id == category_id).all()
    if products:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя удалить категорию с товарами. В категории {len(products)} товаров."
        )
    
    db.delete(category)
    db.commit()
    
    return {
        "message": "Категория удалена",
        "deleted_id": category_id,
        "category_name": category.name
    }

# ===== ТОВАРЫ =====
products_router = APIRouter(prefix="/products", tags=["Товары"])

@products_router.get("", response_model=List[ProductResponse])
def get_products(
    category_id: Optional[int] = Query(None, description="Фильтр по категории"),
    low_stock: Optional[bool] = Query(None, description="Только товары с низким запасом"),
    db: Session = Depends(get_db)
):
    query = db.query(ProductORM)
    
    if category_id:
        query = query.filter(ProductORM.category_id == category_id)
    
    products = query.all()
    
    if low_stock:
        products = [p for p in products if p.current_quantity <= p.min_quantity]
    
    result = []
    for product in products:
        category = db.query(CategoryORM).filter(CategoryORM.id == product.category_id).first()
        category_name = category.name if category else "Неизвестная категория"
        
        result.append({
            "id": product.id,
            "name": product.name,
            "category_id": product.category_id,
            "category_name": category_name,
            "min_quantity": product.min_quantity,
            "unit": product.unit,
            "description": product.description,
            "price": product.price,
            "current_quantity": product.current_quantity
        })
    
    return result

@products_router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ProductORM).filter(ProductORM.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    category = db.query(CategoryORM).filter(CategoryORM.id == product.category_id).first()
    category_name = category.name if category else "Неизвестная категория"
    
    return {
        "id": product.id,
        "name": product.name,
        "category_id": product.category_id,
        "category_name": category_name,
        "min_quantity": product.min_quantity,
        "unit": product.unit,
        "description": product.description,
        "price": product.price,
        "current_quantity": product.current_quantity
    }

@products_router.post("", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Создать новый товар"""
    category = db.query(CategoryORM).filter(CategoryORM.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    new_product = ProductORM(
        name=product.name,
        category_id=product.category_id,
        min_quantity=product.min_quantity,
        unit=product.unit,
        description=product.description,
        price=product.price,
        current_quantity=product.current_quantity
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return {
        "id": new_product.id,
        "name": new_product.name,
        "category_id": new_product.category_id,
        "category_name": category.name,
        "min_quantity": new_product.min_quantity,
        "unit": new_product.unit,
        "description": new_product.description,
        "price": new_product.price,
        "current_quantity": new_product.current_quantity
    }

@products_router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_update: ProductCreate, db: Session = Depends(get_db)):
    """Обновить товар"""
    product = db.query(ProductORM).filter(ProductORM.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    category = db.query(CategoryORM).filter(CategoryORM.id == product_update.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    product.name = product_update.name
    product.category_id = product_update.category_id
    product.min_quantity = product_update.min_quantity
    product.unit = product_update.unit
    product.description = product_update.description
    product.price = product_update.price
    product.current_quantity = product_update.current_quantity
    
    db.commit()
    db.refresh(product)
    
    return {
        "id": product.id,
        "name": product.name,
        "category_id": product.category_id,
        "category_name": category.name,
        "min_quantity": product.min_quantity,
        "unit": product.unit,
        "description": product.description,
        "price": product.price,
        "current_quantity": product.current_quantity
    }

@products_router.delete("/{product_id}", response_model=dict)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Удалить товар"""
    product = db.query(ProductORM).filter(ProductORM.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    db.delete(product)
    db.commit()
    
    return {
        "message": "Товар удален",
        "deleted_id": product_id,
        "product_name": product.name
    }

# ===== СТЕЛЛАЖИ =====
shelves_router = APIRouter(prefix="/shelves", tags=["Стеллажи"])

@shelves_router.get("", response_model=List[ShelfResponse])
def get_shelves(db: Session = Depends(get_db)):
    """Получить все стеллажи"""
    try:
        print("Запрос стеллажей из базы данных...")
        shelves = db.query(ShelfORM).all()
        print(f"Найдено {len(shelves)} стеллажей")
        
        result = []
        for shelf in shelves:
            result.append({
                "id": shelf.id,
                "name": shelf.name,
                "max_capacity": shelf.max_capacity,
                "current_quantity": shelf.current_quantity,
                "category_id": shelf.category_id,
                "free_space": shelf.max_capacity - shelf.current_quantity
            })
        
        print(f"Возвращаем {len(result)} стеллажей")
        return result
    except Exception as e:
        print(f"Ошибка при получении стеллажей: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )

@shelves_router.get("/{shelf_id}", response_model=ShelfResponse)
def get_shelf(shelf_id: int, db: Session = Depends(get_db)):
    """Получить стеллаж по ID"""
    shelf = db.query(ShelfORM).filter(ShelfORM.id == shelf_id).first()
    if not shelf:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")
    
    return {
        "id": shelf.id,
        "name": shelf.name,
        "max_capacity": shelf.max_capacity,
        "current_quantity": shelf.current_quantity,
        "category_id": shelf.category_id,
        "free_space": shelf.max_capacity - shelf.current_quantity
    }

@shelves_router.post("", response_model=ShelfResponse)
def create_shelf(shelf: ShelfCreate, db: Session = Depends(get_db)):
    """Создать новый стеллаж"""
    if shelf.category_id:
        category = db.query(CategoryORM).filter(CategoryORM.id == shelf.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
    
    new_shelf = ShelfORM(
        name=shelf.name,
        max_capacity=shelf.max_capacity,
        current_quantity=shelf.current_quantity,
        category_id=shelf.category_id
    )
    
    try:
        db.add(new_shelf)
        db.commit()
        db.refresh(new_shelf)
        
        return {
            "id": new_shelf.id,
            "name": new_shelf.name,
            "max_capacity": new_shelf.max_capacity,
            "current_quantity": new_shelf.current_quantity,
            "category_id": new_shelf.category_id,
            "free_space": new_shelf.max_capacity - new_shelf.current_quantity
        }
    except Exception as e:
        db.rollback()
        print(f"Ошибка при создании стеллажа: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании стеллажа: {str(e)}"
        )

@shelves_router.put("/{shelf_id}", response_model=ShelfResponse)
def update_shelf(shelf_id: int, shelf_update: ShelfCreate, db: Session = Depends(get_db)):
    """Обновить стеллаж"""
    shelf = db.query(ShelfORM).filter(ShelfORM.id == shelf_id).first()
    if not shelf:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")
    
    if shelf_update.category_id:
        category = db.query(CategoryORM).filter(CategoryORM.id == shelf_update.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
    
    shelf.name = shelf_update.name
    shelf.max_capacity = shelf_update.max_capacity
    shelf.current_quantity = shelf_update.current_quantity
    shelf.category_id = shelf_update.category_id
    
    try:
        db.commit()
        db.refresh(shelf)
        
        return {
            "id": shelf.id,
            "name": shelf.name,
            "max_capacity": shelf.max_capacity,
            "current_quantity": shelf.current_quantity,
            "category_id": shelf.category_id,
            "free_space": shelf.max_capacity - shelf.current_quantity
        }
    except Exception as e:
        db.rollback()
        print(f"Ошибка при обновлении стеллажа: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обновлении стеллажа: {str(e)}"
        )

@shelves_router.delete("/{shelf_id}", response_model=dict)
def delete_shelf(shelf_id: int, db: Session = Depends(get_db)):
    """Удалить стеллаж"""
    shelf = db.query(ShelfORM).filter(ShelfORM.id == shelf_id).first()
    if not shelf:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")
    
    try:
        db.delete(shelf)
        db.commit()
        
        return {
            "message": "Стеллаж удален",
            "deleted_id": shelf_id,
            "shelf_name": shelf.name
        }
    except Exception as e:
        db.rollback()
        print(f"Ошибка при удалении стеллажа: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении стеллажа: {str(e)}"
        )

# ===== ЗАКАЗЫ НА ЗАКУПКУ =====
purchase_orders_router = APIRouter(prefix="/purchase-orders", tags=["Заказы на закупку"])

@purchase_orders_router.get("", response_model=List[PurchaseOrderResponse])
def get_purchase_orders(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    product_id: Optional[int] = Query(None, description="Фильтр по товару"),
    db: Session = Depends(get_db)
):
    query = db.query(PurchaseOrderORM)
    
    if status:
        query = query.filter(PurchaseOrderORM.status == status)
    
    if product_id:
        query = query.filter(PurchaseOrderORM.product_id == product_id)
    
    orders = query.all()
    
    result = []
    for order in orders:
        product = db.query(ProductORM).filter(ProductORM.id == order.product_id).first()
        product_name = product.name if product else "Неизвестный товар"
        
        result.append({
            "id": order.id,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "supplier": order.supplier,
            "expected_delivery_date": order.expected_delivery_date,
            "notes": order.notes,
            "order_date": order.order_date,
            "status": order.status,
            "created_date": order.created_date
        })
    
    return result

@purchase_orders_router.get("/{order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(order_id: int, db: Session = Depends(get_db)):
    """Получить заказ по ID"""
    order = db.query(PurchaseOrderORM).filter(PurchaseOrderORM.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    
    return {
        "id": order.id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "supplier": order.supplier,
        "expected_delivery_date": order.expected_delivery_date,
        "notes": order.notes,
        "order_date": order.order_date,
        "status": order.status,
        "created_date": order.created_date
    }

@purchase_orders_router.post("", response_model=PurchaseOrderResponse)
def create_purchase_order(order: PurchaseOrderCreate, db: Session = Depends(get_db)):
    """Создать новый заказ"""
    product = db.query(ProductORM).filter(ProductORM.id == order.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    new_order = PurchaseOrderORM(
        product_id=order.product_id,
        quantity=order.quantity,
        supplier=order.supplier,
        expected_delivery_date=order.expected_delivery_date,
        notes=order.notes,
        order_date=datetime.now(),
        status="pending",
        created_date=datetime.now()
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    return {
        "id": new_order.id,
        "product_id": new_order.product_id,
        "quantity": new_order.quantity,
        "supplier": new_order.supplier,
        "expected_delivery_date": new_order.expected_delivery_date,
        "notes": new_order.notes,
        "order_date": new_order.order_date,
        "status": new_order.status,
        "created_date": new_order.created_date
    }

@purchase_orders_router.put("/{order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(order_id: int, order_update: PurchaseOrderBase, db: Session = Depends(get_db)):
    """Обновить заказ"""
    order = db.query(PurchaseOrderORM).filter(PurchaseOrderORM.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    
    product = db.query(ProductORM).filter(ProductORM.id == order_update.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    order.product_id = order_update.product_id
    order.quantity = order_update.quantity
    order.supplier = order_update.supplier
    order.expected_delivery_date = order_update.expected_delivery_date
    order.notes = order_update.notes
    
    db.commit()
    db.refresh(order)
    
    return {
        "id": order.id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "supplier": order.supplier,
        "expected_delivery_date": order.expected_delivery_date,
        "notes": order.notes,
        "order_date": order.order_date,
        "status": order.status,
        "created_date": order.created_date
    }

@purchase_orders_router.put("/{order_id}/status", response_model=PurchaseOrderResponse)
def update_order_status(
    order_id: int,
    status: str = Query(..., description="Новый статус заказа"),
    db: Session = Depends(get_db)
):
    """Обновить статус заказа"""
    order = db.query(PurchaseOrderORM).filter(PurchaseOrderORM.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    
    order.status = status
    db.commit()
    db.refresh(order)
    
    return {
        "id": order.id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "supplier": order.supplier,
        "expected_delivery_date": order.expected_delivery_date,
        "notes": order.notes,
        "order_date": order.order_date,
        "status": order.status,
        "created_date": order.created_date
    }

@purchase_orders_router.delete("/{order_id}", response_model=dict)
def delete_purchase_order(order_id: int, db: Session = Depends(get_db)):
    """Удалить заказ"""
    order = db.query(PurchaseOrderORM).filter(PurchaseOrderORM.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ на закупку не найден")
    
    db.delete(order)
    db.commit()
    
    return {
        "message": "Заказ удален",
        "deleted_id": order_id,
        "product_id": order.product_id
    }

# ===== ПОСТАВКИ =====
supplies_router = APIRouter(prefix="/supplies", tags=["Поставки"])

@supplies_router.get("", response_model=List[SupplyResponse])
def get_supplies(
    purchase_order_id: Optional[int] = Query(None, description="Фильтр по заказу на закупку"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db)
):
    query = db.query(SupplyORM)
    
    if purchase_order_id:
        query = query.filter(SupplyORM.purchase_order_id == purchase_order_id)
    
    if status:
        query = query.filter(SupplyORM.status == status)
    
    supplies = query.all()
    
    result = []
    for supply in supplies:
        product = db.query(ProductORM).filter(ProductORM.id == supply.product_id).first()
        product_name = product.name if product else "Неизвестный товар"
        
        purchase_order_status = None
        if supply.purchase_order_id:
            order = db.query(PurchaseOrderORM).filter(PurchaseOrderORM.id == supply.purchase_order_id).first()
            purchase_order_status = order.status if order else None
        
        result.append({
            "id": supply.id,
            "purchase_order_id": supply.purchase_order_id,
            "product_id": supply.product_id,
            "quantity": supply.quantity,
            "supplier": supply.supplier,
            "delivery_date": supply.delivery_date,
            "invoice_number": supply.invoice_number,
            "notes": supply.notes,
            "status": supply.status,
            "supply_date": supply.supply_date,
            "product_name": product_name,
            "purchase_order_status": purchase_order_status
        })
    
    return result

@supplies_router.get("/{supply_id}", response_model=SupplyResponse)
def get_supply(supply_id: int, db: Session = Depends(get_db)):
    """Получить поставку по ID"""
    supply = db.query(SupplyORM).filter(SupplyORM.id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Поставка не найдена")
    
    product = db.query(ProductORM).filter(ProductORM.id == supply.product_id).first()
    product_name = product.name if product else "Неизвестный товар"
    
    purchase_order_status = None
    if supply.purchase_order_id:
        order = db.query(PurchaseOrderORM).filter(PurchaseOrderORM.id == supply.purchase_order_id).first()
        purchase_order_status = order.status if order else None
    
    return {
        "id": supply.id,
        "purchase_order_id": supply.purchase_order_id,
        "product_id": supply.product_id,
        "quantity": supply.quantity,
        "supplier": supply.supplier,
        "delivery_date": supply.delivery_date,
        "invoice_number": supply.invoice_number,
        "notes": supply.notes,
        "status": supply.status,
        "supply_date": supply.supply_date,
        "product_name": product_name,
        "purchase_order_status": purchase_order_status
    }

@supplies_router.post("", response_model=SupplyResponse)
def create_supply(supply: SupplyCreate, db: Session = Depends(get_db)):
    """Создать новую поставку"""
    product = db.query(ProductORM).filter(ProductORM.id == supply.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    if supply.purchase_order_id:
        order = db.query(PurchaseOrderORM).filter(PurchaseOrderORM.id == supply.purchase_order_id).first()
        if order:
            order.status = "delivered"
    
    new_supply = SupplyORM(
        purchase_order_id=supply.purchase_order_id,
        product_id=supply.product_id,
        quantity=supply.quantity,
        supplier=supply.supplier,
        delivery_date=supply.delivery_date,
        invoice_number=supply.invoice_number,
        notes=supply.notes,
        status=supply.status,
        supply_date=datetime.now()
    )
    
    # Обновляем количество товара
    product.current_quantity += supply.quantity
    
    db.add(new_supply)
    db.commit()
    db.refresh(new_supply)
    
    return {
        "id": new_supply.id,
        "purchase_order_id": new_supply.purchase_order_id,
        "product_id": new_supply.product_id,
        "quantity": new_supply.quantity,
        "supplier": new_supply.supplier,
        "delivery_date": new_supply.delivery_date,
        "invoice_number": new_supply.invoice_number,
        "notes": new_supply.notes,
        "status": new_supply.status,
        "supply_date": new_supply.supply_date,
        "product_name": product.name,
        "purchase_order_status": "delivered" if supply.purchase_order_id else None
    }

@supplies_router.put("/{supply_id}", response_model=SupplyResponse)
def update_supply(supply_id: int, supply_update: SupplyBase, db: Session = Depends(get_db)):
    """Обновить поставку"""
    supply = db.query(SupplyORM).filter(SupplyORM.id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Поставка не найдена")
    
    product = db.query(ProductORM).filter(ProductORM.id == supply_update.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Корректируем количество товара
    quantity_diff = supply_update.quantity - supply.quantity
    product.current_quantity += quantity_diff
    
    supply.purchase_order_id = supply_update.purchase_order_id
    supply.product_id = supply_update.product_id
    supply.quantity = supply_update.quantity
    supply.supplier = supply_update.supplier
    supply.delivery_date = supply_update.delivery_date
    supply.invoice_number = supply_update.invoice_number
    supply.notes = supply_update.notes
    supply.status = supply_update.status
    
    db.commit()
    db.refresh(supply)
    
    purchase_order_status = None
    if supply.purchase_order_id:
        order = db.query(PurchaseOrderORM).filter(PurchaseOrderORM.id == supply.purchase_order_id).first()
        purchase_order_status = order.status if order else None
    
    return {
        "id": supply.id,
        "purchase_order_id": supply.purchase_order_id,
        "product_id": supply.product_id,
        "quantity": supply.quantity,
        "supplier": supply.supplier,
        "delivery_date": supply.delivery_date,
        "invoice_number": supply.invoice_number,
        "notes": supply.notes,
        "status": supply.status,
        "supply_date": supply.supply_date,
        "product_name": product.name,
        "purchase_order_status": purchase_order_status
    }

@supplies_router.delete("/{supply_id}", response_model=dict)
def delete_supply(supply_id: int, db: Session = Depends(get_db)):
    """Удалить поставку"""
    supply = db.query(SupplyORM).filter(SupplyORM.id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Поставка не найдена")
    
    product = db.query(ProductORM).filter(ProductORM.id == supply.product_id).first()
    if product:
        product.current_quantity = max(0, product.current_quantity - supply.quantity)
    
    db.delete(supply)
    db.commit()
    
    return {
        "message": "Поставка удалена",
        "deleted_id": supply_id,
        "product_id": supply.product_id,
        "quantity_returned": supply.quantity
    }

# ===== ТОВАРЫ В ОТСТОЙНИКЕ =====
overflow_bins_router = APIRouter(prefix="/overflow-bins", tags=["Отстойники"])

@overflow_bins_router.get("/{item_id}", response_model=OverflowItemResponse)
def get_overflow_item(item_id: int, db: Session = Depends(get_db)):
    """Получить товар в отстойнике по ID"""
    item = db.query(OverflowBinORM).filter(OverflowBinORM.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар в отстойнике не найден")
    
    product = db.query(ProductORM).filter(ProductORM.id == item.product_id).first()
    product_name = product.name if product else "Неизвестный товар"
    
    return {
        "id": item.id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "notes": item.notes,
        "date_added": item.date_added,
        "product_name": product_name
    }

@overflow_bins_router.get("", response_model=List[OverflowItemResponse])
def get_overflow_items(db: Session = Depends(get_db)):
    """Получить все товары в отстойнике"""
    items = db.query(OverflowBinORM).all()
    result = []
    for item in items:
        product = db.query(ProductORM).filter(ProductORM.id == item.product_id).first()
        product_name = product.name if product else "Неизвестный товар"
        
        result.append({
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "notes": item.notes,
            "date_added": item.date_added,
            "product_name": product_name
        })
    
    return result

@overflow_bins_router.post("", response_model=OverflowItemResponse)
def add_to_overflow(item: OverflowItemBase, db: Session = Depends(get_db)):
    """Добавить товар в отстойник"""
    product = db.query(ProductORM).filter(ProductORM.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # ИСПРАВЛЕНИЕ: При добавлении в отстойник НЕ уменьшаем общее количество на складе
    # Товар просто перемещается из доступных на стеллаже в отстойник
    # Общее количество товара на складе остается неизменным
    
    # Создаем запись в отстойнике
    new_item = OverflowBinORM(
        product_id=item.product_id,
        quantity=item.quantity,
        notes=item.notes,
        date_added=datetime.now()
    )
    
    # ИСПРАВЛЕНИЕ: НЕ уменьшаем количество товара на складе
    # product.current_quantity -= item.quantity
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return {
        "id": new_item.id,
        "product_id": new_item.product_id,
        "quantity": new_item.quantity,
        "notes": new_item.notes,
        "date_added": new_item.date_added,
        "product_name": product.name
    }

@overflow_bins_router.post("/move-from-shelf", response_model=dict)
def move_from_shelf_to_overflow(move_data: MoveToOverflowRequest, db: Session = Depends(get_db)):
    """Переместить товар со стеллажа в отстойник"""
    try:
        print("Перемещение товара со стеллажа в отстойник:", move_data.dict())
        
        product = db.query(ProductORM).filter(ProductORM.id == move_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Если указан placement_id, значит товар уже размещен на стеллаже
        if move_data.placement_id:
            placement = db.query(ProductPlacementORM).filter(ProductPlacementORM.id == move_data.placement_id).first()
            if not placement:
                raise HTTPException(status_code=404, detail="Размещение товара не найдено")
            
            if placement.quantity < move_data.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Недостаточно товара на стеллаже. Доступно: {placement.quantity}, запрошено: {move_data.quantity}"
                )
            
            # Уменьшаем количество на стеллаже
            if placement.quantity == move_data.quantity:
                # Если перемещаем все количество, удаляем размещение
                db.delete(placement)
            else:
                # Если перемещаем часть, уменьшаем количество
                placement.quantity -= move_data.quantity
            
            # Освобождаем место на стеллаже
            if placement.shelf_id:
                shelf = db.query(ShelfORM).filter(ShelfORM.id == placement.shelf_id).first()
                if shelf:
                    shelf.current_quantity -= move_data.quantity
        
        # Добавляем товар в отстойник
        new_item = OverflowBinORM(
            product_id=move_data.product_id,
            quantity=move_data.quantity,
            notes=move_data.notes or "Перемещено со стеллажа в отстойник",
            date_added=datetime.now()
        )
        
        db.add(new_item)
        db.commit()
        
        return {
            "success": True,
            "message": "Товар успешно перемещен в отстойник",
            "overflow_item_id": new_item.id,
            "product_id": new_item.product_id,
            "quantity": new_item.quantity
        }
        
    except Exception as e:
        db.rollback()
        print("Ошибка при перемещении в отстойник:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка при перемещении в отстойник: {str(e)}")

@overflow_bins_router.put("/{item_id}", response_model=OverflowItemResponse)
def update_overflow_item(item_id: int, item_update: OverflowItemBase, db: Session = Depends(get_db)):
    """Обновить товар в отстойнике"""
    item = db.query(OverflowBinORM).filter(OverflowBinORM.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар в отстойнике не найден")
    
    # Получаем старый товар
    old_product = db.query(ProductORM).filter(ProductORM.id == item.product_id).first()
    
    # Получаем новый товар
    new_product = db.query(ProductORM).filter(ProductORM.id == item_update.product_id).first()
    if not new_product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Рассчитываем разницу
    quantity_diff = item_update.quantity - item.quantity
    
    # Если меняется количество
    if quantity_diff != 0:
        # ИСПРАВЛЕНИЕ: При изменении количества в отстойнике НЕ меняем общее количество на складе
        # Товар остается в отстойнике, просто меняется его количество там
        pass
    
    # Обновляем запись
    item.product_id = item_update.product_id
    item.quantity = item_update.quantity
    item.notes = item_update.notes
    
    db.commit()
    db.refresh(item)
    
    return {
        "id": item.id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "notes": item.notes,
        "date_added": item.date_added,
        "product_name": new_product.name
    }

@overflow_bins_router.delete("/{item_id}", response_model=dict)
def delete_overflow_item(item_id: int, db: Session = Depends(get_db)):
    """Удалить товар из отстойника"""
    item = db.query(OverflowBinORM).filter(OverflowBinORM.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар в отстойнике не найден")
    
    product = db.query(ProductORM).filter(ProductORM.id == item.product_id).first()
    if product:
        # ИСПРАВЛЕНИЕ: При удалении из отстойника НЕ возвращаем товар на склад
        # Товар и так считается на складе, просто был в отстойнике
        # product.current_quantity += item.quantity
        pass
    
    db.delete(item)
    db.commit()
    
    return {
        "message": "Товар удален из отстойника",
        "deleted_id": item_id,
        "product_id": item.product_id,
        "quantity": item.quantity
    }

# ===== РАЗМЕЩЕНИЕ ТОВАРОВ =====
product_placements_router = APIRouter(prefix="/product-placements", tags=["Размещение товаров"])

# Pydantic модели для размещения товаров
class ProductPlacementCreate(BaseModel):
    product_id: int
    shelf_id: Optional[int] = None
    quantity: int
    notes: Optional[str] = None
    placement_date: Optional[datetime] = None

class ProductPlacementResponse(BaseModel):
    id: int
    product_id: int
    shelf_id: Optional[int] = None
    quantity: int
    placement_date: datetime
    notes: Optional[str] = None
    product_name: Optional[str] = None
    shelf_name: Optional[str] = None
    
    class Config:
        from_attributes = True

@product_placements_router.get("", response_model=List[ProductPlacementResponse])
def get_product_placements(
    product_id: Optional[int] = Query(None, description="Фильтр по товару"),
    shelf_id: Optional[int] = Query(None, description="Фильтр по стеллажу"),
    db: Session = Depends(get_db)
):
    """Получить все размещения товаров"""
    query = db.query(ProductPlacementORM)
    
    if product_id:
        query = query.filter(ProductPlacementORM.product_id == product_id)
    
    if shelf_id:
        query = query.filter(ProductPlacementORM.shelf_id == shelf_id)
    
    placements = query.all()
    
    result = []
    for placement in placements:
        product = db.query(ProductORM).filter(ProductORM.id == placement.product_id).first()
        product_name = product.name if product else "Неизвестный товар"
        
        shelf_name = None
        if placement.shelf_id:
            shelf = db.query(ShelfORM).filter(ShelfORM.id == placement.shelf_id).first()
            shelf_name = shelf.name if shelf else None
        
        result.append({
            "id": placement.id,
            "product_id": placement.product_id,
            "shelf_id": placement.shelf_id,
            "quantity": placement.quantity,
            "placement_date": placement.placement_date,
            "notes": placement.notes,
            "product_name": product_name,
            "shelf_name": shelf_name
        })
    
    return result

@product_placements_router.get("/{placement_id}", response_model=ProductPlacementResponse)
def get_product_placement(placement_id: int, db: Session = Depends(get_db)):
    """Получить размещение по ID"""
    placement = db.query(ProductPlacementORM).filter(ProductPlacementORM.id == placement_id).first()
    if not placement:
        raise HTTPException(status_code=404, detail="Размещение не найдено")
    
    product = db.query(ProductORM).filter(ProductORM.id == placement.product_id).first()
    product_name = product.name if product else "Неизвестный товар"
    
    shelf_name = None
    if placement.shelf_id:
        shelf = db.query(ShelfORM).filter(ShelfORM.id == placement.shelf_id).first()
        shelf_name = shelf.name if shelf else None
    
    return {
        "id": placement.id,
        "product_id": placement.product_id,
        "shelf_id": placement.shelf_id,
        "quantity": placement.quantity,
        "placement_date": placement.placement_date,
        "notes": placement.notes,
        "product_name": product_name,
        "shelf_name": shelf_name
    }

@product_placements_router.post("", response_model=dict)
def create_product_placement(placement: ProductPlacementCreate, db: Session = Depends(get_db)):
    """Создать новое размещение товара"""
    try:
        print("Получен запрос на создание размещения:", placement.dict())
        
        # Проверяем товар
        product = db.query(ProductORM).filter(ProductORM.id == placement.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        shelf_name = None
        if placement.shelf_id:
            # Проверяем стеллаж
            shelf = db.query(ShelfORM).filter(ShelfORM.id == placement.shelf_id).first()
            if not shelf:
                raise HTTPException(status_code=404, detail="Стеллаж не найден")
            
            # Проверяем место на стеллаже
            free_space = shelf.max_capacity - shelf.current_quantity
            if placement.quantity > free_space:
                raise HTTPException(
                    status_code=400,
                    detail=f"Недостаточно места на стеллаже '{shelf.name}'. Свободно: {free_space}, требуется: {placement.quantity}"
                )
            
            # Обновляем стеллаж
            shelf.current_quantity += placement.quantity
            shelf_name = shelf.name
        
        # Проверяем наличие товара на складе
        if placement.quantity > product.current_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара '{product.name}' на складе. Доступно: {product.current_quantity}, требуется: {placement.quantity}"
            )
        
        # Уменьшаем количество товара на складе
        product.current_quantity -= placement.quantity
        
        # Создаем запись размещения
        new_placement = ProductPlacementORM(
            product_id=placement.product_id,
            shelf_id=placement.shelf_id,
            quantity=placement.quantity,
            placement_date=placement.placement_date or datetime.now(),
            notes=placement.notes
        )
        
        db.add(new_placement)
        db.commit()
        db.refresh(new_placement)
        
        return {
            "success": True,
            "message": "Товар успешно размещен",
            "id": new_placement.id,
            "product_id": new_placement.product_id,
            "product_name": product.name,
            "shelf_id": new_placement.shelf_id,
            "shelf_name": shelf_name,
            "quantity": new_placement.quantity,
            "placement_date": new_placement.placement_date
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print("Ошибка при создании размещения:", str(e))
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@product_placements_router.post("/move-from-overflow", response_model=dict)
def move_from_overflow_to_shelf(move_data: MoveFromOverflowRequest, db: Session = Depends(get_db)):
    """Переместить товар из отстойника на стеллаж"""
    try:
        print("Перемещение товара из отстойника на стеллаж:", move_data.dict())
        
        # Проверяем товар
        product = db.query(ProductORM).filter(ProductORM.id == move_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Проверяем стеллаж
        shelf = db.query(ShelfORM).filter(ShelfORM.id == move_data.shelf_id).first()
        if not shelf:
            raise HTTPException(status_code=404, detail="Стеллаж не найден")
        
        # Проверяем место на стеллаже
        free_space = shelf.max_capacity - shelf.current_quantity
        if move_data.quantity > free_space:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно места на стеллаже '{shelf.name}'. Свободно: {free_space}, требуется: {move_data.quantity}"
            )
        
        # ИСПРАВЛЕНИЕ: При перемещении из отстойника НЕ проверяем общее количество на складе
        # Товар и так считается на складе, просто был в отстойнике
        
        # Ищем товар в отстойнике
        overflow_item = db.query(OverflowBinORM).filter(
            OverflowBinORM.product_id == move_data.product_id
        ).first()
        
        if not overflow_item:
            raise HTTPException(status_code=404, detail="Товар не найден в отстойнике")
        
        if overflow_item.quantity < move_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара в отстойнике. Доступно: {overflow_item.quantity}, требуется: {move_data.quantity}"
            )
        
        # Создаем размещение на стеллаже
        new_placement = ProductPlacementORM(
            product_id=move_data.product_id,
            shelf_id=move_data.shelf_id,
            quantity=move_data.quantity,
            placement_date=datetime.now(),
            notes=move_data.notes or "Перемещено из отстойника"
        )
        
        # Обновляем стеллаж
        shelf.current_quantity += move_data.quantity
        
        # Обновляем или удаляем отстойник
        if overflow_item.quantity == move_data.quantity:
            # Если перемещаем все количество, удаляем из отстойника
            db.delete(overflow_item)
        else:
            # Если перемещаем часть, уменьшаем количество в отстойнике
            overflow_item.quantity -= move_data.quantity
        
        db.add(new_placement)
        db.commit()
        db.refresh(new_placement)
        
        return {
            "success": True,
            "message": "Товаар успешно перемещен из отстойника на стеллаж",
            "id": new_placement.id,
            "product_id": new_placement.product_id,
            "shelf_id": new_placement.shelf_id,
            "quantity": new_placement.quantity,
            "overflow_item_remaining": overflow_item.quantity if overflow_item.quantity > move_data.quantity else 0
        }
        
    except Exception as e:
        db.rollback()
        print("Ошибка при перемещении из отстойника:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка при перемещении из отстойника: {str(e)}")

@product_placements_router.put("/{placement_id}", response_model=dict)
def update_product_placement(
    placement_id: int, 
    placement_update: ProductPlacementCreate, 
    db: Session = Depends(get_db)
):
    """Обновить размещение товара"""
    try:
        print("Получен запрос на обновление размещения ID:", placement_id)
        
        placement = db.query(ProductPlacementORM).filter(ProductPlacementORM.id == placement_id).first()
        if not placement:
            raise HTTPException(status_code=404, detail="Размещение не найдено")
        
        # Проверяем товар
        product = db.query(ProductORM).filter(ProductORM.id == placement_update.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Сохраняем старые значения
        old_quantity = placement.quantity
        old_shelf_id = placement.shelf_id
        old_product_id = placement.product_id
        
        # Проверяем доступное количество для нового размещения
        if placement_update.quantity > product.current_quantity + old_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара '{product.name}' на складе. Доступно: {product.current_quantity + old_quantity}, требуется: {placement_update.quantity}"
            )
        
        shelf_name = None
        if placement_update.shelf_id:
            # Проверяем новый стеллаж
            shelf = db.query(ShelfORM).filter(ShelfORM.id == placement_update.shelf_id).first()
            if not shelf:
                raise HTTPException(status_code=404, detail="Стеллаж не найден")
            
            # Рассчитываем свободное место с учетом старого размещения
            if old_shelf_id == placement_update.shelf_id:
                # Если стеллаж тот же, учитываем только разницу в количестве
                quantity_diff = placement_update.quantity - old_quantity
                free_space = shelf.max_capacity - shelf.current_quantity
                if quantity_diff > free_space:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Недостаточно места на стеллаже '{shelf.name}'. Свободно: {free_space}, требуется дополнительно: {quantity_diff}"
                    )
            else:
                # Если новый стеллаж, проверяем все количество
                free_space = shelf.max_capacity - shelf.current_quantity
                if placement_update.quantity > free_space:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Недостаточно места на стеллаже '{shelf.name}'. Свободно: {free_space}, требуется: {placement_update.quantity}"
                    )
            
            shelf_name = shelf.name
        
        # Корректируем количества
        # 1. Возвращаем старое количество на склад
        old_product = db.query(ProductORM).filter(ProductORM.id == old_product_id).first()
        if old_product:
            old_product.current_quantity += old_quantity
        
        # 2. Освобождаем место на старом стеллаже
        if old_shelf_id:
            old_shelf = db.query(ShelfORM).filter(ShelfORM.id == old_shelf_id).first()
            if old_shelf:
                old_shelf.current_quantity = max(0, old_shelf.current_quantity - old_quantity)
        
        # 3. Забираем новое количество со склада
        product.current_quantity -= placement_update.quantity
        
        # 4. Занимаем место на новом стеллаже
        if placement_update.shelf_id:
            shelf.current_quantity += placement_update.quantity
        
        # Обновляем размещение
        placement.product_id = placement_update.product_id
        placement.shelf_id = placement_update.shelf_id
        placement.quantity = placement_update.quantity
        placement.notes = placement_update.notes
        placement.last_updated = datetime.now()
        
        db.commit()
        db.refresh(placement)
        
        return {
            "success": True,
            "message": "Размещение успешно обновлено",
            "id": placement.id,
            "product_id": placement.product_id,
            "product_name": product.name,
            "shelf_id": placement.shelf_id,
            "shelf_name": shelf_name,
            "quantity": placement.quantity,
            "placement_date": placement.placement_date,
            "last_updated": placement.last_updated
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print("Ошибка при обновлении размещения:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@product_placements_router.patch("/{placement_id}", response_model=dict)
def partial_update_product_placement(
    placement_id: int, 
    placement_update: dict, 
    db: Session = Depends(get_db)
):
    """Частично обновить размещение товара"""
    try:
        print("Получен запрос на частичное обновление размещения ID:", placement_id)
        
        placement = db.query(ProductPlacementORM).filter(ProductPlacementORM.id == placement_id).first()
        if not placement:
            raise HTTPException(status_code=404, detail="Размещение не найдено")
        
        # Обновляем только переданные поля
        for field, value in placement_update.items():
            if hasattr(placement, field) and value is not None:
                setattr(placement, field, value)
        
        placement.last_updated = datetime.now()
        
        db.commit()
        db.refresh(placement)
        
        return {
            "success": True,
            "message": "Размещение частично обновлено",
            "id": placement.id
        }
        
    except Exception as e:
        db.rollback()
        print("Ошибка при частичном обновлении размещения:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
    
@product_placements_router.delete("/{placement_id}", response_model=dict)
def delete_product_placement(placement_id: int, db: Session = Depends(get_db)):
    """Удалить размещение товара"""
    try:
        placement = db.query(ProductPlacementORM).filter(ProductPlacementORM.id == placement_id).first()
        if not placement:
            raise HTTPException(status_code=404, detail="Размещение не найдено")
        
        # Возвращаем товар на склад
        product = db.query(ProductORM).filter(ProductORM.id == placement.product_id).first()
        if product:
            product.current_quantity += placement.quantity
        
        # Если размещение было на стеллаже, освобождаем место
        if placement.shelf_id:
            shelf = db.query(ShelfORM).filter(ShelfORM.id == placement.shelf_id).first()
            if shelf:
                shelf.current_quantity = max(0, shelf.current_quantity - placement.quantity)
        
        # Удаляем размещение
        db.delete(placement)
        db.commit()
        
        return {
            "success": True,
            "message": "Размещение удалено. Товар возвращен на склад.",
            "deleted_id": placement_id,
            "product_id": placement.product_id,
            "quantity_returned": placement.quantity
        }
        
    except Exception as e:
        db.rollback()
        print("Ошибка при удалении размещения:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
    
# ===== ОТГРУЗКИ =====
shipments_router = APIRouter(prefix="/shipments", tags=["Отгрузки"])

@shipments_router.get("", response_model=List[ShipmentResponse])
def get_shipments(db: Session = Depends(get_db)):
    """Получить все отгрузки"""
    shipments = db.query(ShipmentORM).all()
    result = []
    for shipment in shipments:
        product = db.query(ProductORM).filter(ProductORM.id == shipment.product_id).first()
        product_name = product.name if product else "Неизвестный товар"
        
        result.append({
            "id": shipment.id,
            "product_id": shipment.product_id,
            "quantity": shipment.quantity,
            "destination": shipment.destination,
            "customer": shipment.customer,
            "order_number": shipment.order_number,
            "status": shipment.status,
            "shipment_date": shipment.shipment_date,
            "product_name": product_name
        })
    
    return result

@shipments_router.post("", response_model=ShipmentResponse)
def create_shipment(shipment: ShipmentBase, db: Session = Depends(get_db)):
    """Создать новую отгрузку"""
    product = db.query(ProductORM).filter(ProductORM.id == shipment.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    if shipment.quantity > product.current_quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Недостаточно товара. Доступно: {product.current_quantity}, запрошено: {shipment.quantity}"
        )
    
    new_shipment = ShipmentORM(
        product_id=shipment.product_id,
        quantity=shipment.quantity,
        destination=shipment.destination,
        customer=shipment.customer,
        order_number=shipment.order_number,
        status=shipment.status,
        shipment_date=datetime.now()
    )
    
    # Уменьшаем количество товара
    product.current_quantity -= shipment.quantity
    
    db.add(new_shipment)
    db.commit()
    db.refresh(new_shipment)
    
    return {
        "id": new_shipment.id,
        "product_id": new_shipment.product_id,
        "quantity": new_shipment.quantity,
        "destination": new_shipment.destination,
        "customer": new_shipment.customer,
        "order_number": new_shipment.order_number,
        "status": new_shipment.status,
        "shipment_date": new_shipment.shipment_date,
        "product_name": product.name
    }

# ===== ОТЧЕТЫ =====
reports_router = APIRouter(prefix="/reports", tags=["Отчеты"])

@reports_router.get("/stock-summary")
def get_stock_summary(db: Session = Depends(get_db)):
    """Получить сводку по запасам"""
    total_products = db.query(ProductORM).count()
    
    products = db.query(ProductORM).all()
    total_quantity = sum(p.current_quantity for p in products)
    total_value = sum(p.current_quantity * (p.price or 0) for p in products)
    
    low_stock_products = []
    for product in products:
        if product.current_quantity <= product.min_quantity:
            category = db.query(CategoryORM).filter(CategoryORM.id == product.category_id).first()
            category_name = category.name if category else "Неизвестная категория"
            
            low_stock_products.append({
                "product_id": product.id,
                "product_name": product.name,
                "category_name": category_name,
                "current_quantity": product.current_quantity,
                "min_quantity": product.min_quantity,
                "deficit": product.min_quantity - product.current_quantity,
                "unit": product.unit,
                "is_critical": product.current_quantity <= product.min_quantity * 0.5
            })
    
    overflow_items = db.query(OverflowBinORM).all()
    overflow_summary = []
    for item in overflow_items:
        product = db.query(ProductORM).filter(ProductORM.id == item.product_id).first()
        if product:
            overflow_summary.append({
                "product_id": item.product_id,
                "product_name": product.name,
                "quantity": item.quantity,
                "date_added": item.date_added
            })
    
    return {
        "total_products": total_products,
        "total_quantity": total_quantity,
        "total_value": round(total_value, 2),
        "low_stock_count": len(low_stock_products),
        "critical_stock_count": len([p for p in low_stock_products if p["is_critical"]]),
        "overflow_count": len(overflow_items),
        "overflow_total_quantity": sum(item.quantity for item in overflow_items),
        "low_stock_products": low_stock_products,
        "overflow_items": overflow_summary
    }

@reports_router.get("/supply-statistics")
def get_supply_statistics(db: Session = Depends(get_db)):
    """Получить статистику по поставкам"""
    total_supplies = db.query(SupplyORM).count()
    supplies = db.query(SupplyORM).all()
    total_quantity = sum(s.quantity for s in supplies)
    
    product_stats = {}
    for supply in supplies:
        product_id = supply.product_id
        if product_id not in product_stats:
            product = db.query(ProductORM).filter(ProductORM.id == product_id).first()
            product_stats[product_id] = {
                "product_id": product_id,
                "product_name": product.name if product else "Неизвестный товар",
                "total_supplied": 0,
                "supply_count": 0
            }
        product_stats[product_id]["total_supplied"] += supply.quantity
        product_stats[product_id]["supply_count"] += 1
    
    return {
        "total_supplies": total_supplies,
        "total_quantity_supplied": total_quantity,
        "average_supply_quantity": round(total_quantity / max(total_supplies, 1), 2),
        "by_product": list(product_stats.values())
    }

@app.get("/reports/placement")
def get_placement_report(service: ProductServiceType):
    return service.get_placement_report()


# Подключаем все роутеры (ДОБАВЛЯЕМ admins_router В СПИСОК)
app.include_router(admins_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(shelves_router)
app.include_router(purchase_orders_router)
app.include_router(supplies_router)
app.include_router(overflow_bins_router)
app.include_router(product_placements_router)
app.include_router(shipments_router)
app.include_router(reports_router)

if __name__ == "__main__":
    uvicorn.run(app)