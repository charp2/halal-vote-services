# our imports
from utils import generate_error_response
from utils import generate_success_response
from users_service.utils import create_session

def activate_user(username: str, activation_value: str, conn, logger):
    try:
        with conn.cursor() as cur:
            cur.execute("select sessionToken, activeStatus from Users where username=%(username)s", {'username': username})
            fetched_activation_value, fetched_active_status = cur.fetchone()

            if fetched_active_status == "INACTIVE":
                if activation_value == fetched_activation_value:
                    session_token, session_timestamp = create_session()

                    cur.execute("update Users set sessionToken=%(sessionToken)s, sessionTimestamp=%(sessionTimestamp)s, activeStatus='ACTIVE' where username=%(username)s", {'sessionToken': session_token, 'sessionTimestamp': session_timestamp, 'username': username})
                    conn.commit()

                    return generate_success_response("Successfully activated User '%s' with sessionToken '%s'" %(username, session_token))
                else:
                    return generate_error_response(401, "Unauthorized Activation")

            elif fetched_active_status == "DELETED":
                return generate_error_response(403, "User is DELETED")
            else:
                return generate_error_response(403, "User is already ACTIVE")

    except Exception as e:
        return generate_error_response(500, str(e))
