# standard python imports
from hashlib import sha256
from secrets import token_hex
import time
import datetime

def create_hashed_password(password: str, salt: str):
    salted_password = password + salt
    return sha256(str.encode(salted_password)).hexdigest()

def create_session():
    session_token = token_hex(10)
    ts = time.time()
    session_timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return session_token, session_timestamp
