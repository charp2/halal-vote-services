# our imports
from users_service.utils import create_hashed_password
from utils import generate_error_response
from utils import generate_success_response
from users_service.utils import create_session

dataType = {
    "username": str,
    "password": str
}

def login(data: dataType, conn, logger):
    username = data["username"]
    password = data["password"]

    try:
        with conn.cursor() as cur:
            cur.execute("select password, salt, sessionToken, activeStatus from Users where username=%(username)s", {'username': username})
            fetched_password, fetched_salt, fetched_session_token, fetched_active_status = cur.fetchone()

            check_hash = create_hashed_password(password, fetched_salt)

            # if user is not active or deleted then return 403
            if fetched_active_status == "INACTIVE":
                return generate_error_response(403, "User is INACTIVE")
            elif fetched_active_status == "DELETED":
                return generate_error_response(403, "User is DELETED")
            elif fetched_password == check_hash:
                if not fetched_session_token:
                    new_session_token, new_session_timestamp = create_session()
                    cur.execute("update Users set sessionToken=%(sessionToken)s, sessionTimestamp=%(sessionTimestamp)s where username=%(username)s", {'sessionToken': new_session_token, 'sessionTimestamp': new_session_timestamp, 'username': username})
                    conn.commit()
                else:
                    new_session_token = fetched_session_token

                return generate_success_response(new_session_token)
            else:
                return generate_error_response(401, "Password is incorrect")


    except Exception as e:
        return generate_error_response(500, str(e))
