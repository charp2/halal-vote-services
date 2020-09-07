# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import flatten_result

dataType = {
    "username": str,
    "topicTitle": str
}
def delete_topic_image(data: dataType, conn, logger):
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
                '''delete from TopicImages where topicTitle=%(topicTitle)s and username=%(username)s''',
                {'topicTitle': topic_title, 'username': username}
            )
            conn.commit()

            if cur.rowcount > 0:
                return generate_success_response("Removed topic image from '%s' for user '%s" %(topic_title, username))
            else:
                return generate_error_response(404, "Topic image not found")

    except Exception as e:
        return generate_error_response(500, str(e))
