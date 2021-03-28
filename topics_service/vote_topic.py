# standard python imports
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import convert_bit_to_int
from utils import generate_timestamp
from datetime import timedelta

dataType = {
    "topicTitle": str,
    "username": str,
    "vote": int
}
def vote_topic(data: dataType, conn, logger):
    username = data['username']
    topic_title = data['topicTitle']
    vote = data['vote']
    
    # Access DB
    try:
        with conn.cursor() as cur:
            prev_vote, prev_vote_time, latitude, longitude, halal_points, haram_points = (None, None, None, None, 0, 0)

            cur.execute(
                '''
                    select vote, voteTime from UserTopicVotes
                    where UserTopicVotes.username = %(username)s and UserTopicVotes.topicTitle = %(topicTitle)s and UserTopicVotes.current = true
                ''',
                {'username': username, 'topicTitle': topic_title}
            )
            vote_results = cur.fetchone()

            if vote_results:
                prev_vote, prev_vote_time = vote_results

            cur.execute(
                '''
                    select lastLatitude, lastLongitude from Users
                    where username = %(username)s
                ''',
                {'username': username}
            )
            location_results = cur.fetchone()

            if location_results:
                latitude, longitude = location_results

            # Update Topics table
            rows_affected = 0
            if prev_vote != None and prev_vote != 0:
                if prev_vote != vote:
                    prev_vote_field = 'halalPoints' if prev_vote > 0 else 'haramPoints'
                    vote_field = 'halalPoints' if vote > 0 else 'haramPoints'

                    if vote == 0:
                        query_set_section = prev_vote_field + " = " + prev_vote_field + " - 1, numVotes = numVotes - 1"
                        query_string, query_params = createSetTopicsQuery(query_set_section, topic_title)
                    else:
                        query_set_section = vote_field + " = " + vote_field + " + 1, " + prev_vote_field + " = " + prev_vote_field + " - 1"
                        query_string, query_params = createSetTopicsQuery(query_set_section, topic_title)
                    
                    rows_affected = cur.execute(query_string, query_params)

            elif vote != 0:
                vote_field = 'halalPoints' if vote > 0 else 'haramPoints'
                query_set_section = vote_field + " = " + vote_field + " + 1, numVotes = numVotes + 1"
                query_string, query_params = createSetTopicsQuery(query_set_section, topic_title)

                rows_affected = cur.execute(query_string, query_params)

            if rows_affected != 0:
                # Update UserTopicVotes table
                vote_bit = int(vote/abs(vote)) if vote != 0 else 0
                current_time = generate_timestamp()

                if prev_vote != None and prev_vote != vote_bit:
                    cur.execute(
                        '''
                            update UserTopicVotes
                            set current = false, removalTime = %(removalTime)s
                            where username = %(username)s and topicTitle = %(topicTitle)s and current = true
                        ''',
                        {'removalTime': current_time, 'username': username, 'topicTitle': topic_title}
                    )

                cur.execute(
                    '''
                        insert into UserTopicVotes (username, topicTitle, vote, voteTime, latitude, longitude)
                        values (%(username)s, %(topicTitle)s, %(vote)s, %(voteTime)s, %(latitude)s, %(longitude)s)
                    ''',
                    {'username': username, 'topicTitle': topic_title, 'vote': vote_bit, 'voteTime': current_time, 'latitude':latitude, 'longitude': longitude}
                )

                conn.commit()
                
                with conn.cursor(pymysql.cursors.DictCursor) as dict_cur:
                    dict_cur.execute(
                        '''
                            select * from Topics where topicTitle = %(topicTitle)s
                        ''',
                        {'topicTitle': topic_title}
                    )
                    result = dict_cur.fetchall()[0]
                    return generate_success_response(result)

            else:
                return generate_success_response({'noUpdates': True})

    except Exception as e:
        return generate_error_response(500, str(e))

def createSetTopicsQuery(query_set_section, topic_title):
    query_string ='''
            update Topics
            set ''' + query_set_section + '''
            where topicTitle = %(topicTitle)s
        '''
    query_params = {'topicTitle': topic_title}
    return (query_string, query_params)

def creatGetVoteCountQuery(topic_title):
    query_string ='''
            select halalPoints, haramPoints from Topics
            where topicTitle = %(topicTitle)s
        '''
    query_params = {'topicTitle': topic_title}
    return (query_string, query_params)