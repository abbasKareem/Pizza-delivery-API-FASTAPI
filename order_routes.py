from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi_jwt_auth import AuthJWT
from models import User, Order
from schemas import OrderModel, OrderStatusModel
from database import Session, engine
from fastapi.encoders import jsonable_encoder

from response import success_response
order_router = APIRouter(
    prefix='/orders',
    tags=['orders']
)

session = Session(bind=engine)


@order_router.get('/')
async def hello(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    return {"message": "Hello World"}


# =======================Order routes ===================
@order_router.post('/order')
async def place_an_order(order: OrderModel, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    current_user = Authorize.get_jwt_subject()

    user = session.query(User).filter(User.username == current_user).first()

    new_order = Order(
        pizza_size=order.pizza_size,
        quantity=order.quantity,
    )

    new_order.user = user
    session.add(new_order)
    session.commit()

    response = {
        "data": {
            "pizza_size": new_order.pizza_size,
            "quantity": new_order.quantity,
            "id": new_order.id,
        },
        "status_code": 201,
        "message": "Order Placed Successfully"
    },

    return jsonable_encoder(response)


# =======================All Orders routes ===================
@order_router.get('/orders')
async def list_all_orders(page_num: int = 1, page_size: int = 5, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    current_user = Authorize.get_jwt_subject()
    user = session.query(User).filter(User.username == current_user).first()
    if user.is_staff:
        orders = session.query(Order).all()
        orders_length = len(orders)

        start = (page_num - 1) * page_size
        end = start + page_size
        response = {
            "data": orders[start:end],
            "total": orders_length,
            "count": page_size,
            "pagination": {},

            "status_code": 200,
            "message": "Orders list Successfully"
        }
        if end >= orders_length:
            response["pagination"]["next"] = None

            if page_num > 1:
                response["pagination"][
                    "previous"] = f"/orders/orders?page_num={page_num-1}&page_size={page_size}"
            else:
                response["pagination"]["previous"] = None
        else:
            if page_num > 1:
                response["pagination"][
                    "previous"] = f"/orders/orders?page_num={page_num-1}&page_size={page_size}"
            else:
                response["pagination"]["previous"] = None

            response["pagination"]["next"] = f"/orders/orders?page_num={page_num+1}&page_size={page_size}"

        return jsonable_encoder(response)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You are not a superuser")

# =======================Get Single Orederroutes ===================


@order_router.get('/orders/{id}')
async def get_order_by_id(id: int, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    user = Authorize.get_jwt_subject()

    current_user = session.query(User).filter(User.username == user).first()

    if current_user.is_staff:
        order = session.query(Order).filter(Order.id == id).first()

        if order:
            return jsonable_encoder(order)
        else:
            response = {
                "data": {},
                "message": "Order with this id not found"
            }
            return jsonable_encoder(response)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not allowed to carry the request")

# =======================Get Single Orederroutes ===================


@order_router.get('/user/orders')
async def get_user_orders(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    user = Authorize.get_jwt_subject()

    current_user = session.query(User).filter(User.username == user).first()

    if current_user.orders:
        response = {
            "data": current_user.orders
        }
        return jsonable_encoder(response)
    else:
        response = {
            "data": {},
            "message": "This user has no orders!"
        }
        return jsonable_encoder(response)
# =======================Get Single Orederroutes ===================


@order_router.get('/user/orders/{id}')
async def get_specific_order(id: int, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    subject = Authorize.get_jwt_subject()
    current_user = session.query(User).filter(User.username == subject).first()

    orders = current_user.orders
    if orders:
        for order in orders:
            if order.id == id:
                return jsonable_encoder(order)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No order with this id")

# =======================Update order routes ===================


@order_router.put('/order/update/{id}')
async def update_order(id: int, order: OrderModel, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    order_to_update = session.query(Order).filter(Order.id == id).first()
    if order_to_update:
        order_to_update.quantity = order.quantity
        order_to_update.pizza_size = order.pizza_size
        session.commit()
        response = {
            "data": {
                "order": order_to_update,
                "message": "Order Updated Successfully"
            }
        }
        return jsonable_encoder(response)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Order not found!")


# =======================Update status order routes ===================
@order_router.patch('/order/update/{id}')
async def update_order_status(id: int, order: OrderStatusModel, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    username = Authorize.get_jwt_subject()
    current_user = session.query(User).filter(
        User.username == username).first()

# Check if user is admin
    if current_user.is_staff:
        order_to_update = session.query(Order).filter(Order.id == id).first()
        # Check if there order found
        if order_to_update:
            order_to_update.order_status = order.order_status
            session.commit()
            response = {
                "data": {
                    "order_status": order_to_update.order_status,
                    "user": order_to_update.user.username,
                    "message": "Order Updated Successfully"
                },
            }
            return jsonable_encoder(response)
        # No order found with given id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Order not found!")
    # User is not admin
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token Not An Admin!")

# =======================Update status order routes ===================


@order_router.delete('/order/delete/{id}')
async def delete_order(id: int, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    order_to_delete = session.query(Order).filter(Order.id == id).first()
    # Check if order found
    if order_to_delete:
        session.delete(order_to_delete)
        session.commit()
        response = {
            "data": {
                "status": 204,
                "order": order_to_delete
            },
        }
        return jsonable_encoder(response)
    # No order found
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No Order Found With This id")
