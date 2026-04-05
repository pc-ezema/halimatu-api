import hashlib
import hmac
import json
import secrets
from datetime import datetime
from typing import Dict, Optional, Any
import requests
from sqlalchemy.orm import Session
from app.config.settings import settings

class FlutterwaveService:
    """Flutterwave payment gateway integration - Inline Mode"""
    
    def __init__(self):
        self.public_key = settings.flutterwave_public_key
        self.secret_key = settings.flutterwave_secret_key
        self.production = settings.flutterwave_production
        self.base_url = "https://api.flutterwave.com/v3"
        
    def generate_transaction_reference(self) -> str:
        """Generate unique transaction reference"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = secrets.token_hex(4).upper()
        return f"HALIMATU-{timestamp}-{random_str}"
    
    def initialize_payment(self, user_email: str, amount: float, tx_ref: str,
                          user_name: str = None, user_phone: str = None) -> Dict:
        """
        Initialize payment - returns payment link for standard mode
        For inline mode, we don't call this - frontend handles it directly
        """
        # This is kept for reference but inline mode is handled by frontend
        pass
    
    def verify_payment(self, tx_ref: str) -> Dict:
        """
        Verify payment status using transaction reference (Server-side)
        Always do this after payment completes
        """
        try:
            url = f"{self.base_url}/transactions/verify_by_reference?tx_ref={tx_ref}"
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if result.get("status") == "success":
                data = result.get("data", {})
                return {
                    "status": "success",
                    "message": "Payment verified successfully",
                    "tx_ref": tx_ref,
                    "amount": data.get("amount"),
                    "currency": data.get("currency"),
                    "flw_ref": data.get("flw_ref"),
                    "transaction_id": data.get("id"),
                    "customer": data.get("customer", {}),
                    "data": data
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "Verification failed"),
                    "tx_ref": tx_ref
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "tx_ref": tx_ref
            }
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature to ensure request is from Flutterwave"""
        try:
            expected_signature = hmac.new(
                settings.flutterwave_webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha512
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False

# Create singleton instance
flutterwave = FlutterwaveService()