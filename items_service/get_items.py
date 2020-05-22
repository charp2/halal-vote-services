# standard python imports
import sys
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    'itemNames': [str],
    'n': int,
    'offset': int
}

def get_items(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            if (data.get('itemNames') != None):
                itemsToGet = ','.join(map(lambda x: '"%s"' %(x), data['itemNames']))
                cur.execute('select * from Items where itemName in (%s)' %(itemsToGet))
                result = cur.fetchall()
            else:
                cur.execute('select * from Items limit %(offset)s, %(n)s', { 'offset': data.get('offset', 0), 'n': data.get('n', sys.maxsize) })
                result = cur.fetchall()
        conn.commit()
    except Exception as e:
        return generate_error_response(500, str(e))

    responseBody = json.dumps(result, default=str)

    return generate_success_response("Retreived Items '%s' from Items table" %(responseBody))
