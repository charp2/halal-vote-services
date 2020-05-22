# standard python imports
from hashlib import sha256

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

def create_hashed_password(password, salt):
    salted_password = password + salt
    return sha256(str.encode(salted_password)).hexdigest()
