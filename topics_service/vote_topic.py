# standard python imports
import json

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

    if vote < -100 or vote > 100:
        return generate_error_response(400, "Invalid vote passed in.")
    
    # Access DB
    try:
        with conn.cursor() as cur:
            vote_field = 'halalPoints' if vote > 0 else 'haramPoints'
            vote_abs = abs(vote)
            prev_vote_abs = None

            cur.execute(
                '''
                    select vote from UserTopicVotes
                    where username = %(username)s and topicTitle = %(topicTitle)s
                ''',
                {'username': username, 'topicTitle': topic_title}
            )
            prev_vote = cur.fetchone()

            query_set_section = ""

            # Update Topics table
            if prev_vote != None:
                prev_vote = prev_vote[0]
                prev_vote_field = 'halalPoints' if prev_vote > 0 else 'haramPoints'
                prev_vote_abs = abs(prev_vote)
                num_votes_decrement = 1 if vote == 0 else 0

                if prev_vote_field != vote_field:
                    query_set_section = vote_field + " = " + vote_field + " + %(vote)s, " + prev_vote_field + " = " + prev_vote_field + " - %(prev_vote)s, " + "numVotes = numVotes - " + str(num_votes_decrement)
                else:
                    query_set_section = vote_field + " = " + vote_field + " + %(vote)s - %(prev_vote)s, " + "numVotes = numVotes - " + str(num_votes_decrement)

            else:
                num_votes_increment = 0 if vote == 0 else 1
                query_set_section = vote_field + " = " + vote_field + " + %(vote)s, " + "numVotes = numVotes + " + str(num_votes_increment)

            rows_affected = cur.execute(
                '''
                    update Topics
                    set ''' + query_set_section + '''
                    where topicTitle = %(topicTitle)s
                ''',
                {'topicTitle': topic_title, 'vote': vote_abs, 'prev_vote': prev_vote_abs}
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
                    cur.execute(
                        '''
                            insert into UserTopicVotes (username, topicTitle, vote)
                            values (%(username)s, %(topicTitle)s, %(vote)s)
                            ON DUPLICATE KEY UPDATE
                            vote=%(vote)s
                        ''',
                        {'username': username, 'topicTitle': topic_title, 'vote': vote}
                    )
                    conn.commit()
                    
                return generate_success_response({'updated': True})
            else:
                return generate_success_response({'updated': False})
                    

    except Exception as e:
        return generate_error_response(500, str(e))
