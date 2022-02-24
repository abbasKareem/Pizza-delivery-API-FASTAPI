from fastapi import FastAPI
from auth_routes import auth_rotuer
from order_routes import order_router
from fastapi_jwt_auth import AuthJWT
from schemas import Settings


app = FastAPI()


@AuthJWT.load_config
def get_config():
    return Settings()


app.include_router(auth_rotuer)
app.include_router(order_router)

# sudo lsof -i :8000
#  sudo kill -9 1787
