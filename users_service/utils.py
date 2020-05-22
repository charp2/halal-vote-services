# standard python imports
from hashlib import sha256
from secrets import token_hex
import logging
import time
import datetime

# logging config
logger = logging.getLogger()

def create_hashed_password(password: str, salt: str):
    salted_password = password + salt
    return sha256(str.encode(salted_password)).hexdigest()

def generate_error_response(status_code: int, error_msg: str):
    logger.error(error_msg)
    return status_code, error_msg

def generate_success_response(msg: str):
    logger.info(msg)
    return 200, msg

def create_session():
    session_token = token_hex(10)
    ts = time.time()
    session_timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return session_token, session_timestamp
