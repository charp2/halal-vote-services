# standard python imports
import json

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "itemName": str,
    "username": str,
    "description": str
}
def add_item(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            item_name = data['itemName']
            username = data['username']
            description = data['description']

            cur.execute('select exists(select * from Items where itemName=%(itemName)s)', {'itemName': item_name})
            conn.commit()

            result = cur.fetchone()
            if result:
                if result[0] == 1:
                    cur.execute('insert into ItemDescriptions (itemName, username, description) values(%(itemName)s, %(username)s, %(description)s) on duplicate key update description=%(description)s', {'itemName': item_name, 'username': username, 'description': description})
                    conn.commit()
                    return generate_success_response(item_name)
                else:
                    cur.execute('insert into Items (itemName, username, halalPoints, haramPoints, numVotes) values(%(itemName)s, %(username)s, 0, 0, 0)', {'itemName': item_name, 'username': username})
                    cur.execute('insert into ItemDescriptions (itemName, username, description) values(%(itemName)s, %(username)s, %(description)s)', {'itemName': item_name, 'username': username, 'description': description})
                    conn.commit()
                    return generate_success_response(item_name)
            else:
                return generate_error_response(500, "Checking if item exists failed.")

    except Exception as e:
        return generate_error_response(500, str(e))
