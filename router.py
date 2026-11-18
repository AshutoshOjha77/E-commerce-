from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Query, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from databases import get_db
from confige import settings
import models
import json
import schemass
import securitye
from elastic_client import get_elasticsearch
from payment import KhaltiGateway
from typing import Optional, List
from redis_client import get_redis

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Interceptors that unpack the Authorization access header tokens to confirm identity blocks."""
    payload = securitye.verify_token(token, expected_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token payload claims missing user reference pointers.")
    return int(user_id)

@router.get("/api/products",)
# =========================================================================
# 👤 USER REGISTRATION & MULTI-TOKEN AUTH LIFECYCLES
# =========================================================================
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: schemass.UserRegister, db: Session = Depends(get_db)):
    username_clean = user_data.username.strip().lower()
    email_clean = user_data.email.strip().lower()

    if db.query(models.User).filter((models.User.email == email_clean) | (models.User.username == username_clean)).first():
        raise HTTPException(status_code=400, detail="Account username or registration email already in use.")

    new_user = models.User(
        username=username_clean,
        email=email_clean,
        phone=user_data.phone.strip(),
        hashed_password=securitye.hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    return {"message": f"User account '{username_clean}' registered successfully!"}

@router.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    input_clean = form_data.username.strip().lower()

    user = db.query(models.User).filter(
        (models.User.email == input_clean) | (models.User.username == input_clean)
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials."
        )

    if not securitye.verify_password(form_data.password, user.hashed_password):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials."
        )

    access = securitye.create_access_token({"sub": str(user.id)})
    refresh = securitye.create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )

    return {
        "access_token": access,
        "token_type": "bearer"
    }
@router.post("/refresh")
def refresh_session(refresh_token: Optional[str] = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Secure session token tracking cookie missing.")
    payload = securitye.verify_token(refresh_token, expected_type="refresh")
    new_access = securitye.create_access_token({"sub": payload.get("sub")})
    return {"access_token": new_access, "token_type": "bearer"}


@router.get("/me")
def read_profile(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone
    }

@router.post("/logout")
def logout(response: Response, refresh_token: Optional[str] = Cookie(None)):
    if refresh_token:
        securitye.blacklist_token(refresh_token)
    response.delete_cookie(key="refresh_token", httponly=True, secure=False, samesite="lax")
    return {"message": "Logged out and closed active authorization cycles successfully."}

# STORE CATALOG PRODUCT MANAGEMENT ROUTERS

# @router.post("/products", response_model=schemass.ProductResponse, status_code=status.HTTP_201_CREATED)
# async def add_products(payload: schemass.ProductCreate, db: Session = Depends(get_db), current_user: int = Depends(get_current_user_id)):
#     new_item = models.Product(name=payload.name.strip(), price_rs=payload.price_rs, stock=payload.stock)
#     db.add(new_item)
#     db.commit()
#     db.refresh(new_item)
#     r = get_redis()
#     await r.delete("catalog:Products")
#     return new_item

@router.post("/products", response_model=schemass.ProductResponse, status_code=status.HTTP_201_CREATED)
async def add_products(payload: schemass.ProductCreate, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    user = db.query(models.User).filter(models.User.id == current_user_id).first() 

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not Found")

    if user.role!= "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can add the products")
    new_item = models.Product(name=payload.name, price_rs=payload.price_rs, stock=payload.stock)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    es= get_elasticsearch()
    await es.index(index="products", id=str(new_item.id), document={
        "id":new_item.id,
        "name": new_item.name,
        "price_rs": new_item.price_rs,
        "stock": new_item.stock
    })
    r = get_redis()
    await r.delete("catalog:Products")
    return new_item

@router.get("/api/products/search")
async def search_query(q:str):
    if not q or not q.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Search is required")
    es = get_elasticsearch()
    query_body = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["name"],
                "fuzziness": "AUTO"
            }
        }
    }
    response = await es.search(index="products", body=query_body)
    results = []
    for hit in response["hits"]["hits"]:
        results.append(hit["_source"])

    return {
        "query": q,
        "total": response["hits"]["total"]["value"],
        "results": results
    }

@router.put("/products/update", response_model=schemass.ProductResponse)
async def update_products(product_id: int, payload: schemass.ProductCreate, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):

    user = db.query(models.User).filter(models.User.id == current_user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not Found")
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update the products")
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product of this id is not found")

    product.name = payload.name.strip()
    product.price_rs = payload.price_rs
    product.stock = payload.stock
    db.commit()
    db.refresh(product)

    es = get_elasticsearch()

    await es.index(index="products", id=str(product.id),
                   document={
                       "id": product.id,
                       "name": product.name,
                       "price_rs": product.price_rs,
                       "stock": product.stock

                   })
    r = get_redis()
    await r.delete("catalog:Products")
    return product

@router.delete("/product/delete", response_model=schemass.ProductResponse)
async def delete_product(product_id: int, payload: schemass.ProductCreate,db: Session = Depends(get_db), current_user_id:int = Depends(get_current_user_id) ):
    user = db.query(models.User).filter(models.User.id == current_user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete the products")
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db.delete(product)
    db.commit()

    es = get_elasticsearch()
    try:
        await es.delete(index="products", id= str(product_id))
    except Exception:
        pass

    r = get_redis()
    await r.delete("catalog:Products")
    return {"message": f"Product of id  {product_id} is deleted seccessfully"}


# @router.get("/api/products", response_model=List[schemass.ProductResponse])
# async def get_catalog(db: Session = Depends(get_db)):
#     r = get_redis()
#     cache_key = "catalog:products"
#     cached_data = await r.get(cache_key)

#     if cached_data:
#         products = json.loads(cached_data)
#         return products
#     products_from_db = db.query(models.Product).all()

#     product_list = []
#     for p in products_from_db:
#         product_list.append({
#             "id": p.id,
#             "name" : p.name,
#             "price_rs" : p.price_rs,
#             "stock" : p.stock
#         })
#     await r.setex(cache_key, 300, json.dumps(product_list))

#     return product_list
@router.get("/api/products", response_model=List[schemass.ProductResponse])
async def get_products(db: Session = Depends(get_db)):
    r = get_redis
    cache_key = "catalog:Products"
    cached_data = await r.get(cache_key)
    if cache_key:
        products = json.loads(cached_data)
        return products
    products_from_db = db.query(models.Product).all()
    product_list= []
    for p in products_from_db:
        product_list.append({
            "id": p.id,
            "name": p.name,
            "price_rs": p.price_rs,
            "stock": p.stock
        })
    await r.setex(cache_key, 300, json.dumps(product_list))
    return product_list





# =========================================================================
# 🛒 TRANSACTION STAGING FLOW & KHALTI WEBHOOK CALL BACKS
# =========================================================================
@router.post("/api/checkout")
async def secure_checkout(
    payload: schemass.OrderCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    # 1. Get product
    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Target product not found in database catalog.")

    # 2. Check stock
    if product.stock < payload.quantity:  # type: ignore
        raise HTTPException(status_code=400, detail="Insufficient item inventory levels to process purchase.")

    # 3. Get user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 4. Calculate total
    total_cost: float = product.price_rs * payload.quantity  # type: ignore

    # 5. Create order
    new_order = models.Order(
        user_id=user_id,
        product_id=product.id,  # type: ignore
        quantity=payload.quantity,
        total_amount=total_cost,
        payment_status="PENDING"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # 6. Call Khalti
    payment_session = await KhaltiGateway.initiate_payment(
        purchase_order_id=str(new_order.id),
        amount_rs=total_cost,
        customer_email=user.email,      # type: ignore
        customer_phone=str(user.phone)  # type: ignore
    )

    if "error" in payment_session:
        raise HTTPException(status_code=502, detail=payment_session["error"])

    # 7. Save pidx
    new_order.khalti_pidx = payment_session["pidx"]  # type: ignore
    db.commit()

    return {
        "order_id": new_order.id,
        "khalti_pidx": new_order.khalti_pidx,
        "payment_url": payment_session["payment_url"]
    }

@router.get("/api/payment/verify-callback")
async def verification_callback(
        pidx: str = Query(...),
        purchase_order_id: int = Query(...),
        db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(models.Order.id == purchase_order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    khalti_status = await KhaltiGateway.verify_payment(pidx)

    if khalti_status.get("status") == "Completed":
        product = db.query(models.Product).filter(models.Product.id == order.product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        if product.stock >= order.quantity:  # type: ignore
            product.stock -= order.quantity  # type: ignore
            order.payment_status = "COMPLETED"  # type: ignore
            db.commit()
            return {
                "status": "SUCCESS",
                "message": "Khalti cleared transaction successfully. Stock updated."
            }
        else:
            order.payment_status = "FAILED"  # type: ignore
            db.commit()
            raise HTTPException(status_code=400, detail="Insufficient stock to complete the order")

    order.payment_status = "FAILED"  # type: ignore
    db.commit()
    raise HTTPException(
        status_code=400,
        detail="Transaction validation declined by payment gateway provider"
    )

