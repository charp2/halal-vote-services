# standard python imports
from secrets import token_hex

# our imports
from common.user_auth import create_hashed_password

dataType = {
    "username": str,
    "password": str
}

def login(data: dataType, conn, logger):
    username = data["username"]
    password = data["password"]

    try:
        with conn.cursor() as cur:
            cur.execute("select password, salt, sessionToken from Users where username=%(username)s", {'username': username})
            fetched_password, fetched_salt, session_token = cur.fetchone()

            check_hash = create_hashed_password(password, fetched_salt)

            if fetched_password == check_hash:
                if not session_token:
                    new_session_token = token_hex(10)
                else:
                    new_session_token = session_token

                cur.execute("update Users set sessionToken=%(sessionToken)s where username=%(username)s", {'sessionToken': new_session_token, 'username': username})
                conn.commit()

                return 200, new_session_token
            else:
                error_str = "Password incorrect"
                logger.error(error_str)
                return 401, error_str


    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    success_message = "Successfully logged in as '%s'" %(username)
    logger.info(success_message)
    return 200, success_message
