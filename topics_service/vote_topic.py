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
            prev_vote, prev_vote_time, latitude, longitude = (None, None, None, None)

            cur.execute(
                '''
                    select vote, timeStamp from UserTopicVotes
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

            rows_affected = 0
            # Update Topics table
            if prev_vote != None and prev_vote != 0:
                if prev_vote != vote:
                    prev_vote_field = 'halalPoints' if prev_vote > 0 else 'haramPoints'

                    if vote == 0:
                        query_set_section = prev_vote_field + " = " + prev_vote_field + " - 1, numVotes = numVotes - 1"
                    else:
                        vote_field = 'halalPoints' if vote > 0 else 'haramPoints'
                        query_set_section = vote_field + " = " + vote_field + " + 1, " + prev_vote_field + " = " + prev_vote_field + " - 1"

                    rows_affected = cur.execute(
                        '''
                            update Topics
                            set ''' + query_set_section + '''
                            where topicTitle = %(topicTitle)s
                        ''',
                        {'topicTitle': topic_title}
                    )
                    conn.commit()

            elif vote != 0:
                vote_field = 'halalPoints' if vote > 0 else 'haramPoints'
                query_set_section = vote_field + " = " + vote_field + " + 1, numVotes = numVotes + 1"

                rows_affected = cur.execute(
                    '''
                        update Topics
                        set ''' + query_set_section + '''
                        where topicTitle = %(topicTitle)s
                    ''',
                    {'topicTitle': topic_title}
                )
                conn.commit()

            if rows_affected != 0:
                # Update UserTopicVotes table
                vote_bit = int(vote/abs(vote)) if vote != 0 else 0
                current_time = generate_timestamp()

                if prev_vote_time != None and current_time < (prev_vote_time + timedelta(days=1)):
                    if vote_bit == 0:
                        cur.execute(
                            '''
                                delete from UserTopicVotes
                                where username = %(username)s and topicTitle = %(topicTitle)s and current = true
                            ''',
                            {'username': username, 'topicTitle': topic_title}
                        )
                        conn.commit()
                    else:
                        cur.execute(
                            '''
                                update UserTopicVotes
                                set vote = %(vote)s, timeStamp = %(timeStamp)s, latitude = %(latitude)s, longitude = %(longitude)s
                                where username = %(username)s and topicTitle = %(topicTitle)s and current = true
                            ''',
                            {'vote': vote_bit, 'timeStamp': current_time, 'latitude': latitude, 'longitude': longitude, 'username': username, 'topicTitle': topic_title}
                        )
                        conn.commit()
                else:
                    if prev_vote != None or prev_vote != vote_bit:
                        cur.execute(
                            '''
                                update UserTopicVotes
                                set current = false
                                where username = %(username)s and topicTitle = %(topicTitle)s and current = true
                            ''',
                            {'username': username, 'topicTitle': topic_title}
                        )
                        conn.commit()

                    if vote_bit != 0:
                        cur.execute(
                            '''
                                insert into UserTopicVotes (username, topicTitle, vote, latitude, longitude)
                                values (%(username)s, %(topicTitle)s, %(vote)s, %(latitude)s, %(longitude)s)
                            ''',
                            {'username': username, 'topicTitle': topic_title, 'vote': vote_bit, 'latitude':latitude, 'longitude': longitude}
                        )
                        conn.commit()
                
                with conn.cursor(pymysql.cursors.DictCursor) as dict_cur:
                    dict_cur.execute(
                        '''
                            select * from Topics where topicTitle = %(topicTitle)s
                        ''',
                        {'topicTitle': topic_title}
                    )
                    conn.commit()
                    result = dict_cur.fetchall()[0]
                    return generate_success_response(result)
            else:
                return generate_success_response({'noUpdates': True})
                    

    except Exception as e:
        return generate_error_response(500, str(e))