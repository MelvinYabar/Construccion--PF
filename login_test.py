import requests

SUPABASE_URL = "https://epxuvpkzhtnutupfrcnl.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVweHV2cGt6aHRudXR1cGZyY25sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg4MTA4OTMsImV4cCI6MjA5NDM4Njg5M30.TL8Iune8ceWTsnWAMYP-IFYKWj2H9DnFTqoQApnvLOs"

email = "emprendedor@test.com"
password = "Emprendedor123$"

url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"

headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Content-Type": "application/json"
}

data = {
    "email": email,
    "password": password
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.json())

if response.status_code == 200:
    print("\nACCESS TOKEN:\n")
    print(response.json()["access_token"])