# standard python imports
import sys
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    'searchTerm': str,
    'limit': int
}

def search_topics(data: dataType, conn, logger):
    search_term = data.get('searchTerm')
    limit = int(data.get('limit', 5))

    # Access DB
    try:
        with conn.cursor() as cur:
            query = 'select topicTitle from Topics where lower(searchableTopicTitle) like %(searchTermWB1)s or lower(searchableTopicTitle) like %(searchTermWB2)s limit %(limit)s'
            query_map = {}
            query_map['searchTermWB1'] = search_term.lower() + "%" #WB = Word Boundary
            query_map['searchTermWB2'] = "% " + search_term.lower() + "%"
            query_map['limit'] = limit

            cur.execute(query, query_map)

            result = cur.fetchall()
            return generate_success_response(result)

    except Exception as e:
        return generate_error_response(500, str(e))