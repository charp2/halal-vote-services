# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import flatten_result

dataType = {
    "username": str,
    "itemName": str
}
def delete_item(data: dataType, conn, logger):
    username = data.get('username')
    item_name = data.get('itemName')

    if not username:
        return generate_error_response(500, "Invalid username passed in")

    if not item_name:
        return generate_error_response(500, "Invalid itemName passed in")

    # Access DB
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''delete from Items where itemName=%(itemName)s and username=%(username)s''',
                {'itemName': item_name, 'username': username}
            )

            if cur.rowcount > 0:
                cur.execute(
                    '''select id from Comments where itemName=%(itemName)s''',
                     {'itemName': item_name}
                )
                result = cur.fetchall()

                if result:
                    comment_ids = flatten_result(result)

                    cur.execute(
                        '''delete from Comments where id in %(ids)s''',
                        {'ids': comment_ids}
                    )
                    cur.execute(
                        '''delete from CommentsClosure where ancestor in %(ids)s or descendent in %(ids)s''',
                        {'ids': comment_ids}
                    )

                conn.commit()
                return generate_success_response("Removed Item '%s' from Items table" %(item_name))

            else:
                return generate_error_response(500, "Unsuccesful delete attempt")

    except Exception as e:
        return generate_error_response(500, str(e))
