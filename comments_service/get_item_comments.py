# standard python imports
import json
import pymysql

#  our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "itemName": str,
    "parentId": int,
    "depth": int,
    "n": int
}
def get_item_comments(data: dataType, conn, logger):
    # Access DB
    try:
        item_name = data.get('itemName')
        parent_id = data.get('parentId')
        depth = data.get('depth')
        n = data.get('n')

        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            if is_show_more_request(parent_id):
                print("show more request")
            else:
                cur.execute('select * from Comments where itemName=%(itemName)s order by upVotes limit %(n)s', {'itemName': item_name, 'n': n})
        result = cur.fetchall()
        conn.commit()
    except Exception as e:
        return generate_error_response(500, str(e))

    responseBody = json.dumps(result)

    return generate_success_response(responseBody)

def is_show_more_request(parent_id: int):
    return parent_id == None