# standard python imports
import json

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
            item_name = data['itemName']
            username = data['username']

            cur.execute('insert into Items (itemName, username, halalVotes, haramVotes) values(%(itemName)s, %(username)s, 0, 0)', {'itemName': item_name, 'username': username})
            conn.commit()

            return generate_success_response(json.dumps(item_name, default=str))

    except Exception as e:
        return generate_error_response(500, str(e))
