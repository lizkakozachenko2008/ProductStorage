from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import APIRouter, Body, FastAPI, HTTPException, Depends, Path, Query, Request
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
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import secrets

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
    ShipmentORM,
    OrderORM
)

DATABASE_URL = 'sqlite:///mydb.db'

class Database:
    def __init__(self) -> None:
        self.engine: Engine = create_engine(
            url=DATABASE_URL,
            echo=True
        )
        
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

def get_db():
    db_session = db.session
    try:
        yield db_session
    finally:
        db_session.close()

app = FastAPI(title="Продуктовый склад API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*60)
    print("🚀 ЗАПУСК FASTAPI СЕРВЕРА")
    print("="*60)
    
    try:
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

# ===== PYDANTIC МОДЕЛИ =====

class UserLoginRequest(BaseModel):
    login: str
    password: str

class UserLoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None

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
    customer_email: Optional[str] = None
    order_number: Optional[str] = None
    status: str = "pending"
    user_id: Optional[int] = None
    order_id: Optional[int] = None

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentResponse(ShipmentBase):
    id: int
    shipment_date: datetime
    product_name: Optional[str] = None

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    product_name: str
    price: float
    unit: str

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    delivery_address: str
    customer_phone: Optional[str] = None
    order_comment: Optional[str] = None
    items: List[OrderItemBase]
    total_amount: float
    status: str = "pending"
    user_token: Optional[str] = None  

class OrderResponse(OrderCreate):
    id: int
    order_date: datetime
    order_number: str

class OrderItemResponse(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    unit: Optional[str] = None

class OrderShipmentResponse(BaseModel):
    id: Optional[int] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    shipment_date: Optional[datetime] = None

class AdminOrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: Optional[int] = None
    customer_name: str
    customer_email: str
    delivery_address: str
    customer_phone: Optional[str] = None
    order_comment: Optional[str] = None
    total_amount: float
    status: str
    order_date: datetime
    items: List[OrderItemResponse] = []
    shipments: List[OrderShipmentResponse] = []
    
    class Config:
        from_attributes = True

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

@admins_router.get("/test-orders")
def test_orders_endpoint(db: Session = Depends(get_db)):
    """Тестовый эндпоинт для проверки"""
    try:
        orders = db.query(OrderORM).limit(5).all()
        
        result = []
        for order in orders:
            result.append({
                "id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name,
                "status": order.status
            })
        
        return {
            "success": True,
            "count": len(result),
            "orders": result,
            "message": f"Найдено {len(orders)} заказов в базе"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при получении заказов"
        }

@admins_router.get("/orders", response_model=List[AdminOrderResponse])
def get_all_orders_admin(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db)
):
    """Получить все заказы (для администратора)"""
    try:
        print(f" Запрос заказов (статус={status})")
        
        query = db.query(OrderORM)
        
        if status:
            query = query.filter(OrderORM.status == status)
        
        orders = query.order_by(OrderORM.order_date.desc()).all()
        print(f" Найдено {len(orders)} заказов")
        
        result = []
        for order in orders:
            items = []
            try:
                if order.items_json:
                    items_data = json.loads(order.items_json)
                    if isinstance(items_data, list):
                        for item in items_data:
                            items.append(OrderItemResponse(
                                product_id=item.get('product_id'),
                                product_name=item.get('product_name'),
                                quantity=item.get('quantity'),
                                price=item.get('price'),
                                unit=item.get('unit')
                            ))
            except Exception as e:
                print(f" Ошибка парсинга items для заказа {order.id}: {e}")
                items = []
            
            shipments = db.query(ShipmentORM).filter(
                ShipmentORM.order_id == order.id
            ).all()
            
            shipments_list = []
            for shipment in shipments:
                product = db.query(ProductORM).filter(ProductORM.id == shipment.product_id).first()
                shipments_list.append(OrderShipmentResponse(
                    id=shipment.id,
                    product_id=shipment.product_id,
                    product_name=product.name if product else None,
                    quantity=shipment.quantity,
                    status=shipment.status,
                    shipment_date=shipment.shipment_date
                ))
            
            order_response = AdminOrderResponse(
                id=order.id,
                order_number=order.order_number,
                user_id=order.user_id,
                customer_name=order.customer_name,
                customer_email=order.customer_email,
                delivery_address=order.delivery_address,
                customer_phone=order.customer_phone,
                order_comment=order.order_comment,
                total_amount=float(order.total_amount) if order.total_amount else 0.0,
                status=order.status,
                order_date=order.order_date,
                items=items,
                shipments=shipments_list
            )
            
            result.append(order_response)
        
        print(f" Возвращаем {len(result)} заказов")
        return result
        
    except Exception as e:
        print(f" Критическая ошибка в /admins/orders: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )

@admins_router.put("/orders/{order_id}/status", response_model=dict)
def update_admin_order_status(
    order_id: int,
    status: str = Query(..., description="Новый статус"),
    db: Session = Depends(get_db)
):
    """Обновить статус заказа"""
    print(f" Обновление статуса заказа {order_id} на '{status}'")
    
    order = db.query(OrderORM).filter(OrderORM.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    order.status = status
    db.commit()
    
    return {
        "success": True,
        "message": f"Статус заказа #{order.order_number} обновлен на '{status}'",
        "order_id": order_id,
        "order_number": order.order_number,
        "new_status": status
    }

@admins_router.put("/orders/{order_id}/status", response_model=dict)
def update_order_status(
    order_id: int,
    status: str = Query(..., description="Новый статус заказа"),
    db: Session = Depends(get_db)
):
    """Обновить статус заказа"""
    order = db.query(OrderORM).filter(OrderORM.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    order.status = status
    
    shipments = db.query(ShipmentORM).filter(ShipmentORM.order_id == order_id).all()
    for shipment in shipments:
        shipment.status = status
        
        if status == 'completed':
            product = db.query(ProductORM).filter(ProductORM.id == shipment.product_id).first()
            if product:
                if product.current_quantity >= shipment.quantity:
                    product.current_quantity -= shipment.quantity
                else:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Недостаточно товара '{product.name}' для отгрузки"
                    )
    
    db.commit()
    
    return {
        "message": "Статус заказа обновлен",
        "order_id": order_id,
        "new_status": status,
        "shipments_updated": len(shipments)
    }

@admins_router.get("/orders/debug")
def debug_admin_orders(db: Session = Depends(get_db)):
    """Отладочный эндпоинт для проверки структуры данных"""
    try:
        order = db.query(OrderORM).first()
        
        if not order:
            return {
                "success": False,
                "message": "Нет заказов в базе",
                "total_orders": 0
            }
        
        test_data = {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "delivery_address": order.delivery_address,
            "total_amount": float(order.total_amount) if order.total_amount else 0.0,
            "status": order.status,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "has_items_json": bool(order.items_json),
            "items_json_length": len(order.items_json) if order.items_json else 0,
            "items_json_sample": order.items_json[:100] + "..." if order.items_json and len(order.items_json) > 100 else order.items_json
        }
        
        return {
            "success": True,
            "message": "Данные доступны",
            "sample_order": test_data,
            "total_orders": db.query(OrderORM).count(),
            "api_status": {
                "/admins/orders": "available",
                "/admins/orders/debug": "available",
                "database_connected": True
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при проверке данных",
            "api_status": {
                "/admins/orders": "error",
                "database_connected": False
            }
        }

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
    """Вход администратора"""
    print(f"\n ===== ПОПЫТКА ВХОДА АДМИНИСТРАТОРА =====")
    print(f" Получены данные: login='{login_data.login}', password='{login_data.password}'")
    
    try:
        print(f"\n СОДЕРЖИМОЕ БАЗЫ ДАННЫХ:")
        all_admins = db.query(AdminORM).all()
        print(f"   Всего администраторов: {len(all_admins)}")
        
        if not all_admins:
            print("    В БАЗЕ ДАННЫХ НЕТ НИ ОДНОГО АДМИНИСТРАТОРА!")
            print("    Создаем администратора по умолчанию...")
            
            new_admin = AdminORM(
                login="admin",
                password="12341234"
            )
            db.add(new_admin)
            db.commit()
            print("    Администратор 'admin' создан с паролем '12341234'")
            
            all_admins = db.query(AdminORM).all()
            print(f"   Теперь администраторов: {len(all_admins)}")
        
        for idx, admin in enumerate(all_admins, 1):
            print(f"   {idx}. ID: {admin.id}, Логин: '{admin.login}', Пароль: '{admin.password}'")
        
        print(f"\n Поиск администратора с login='{login_data.login}'...")
        admin = db.query(AdminORM).filter(AdminORM.login == login_data.login).first()
        
        if not admin:
            print(f" Администратор с логином '{login_data.login}' НЕ НАЙДЕН!")
            print(f"   Доступные логины: {[a.login for a in all_admins]}")
            raise HTTPException(
                status_code=401, 
                detail=f"Неверный логин или пароль. Администратор '{login_data.login}' не существует."
            )
        
        print(f" Администратор найден: ID={admin.id}")
        print(f"   Логин в БД: '{admin.login}'")
        print(f"   Пароль в БД: '{admin.password}'")
        print(f"   Введенный пароль: '{login_data.password}'")
        
        if admin.password != login_data.password:
            print(f" ПАРОЛЬ НЕ СОВПАДАЕТ!")
            print(f"   Ожидалось: '{admin.password}'")
            print(f"   Получено: '{login_data.password}'")
            raise HTTPException(
                status_code=401, 
                detail="Неверный логин или пароль"
            )
        
        print(f" ПАРОЛЬ СОВПАЛ!")
        print(f" УСПЕШНЫЙ ВХОД для администратора '{admin.login}'")
        print("=" * 50 + "\n")
        
        return {
            "message": "Успешный вход",
            "login": admin.login,
            "is_authenticated": True
        }
        
    except HTTPException as he:
        print(f"ОШИБКА АВТОРИЗАЦИИ: {he.detail}")
        print("=" * 50 + "\n")
        raise
    except Exception as e:
        print(f" НЕИЗВЕСТНАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50 + "\n")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@admins_router.post("", response_model=AdminResponse)
def create_admin(admin_data: AdminCreate, db: Session = Depends(get_db)):
    """Создать нового администратора"""
    existing_admin = db.query(AdminORM).filter(AdminORM.login == admin_data.login).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Администратор с таким логином уже существует")
    
    new_admin = AdminORM(
        login=admin_data.login,
        password=admin_data.password
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
user_tokens = {}

@users_router.post("/login", response_model=UserLoginResponse)
def user_login(login_data: UserLoginRequest, db: Session = Depends(get_db)):
    """Вход пользователя"""
    print(f" Попытка входа пользователя: {login_data.login}")
    print(f"Полученные данные: login='{login_data.login}', password='{login_data.password}'")
    
    user = db.query(UserORM).filter(UserORM.login == login_data.login).first()
    
    if not user:
        print(f" Пользователь {login_data.login} не найден")
        return UserLoginResponse(
            success=False,
            message="Пользователь не найден"
        )
    
    print(f" Пользователь найден: ID={user.id}")
    print(f"   Введенный пароль: {login_data.password}")
    print(f"   Пароль в БД: {user.password}")
    
    if user.password != login_data.password:
        print(f" Неверный пароль для пользователя {login_data.login}")
        return UserLoginResponse(
            success=False,
            message="Неверный пароль"
        )
    
    token = secrets.token_hex(32)
    user_tokens[token] = {
        "user_id": user.id,
        "login": user.login,
        "email": user.email,
        "created_at": datetime.now().isoformat()
    }
    
    print(f" Успешный вход для пользователя {user.login}")
    print(f"   Создан токен: {token[:20]}...")
    
    return UserLoginResponse(
        success=True,
        message="Успешный вход",
        token=token,
        user={
            "id": user.id,
            "login": user.login,
            "email": user.email
        }
    )

@users_router.get("/check-token/{token}")
def check_token(token: str):
    """Проверить валидность токена"""
    print(f" Проверка токена: {token[:20]}...")
    
    user_data = user_tokens.get(token)
    if not user_data:
        print(f" Токен не найден или истек")
        return {"valid": False, "message": "Невалидный токен"}
    
    print(f" Токен валиден для пользователя: {user_data['login']}")
    return {
        "valid": True,
        "user": user_data
    }

@users_router.post("/logout")
def user_logout(token: str):
    """Выход пользователя"""
    print(f" Выход пользователя, токен: {token[:20]}...")
    
    if token in user_tokens:
        del user_tokens[token]
        print(f" Токен удален")
    else:
        print(f"Токен не найден при выходе")
    
    return {"success": True, "message": "Успешный выход"}

@users_router.get("/me")
def get_current_user(token: str):
    """Получить информацию о текущем пользователе"""
    user_data = user_tokens.get(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Неавторизованный доступ")
    
    return {
        "success": True,
        "user": user_data
    }

@users_router.get("", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """Получить всех пользователей"""
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

@users_router.get("/orders", response_model=List[dict])
def get_user_orders(
    token: str = Query(..., description="Токен пользователя"),
    db: Session = Depends(get_db)
):
    """Получить заказы пользователя по токену"""
    user_data = user_tokens.get(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Неавторизованный доступ")
    
    user_id = user_data["user_id"]
    
    orders = db.query(OrderORM).filter(
        (OrderORM.user_id == user_id) | (OrderORM.customer_email == user_data["email"])
    ).all()
    
    result = []
    for order in orders:
        items = []
        try:
            items = json.loads(order.items_json) if order.items_json else []
        except:
            items = []
        
        shipments = db.query(ShipmentORM).filter(
            ShipmentORM.order_id == order.id
        ).all()
        
        result.append({
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "delivery_address": order.delivery_address,
            "customer_phone": order.customer_phone,
            "order_comment": order.order_comment,
            "total_amount": order.total_amount,
            "status": order.status,
            "order_date": order.order_date,
            "items": items,
            "shipments": [
                {
                    "id": s.id,
                    "product_id": s.product_id,
                    "product_name": s.product.name if s.product else "Неизвестный товар",
                    "quantity": s.quantity,
                    "status": s.status,
                    "shipment_date": s.shipment_date,
                    "destination": s.destination
                }
                for s in shipments
            ]
        })
    
    return result

@users_router.post("", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Создать нового пользователя"""
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
    
    new_item = OverflowBinORM(
        product_id=item.product_id,
        quantity=item.quantity,
        notes=item.notes,
        date_added=datetime.now()
    )
    
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
        
        if move_data.placement_id:
            placement = db.query(ProductPlacementORM).filter(ProductPlacementORM.id == move_data.placement_id).first()
            if not placement:
                raise HTTPException(status_code=404, detail="Размещение товара не найдено")
            
            if placement.quantity < move_data.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Недостаточно товара на стеллаже. Доступно: {placement.quantity}, запрошено: {move_data.quantity}"
                )
            
            if placement.quantity == move_data.quantity:
                db.delete(placement)
            else:
                placement.quantity -= move_data.quantity
            
            if placement.shelf_id:
                shelf = db.query(ShelfORM).filter(ShelfORM.id == placement.shelf_id).first()
                if shelf:
                    shelf.current_quantity -= move_data.quantity
        
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
    
    new_product = db.query(ProductORM).filter(ProductORM.id == item_update.product_id).first()
    if not new_product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
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
        
        product = db.query(ProductORM).filter(ProductORM.id == placement.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        shelf_name = None
        if placement.shelf_id:
            shelf = db.query(ShelfORM).filter(ShelfORM.id == placement.shelf_id).first()
            if not shelf:
                raise HTTPException(status_code=404, detail="Стеллаж не найден")
            
            free_space = shelf.max_capacity - shelf.current_quantity
            if placement.quantity > free_space:
                raise HTTPException(
                    status_code=400,
                    detail=f"Недостаточно места на стеллаже '{shelf.name}'. Свободно: {free_space}, требуется: {placement.quantity}"
                )
            
            shelf.current_quantity += placement.quantity
            shelf_name = shelf.name
        
        if placement.quantity > product.current_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара '{product.name}' на складе. Доступно: {product.current_quantity}, требуется: {placement.quantity}"
            )
        
        product.current_quantity -= placement.quantity
        
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
        
        product = db.query(ProductORM).filter(ProductORM.id == move_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        shelf = db.query(ShelfORM).filter(ShelfORM.id == move_data.shelf_id).first()
        if not shelf:
            raise HTTPException(status_code=404, detail="Стеллаж не найден")
        
        free_space = shelf.max_capacity - shelf.current_quantity
        if move_data.quantity > free_space:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно места на стеллаже '{shelf.name}'. Свободно: {free_space}, требуется: {move_data.quantity}"
            )
        
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
        
        new_placement = ProductPlacementORM(
            product_id=move_data.product_id,
            shelf_id=move_data.shelf_id,
            quantity=move_data.quantity,
            placement_date=datetime.now(),
            notes=move_data.notes or "Перемещено из отстойника"
        )
        
        shelf.current_quantity += move_data.quantity
        
        if overflow_item.quantity == move_data.quantity:
            db.delete(overflow_item)
        else:
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
        
        product = db.query(ProductORM).filter(ProductORM.id == placement_update.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        old_quantity = placement.quantity
        old_shelf_id = placement.shelf_id
        old_product_id = placement.product_id
        
        if placement_update.quantity > product.current_quantity + old_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара '{product.name}' на складе. Доступно: {product.current_quantity + old_quantity}, требуется: {placement_update.quantity}"
            )
        
        shelf_name = None
        if placement_update.shelf_id:
            shelf = db.query(ShelfORM).filter(ShelfORM.id == placement_update.shelf_id).first()
            if not shelf:
                raise HTTPException(status_code=404, detail="Стеллаж не найден")
            
            if old_shelf_id == placement_update.shelf_id:
                quantity_diff = placement_update.quantity - old_quantity
                free_space = shelf.max_capacity - shelf.current_quantity
                if quantity_diff > free_space:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Недостаточно места на стеллаже '{shelf.name}'. Свободно: {free_space}, требуется дополнительно: {quantity_diff}"
                    )
            else:
                free_space = shelf.max_capacity - shelf.current_quantity
                if placement_update.quantity > free_space:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Недостаточно места на стеллаже '{shelf.name}'. Свободно: {free_space}, требуется: {placement_update.quantity}"
                    )
            
            shelf_name = shelf.name
        
        old_product = db.query(ProductORM).filter(ProductORM.id == old_product_id).first()
        if old_product:
            old_product.current_quantity += old_quantity
        
        if old_shelf_id:
            old_shelf = db.query(ShelfORM).filter(ShelfORM.id == old_shelf_id).first()
            if old_shelf:
                old_shelf.current_quantity = max(0, old_shelf.current_quantity - old_quantity)
        
        product.current_quantity -= placement_update.quantity
        
        if placement_update.shelf_id:
            shelf.current_quantity += placement_update.quantity
        
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
        
        product = db.query(ProductORM).filter(ProductORM.id == placement.product_id).first()
        if product:
            product.current_quantity += placement.quantity
        
        if placement.shelf_id:
            shelf = db.query(ShelfORM).filter(ShelfORM.id == placement.shelf_id).first()
            if shelf:
                shelf.current_quantity = max(0, shelf.current_quantity - placement.quantity)
        
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
def get_shipments(
    user_email: Optional[str] = Query(None, description="Фильтр по email пользователя"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    order_number: Optional[str] = Query(None, description="Фильтр по номеру заказа"),
    db: Session = Depends(get_db)
):
    """Получить все отгрузки с возможностью фильтрации"""
    
    query = db.query(ShipmentORM)
    
    if user_email:
        query = query.filter(ShipmentORM.customer_email == user_email)
    
    if status:
        query = query.filter(ShipmentORM.status == status)
    
    if order_number:
        query = query.filter(ShipmentORM.order_number == order_number)
    
    shipments = query.order_by(ShipmentORM.shipment_date.desc()).all()
    
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
            "customer_email": shipment.customer_email,
            "order_number": shipment.order_number,
            "status": shipment.status,
            "shipment_date": shipment.shipment_date,
            "user_id": shipment.user_id,
            "order_id": shipment.order_id,
            "product_name": product_name
        })
    
    return result

@shipments_router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    """Получить отгрузку по ID"""
    shipment = db.query(ShipmentORM).filter(ShipmentORM.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Отгрузка не найдена")
    
    product = db.query(ProductORM).filter(ProductORM.id == shipment.product_id).first()
    product_name = product.name if product else "Неизвестный товар"
    
    return {
        "id": shipment.id,
        "product_id": shipment.product_id,
        "quantity": shipment.quantity,
        "destination": shipment.destination,
        "customer": shipment.customer,
        "customer_email": shipment.customer_email,
        "order_number": shipment.order_number,
        "status": shipment.status,
        "shipment_date": shipment.shipment_date,
        "user_id": shipment.user_id,
        "order_id": shipment.order_id,
        "product_name": product_name
    }

@shipments_router.patch("/{shipment_id}/status")
def update_shipment_status(
    shipment_id: int,
    status_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Обновить только статус отгрузки"""
    shipment = db.query(ShipmentORM).filter(ShipmentORM.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Отгрузка не найдена")
    
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Статус не указан")
    
    valid_statuses = ["pending", "processing", "completed", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Неверный статус. Допустимые: {', '.join(valid_statuses)}")
    
    shipment.status = new_status
    db.commit()
    
    return {
        "success": True,
        "message": "Статус обновлен",
        "shipment_id": shipment_id,
        "new_status": new_status
    }

@shipments_router.get("/user/{user_email}", response_model=List[ShipmentResponse])
def get_shipments_by_user(
    user_email: str,
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db)
):
    """Получить отгрузки по email пользователя"""
    
    query = db.query(ShipmentORM).filter(ShipmentORM.customer_email == user_email)
    
    if status:
        query = query.filter(ShipmentORM.status == status)
    
    shipments = query.order_by(ShipmentORM.shipment_date.desc()).all()
    
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
            "customer_email": shipment.customer_email,
            "order_number": shipment.order_number,
            "status": shipment.status,
            "shipment_date": shipment.shipment_date,
            "user_id": shipment.user_id,
            "order_id": shipment.order_id,
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

@shipments_router.put("/{shipment_id}", response_model=ShipmentResponse)
def update_shipment(
    shipment_id: int,
    shipment_update: ShipmentBase,
    db: Session = Depends(get_db)
):
    """Обновить отгрузку"""
    print(f"Обновление отгрузки {shipment_id}: {shipment_update.dict()}")
    
    shipment = db.query(ShipmentORM).filter(ShipmentORM.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Отгрузка не найдена")
    
    product = db.query(ProductORM).filter(ProductORM.id == shipment_update.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Проверяем изменение количества
    if shipment_update.quantity != shipment.quantity:
        print(f"Изменение количества: было {shipment.quantity}, стало {shipment_update.quantity}")
        
        # Возвращаем старое количество на склад
        old_product = db.query(ProductORM).filter(ProductORM.id == shipment.product_id).first()
        if old_product:
            old_product.current_quantity += shipment.quantity
            print(f"Вернули на склад {shipment.quantity} товара {old_product.name}")
        
        # Проверяем доступность нового количества
        if shipment_update.quantity > product.current_quantity:
            print(f"Недостаточно товара: требуется {shipment_update.quantity}, доступно {product.current_quantity}")
            if old_product:
                old_product.current_quantity -= shipment.quantity
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара '{product.name}'. Доступно: {product.current_quantity}, требуется: {shipment_update.quantity}"
            )
        
        # Вычитаем новое количество
        product.current_quantity -= shipment_update.quantity
        print(f"Вычли со склада {shipment_update.quantity} товара {product.name}")
    
    # Обновляем отгрузку
    shipment.product_id = shipment_update.product_id
    shipment.quantity = shipment_update.quantity
    shipment.destination = shipment_update.destination
    shipment.customer = shipment_update.customer
    shipment.order_number = shipment_update.order_number
    shipment.status = shipment_update.status
    
    db.commit()
    db.refresh(shipment)
    
    print(f"Отгрузка {shipment_id} обновлена успешно")
    
    return {
        "id": shipment.id,
        "product_id": shipment.product_id,
        "quantity": shipment.quantity,
        "destination": shipment.destination,
        "customer": shipment.customer,
        "order_number": shipment.order_number,
        "status": shipment.status,
        "shipment_date": shipment.shipment_date,
        "product_name": product.name
    }

@shipments_router.delete("/{shipment_id}", response_model=dict)
def delete_shipment(shipment_id: int, db: Session = Depends(get_db)):
    """Удалить отгрузку"""
    shipment = db.query(ShipmentORM).filter(ShipmentORM.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Отгрузка не найдена")
    
    product = db.query(ProductORM).filter(ProductORM.id == shipment.product_id).first()
    if product:
        product.current_quantity += shipment.quantity
    
    db.delete(shipment)
    db.commit()
    
    return {
        "message": "Отгрузка удалена",
        "deleted_id": shipment_id,
        "product_id": shipment.product_id,
        "quantity_returned": shipment.quantity
    }

@app.post("/api/orders", response_model=OrderResponse)
def create_customer_order(
    order: OrderCreate, 
    db: Session = Depends(get_db)
):
    """Создать заказ клиента с привязкой к пользователю"""
    try:
        print(f"Создание заказа для: {order.customer_email}")
        print(f"Товары: {order.items}")
        
        user_id = None
        if order.user_token:
            print(f"Проверяем токен: {order.user_token[:20]}...")
            user_data = user_tokens.get(order.user_token)
            if user_data:
                user_id = user_data["user_id"]
                print(f"Найден пользователь ID: {user_id}")
                order.customer_email = user_data["email"]
        
        order_number = f"ORDER_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for item in order.items:
            product = db.query(ProductORM).filter(ProductORM.id == item.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Товар с ID {item.product_id} не найден"
                )
            
            if product.current_quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Недостаточно товара '{product.name}'. В наличии: {product.current_quantity}, требуется: {item.quantity}"
                )
        
        new_order = OrderORM(
            order_number=order_number,
            user_id=user_id,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            delivery_address=order.delivery_address,
            customer_phone=order.customer_phone,
            order_comment=order.order_comment,
            total_amount=order.total_amount,
            status="pending",
            items_json=json.dumps([item.dict() for item in order.items])
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        for item in order.items:
            product = db.query(ProductORM).filter(ProductORM.id == item.product_id).first()
            
            shipment = ShipmentORM(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                destination=order.delivery_address,
                customer=order.customer_name,
                customer_email=order.customer_email,
                order_number=order_number,
                status='pending',
                user_id=user_id
            )
            db.add(shipment)
        
        db.commit()
        
        print(f"Заказ успешно создан: {order_number}")
        
        return {
            "id": new_order.id,
            "order_number": order_number,
            "customer_name": new_order.customer_name,
            "customer_email": new_order.customer_email,
            "delivery_address": new_order.delivery_address,
            "customer_phone": new_order.customer_phone,
            "order_comment": new_order.order_comment,
            "total_amount": new_order.total_amount,
            "status": new_order.status,
            "order_date": new_order.order_date,
            "items": order.items,
            "user_token": order.user_token
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Ошибка создания заказа: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка создания заказа: {str(e)}"
        )

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

# ===== ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ ДЛЯ МАГАЗИНА =====
shop_router = APIRouter(prefix="/shop", tags=["Магазин"])

@app.get("/api/products/shop", response_model=List[ProductResponse])
def get_products_for_shop(
    category_id: Optional[int] = Query(None, description="Фильтр по категории"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    include_low_stock: Optional[bool] = Query(None, description="Включать товары с низким запасом"),
    db: Session = Depends(get_db)
):
    """Получить товары для магазина с поиском"""
    query = db.query(ProductORM)
    
    if category_id and category_id > 0:
        query = query.filter(ProductORM.category_id == category_id)
    
    if search:
        query = query.filter(ProductORM.name.ilike(f"%{search}%"))
    
    products = query.all()
    
    result = []
    for product in products:
        category = db.query(CategoryORM).filter(CategoryORM.id == product.category_id).first()
        category_name = category.name if category else "Без категории"
        
        is_low_stock = product.current_quantity <= product.min_quantity
        
        if include_low_stock is False and is_low_stock:
            continue
        
        result.append({
            "id": product.id,
            "name": product.name,
            "category_id": product.category_id,
            "category_name": category_name,
            "min_quantity": product.min_quantity,
            "unit": product.unit,
            "description": product.description,
            "price": product.price,
            "current_quantity": product.current_quantity,
            "is_low_stock": is_low_stock,
            "stock_percentage": min(100, (product.current_quantity / (product.min_quantity or 1)) * 100)
        })
    
    return result

@app.get("/api/categories/shop", response_model=List[CategoryResponse])
def get_categories_for_shop(db: Session = Depends(get_db)):
    """Получить категории для магазина"""
    categories = db.query(CategoryORM).all()
    result = []
    for category in categories:
        product_count = db.query(ProductORM).filter(ProductORM.category_id == category.id).count()
        if product_count > 0:
            result.append({
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "product_count": product_count
            })
    return result

# ===== КОРЗИНА С ПРОВЕРКОЙ АУТЕНТИФИКАЦИИ =====

class CartItemRequest(BaseModel):
    product_id: int
    quantity: int = 1

@users_router.post("/cart/add")
def add_to_cart(
    cart_item: CartItemRequest,
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавить товар в корзину пользователя"""
    user_id = user_data["user_id"]
    
    product = db.query(ProductORM).filter(ProductORM.id == cart_item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    if product.current_quantity < cart_item.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно товара. В наличии: {product.current_quantity}"
        )
    
    return {
        "success": True,
        "message": "Товар добавлен в корзину",
        "product": {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": cart_item.quantity
        }
    }

@users_router.get("/cart")
def get_cart(user_data: dict = Depends(get_current_user)):
    """Получить корзину пользователя"""
    return {
        "success": True,
        "cart": []
    }

# ===== ПОДКЛЮЧЕНИЕ ВСЕХ РОУТЕРОВ =====

app.include_router(admins_router)  # ПЕРВЫЙ И ВАЖНЫЙ!
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
app.include_router(shop_router)

if __name__ == "__main__":
    uvicorn.run(app)