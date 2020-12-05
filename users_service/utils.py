# standard python imports
from hashlib import sha256
from secrets import token_hex
import time
from datetime import datetime
import requests

# our imports
from utils import generate_timestamp

def create_hashed_password(password: str, salt: str):
    salted_password = password + salt
    return sha256(str.encode(salted_password)).hexdigest()

def create_session():
    session_token = token_hex(10)
    session_timestamp = generate_timestamp()
    return session_token, session_timestamp

def get_user_location(ip_address: str):
    # response = requests.get("http://extreme-ip-lookup.com/json/" + ip_address, timeout=5)
    # if response.status_code == 200:
    #     content = response.json()
    #     return {"latitude": content["lat"], "longitude": content["lon"]}
    # else:
    #     return None
    return {"latitude": None, "longitude": None}
