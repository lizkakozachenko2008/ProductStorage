from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import Optional, Annotated
from datetime import datetime

PasswordType = Annotated[str, Field(min_length=8, max_length=15)]

# User DTOs
class UserBaseDTO(BaseModel):
    email: EmailStr
    login: Annotated[str, Field(max_length=100)]

class UserCreateDTO(UserBaseDTO):
    password: PasswordType
    confirm_password: PasswordType

class UserDTO(UserBaseDTO):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Admin DTOs
class AdminBaseDTO(BaseModel):
    login: Annotated[str, Field(max_length=100)]

class AdminCreateDTO(AdminBaseDTO):
    password: PasswordType
    confirm_password: PasswordType

class AdminDTO(AdminBaseDTO):
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

# Product DTOs
class ProductBaseDTO(BaseModel):
    name: Annotated[str, Field(max_length=200)]
    category_id: int
    min_quantity: int = 0
    unit: Annotated[str, Field(max_length=50)]
    description: Optional[str] = None
    current_quantity: int = 0
    price: Optional[float] = None

class ProductCreateDTO(ProductBaseDTO):
    pass

class ProductDTO(ProductBaseDTO):
    id: int
    model_config = ConfigDict(from_attributes=True)

# OverflowBin DTOs
class OverflowBinBaseDTO(BaseModel):
    product_id: int
    quantity: int = 0

class OverflowBinCreateDTO(OverflowBinBaseDTO):
    pass

class OverflowBinDTO(OverflowBinBaseDTO):
    id: int
    date_added: datetime
    model_config = ConfigDict(from_attributes=True)

# PurchaseOrder DTOs
class PurchaseOrderBaseDTO(BaseModel):
    product_id: int
    quantity: int = 0
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
    max_capacity: int
    current_quantity: int = 0

class ShelfCreateDTO(ShelfBaseDTO):
    pass

class ShelfDTO(ShelfBaseDTO):
    id: int
    model_config = ConfigDict(from_attributes=True)

# MovementHistory DTOs
class MovementHistoryBaseDTO(BaseModel):
    product_id: int
    from_shelf_id: Optional[int] = None
    to_shelf_id: Optional[int] = None
    from_overflow: bool = False
    to_overflow: bool = False
    quantity: int = 0

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
    quantity: int = 0

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
    quantity: int
    status: Annotated[str, Field(max_length=50)] = 'delivered'

class SupplyCreateDTO(SupplyBaseDTO):
    pass

class SupplyDTO(SupplyBaseDTO):
    id: int
    supply_date: datetime
    model_config = ConfigDict(from_attributes=True)