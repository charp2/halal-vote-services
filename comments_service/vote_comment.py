# standard python imports

#  our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import convert_bit_to_int

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

        prev_vote = get_user_vote(conn, comment_id, username)
        update_comment_vote(conn, comment_id, vote, prev_vote)
        if vote_exists(prev_vote):
            update_user_comment_vote(conn, comment_id, username, vote, prev_vote)
        else:
            add_user_comment_vote(conn, comment_id, username, vote)

        conn.commit()
        return generate_success_response(vote)

    except Exception as e:
        conn.rollback()
        return generate_error_response(500, str(e))

def vote_exists(prev_vote):
    return prev_vote != None

def get_user_vote(conn, comment_id, username):
    with conn.cursor() as cur:
        cur.execute('''select vote from UserCommentVotes where commentId = %(commentId)s and username = %(username)s''', {'commentId': comment_id, 'username': username})
        result = cur.fetchone()
        
        if result:
            return convert_bit_to_int(result[0])
        else:
            return None

def update_user_comment_vote(conn, comment_id: int, username: str, vote: int, prev_vote: int):
    with conn.cursor() as cur:
        if vote == prev_vote:
            cur.execute('''delete from UserCommentVotes where (username = %(username)s) and (commentId = %(commentId)s)''', {'username': username, 'commentId': comment_id})
        elif vote != prev_vote:
            cur.execute('''update UserCommentVotes set vote = %(vote)s where username = %(username)s and commentId = %(commentId)s''', {'vote': vote, 'username': username, 'commentId': comment_id})

def add_user_comment_vote(conn, comment_id: int, username: str, vote: int):
    with conn.cursor() as cur:
        cur.execute('''insert into UserCommentVotes(username, commentId, vote) values (%(username)s, %(commentId)s, %(vote)s)''', {'username': username, 'commentId': comment_id, 'vote': vote})


def update_comment_vote(conn, comment_id, vote, prev_vote: int = None):
    with conn.cursor() as cur:
        if vote_exists(prev_vote):
            if vote != prev_vote:
                if vote:
                    query = '''
                        update Comments 
                        set upVotes = upVotes + 1, downVotes = downVotes - 1 
                        WHERE id = %(id)s
                    '''
                else:
                    query = '''
                        update Comments 
                        set upVotes = upVotes - 1, downVotes = downVotes + 1 
                        WHERE id = %(id)s
                    '''
            elif vote == prev_vote:
                if vote:
                    query = '''
                        update Comments 
                        set upVotes = upVotes - 1 
                        WHERE id = %(id)s
                    '''
                else:
                    query = '''
                        update Comments 
                        set downVotes = downVotes - 1 
                        WHERE id = %(id)s
                    '''
        elif not vote_exists(prev_vote):
            if vote:
                query = '''
                    update Comments 
                    set upVotes = upVotes + 1 
                    WHERE id = %(id)s
                '''
            else:
                query = '''
                    update Comments 
                    set downVotes = downVotes + 1
                    WHERE id = %(id)s
                '''

        cur.execute(query, {'id': comment_id})