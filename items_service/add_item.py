# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "itemName": str,
    "username": str
}
def add_item(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            cur.execute('insert into Items (itemName, username, halalVotes, haramVotes, numComments) values(%(itemName)s, %(username)s, 0, 0, 0)', {'itemName': data['itemName'], 'username': data['username']})
        conn.commit()
    except Exception as e:
        return generate_error_response(500, str(e))

    return generate_success_response("Added Item '%s' into Items table" %(data['itemName']))
