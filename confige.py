import os
class Setting():
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-production-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = os.getenv("DATABASE_URL","postgresql://admin:secret@localhost:5433/ecommerce")

    REDIS_URL: str = os.getenv("REDIS_URL","redis://localhost:6379/0")


    KHALTI_SECRET_KEY: str = os.getenv("KHALTI_SECRET_KEY","super-secret-khalti-key")
    KHALTI_INITIATE_URL: str = "https://khalti.com"
    KHALTI_VERIFY_URL: str = "https://khalti.com"

settings = Setting()




