from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
from src.setup_db import setup_db
from src.schemas import UserBaseDTO
from src.service import UserServiceType
from src.database import db

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

@app.get("/users")
def get_users(
    user_service: UserServiceType
):
    return user_service.get_all_users()

@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    user_service: UserServiceType
):
    return user_service.get_one_user(user_id)

@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    user: UserBaseDTO,
    user_service: UserServiceType
):
    return user_service.update_user(user_id, user)

@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    user_service: UserServiceType
):
    return user_service.delete_user(user_id)

@app.get('/')
def root():
    return RedirectResponse('/docs')

if __name__ == '__main__':
    uvicorn.run()