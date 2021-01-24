# standard python imports

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "email": str
}

def email_available(data: dataType, conn, logger):
    email = data["email"]

    try:
        with conn.cursor() as cur:
            cur.execute('''
                select email from Users
                where email=%(email)s
            ''', {'email': email})

            results = cur.fetchall()

            if results:
                return generate_success_response({"available": False})
            else:
                return generate_success_response({"available": True})


    except Exception as e:
        return generate_error_response(500, "There was an error")
