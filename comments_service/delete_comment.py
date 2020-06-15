# standard python imports
import pymysql
import json

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "username": str,
    "id": int
}
def delete_comment(data: dataType, conn, logger):
    username = data.get('username')
    id = data.get('id')

    if not username:
        return generate_error_response(500, "Invalid username passed in")

    if not id:
        return generate_error_response(500, "Invalid id passed in")

    # Access DB
    try:
        if has_descendent(conn, id):
            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE Comments SET comment = "__deleted__" WHERE id=%(id)s and username=%(username)s''',
                    {'id': id, 'username': username}
                )
                if cur.rowcount <= 0:
                    return generate_error_response(500, "Unsuccesful delete attempt")

                conn.commit()

            return generate_success_response(json.dumps({ "deletedId": id, "psuedoDelete": 1 }, default=str))

        else:
            with conn.cursor() as cur:
                cur.execute(
                    '''delete from Comments where id=%(id)s and username=%(username)s''', 
                    {'id': id, 'username': username}
                )
                if has_ancestor(conn, id):
                    cur.execute(
                        '''UPDATE Comments SET numReplies = numReplies - 1 
                        WHERE id in (select ancestor from CommentsClosure where descendent=%(id)s and isDirect=1)''', #TODO: optimize this
                        {'id': id}
                    )
                if cur.rowcount > 0:
                    cur.execute(
                        '''delete from CommentsClosure where descendent=%(id)s''',
                        {'id': id}
                    )
                else:
                    return generate_error_response(500, "Unsuccesful delete attempt")

                conn.commit()

            return generate_success_response(json.dumps({ "deletedId": id, "psuedoDelete": 0 }, default=str))
                

    except Exception as e:
        return generate_error_response(500, str(e))

def has_descendent(conn, id: int):
    with conn.cursor() as cur:
        cur.execute('''SELECT EXISTS (SELECT * FROM CommentsClosure WHERE ancestor=%(id)s)''', 
            {'id': id}
        )
        conn.commit()

    return cur.fetchone()[0]

def has_ancestor(conn, id: int):
    with conn.cursor() as cur:
        cur.execute('''SELECT EXISTS (SELECT * FROM CommentsClosure WHERE descendent=%(id)s)''', 
            {'id': id}
        )
        conn.commit()

    return cur.fetchone()[0]