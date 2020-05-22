# standard python imports
import logging

# logging config
logger = logging.getLogger()

def valid_user(username, session_token, conn, logger):
    if not username:
        error_message = "Invalid username passed in"
        logger.error(error_message)
        return error_message

    if not session_token:
        error_message = "Invalid sessionToken passed in"
        logger.error(error_message)
        return error_message

    try:
        with conn.cursor() as cur:
            cur.execute("select sessionToken from Users where username=%(username)s", {'username': username})
            retrieved_session_token = cur.fetchone()[0]
            return session_token == retrieved_session_token

    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return error_str

def generate_error_response(status_code: int, error_msg: str):
    logger.error(error_msg)
    return status_code, error_msg

def generate_success_response(msg: str):
    logger.info(msg)
    return 200, msg
