# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import flatten_result

dataType = {
    "username": str,
    "topicTitle": str
}
def delete_topic(data: dataType, conn, logger):
    username = data.get('username')
    topic_title = data.get('topicTitle')

    if not username:
        return generate_error_response(500, "Invalid username passed in")

    if not topic_title:
        return generate_error_response(500, "Invalid topicTitle passed in")

    # Access DB
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''delete from Topics where topicTitle=%(topicTitle)s and username=%(username)s''',
                {'topicTitle': topic_title, 'username': username}
            )

            if cur.rowcount > 0:
                cur.execute(
                    '''select id from Comments where topicTitle=%(topicTitle)s''',
                    {'topicTitle': topic_title}
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
                
                cur.execute(
                    '''delete from TopicImages where topicTitle=%(topicTitle)s''',
                    {'topicTitle': topic_title}
                )
                

                conn.commit()
                return generate_success_response("Removed Topic '%s' from Topics table" %(topic_title))

            else:
                return generate_error_response(500, "Unsuccesful delete attempt")

    except Exception as e:
        return generate_error_response(500, str(e))
