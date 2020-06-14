# standard python imports
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from comments_service.utils import get_parent_depth
from comments_service.utils import parent_depth_found

dataType = {
    "parentId": int,
    "username": str,
    "itemName": str,
    "comment": str,
    "commentType": str
}
def add_comment(data: dataType, conn, logger):
    parent_id = data.get('parentId')
    username = data.get('username')
    item_name = data.get('itemName')
    comment = data.get('comment')
    comment_type = data.get('commentType', 'OTHER')

    if not username:
        return generate_error_response(500, "Invalid username passed in")

    if not item_name:
        return generate_error_response(500, "Invalid itemName passed in")
    
    if not comment:
        return generate_error_response(500, "Invalid comment passed in")

    # Access DB
    try:
        if is_top_level_comment(parent_id):
            new_comment_id = insert_comment(conn, parent_id, item_name, username, comment, comment_type, 1)
            return generate_success_response(new_comment_id)

        else:
            parent_depth = get_parent_depth(conn, parent_id)
            if parent_depth_found(parent_depth):
                new_comment_id = insert_comment(conn, parent_id, item_name, username, comment, comment_type, parent_depth + 1, top_level=False)

                update_closure_table(conn, parent_id, new_comment_id)

                return generate_success_response(new_comment_id)

            else:
                return generate_error_response(404, "parentId does not exist")

    except Exception as e:
        return generate_error_response(500, str(e))

def is_top_level_comment(parent_id):
    return parent_id == None

def insert_comment(conn, parent_id, item_name, username, comment, comment_type, depth, top_level=True):
    with conn.cursor() as cur:
        cur.execute(
            '''
            insert into Comments (itemName, username, comment, commentType, depth) 
            values(%(itemName)s, %(username)s, %(comment)s, %(commentType)s, %(depth)s)
            ''', 
            {'itemName': item_name, 'username': username, 'comment': comment, 'commentType': comment_type, 'depth': depth}
        )
        cur.execute(
            '''
            Update Comments
            Set numReplies = numReplies + 1
            Where id = %(parentId)s
            ''',
            { "parentId": parent_id }
        )
        conn.commit()

        cur.execute('select LAST_INSERT_ID()')
        conn.commit()
        return cur.fetchone()[0]

def update_closure_table(conn, parent_id, new_comment_id):
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        closure_values_map = {'parentId': parent_id, 'newCommentId': new_comment_id}
        cur.execute('insert into CommentsClosure (ancestor, descendent, isDirect) select ancestor, %(newCommentId)s, false from CommentsClosure where descendent=%(parentId)s union all select %(parentId)s, %(newCommentId)s, true', closure_values_map)
        conn.commit()