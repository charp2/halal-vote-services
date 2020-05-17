def valid_user(username, sessionToken, conn, logger):
    if not username:
        error_message = "Invalid username passed in"
        logger.error(error_message)
        return error_message

    if not sessionToken:
        error_message = "Invalid sessionToken passed in"
        logger.error(error_message)
        return error_message

    try:
        with conn.cursor() as cur:
            cur.execute("select sessionToken from Users where username='%s'" %(username))
            retrievedSessionToken = cur.fetchone()[0]
            return sessionToken == retrievedSessionToken

    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return error_str
