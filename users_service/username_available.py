# standard python imports

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "username": str
}

def username_available(data: dataType, conn, logger):
    username = data["username"]

    try:
        with conn.cursor() as cur:
            cur.execute('''
                select username from Users
                where username=%(username)s
            ''', {'username': username})

            results = cur.fetchall()

            if results:
                return generate_success_response({"available": False})
            else:
                return generate_success_response({"available": True})


    except Exception as e:
        return generate_error_response(500, "There was an error")
