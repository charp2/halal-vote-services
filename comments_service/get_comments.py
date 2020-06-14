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
                    comment_rows = fetch_comments(conn, item_name, comment_type, parent_depth, parent_depth + depth, n, excluded_comment_ids, parent_id=parent_id)
                    comments_object = make_comments_object(comment_rows)
                    return generate_success_response(json.dumps(comments_object, default=str))

                else:
                    return generate_error_response(404, "parentId does not exist")

            else:
                comment_rows = fetch_comments(conn, item_name, comment_type, 0, depth, n, excluded_comment_ids)
                comments_object = make_comments_object(comment_rows)
                return generate_success_response(json.dumps(comments_object, default=str))

    except Exception as e:
        return generate_error_response(500, str(e))

def is_show_more_request(parent_id: int):
    return parent_id != None

def fetch_comments(conn, item_name, comment_type, start_depth, end_depth, n, excluded_comment_ids, parent_id=None):
    with conn.cursor() as cur:
        query = '''
            select id from Comments
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

        return relevant_comments

def fetch_relevant_comments(conn, comment_ids):
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(
            '''
                select id, username, comment, upVotes, downVotes, numReplies, ancestor, descendent
                from Comments left join CommentsClosure
                on (id = ancestor or id = descendent) and isDirect = 1 and ( (ancestor in %(commentIds)s or ancestor is NULL) and (descendent in %(commentIds)s or descendent is NULL) )
                where id in %(commentIds)s
            ''',
            { 'commentIds': comment_ids}
        )
        conn.commit()
        return cur.fetchall()

def make_comments_object(rows):
    comments_object = {}
    ancestor_map = {}
    tree_sets = []
    next_tree_set_id = 0
    filled_comments = set()

    for row in rows:
        # comment details
        comment_id = row["id"]
        username = row["username"]
        comment = row["comment"]
        up_votes = row["upVotes"]
        down_votes = row["downVotes"]
        num_replies = row["numReplies"]
        ancestor_id = row["ancestor"]
        descendent_id = row["descendent"]

        # tracking variables
        ancestor_tree_set_id = None
        descendent_tree_set_id = None

        for tree_id, tree_set in tree_sets:
            if ancestor_id in tree_set:
                ancestor_tree_set_id = tree_id

            if descendent_id in tree_set:
                descendent_tree_set_id = tree_id

            if ancestor_tree_set_id and descendent_tree_set_id:
                break

        if not ancestor_tree_set_id and not descendent_tree_set_id:
            next_tree_set_id -= 1
            if ancestor_id and descendent_id:
                handle_case_one(comments_object, ancestor_map, tree_sets, next_tree_set_id, ancestor_id, descendent_id)
            else:
                handle_case_one(comments_object, ancestor_map, tree_sets, next_tree_set_id, comment_id, None)

        elif ancestor_tree_set_id and not descendent_tree_set_id:
            handle_case_two(comments_object, ancestor_map, tree_sets, ancestor_id, ancestor_tree_set_id, descendent_id)

        elif ancestor_tree_set_id and descendent_tree_set_id and ancestor_tree_set_id != descendent_tree_set_id:
            handle_case_three(comments_object, ancestor_map, tree_sets, ancestor_id, ancestor_tree_set_id, descendent_id, descendent_tree_set_id)

        if not comment_id in filled_comments:
            comment = {
                "id": comment_id,
                "username": username,
                "comment": comment,
                "upVotes": up_votes,
                "downVotes": down_votes,
                "numReplies": num_replies
            }
            set_comment_details(comments_object, ancestor_map, comment)
            filled_comments.add(comment_id)

    return transform_comments_object(comments_object)


# ancestor and descendent not part of any tree. If descendent_id is None, then ancestor_id will be singular comment
def handle_case_one(comments_object, ancestor_map, tree_sets, next_tree_set_id, ancestor_id, descendent_id):
    if descendent_id:
        tree_sets.append((next_tree_set_id, {ancestor_id, descendent_id}))
        ancestor_map[ancestor_id] = next_tree_set_id
        ancestor_map[descendent_id] = ancestor_id

        tree = {
            "root": ancestor_id,
            "replies": {
                descendent_id: {
                    "replies": {}
                }
            }
        }
    else:
        tree_sets.append((next_tree_set_id, {ancestor_id}))
        ancestor_map[ancestor_id] = next_tree_set_id

        tree = {
            "root": ancestor_id,
            "replies": {}
        }

    comments_object[next_tree_set_id] = tree

# ancestor part of tree, but descendent is not
def handle_case_two(comments_object, ancestor_map, tree_sets, ancestor_id, ancestor_tree_set_id, descendent_id):
    for tree_id, tree_set in tree_sets:
        if tree_id == ancestor_tree_set_id:
            tree_set.add(descendent_id)
            break

    ancestor_map[descendent_id] = ancestor_id

    ancestor_replies = get_comment_object(comments_object, ancestor_map, ancestor_id)["replies"]
    ancestor_replies[descendent_id] = {
        "replies": {}
    }

# ancestor and descendent are part of different trees
def handle_case_three(comments_object, ancestor_map, tree_sets, ancestor_id, ancestor_tree_set_id, descendent_id, descendent_tree_set_id):
    for tree_id, tree_set in tree_sets:
        if tree_id == descendent_tree_set_id:
            descendent_tree_set = tree_set
            tree_sets.remove((tree_id, tree_set))
            break

    for tree_id, tree_set in tree_sets:
        if tree_id == ancestor_tree_set_id:
            tree_set = tree_set.union(descendent_tree_set)
            break

    ancestor_map[descendent_id] = ancestor_id

    descendent = comments_object[descendent_tree_set_id]
    del descendent["root"]
    del comments_object[descendent_tree_set_id]
    ancestor_replies = get_comment_object(comments_object, ancestor_map, ancestor_id)["replies"]
    ancestor_replies[descendent_id] = descendent

def get_comment_object(comments_object, ancestor_map, comment_id):
    next_parent_id = ancestor_map[comment_id]
    path = [comment_id]
    tree_id = None
    while not tree_id:
        if next_parent_id < 0:
            tree_id = next_parent_id
        else:
            path.insert(0, next_parent_id)
            next_parent_id = ancestor_map[next_parent_id]

    path.pop(0)
    comment_object = comments_object[tree_id]

    for index in path:
        comment_object = comment_object["replies"]
        comment_object = comment_object[index]

    return comment_object

def set_comment_details(comments_object, ancestor_map, comment):
    comment_object = get_comment_object(comments_object, ancestor_map, comment["id"])
    comment_object["username"] = comment["username"]
    comment_object["comment"] = comment["comment"]
    comment_object["upVotes"] = comment["upVotes"]
    comment_object["downVotes"] = comment["downVotes"]
    comment_object["numReplies"] = comment["numReplies"]

def transform_comments_object(comments_object):
    transformed_comments_object = []
    for tree_id, comment in comments_object.items():
        replies = transform_comments_object_helper(comment["replies"])
        top_level_comment = {
            "id": comment["root"],
            "username": comment["username"],
            "comment": comment["comment"],
            "upVotes": comment["upVotes"],
            "downVotes": comment["downVotes"],
            "numReplies": comment["numReplies"],
            "replies": replies
        }
        transformed_comments_object.append(top_level_comment)

    return transformed_comments_object

def transform_comments_object_helper(comment_object_replies):
    replies = []
    for comment_id, comment in comment_object_replies.items():
        nested_replies = transform_comments_object_helper(comment["replies"])
        replies.append({
            "id": comment_id,
            "username": comment["username"],
            "comment": comment["comment"],
            "upVotes": comment["upVotes"],
            "downVotes": comment["downVotes"],
            "numReplies": comment["numReplies"],
            "replies": nested_replies
        })
    return replies