# standard python imports
import json

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import convert_bit_to_int

dataType = {
    "itemName": str,
    "username": str,
    "vote": int
}
def vote_item(data: dataType, conn, logger):
    username = data['username']
    item_name = data['itemName']
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
                    select vote from UserItemVotes
                    where username = %(username)s and itemName = %(itemName)s
                ''',
                {'username': username, 'itemName': item_name}
            )
            prev_vote = cur.fetchone()

            query_set_section = ""

            # Update Items table
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
                query_set_section = vote_field + " = " + vote_field + " + %(vote)s, " + "numVotes = numVotes + 1"

            rows_affected = cur.execute(
                '''
                    update Items
                    set ''' + query_set_section + '''
                    where itemName = %(itemName)s
                ''',
                {'itemName': item_name, 'vote': vote_abs, 'prev_vote': prev_vote_abs}
            )
            conn.commit()

            if rows_affected != 0:
                # Update UserItemVotes table
                if vote == 0:
                    cur.execute(
                        '''
                            delete from UserItemVotes
                            where username = %(username)s and itemName = %(itemName)s
                        ''',
                        {'username': username, 'itemName': item_name}
                    )
                    conn.commit()

                else:
                    cur.execute(
                        '''
                            insert into UserItemVotes (username, itemName, vote)
                            values (%(username)s, %(itemName)s, %(vote)s)
                            ON DUPLICATE KEY UPDATE
                            vote=%(vote)s
                        ''',
                        {'username': username, 'itemName': item_name, 'vote': vote}
                    )
                    conn.commit()
                    
                return generate_success_response(json.dumps({'updated': True}, default=str))
            else:
                return generate_success_response(json.dumps({'updated': False}, default=str))
                    

    except Exception as e:
        return generate_error_response(500, str(e))
