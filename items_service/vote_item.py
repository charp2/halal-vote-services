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

    if vote != 0 and vote != 1:
        return generate_error_response(400, "Ivalid vote passed in.")
    
    # Access DB
    try:
        with conn.cursor() as cur:
            item_vote_field = 'halalVotes' if vote == 0 else 'haramVotes'

            cur.execute(
                '''
                    select vote from UserItemVotes
                    where username = %(username)s and itemName = %(itemName)s
                ''',
                {'username': username, 'itemName': item_name}
            )
            user_vote = cur.fetchone()

            vote_removed = False

            if user_vote != None:
                user_vote = convert_bit_to_int(user_vote[0])

                if user_vote != vote:
                    prev_item_vote_field = 'halalVotes' if vote == 1 else "haramVotes"

                    rows_affected = cur.execute(
                        '''
                            update Items
                            set ''' + item_vote_field + ''' = ''' + item_vote_field + ''' + 1, ''' + prev_item_vote_field + ''' = ''' + prev_item_vote_field + ''' - 1
                            where username = %(username)s and itemName = %(itemName)s
                        ''',
                        {'username': username, 'itemName': item_name}
                    )
                    conn.commit()

                    if rows_affected == 0:
                        return generate_error_response(404, "Item not found.")

                else:
                    cur.execute(
                        '''
                            update Items
                            set ''' + item_vote_field + ''' = ''' + item_vote_field + ''' - 1
                            where username = %(username)s and itemName = %(itemName)s
                        ''',
                        {'username': username, 'itemName': item_name}
                    )
                    conn.commit()

                    vote_removed = True

            else:
                rows_affected = cur.execute(
                    '''
                        update Items
                        set ''' + item_vote_field + ''' = ''' + item_vote_field + ''' + 1
                        where username = %(username)s and itemName = %(itemName)s
                    ''',
                    {'username': username, 'itemName': item_name}
                )
                conn.commit()

                if rows_affected == 0:
                    return generate_error_response(404, "Item not found.")
            
            if vote_removed:
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
                
            return generate_success_response(json.dumps({'success': True}, default=str))
                    

    except Exception as e:
        return generate_error_response(500, str(e))
