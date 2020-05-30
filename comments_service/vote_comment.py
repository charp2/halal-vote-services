# standard python imports

#  our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "commentId": int,
    "username": str,
    "vote": int
}
def vote_comment(data: dataType, conn, logger):
    # Access DB
    try:
        comment_id = data.get('commentId')
        username = data.get('username')
        vote = data.get('vote')

        with conn.cursor() as cur:
            fetched_vote = get_user_vote(conn, comment_id, username)

            if fetched_vote:
                if vote != fetched_vote:
                    if vote:
                        cur.execute('update Comments set upVotes = upVotes + 1, downVotes = downVotes - 1 WHERE id = %(id)s', {'id': comment_id})
                        conn.commit()
                    else:
                        cur.execute('update Comments set upVotes = upVotes - 1, downVotes = downVotes + 1 WHERE id = %(id)s', {'id': comment_id})
                        conn.commit()
                    
                    update_user_comment_vote(conn, comment_id, username, vote)

                    return generate_success_response("Vote successfully changed to %s" %(vote))

                else:
                    return generate_success_response("Already voted %s" %(vote))

            else:
                if vote:
                    cur.execute('update Comments set upVotes = upVotes + 1 WHERE id = %(id)s', {'id': comment_id})
                    conn.commit()
                else:
                    cur.execute('update Comments set downVotes = downVotes + 1 WHERE id = %(id)s', {'id': comment_id})
                    conn.commit()
                
                add_user_comment_vote(conn, comment_id, username, vote)

                return generate_success_response("Vote successfully added as %s" %(vote))

    except Exception as e:
        return generate_error_response(500, str(e))

def get_user_vote(conn, comment_id, username):
    with conn.cursor() as cur:
        cur.execute('select vote from UserCommentVotes where commentId = %(commentId)s and username = %(username)s', {'commentId': comment_id, 'username': username})
        result = cur.fetchone()
        
        if result:
            return result[0]
        else:
            return None

def update_user_comment_vote(conn, comment_id: int, username: str, vote: int):
    with conn.cursor() as cur:
        cur.execute('update UserCommentVotes set vote = %(vote)s WHERE username = %(username)s and commentId = %(commentId)s', {'vote': vote, 'username': username, 'commentId': comment_id})
        conn.commit()

def add_user_comment_vote(conn, comment_id: int, username: str, vote: int):
    with conn.cursor() as cur:
        cur.execute('insert into UserCommentVotes(username, commentId, vote) values (%(username)s, %(commentId)s, %(vote)s)', {'username': username, 'commentId': comment_id, 'vote': vote})
        conn.commit()
