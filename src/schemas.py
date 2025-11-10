from typing import Annotated
from pydantic import ConfigDict, EmailStr, BaseModel, Field

PasswordType = Annotated[str, Field(min_length=8, max_length=64)]

class UserBaseDTO(BaseModel):
    email: EmailStr
    login: Annotated[str, Field(max_length=100)]

class UserCreateDTO(UserBaseDTO):
    password: PasswordType
    confirm_password: PasswordType

class UserDTO(UserBaseDTO):
    model_config = ConfigDict(from_attributes=True)