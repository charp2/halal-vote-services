# standard python imports
import sys
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import valid_user

sort_query = '''
    order by Date(T.timeStamp) desc, (POWER(T.numVotes, 1/2)*2 + POWER(T.numComments, 1/3)*4 + POWER(T.mediaLikes, 1/2)*5) desc
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
                select Topics.*, 0 as vote, SUM(CASE WHEN TopicImages.id IS NULL THEN 0 ELSE TopicImages.likes+1 END) as mediaLikes
                from Topics left join TopicImages on Topics.topicTitle = TopicImages.topicTitle
            '''
            query_map = {}

            if username != None:
                status_code, msg = valid_user(username, sessiontoken, conn, logger, False)

                if status_code != 200:
                    return generate_error_response(status_code, msg)

                query = '''
                    select Topics.*, IFNULL(UserTopicVotes.vote, 0) as vote, SUM(CASE WHEN TopicImages.id IS NULL OR UserSeenMedia.mediaId IS NOT NULL THEN 0 ELSE TopicImages.likes+1 END) as mediaLikes, (CASE WHEN UserSeenMedia.mediaId IS NULL OR Topics.topicTitle in %(topicTitles)s THEN 0 ELSE 1 END) as userSeen
                    from Topics left join UserTopicVotes on Topics.topicTitle = UserTopicVotes.topicTitle and UserTopicVotes.username = %(username)s and UserTopicVotes.current = true
                    left join TopicImages on Topics.topicTitle = TopicImages.topicTitle
                    left join UserSeenMedia on TopicImages.id = UserSeenMedia.mediaId and UserSeenMedia.username = %(username)s
                '''
                query_map['username'] = username

            if excluded_topics and not topic_titles:
                query = query + '''
                    where Topics.topicTitle not in %(excludedTopics)s
                '''
                query_map['excludedTopics'] = excluded_topics

            query_map['topicTitles'] = ['']
            if topic_titles and not excluded_topics:
                query = query + '''
                    where Topics.topicTitle in %(topicTitles)s
                '''
                query_map['topicTitles']  = topic_titles

            query = '''select * from (''' + query + '''
                group by Topics.topicTitle) as T
            '''

            if username != None:
                user_seen_exclusive_query = query + '''
                    where T.userSeen = 0
                '''

            query = add_sorting_to_query(query, sort_query)

            if username != None:
                user_seen_exclusive_query = add_sorting_to_query(user_seen_exclusive_query, sort_query)

            query_map['offset'] = offset
            query_map['n'] = n

            if username != None:
                result = execute_query(conn, cur, user_seen_exclusive_query, query_map)

                if len(result) == 0:
                    result = execute_query(conn, cur, query, query_map)

            else:
                result = execute_query(conn, cur, query, query_map)

            conn.commit()
            # logger.info(cur._last_executed)
            # print(cur._last_executed)
            return generate_success_response(result)

    except Exception as e:
        return generate_error_response(500, str(e))

def add_sorting_to_query(query, sort_query):
    return query + sort_query + '''
        limit %(offset)s, %(n)s
    '''

def execute_query(conn, cur, query, query_map):
    cur.execute(query, query_map)
    result = cur.fetchall()
    return result