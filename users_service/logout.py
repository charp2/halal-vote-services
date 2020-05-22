# standard python imports
from secrets import token_hex

# our imports
from common.user_auth import create_hashed_password

dataType = {
    "username": str
}

def logout(data: dataType, session_token, conn, logger):
    username = data["username"]

    try:
        with conn.cursor() as cur:
            cur.execute("select sessionToken from Users where username=%(username)s", {'username': username})
            fetched_session_token = cur.fetchone()[0]

            if fetched_session_token:

                if fetched_session_token == session_token:
                    cur.execute("update Users set sessionToken=%(sessionToken)s where username=%(username)s", {'sessionToken': None, 'username': username})
                    conn.commit()

                    response_str = "Successfully logged out"
                    logger.error(response_str)
                    return 200, response_str

                else:
                    error_str = "User Not Authorized"
                    logger.error(error_str)
                    return 401, error_str

            else:
                response_str = "Already logged out"
                logger.error(response_str)
                return 200, response_str


    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    success_message = "Successfully logged in as '%s'" %(username)
    logger.info(success_message)
    return 200, success_message
