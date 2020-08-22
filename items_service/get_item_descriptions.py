# standard python imports
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "itemName": str
}
def get_item_descriptions(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            item_name = data['itemName']

            cur.execute('select username, description from ItemDescriptions where itemName=%(itemName)s', {'itemName': item_name})
            conn.commit()

            result = cur.fetchall()
            if result:
                return generate_success_response(result)
            else:
                return generate_error_response(500, "Getting Item Descriptions failed.")

    except Exception as e:
        return generate_error_response(500, str(e))
