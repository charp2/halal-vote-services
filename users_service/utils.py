# standard python imports
from hashlib import sha256
from secrets import token_hex
import time
from datetime import datetime

# our imports
from utils import generate_timestamp

def create_hashed_password(password: str, salt: str):
    salted_password = password + salt
    return sha256(str.encode(salted_password)).hexdigest()

def create_session():
    session_token = token_hex(10)
    session_timestamp = generate_timestamp()
    return session_token, session_timestamp
