# standard python imports
from secrets import token_hex
import json

# our imports
from users_service.utils import create_hashed_password
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "email": str,
    "username": str,
    "password": str
}

def register_user(data: dataType, conn, logger):
    email = data["email"]
    username = data["username"]
    password = data["password"]
    salt = token_hex(10)
    activation_value = token_hex(10)

    if not email:
        return generate_error_response(500, "Invalid email passed in")

    if not username:
        return generate_error_response(500, "Invalid username passed in")

    if not password:
        return generate_error_response(500, "Invalid password passed in")

    hashed_password = create_hashed_password(password, salt)
    logger.info(hashed_password)

    try:
        with conn.cursor() as cur:
            cur.execute("insert into Users (username, email, password, salt, sessionToken, activeStatus) values(%(username)s, %(email)s, %(password)s, %(salt)s, %(activationValue)s, 'INACTIVE')", {'username': username, 'email': email, 'password': hashed_password, 'salt': salt, 'activationValue': activation_value})
        conn.commit()
    except Exception as e:
        return generate_error_response(500, str(e))

    return generate_success_response(json.dumps(username, default=str))
