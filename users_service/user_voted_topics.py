# standard python imports
import sys
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    'username': [str],
    'n': int,
    'offset': int
}

def user_voted_topics(data: dataType, request_headers: any, conn, logger):
    n = data.get('n', sys.maxsize)
    offset = data.get('offset', 0)
    username = data.get('username')
    sessiontoken = request_headers.get('sessiontoken', '')

    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            if username != None:
                query = '''
                            select Topics.*, IFNULL(UserTopicVotes.vote, 0) as vote
                            from Topics left join UserTopicVotes on Topics.topicTitle = UserTopicVotes.topicTitle and UserTopicVotes.username = %(username)s
                            where vote != 0 and UserTopicVotes.current = true
                            limit %(offset)s, %(n)s
                        '''
                query_map = {'username': username, 'offset': offset, 'n': n}
                cur.execute(query, query_map)
                conn.commit()
                result = cur.fetchall()
                return generate_success_response(result)

    except Exception as e:
        return generate_error_response(500, str(e))