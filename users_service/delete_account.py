# standard python imports

# our imports
from users_service.utils import create_hashed_password
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "username": str,
    "password": str
}

def delete_account(data: dataType, conn, logger):
    username = data["username"]
    password = data["password"]

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

                if fetched_password != create_hashed_password(password, fetched_salt):
                    return generate_error_response(401, "Incorrect password")
            else:
                return generate_error_response(404, "Username does not exist")

            cur.execute('''
                update Users
                set activeStatus='DELETED'
                where username=%(username)s
            ''', {'username': username})
            conn.commit()

            return generate_success_response("Successfully deleted %s" %(username))

    except Exception as e:
        conn.rollback()
        return generate_error_response(500, "There was an error")    
