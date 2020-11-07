# standard python imports
import sys
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import valid_user

dataType = {
    "topicTitle": str,
    "username": str,
    "n": int,
    "excludedIds": [int]
}
def get_topic_images(data: dataType, request_headers: any, conn, logger):
    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            topic_title = data['topicTitle']
            username = data.get('username')
            n = int(data.get('n', sys.maxsize))
            excluded_ids = list(map(str, data.get('excludedIds', [])))
            sessiontoken = request_headers.get('sessiontoken', '')

            query = ''
            query_map = {}
            if username != None:
                status_code, msg = valid_user(username, sessiontoken, conn, logger)

                if status_code != 200:
                    return generate_error_response(status_code, msg)

                query = '''
                    select TopicImages.*, UserTopicImageLikes.imageId is not null as userLike
                    from TopicImages left join UserTopicImageLikes on TopicImages.id = UserTopicImageLikes.imageId and UserTopicImageLikes.username = %(username)s
                    where topicTitle=%(topicTitle)s
                '''
                query_map['username'] = username
                query_map['topicTitle'] = topic_title

                if excluded_ids:
                    query = query + '''
                        and TopicImages.id not in %(excludedIds)s
                    '''
                    query_map['excludedIds'] = excluded_ids
            
                query = query + '''
                    order by TopicImages.likes DESC
                    limit %(n)s
                '''
                query_map['n'] = n
            else:
                query = '''
                    select id, username, image, likes from TopicImages 
                    where topicTitle=%(topicTitle)s
                '''
                query_map['topicTitle'] = topic_title
                query_map['excludedIds'] = excluded_ids

                if excluded_ids:
                    query = query + '''
                        and id not in %(excludedIds)s
                    '''
                    query_map['excludedIds'] = excluded_ids

                query = query + '''
                    order by likes DESC 
                    limit %(n)s
                '''
                query_map['n'] = n

            cur.execute(query, query_map)
            conn.commit()

            result = cur.fetchall()
            return generate_success_response(result)

    except Exception as e:
        return generate_error_response(500, str(e))
