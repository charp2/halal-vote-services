# standard python imports
from secrets import token_hex

# our imports
from common.user_auth import create_hashed_password

dataType = {
    "username": str,
    "password": str
}

def register_user(data: dataType, conn, logger):
    username = data["username"]
    password = data["password"]
    salt = token_hex(10)

    if not username:
        error_message = "Invalid username passed in"
        logger.error(error_message)
        return 500, error_message

    if not password:
        error_message = "Invalid password passed in"
        logger.error(error_message)
        return 500, error_message

    hashed_password = create_hashed_password(password, salt)
    logger.info(hashed_password)

    try:
        with conn.cursor() as cur:
            cur.execute("insert into Users (username, password, salt, activeStatus) values(%(username)s, %(password)s, %(salt)s, 'INACTIVE')", {'username': username, 'password': hashed_password, 'salt': salt})
            conn.commit()
    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    success_message = "Added User '%s' into Users table" %(username)
    logger.info(success_message)
    return 200, success_message
