from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator, validator
from typing import Optional, Annotated, List
from datetime import datetime
from decimal import Decimal

PasswordType = Annotated[str, Field(min_length=8, max_length=15)]

# User DTOs
class UserBaseDTO(BaseModel):
    email: EmailStr
    login: Annotated[str, Field(max_length=100)]

class UserCreateDTO(UserBaseDTO):
    password: PasswordType

class UserDTO(UserCreateDTO):
    model_config = ConfigDict(from_attributes=True)
    id: int

# Admin DTOs
class AdminCreateDTO(BaseModel):
    login: Annotated[str, Field(max_length=100)]
    password: PasswordType

class AdminDTO(AdminCreateDTO):
    model_config = ConfigDict(from_attributes=True)

# Category DTOs
class CategoryBaseDTO(BaseModel):
    name: Annotated[str, Field(max_length=100)]
    description: Optional[str] = None

class CategoryCreateDTO(CategoryBaseDTO):
    pass

class CategoryDTO(CategoryBaseDTO):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Stock DTOs
class StockBaseDTO(BaseModel):
    product_id: int
    total_quantity: int = 0
    reserved_quantity: int = 0

class StockCreateDTO(StockBaseDTO):
    pass

class StockDTO(StockBaseDTO):
    id: int
    available_quantity: int
    last_updated: datetime
    model_config = ConfigDict(from_attributes=True)

# Product DTOs
class ProductBaseDTO(BaseModel):
    name: Annotated[str, Field(max_length=200)]
    category_id: int
    min_quantity: int = 0
    unit: Annotated[str, Field(max_length=50)]
    description: Optional[str] = None
    price: Optional[float] = None
    current_quantity: int = Field(default=0)
    
    @field_validator('current_quantity', mode='before')
    @classmethod
    def set_current_quantity(cls, v, info):
        if v is None and 'stock' in info.data and info.data['stock']:
            return info.data['stock'].available_quantity
        return v or 0

class ProductCreateDTO(ProductBaseDTO):
    pass

class ProductDTO(ProductBaseDTO):
    id: int
    stock: Optional[StockDTO] = None
    
    model_config = ConfigDict(from_attributes=True)

# OverflowBin DTOs
class OverflowBinBaseDTO(BaseModel):
    product_id: int
    quantity: int = Field(ge=0)

class OverflowBinCreateDTO(OverflowBinBaseDTO):
    pass

class OverflowBinDTO(OverflowBinBaseDTO):
    id: int
    date_added: datetime
    model_config = ConfigDict(from_attributes=True)

# PurchaseOrder DTOs
class PurchaseOrderBaseDTO(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    status: Annotated[str, Field(max_length=50)] = 'pending'

class PurchaseOrderCreateDTO(PurchaseOrderBaseDTO):
    pass

class PurchaseOrderDTO(PurchaseOrderBaseDTO):
    id: int
    order_date: datetime
    created_date: datetime
    model_config = ConfigDict(from_attributes=True)

# Shelf DTOs
class ShelfBaseDTO(BaseModel):
    name: Annotated[str, Field(max_length=100)]
    category_id: Optional[int] = None
    max_capacity: int = Field(gt=0)
    current_quantity: int = Field(ge=0, default=0)

class ShelfCreateDTO(ShelfBaseDTO):
    pass

class ShelfDTO(ShelfBaseDTO):
    id: int
    free_space: int = Field(default=0)
    
    @field_validator('free_space', mode='before')
    @classmethod
    def calculate_free_space(cls, v, info):
        if 'max_capacity' in info.data and 'current_quantity' in info.data:
            return info.data['max_capacity'] - info.data['current_quantity']
        return v
    
    model_config = ConfigDict(from_attributes=True)

# MovementHistory DTOs
class MovementHistoryBaseDTO(BaseModel):
    product_id: int
    from_shelf_id: Optional[int] = None
    to_shelf_id: Optional[int] = None
    from_overflow: bool = False
    to_overflow: bool = False
    quantity: int = Field(gt=0)
    movement_type: str = Field(default='placement')

class MovementHistoryCreateDTO(MovementHistoryBaseDTO):
    pass

class MovementHistoryDTO(MovementHistoryBaseDTO):
    id: int
    movement_date: datetime
    model_config = ConfigDict(from_attributes=True)

# Notification DTOs
class NotificationBaseDTO(BaseModel):
    product_id: int
    shelf_id: Optional[int] = None
    message: str
    priority: Annotated[str, Field(max_length=20)] = 'medium'
    notification_type: str = Field(default='info')

class NotificationCreateDTO(NotificationBaseDTO):
    pass

class NotificationDTO(NotificationBaseDTO):
    id: int
    is_read: bool = False
    created_date: datetime
    model_config = ConfigDict(from_attributes=True)

# ProductPlacement DTOs
class ProductPlacementBaseDTO(BaseModel):
    product_id: int
    shelf_id: Optional[int] = None
    overflow_id: Optional[int] = None
    quantity: int = Field(gt=0)

class ProductPlacementCreateDTO(ProductPlacementBaseDTO):
    pass

class ProductPlacementDTO(ProductPlacementBaseDTO):
    id: int
    placement_date: datetime
    last_updated: datetime
    model_config = ConfigDict(from_attributes=True)

# Supply DTOs
class SupplyBaseDTO(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    status: Annotated[str, Field(max_length=50)] = 'delivered'
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None

class SupplyCreateDTO(SupplyBaseDTO):
    pass

class SupplyDTO(SupplyBaseDTO):
    id: int
    supply_date: datetime
    model_config = ConfigDict(from_attributes=True)


# Shipment DTOs
class ShipmentBaseDTO(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    destination: str = Field(max_length=200)
    customer: Optional[str] = None
    order_number: Optional[str] = None
    status: str = Field(default='completed')

class ShipmentCreateDTO(ShipmentBaseDTO):
    pass

class ShipmentDTO(ShipmentBaseDTO):
    id: int
    shipment_date: datetime
    model_config = ConfigDict(from_attributes=True)

# Warehouse Operation DTOs
class ProductPlaceRequestDTO(BaseModel):
    product_id: int = Field(gt=0, description="ID товара")
    shelf_id: Optional[int] = Field(None, gt=0, description="ID стеллажа")
    overflow_id: Optional[int] = Field(None, gt=0, description="ID отстойника")
    quantity: int = Field(gt=0, description="Количество для размещения")
    operation_type: str = Field(default="place", pattern="^(place|reserve)$")

class ShipmentRequestDTO(BaseModel):
    product_id: int = Field(gt=0, description="ID товара")
    quantity: int = Field(gt=0, description="Количество для отгрузки")
    destination: str = Field(..., description="Куда отгружается товар")
    customer: Optional[str] = Field(None, description="Клиент")
    order_number: Optional[str] = Field(None, description="Номер заказа")
    from_shelf_id: Optional[int] = Field(None, gt=0, description="С какого стеллажа отгружать")
    from_overflow: bool = Field(default=False, description="Отгружать из отстойника")

# Report DTOs
class PlacementReportItemDTO(BaseModel):
    product_id: int
    product_name: str
    shelf_id: Optional[int]
    shelf_name: Optional[str]
    overflow_id: Optional[int]
    quantity: int
    total_quantity: int  
    unit: str 
    is_low_stock: bool

class PlacementReportDTO(BaseModel):
    items: List[PlacementReportItemDTO]
    total_products: int
    total_quantity: int
    shelves_used: int
    overflow_used: int
    low_stock_count: int

class MonthlyReportItemDTO(BaseModel):
    date: datetime
    product_id: int
    product_name: str
    type: str 
    quantity: int
    reference_id: int
    details: Optional[str] = None

class MonthlyReportDTO(BaseModel):
    year: int
    month: int
    items: List[MonthlyReportItemDTO]
    total_supplied: int
    total_shipped: int
    net_change: int
    total_transactions: int

class InventoryStatusDTO(BaseModel):
    product_id: int
    product_name: str
    category_id: int
    category_name: str
    current_quantity: int
    min_quantity: int
    unit: str
    is_low_stock: bool
    in_overflow: bool
    overflow_quantity: Optional[int] = None
    placement_count: int
    total_value: Optional[float] = None

class InventoryReportDTO(BaseModel):
    summary: dict
    products: List[InventoryStatusDTO]
    low_stock_items: List[dict]
    overflow_items: List[dict]

# Notification DTOs
class FreeSpaceNotificationDTO(BaseModel):
    shelf_id: int
    shelf_name: str
    product_id: int
    product_name: str
    overflow_bin_id: int
    available_quantity: int 
    shelf_capacity: int
    shelf_current: int
    free_space: int
    can_fit: bool
    fit_percentage: float

class LowStockNotificationDTO(BaseModel):
    product_id: int
    product_name: str
    current_quantity: int
    min_quantity: int
    deficit: int
    unit: str
    is_critical: bool
    message: str

# Response DTOs
class PlacementResponseDTO(BaseModel):
    placement: ProductPlacementDTO
    stock_updated: StockDTO
    shelf_updated: Optional[ShelfDTO] = None
    message: str

class ShipmentResponseDTO(BaseModel):
    shipment: ShipmentDTO
    stock_updated: StockDTO
    shelf_updated: Optional[ShelfDTO] = None
    message: str

class SupplyResponseDTO(BaseModel):
    supply: SupplyDTO
    stock_updated: StockDTO
    message: str

# Statistics DTOs
class StockStatisticsDTO(BaseModel):
    total_products: int
    total_quantity: int
    total_reserved: int
    total_available: int
    total_value: float
    low_stock_count: int
    out_of_stock_count: int
    average_stock_level: float
    stock_turnover_rate: float

class MonthlyStatisticsDTO(BaseModel):
    month: str
    total_supplied: int
    total_shipped: int
    net_change: int
    stock_value_change: float
    most_moved_product: Optional[dict] = None