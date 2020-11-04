# standard python imports
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import convert_bit_to_int

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
            rows_affected = 0

            cur.execute(
                '''
                    select vote from UserTopicVotes
                    where username = %(username)s and topicTitle = %(topicTitle)s
                ''',
                {'username': username, 'topicTitle': topic_title}
            )
            prev_vote = cur.fetchone()

            # Update Topics table
            if prev_vote != None and prev_vote[0] != 0:
                prev_vote = prev_vote[0]

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
                if vote == 0:
                    cur.execute(
                        '''
                            delete from UserTopicVotes
                            where username = %(username)s and topicTitle = %(topicTitle)s
                        ''',
                        {'username': username, 'topicTitle': topic_title}
                    )
                    conn.commit()

                else:
                    vote_bit = 1 if vote > 0 else -1
                    cur.execute(
                        '''
                            insert into UserTopicVotes (username, topicTitle, vote)
                            values (%(username)s, %(topicTitle)s, %(vote)s)
                            ON DUPLICATE KEY UPDATE
                            vote=%(vote)s, timeStamp=now()
                        ''',
                        {'username': username, 'topicTitle': topic_title, 'vote': vote_bit}
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