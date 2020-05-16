from secrets import token_hex

def register_user(data, conn, logger):
    logger.info("register_user incoming data: %s", data)

    salt = token_hex(20)

    try:
        with conn.cursor() as cur:
            cur.execute("insert into Users (username, password, salt, activeStatus) values('%s', '%s', '%s', 'INACTIVE')" %(data["username"], data["password"], salt))
        conn.commit()
    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    success_message = "Added User '%s' into Users table" %(data['username'])
    logger.info(success_message)
    return 200, success_message
