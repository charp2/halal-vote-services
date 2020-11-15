# standard python imports
import sys
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import valid_user

sort_query = '''
    order by ((T.numVotes*2) + POWER(T.numComments, 1/2)*4 + POWER(T.numImages, 1/3)*5) desc, T.timeStamp desc
'''

dataType = {
    'topicTitles': [str],
    'n': int,
    'offset': int,
    'username': str,
    "excludedTopics": [str]
}

def get_topics(data: dataType, request_headers: any, conn, logger):
    topic_titles = data.get('topicTitles')
    n = data.get('n', sys.maxsize)
    offset = data.get('offset', 0)
    excluded_topics = data.get('excludedTopics')
    username = data.get('username')
    sessiontoken = request_headers.get('sessiontoken', '')

    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            query = '''
                select Topics.*, null as vote, (COUNT(*) * CASE WHEN TopicImages.id IS NULL THEN 0 ELSE 1 END) as numImages
                from Topics left join TopicImages on Topics.topicTitle = TopicImages.topicTitle
            '''
            query_map = {}

            if username != None:
                status_code, msg = valid_user(username, sessiontoken, conn, logger)

                if status_code != 200:
                    return generate_error_response(status_code, msg)

                query = '''
                    select Topics.*, IFNULL(UserTopicVotes.vote, 0) as vote, (COUNT(*) * CASE WHEN TopicImages.id IS NULL THEN 0 ELSE 1 END) as numImages
                    from Topics left join UserTopicVotes on Topics.topicTitle = UserTopicVotes.topicTitle and UserTopicVotes.username = %(username)s and UserTopicVotes.current = true
                    left join TopicImages on Topics.topicTitle = TopicImages.topicTitle
                '''
                query_map['username'] = username

            if excluded_topics != None and topic_titles == None:
                query = query + '''
                    where Topics.topicTitle not in %(excludedTopics)s
                '''
                query_map['excludedTopics'] = excluded_topics

            if topic_titles != None and excluded_topics == None:
                query = query + '''
                    where Topics.topicTitle in %(topicTitles)s
                '''
                query_map['topicTitles']  = topic_titles
            else:
                query = '''select * from (''' + query + '''
                group by Topics.topicTitle) as T
                ''' + sort_query + '''
                limit %(offset)s, %(n)s'''
                query_map['offset'] = offset
                query_map['n'] = n

            cur.execute(query, query_map)
            conn.commit()

            result = cur.fetchall()
            return generate_success_response(result)

    except Exception as e:
        return generate_error_response(500, str(e))
