import httpx
from confige import settings

class KhaltiGateway:
    """Asynchronous outward gateway client handling Khalti API requests cleanly."""
    
    @staticmethod
    async def initiate_payment(purchase_order_id: str, amount_rs: float, customer_email: str, customer_phone: str) -> dict:
        """Converts float currency to integer Paisa and requests a valid single-use checkout portal link."""
        amount_paisa = int(amount_rs * 100)
        
        headers = {
            "Authorization": settings.KHALTI_SECRET_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "return_url": "http://127.0.0",
            "website_url": "http://127.0.0",
            "amount": amount_paisa,
            "purchase_order_id": str(purchase_order_id),
            "purchase_order_name": f"E store purchase #{purchase_order_id}",
            "customer_info": {
                "name": "E-commerce Customer",
                "email": customer_email,
                "phone": customer_phone 
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.KHALTI_INITIATE_URL, json=payload, headers=headers)
            if response.status_code != 200:
                return {"error": "Failed to communicate securely with the Khalti API network stack."}
            return response.json()

    @staticmethod
    async def verify_payment(pidx: str) -> dict:
        """Queries Khalti's lookup server to confirm the status of a specific payment reference index code."""
        headers = {
            "Authorization": settings.KHALTI_SECRET_KEY,
            "Content-Type": "application/json"
        }
        payload = {"pidx": pidx}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.KHALTI_VERIFY_URL, json=payload, headers=headers)
            return response.json()






