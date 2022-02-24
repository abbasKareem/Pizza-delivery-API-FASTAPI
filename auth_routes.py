from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from database import Session, engine
from schemas import SignUpModel, LoginModel
from models import User
from fastapi_jwt_auth import AuthJWT
from fastapi.encoders import jsonable_encoder

# =======================Main routes ===================
auth_rotuer = APIRouter(
    prefix='/auth',
    tags=['auth']
)

session = Session(bind=engine)

# =======================SignUp route ===================


@auth_rotuer.get('/')
async def hello(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {"message": "hlleo"}


@auth_rotuer.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(user: SignUpModel,  Authorize: AuthJWT = Depends()):
    db_email = session.query(User).filter(User.email == user.email).first()
    if db_email is not None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")
    db_username = session.query(User).filter(
        User.username == user.username).first()
    if db_username is not None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already exists")

    access_token = Authorize.create_access_token(subject=user.username)
    refresh_token = Authorize.create_refresh_token(subject=user.username)

    new_user = User(
        username=user.username,
        email=user.email,
        password=generate_password_hash(user.password),
        is_active=user.is_active or True,
        is_staff=user.is_staff or False,
    )

    session.add(new_user)
    session.commit()

    response = {
        "user": {
            "username": user.username,
            "password": user.password,
            "access_token": access_token,
            "refresh_token": refresh_token
        },
        "status_code": 201,
        "details": "User Created Successfully"
    }

    return jsonable_encoder(response)

# =======================Login route ===================


@auth_rotuer.post('/login', status_code=200)
async def login(user: LoginModel, Authorize: AuthJWT = Depends()):
    if not user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="username field is required")
    if not user.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="password field is required")

    db_user = session.query(User).filter(
        User.username == user.username).first()

    if db_user and check_password_hash(db_user.password, user.password):
        access_token = Authorize.create_access_token(subject=db_user.username)
        refresh_token = Authorize.create_refresh_token(
            subject=db_user.username)

        response = {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

        return jsonable_encoder(response)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid username or password")

# =======================Refresh route ===================


@auth_rotuer.get('/refresh')
async def refresh_token(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_refresh_token_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Please provide a valid refresh token")

    currnent_user = Authorize.get_jwt_subject()
    access_token = Authorize.create_access_token(subject=currnent_user)

    return jsonable_encoder({"access": access_token, "user": currnent_user})


#  data = db.query(table_name).\
#         options(load_only("p_key", 'name', 'email')).\ #Return only Specific Column from the table
#         order_by(table_name.p_key)
