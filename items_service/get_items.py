# standard python imports
import sys
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import valid_user

dataType = {
    'itemNames': [str],
    'n': int,
    'offset': int,
    'username': str,
    "excludedItems": [str]
}

def get_items(data: dataType, request_headers: any, conn, logger):
    item_names = data.get('itemNames')
    n = data.get('n', sys.maxsize)
    offset = data.get('offset', 0)
    excluded_items = data.get('excludedItems')
    username = data.get('username')
    sessiontoken = request_headers.get('sessiontoken', '')

    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            query = 'select *, null as vote from Items'
            query_map = {}

            if username != None:
                status_code, msg = valid_user(username, sessiontoken, conn, logger)

                if status_code != 200:
                    return generate_error_response(status_code, msg)

                query = '''
                    select Items.*, cast(UserItemVotes.vote as unsigned) as vote
                    from Items left join UserItemVotes on Items.itemName = UserItemVotes.itemName and UserItemVotes.username = %(username)s
                '''
                query_map['username'] = username

                
            if item_names != None:
                query = query + '''
                    where Items.itemName in %(itemNames)s
                '''
                query_map['itemNames']  = item_names

            if excluded_items != None:
                query = query + '''
                    where itemName not in %(excludedItems)s
                '''
                query_map['excludedItems'] = excluded_items

            else:
                query = query + '''
                    limit %(offset)s, %(n)s
                '''
                query_map['offset'] = offset
                query_map['n'] = n

            cur.execute(query, query_map)
            conn.commit()

            result = cur.fetchall()
            responseBody = json.dumps(result, default=str)
            return generate_success_response(responseBody)

    except Exception as e:
        return generate_error_response(500, str(e))
