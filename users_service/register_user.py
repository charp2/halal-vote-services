from secrets import token_hex
from hashlib import sha256

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

    salted_password = password + salt
    hashed_password = sha256(str.encode(salted_password)).hexdigest()
    logger.info(hashed_password)

    try:
        with conn.cursor() as cur:
            cur.execute("insert into Users (username, password, salt, activeStatus) values('%s', '%s', '%s', 'INACTIVE')" %(username, hashed_password, salt))
            conn.commit()
    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    success_message = "Added User '%s' into Users table" %(data['username'])
    logger.info(success_message)
    return 200, success_message
