# standard python imports
import json
import pymysql

#  our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import flatten_result
from comments_service.utils import get_parent_depth
from comments_service.utils import parent_depth_found

sort_query = '''
    order by (25 * (upVotes + downVotes + 1)) / GREATEST(1, POWER(TIMESTAMPDIFF(HOUR, timeStamp, CURRENT_TIMESTAMP()), 1/2)) desc,
    timeStamp desc
'''

dataType = {
    "topicTitle": str,
    "username": str,
    "commentType": str,
    "parentId": int,
    "depth": int,
    "n": int,
    "excludedCommentIds": [int],
    "singleCommentId": int,
}
def get_comments(data: dataType, conn, logger):
    # Access DB
    try:
        topic_title = data.get('topicTitle')
        username = data.get('username')
        comment_type = data.get('commentType')
        parent_id = data.get('parentId')
        depth = data.get('depth')
        n = data.get('n')
        excluded_comment_ids = list(map(str, data.get('excludedCommentIds', [])))
        single_comment_id = data.get('singleCommentId')

        with conn.cursor() as cur:
            if is_show_more_request(parent_id):
                parent_depth = get_parent_depth(conn, parent_id)

                if parent_depth_found(parent_depth):
                    comment_rows = fetch_comments(conn, topic_title, comment_type, parent_depth, parent_depth + depth, n, excluded_comment_ids, parent_id=parent_id, requestors_username=username)
                    comments_object = make_comments_object(comment_rows)
                    return generate_success_response(comments_object)

                else:
                    return generate_error_response(404, "parentId does not exist")

            else:
                comment_rows = fetch_comments(conn, topic_title, comment_type, 0, depth, n, excluded_comment_ids, single_comment_id, requestors_username=username)
                comments_object = make_comments_object(comment_rows)
                return generate_success_response(comments_object)

    except Exception as e:
        return generate_error_response(500, str(e))

def is_show_more_request(parent_id: int):
    return parent_id != None

def fetch_comments(conn, topic_title, comment_type, start_depth, end_depth, n, excluded_comment_ids, single_comment_id, parent_id=None, requestors_username:str = None):
    with conn.cursor() as cur:
        query_map = {'startDepth': start_depth, 'endDepth': end_depth, 'n': n}
        
        if start_depth > 0:
            query = '''
                select * from Comments
                where %(startDepth)s < depth and depth <= %(endDepth)s
                and exists(select 1 from CommentsClosure
                where %(parentId)s = CommentsClosure.ancestor and Comments.id = CommentsClosure.descendent)
            '''
            query_map['parentId'] = parent_id
        else:
            query = '''
                select * from Comments
                where topicTitle=%(topicTitle)s and commentType=%(commentType)s and %(startDepth)s < depth and depth <= %(endDepth)s
            '''
            query_map['topicTitle'] = topic_title
            query_map['commentType'] = comment_type

        if excluded_comment_ids:
            query = '''
                select * from (
                    select * from (''' + query + ''') a left join CommentsClosure
                    on ( (id = descendent and ancestor in %(excludedCommentIds)s ) )
                ) c
                where c.id not in %(excludedCommentIds)s and c.ancestor is NULL
            '''
            query_map['excludedCommentIds'] = excluded_comment_ids

        if single_comment_id:
            query = '''
                select * from Comments
                where topicTitle=%(topicTitle)s and commentType=%(commentType)s and id=%(singleCommentId)s
            '''
            query_map['singleCommentId'] = single_comment_id

        query = query + sort_query + '''
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

            relevant_comments = fetch_relevant_comments(conn, comment_ids, requestors_username=requestors_username)

        return relevant_comments

def fetch_relevant_comments(conn, comment_ids, requestors_username: str = None):
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        if requestors_username == None:
            cur.execute(
                '''
                    select id, timeStamp, username, comment, commentType, upVotes, downVotes, numReplies, ancestor, descendent
                    from Comments left join CommentsClosure
                    on (id = ancestor or id = descendent) and isDirect = 1 and ( (ancestor in %(commentIds)s or ancestor is NULL) and (descendent in %(commentIds)s or descendent is NULL) )
                    where id in %(commentIds)s
                ''' + sort_query,
                { 'commentIds': comment_ids }
            )
        elif requestors_username != None:
            cur.execute(
                '''
                    select id, timeStamp, c.username, comment, commentType, upVotes, downVotes, numReplies, ancestor, descendent, vote 
                    from 
                        (select * from Comments left join CommentsClosure
                        on (id = ancestor or id = descendent) and isDirect = 1 and ( (ancestor in %(commentIds)s or ancestor is NULL) and (descendent in %(commentIds)s or descendent is NULL) )
                        where id in %(commentIds)s
                        ''' + sort_query + ''') c
                    left join UserCommentVotes ucv
                    on (c.id = ucv.commentId) and ucv.username = %(requestorsUsername)s
                ''',
                { 'commentIds': comment_ids, 'requestorsUsername': requestors_username }
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
        timestamp = row["timeStamp"]
        username = row["username"]
        comment = row["comment"]
        comment_type = row["commentType"]
        up_votes = row["upVotes"]
        down_votes = row["downVotes"]
        num_replies = row["numReplies"]
        ancestor_id = row["ancestor"]
        descendent_id = row["descendent"]
        user_vote = row.get("vote")

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

        elif not ancestor_tree_set_id and descendent_tree_set_id:
            handle_case_three(comments_object, ancestor_map, tree_sets, ancestor_id, descendent_id, descendent_tree_set_id)

        elif ancestor_tree_set_id and descendent_tree_set_id and ancestor_tree_set_id != descendent_tree_set_id:
            handle_case_four(comments_object, ancestor_map, tree_sets, ancestor_id, ancestor_tree_set_id, descendent_id, descendent_tree_set_id)

        if not comment_id in filled_comments:
            comment = {
                "id": comment_id,
                "timeStamp": timestamp,
                "username": username,
                "comment": comment,
                "commentType": comment_type,
                "upVotes": up_votes,
                "downVotes": down_votes,
                "numReplies": num_replies,
                "userVote": None if (user_vote == None) else ord(user_vote)
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

# descendent part of tree, but ancestor is not
def handle_case_three(comments_object, ancestor_map, tree_sets, ancestor_id, descendent_id, descendent_tree_set_id):
    for tree_id, tree_set in tree_sets:
        if tree_id == descendent_tree_set_id:
            tree_set.add(ancestor_id)
            break

    descendent_comment_object = comments_object[descendent_tree_set_id]
    del descendent_comment_object['root']
    comments_object[descendent_tree_set_id] = {
        "root": ancestor_id,
        "replies": {
            descendent_id: descendent_comment_object
        }
    }

    ancestor_map[descendent_id] = ancestor_id
    ancestor_map[ancestor_id] = descendent_tree_set_id

# ancestor and descendent are part of different trees
def handle_case_four(comments_object, ancestor_map, tree_sets, ancestor_id, ancestor_tree_set_id, descendent_id, descendent_tree_set_id):
    for tree_id, tree_set in tree_sets:
        if tree_id == descendent_tree_set_id:
            descendent_tree_set = tree_set
            tree_sets.remove((tree_id, tree_set))
            break

    index = 0
    for tree_id, tree_set in tree_sets:
        if tree_id == ancestor_tree_set_id:
            tree_sets[index] = (tree_id, tree_set.union(descendent_tree_set))
            break
        index += 1

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
    comment_object["timeStamp"] = comment["timeStamp"]
    comment_object["username"] = comment["username"]
    comment_object["comment"] = comment["comment"]
    comment_object["commentType"] = comment["commentType"]
    comment_object["upVotes"] = comment["upVotes"]
    comment_object["downVotes"] = comment["downVotes"]
    comment_object["numReplies"] = comment["numReplies"]
    comment_object["userVote"] = comment["userVote"]

def transform_comments_object(comments_object):
    transformed_comments_object = []
    for tree_id, comment in comments_object.items():
        replies = transform_comments_object_helper(comment["replies"])
        top_level_comment = {
            "id": comment["root"],
            "timeStamp": comment["timeStamp"],
            "username": comment["username"],
            "comment": comment["comment"],
            "commentType": comment["commentType"],
            "upVotes": comment["upVotes"],
            "downVotes": comment["downVotes"],
            "numReplies": comment["numReplies"],
            "userVote": comment["userVote"],
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
            "timeStamp": comment["timeStamp"],
            "username": comment["username"],
            "comment": comment["comment"],
            "commentType": comment["commentType"],
            "upVotes": comment["upVotes"],
            "downVotes": comment["downVotes"],
            "numReplies": comment["numReplies"],
            "userVote": comment["userVote"],
            "replies": nested_replies
        })
    return replies
