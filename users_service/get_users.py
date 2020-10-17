# standard python imports
import sys
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    'n': int,
    'searchTerm': str
}

def get_users(data: dataType, request_headers: any, conn, logger):
    search_term = data.get('searchTerm')
    limit = int(data.get('limit', 5))

    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            query = '''
                        select username from Users 
                        where activeStatus='ACTIVE' and (lower(username) like %(searchTermWB1)s or lower(username) like %(searchTermWB2)s)
                    '''
            query_map = {}
            query_map['searchTermWB1'] = search_term.lower() + "%" #WB = Word Boundary
            query_map['searchTermWB2'] = "% " + search_term.lower() + "%"
            query_map['limit'] = limit

            cur.execute(query, query_map)
            conn.commit()
            result = cur.fetchall()
            return generate_success_response(result)

    except Exception as e:
        return generate_error_response(500, str(e))