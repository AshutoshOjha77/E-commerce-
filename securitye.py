import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from confige import settings

BLACKLISTED_TOKENS = set()

def hash_password(password: str) ->  str:
    password_bytes = password.encode("utf-8") 
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password:str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes= settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm= settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type":"refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)

def blacklist_token(token: str):
    BLACKLISTED_TOKENS.add(token)

def verify_token(token: str, expected_type: str) -> dict:
    if token in BLACKLISTED_TOKENS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token has been revoked via logout")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type used")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired!")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")
    