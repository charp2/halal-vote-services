# standard python imports

# our imports
from users_service.utils import create_hashed_password
from utils import generate_error_response
from utils import generate_success_response
from utils import is_session_expired

dataType = {
    "username": str,
    "newPassword": str,
    "resetToken": str
}

def reset_password(data: dataType, conn, logger):
    username = data["username"]
    new_password = data["newPassword"]
    reset_token = data["resetToken"]

    try:
        with conn.cursor() as cur:
            cur.execute('''
                select salt, activeStatus, passwordResetToken, passwordResetTimestamp from Users
                where username=%(username)s
            ''', {'username': username})

            result = cur.fetchone()

            if result:
                fetched_salt, fetched_active_status, fetched_reset_token, fetched_reset_timestamp = result

                if fetched_active_status != "ACTIVE":
                    return generate_error_response(400, "Account is not ACTIVE")

                if fetched_reset_token != reset_token or is_session_expired(fetched_reset_timestamp):
                    return generate_error_response(403, "Unauthorized change of password")
                
            else:
                return generate_error_response(404, "Username does not exist")

            cur.execute('''
                update Users
                set passwordResetToken=%(passwordResetToken)s, passwordResetTimestamp=%(passwordResetTimestamp)s, password=%(password)s
                where username=%(username)s
            ''', {'passwordResetToken': None, 'passwordResetTimestamp': None, 'password': create_hashed_password(new_password, fetched_salt), 'username': username})
            conn.commit()

            return generate_success_response("Successfully reset password")

    except Exception as e:
        conn.rollback()
        return generate_error_response(500, "There was an error")
