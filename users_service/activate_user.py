# our imports
from utils import generate_error_response
from utils import generate_success_response
from users_service.utils import create_session

def activate_user(username: str, activation_value: str, conn, logger):
    try:
        with conn.cursor() as cur:
            cur.execute("select sessionToken, activeStatus from Users where username=%(username)s", {'username': username})
            results = cur.fetchone()

            if results:
                fetched_activation_value, fetched_active_status = results
            else:
                return generate_error_response(404, "User not found")

            if fetched_active_status == "INACTIVE":
                if activation_value == fetched_activation_value:
                    session_token, session_timestamp = create_session()

                    cur.execute("update Users set sessionToken=%(sessionToken)s, sessionTimestamp=%(sessionTimestamp)s, activeStatus='ACTIVE' where username=%(username)s", {'sessionToken': session_token, 'sessionTimestamp': session_timestamp, 'username': username})
                    conn.commit()

                    return generate_success_response("Successfully activated %s!" %(username))
                else:
                    return generate_error_response(401, "Unauthorized Activation")

            elif fetched_active_status == "DELETED":
                return generate_error_response(403, "User is DELETED")
            else:
                return generate_success_response("%s is already ACTIVE!" %(username))

    except Exception as e:
        conn.rollback()
        return generate_error_response(500, str(e))
