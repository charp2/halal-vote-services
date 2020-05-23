# standard python imports
from secrets import token_hex

# our imports
from users_service.utils import create_hashed_password
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "username": str
}

def logout(data: dataType, session_token, conn, logger):
    username = data["username"]

    try:
        with conn.cursor() as cur:
            cur.execute("select sessionToken, activeStatus from Users where username=%(username)s", {'username': username})
            results = cur.fetchone()
            conn.commit()

            if results:
                fetched_session_token, fetched_active_status = results
            else:
                return generate_error_response(404, "User not found")

            if fetched_session_token:
                if fetched_active_status == "INACTIVE":
                    return generate_error_response(403, "User is INACTIVE")
                elif fetched_active_status == "DELETED":
                    return generate_error_response(403, "User is DELETED")
                if fetched_session_token == session_token:
                    cur.execute("update Users set sessionToken=%(sessionToken)s, sessionTimestamp=%(sessionTimestamp)s where username=%(username)s", {'sessionToken': None, 'sessionTimestamp': None, 'username': username})
                    conn.commit()

                    return generate_success_response("Successfully logged out")

                else:
                    return generate_error_response(401, "User Not Authorized")

            else:
                return generate_success_response("Already logged out")

    except Exception as e:
        return generate_error_response(500, str(e))
