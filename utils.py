# standard python imports
import logging

# logging config
logger = logging.getLogger()

def valid_user(username: str, session_token: str, conn, logger):
    if not username:
        return generate_error_response(500, "Invalid username passed in")

    if not session_token:
        return generate_error_response(500, "Invalid sessionToken passed in")

    try:
        with conn.cursor() as cur:
            cur.execute("select sessionToken, activeStatus from Users where username=%(username)s", {'username': username})
            retrieved_session_token, active_status = cur.fetchone()

            if active_status != "ACTIVE":
                return generate_error_response(403, "User is Not ACTIVE")
            elif session_token != retrieved_session_token:
                return generate_error_response(401, "User Not Authorized")
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
