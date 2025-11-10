from typing import Annotated, TypeVar
from fastapi import Depends
from pydantic import BaseModel
from src.repository import RepoFactory, SqlAlchemyRepository
from src.schemas import UserBaseDTO, UserCreateDTO, UserDTO


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
    return UserService(
        user_repo=RepoFactory.user_repo()
    )

UserServiceType = Annotated[UserService, Depends(user_service)]