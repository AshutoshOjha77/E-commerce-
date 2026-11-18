from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    email :EmailStr
    username: str = Field(...,min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$",
                           description="The userame must atleast have 3 characters and maximum of 20 characters no special characters except underscore(_)")
    password: str = Field(..., min_length=6,
                description="The password should atleast have 6 characters")
    phone: str = Field(...,pattern=r"^(98|97)\d{8}$",
                       description="Must be a valid 10-digit Nepalese mobile carrier line number.")
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2)
    price_rs: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

class ProductResponse(BaseModel):
    id: int
    name: str
    price_rs : float
    stock: int 

    class confige:
        from_attributes = True

class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(...,gt=0)

class OrderResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    total_amount: float
    payment_status: str
    khalti_pidx: Optional[str] = None

    class confige:
        from_attributes = True


