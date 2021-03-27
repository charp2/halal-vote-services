# standard python imports

# our imports
from users_service.utils import create_hashed_password
from utils import generate_error_response
from utils import generate_success_response
from utils import is_session_expired

dataType = {
    "username": str,
    "currentPassword": str,
    "newPassword": str
}

def change_password(data: dataType, conn, logger):
    username = data["username"]
    current_password = data["currentPassword"]
    new_password = data["newPassword"]

    try:
        with conn.cursor() as cur:
            cur.execute('''
                select salt, password from Users
                where username=%(username)s
            ''', {'username': username})

            result = cur.fetchone()

            if result:
                fetched_salt = result[0]
                fetched_password = result[1]

                if fetched_password != create_hashed_password(current_password, fetched_salt):
                    return generate_error_response(401, "Incorrect password")
            else:
                return generate_error_response(404, "Username does not exist")

            cur.execute('''
                update Users
                set password=%(password)s, sessionToken=%(sessionToken)s, sessionTimestamp=%(sessionTimestamp)s
                where username=%(username)s
            ''', {'password': create_hashed_password(new_password, fetched_salt), 'sessionToken': None, 'sessionTimestamp': None, 'username': username})
            conn.commit()

            return generate_success_response("Successfully changed password")

    except Exception as e:
        conn.rollback()
        return generate_error_response(500, "There was an error")
