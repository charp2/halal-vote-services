# standard python imports
import json
import pymysql

#  our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "itemName": str,
    "parentId": int,
    "depth": int,
    "n": int
}
def get_item_comments(data: dataType, conn, logger):
    # Access DB
    try:
        item_name = data.get('itemName')
        parent_id = data.get('parentId')
        depth = data.get('depth')
        n = data.get('n')

        with conn.cursor() as cur:
            if is_show_more_request(parent_id):
                return generate_success_response("show more request")
            else:
                cur.execute('select id, upVotes, downVotes, depth from Comments where itemName=%(itemName)s and depth <= %(depth)s order by ((2 * (upVotes + downVotes)) / depth) desc, depth asc, id asc limit %(n)s', {'itemName': item_name, 'depth': depth, 'n': n})
                conn.commit()
                top_rated_result = cur.fetchall()

                if top_rated_result:
                    comment_ids = flatten_result(top_rated_result)

                    cur.execute('select ancestor from CommentsClosure where descendent in %(commentIds)s', {'commentIds': comment_ids})
                    conn.commit()
                    ancestors_result = cur.fetchall()

                    if ancestors_result:
                        backtracked_comment_ids = flatten_result(ancestors_result)
                        comment_ids = comment_ids + backtracked_comment_ids

                    cur.execute('select * from Comments where id in %(allCommentIds)s', { 'allCommentIds': comment_ids})
                    conn.commit()
                    comment_details_result = cur.fetchall()

                    return generate_success_response(json.dumps(comment_details_result, default=str))

                else:
                    return generate_error_response(500, "Couldn't generate top rated comments")

    except Exception as e:
        return generate_error_response(500, str(e))

def is_show_more_request(parent_id: int):
    return parent_id != None

def flatten_result(result):
    return list(map(lambda t: t[0], result))