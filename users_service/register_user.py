from secrets import token_hex

dataType = {
    "username": str,
    "password": str
}

def register_user(data: dataType, conn, logger):
    salt = token_hex(10)

    username = data["username"]
    password = data["password"]

    if not username:
        error_message = "Invalid username passed in"
        logger.error(error_message)
        return 500, error_message

    if not password:
        error_message = "Invalid password passed in"
        logger.error(error_message)
        return 500, error_message

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
