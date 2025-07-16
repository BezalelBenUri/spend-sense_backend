# wallet/paystack.py
import requests

from django.conf import settings

def initialize_payment(email, amount, reference):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "amount": int(amount * 100),  # convert to kobo
        "reference": reference
    }
    response = requests.post(url, json = payload, headers=headers)
    return response.json()


def verify_payment(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
    }
    response = requests.get(url, headers = headers)
    print("Paystack Response:", response.json())
    return response.json()