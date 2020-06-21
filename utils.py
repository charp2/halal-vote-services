# standard python imports
import logging
import time
from datetime import datetime, timedelta

# logging config
logger = logging.getLogger()

# response headers
response_headers = {'Access-Control-Allow-Origin': '*'}

def valid_user(username: str, session_token: str, conn, logger):
    if not username:
        return generate_error_response(500, "Invalid username passed in")

    if not session_token:
        return generate_error_response(500, "Invalid sessionToken passed in")

    try:
        with conn.cursor() as cur:
            cur.execute("select sessionToken, sessionTimestamp, activeStatus from Users where username=%(username)s", {'username': username})
            results = cur.fetchone()
            conn.commit()

            if results:
                retrieved_session_token, session_timestamp, active_status = results
            else:
                return generate_error_response(404, "User not found")

            if active_status != "ACTIVE":
                return generate_error_response(403, "User is Not ACTIVE")
            elif session_token != retrieved_session_token:
                return generate_error_response(401, "User Not Authorized")
            elif is_session_expired(session_timestamp):
                return generate_error_response(440, "Session Expired")
            else:
                return generate_success_response("")

    except Exception as e:
        return generate_error_response(500, str(e))

def generate_error_response(status_code: int, error_msg: str):
    logger.error(error_msg)
    return status_code, error_msg

def generate_success_response(msg: str):
    logger.info(msg)
    return 200, msg

def generate_timestamp():
    ts = time.time()
    return datetime.fromtimestamp(ts)

def is_session_expired(session_timestamp):
    current_timestamp = generate_timestamp()
    return session_timestamp < (current_timestamp - timedelta(hours=24))

def get_response_headers():
    return response_headers

def flatten_result(result):
    return list(map(lambda t: t[0], result))

def convert_bit_to_int(bit):
    return 0 if bit == b'\x00' else 1
