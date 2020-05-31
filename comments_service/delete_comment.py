# standard python imports
import pymysql

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
        return generate_error_response(500, "Invalid itemName passed in")

    # Access DB
    try:
        if has_descendent(conn, id):
            with conn.cursor() as cur:
                cur.execute(
                    '''UPDATE Comments SET comment = "__DELETED__" WHERE id = %(id)s''',
                    {'id': id}
                )
                conn.commit()
            return generate_success_response("Updated comment with id: %s to reflect __DELETED__ status" %(id))

        else:
            with conn.cursor() as cur:
                cur.execute(
                    '''delete from Comments where id=%(id)s''', 
                    {'id': id}
                )
                conn.commit()
                cur.execute(
                    '''delete from CommentsClosure where descendent=%(id)s''',
                    {'id': id}
                )
                conn.commit()
            return generate_success_response("Deleted comment with id: %s" %(id))
                

    except Exception as e:
        return generate_error_response(500, str(e))

def has_descendent(conn, id: int):
    with conn.cursor() as cur:
        cur.execute('''SELECT EXISTS (SELECT * FROM CommentsClosure WHERE ancestor=%(id)s)''', 
            {'id': id}
        )
        conn.commit()

    return cur.fetchone()[0]