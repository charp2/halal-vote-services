# standard python imports
import json
import pymysql

#  our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import flatten_result
from comments_service.utils import get_parent_depth
from comments_service.utils import parent_depth_found

dataType = {
    "itemName": str,
    "commentType": str,
    "parentId": int,
    "depth": int,
    "n": int,
    "excludedCommentIds": [int]
}
def get_comments(data: dataType, conn, logger):
    # Access DB
    try:
        item_name = data.get('itemName')
        comment_type = data.get('commentType')
        parent_id = data.get('parentId')
        depth = data.get('depth')
        n = data.get('n')
        excluded_comment_ids = list(map(str, data.get('excludedCommentIds', [])))

        with conn.cursor() as cur:
            if is_show_more_request(parent_id):
                parent_depth = get_parent_depth(conn, parent_id)

                if parent_depth_found(parent_depth):
                    return fetch_comments(conn, item_name, comment_type, parent_depth, parent_depth + depth, n, excluded_comment_ids, parent_id=parent_id)

                else:
                    return generate_error_response(404, "parentId does not exist")

            else:
                return fetch_comments(conn, item_name, comment_type, 0, depth, n, excluded_comment_ids)

    except Exception as e:
        return generate_error_response(500, str(e))

def is_show_more_request(parent_id: int):
    return parent_id != None

def fetch_comments(conn, item_name, comment_type, start_depth, end_depth, n, excluded_comment_ids, parent_id=None):
    with conn.cursor() as cur:
        query = '''
            select id, upVotes, downVotes, depth from Comments
            where itemName=%(itemName)s and commentType=%(commentType)s and %(startDepth)s < depth and depth <= %(endDepth)s
        '''
        query_map = {'itemName': item_name, 'commentType': comment_type, 'startDepth': start_depth, 'endDepth': end_depth, 'n': n}

        if start_depth > 0:
            query = query + '''
                and exists(select 1 from CommentsClosure
                where %(parentId)s = CommentsClosure.ancestor and Comments.id = CommentsClosure.descendent)
            '''
            query_map['parentId'] = parent_id

        if excluded_comment_ids:
            query = '''
                select * from (
                    select * from (''' + query + ''') a left join CommentsClosure
                    on ( (id = descendent and ancestor in %(excludedCommentIds)s ) )
                ) c
                where c.id not in %(excludedCommentIds)s and c.ancestor is NULL
            '''
            query_map['excludedCommentIds'] = excluded_comment_ids

        query = query + '''
            order by ((2 * (upVotes + downVotes)) / depth) desc, depth asc
            limit %(n)s
        '''

        relevant_comments = []

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

            relevant_comments = fetch_relevant_comments(conn, comment_ids)

        return generate_success_response(json.dumps(relevant_comments, default=str))

def fetch_relevant_comments(conn, comment_ids):
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(
            '''
                select id, username, comment, upVotes, downVotes, ancestor, descendent
                from Comments left join CommentsClosure
                on (id = ancestor or id = descendent) and isDirect = 1
                where id in %(commentIds)s and ( (ancestor in %(commentIds)s or ancestor is NULL) or (descendent in %(commentIds)s or descendent is NULL) )
            ''',
            { 'commentIds': comment_ids}
        )
        conn.commit()
        return cur.fetchall()