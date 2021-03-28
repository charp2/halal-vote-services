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

def user_liked_media(data: dataType, request_headers: any, conn, logger):
    n = int(data.get('n', sys.maxsize))
    offset = int(data.get('offset', 0))
    username = data.get('username')

    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            if username != None:
                query = '''
                            select * from TopicImages
                            left join UserTopicImageLikes
                            on UserTopicImageLikes.imageId = TopicImages.id
                            where UserTopicImageLikes.username = %(username)s
                            limit %(offset)s, %(n)s
                        '''
                query_map = {'username': username, 'offset': offset, 'n': n}
                cur.execute(query, query_map)
                result = cur.fetchall()
                conn.commit()
                return generate_success_response(result)

    except Exception as e:
        return generate_error_response(500, str(e))