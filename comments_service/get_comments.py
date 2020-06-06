# standard python imports
import json
import pymysql

#  our imports
from utils import generate_error_response
from utils import generate_success_response
from comments_service.utils import get_parent_depth
from comments_service.utils import parent_depth_found

dataType = {
    "itemName": str,
    "parentId": int,
    "depth": int,
    "n": int
}
def get_comments(data: dataType, conn, logger):
    # Access DB
    try:
        item_name = data.get('itemName')
        parent_id = data.get('parentId')
        depth = data.get('depth')
        n = data.get('n')

        with conn.cursor() as cur:
            if is_show_more_request(parent_id):
                parent_depth = get_parent_depth(conn, parent_id)

                if parent_depth_found(parent_depth):
                    return fetch_comments(conn, item_name, parent_depth, parent_depth + depth, n, parent_id=parent_id)

                else:
                    return generate_error_response(404, "parentId does not exist")

            else:
                return fetch_comments(conn, item_name, 0, depth, n)

    except Exception as e:
        return generate_error_response(500, str(e))

def is_show_more_request(parent_id: int):
    return parent_id != None

def flatten_result(result):
    return list(map(lambda t: t[0], result))

def fetch_comments(conn, item_name, start_depth, end_depth, n, parent_id=None):
    with conn.cursor() as cur:
        query = '''
            select id, upVotes, downVotes, depth from Comments
            where itemName=%(itemName)s and %(startDepth)s < depth and depth <= %(endDepth)s
        '''
        query_map = {'itemName': item_name, 'startDepth': start_depth, 'endDepth': end_depth, 'n': n}

        if start_depth > 0:
            query = query + '''
                and exists(select 1 from CommentsClosure
                where %(parentId)s = CommentsClosure.ancestor and Comments.id = CommentsClosure.descendent)
            '''
            query_map['parentId'] = parent_id

        query = query + '''
            order by ((2 * (upVotes + downVotes)) / depth) desc, depth asc, id asc
            limit %(n)s
        '''

        returned_comments = []

        cur.execute(query, query_map)
        conn.commit()
        top_rated_result = cur.fetchall()

        if top_rated_result:
            comment_ids = flatten_result(top_rated_result)

            cur.execute(
                '''
                    select ancestor from CommentsClosure
                    join Comments on ancestor = id
                    where descendent in %(commentIds)s and depth > %(startDepth)s
                ''',
                {'commentIds': comment_ids, 'startDepth': start_depth}
            )
            conn.commit()
            ancestors_result = cur.fetchall()

            if ancestors_result:
                backtracked_comment_ids = flatten_result(ancestors_result)
                comment_ids = comment_ids + backtracked_comment_ids

            relevant_comments = fetch_relevant_comments_dict(conn, comment_ids)

        return generate_success_response(json.dumps(relevant_comments, default=str))

def fetch_relevant_comments_dict(conn, comment_ids):
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(
            '''
                select * from Comments
                where id in %(commentIds)s
            ''',
            { 'commentIds': comment_ids}
        )
        conn.commit()
        return cur.fetchall()