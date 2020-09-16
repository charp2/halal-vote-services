# standard python imports
import json

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "topicTitle": str,
    "username": str,
    "like": bool
}
def update_topic_image_like(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            topic_title = data['topicTitle']
            username = data['username']
            like = data['like']

            num_rows = cur.execute('select topicTitle from Topics where topicTitle=%(topicTitle)s', {'topicTitle': topic_title})

            if num_rows != 0:
                change = ""
                if like:
                    rows_affected = cur.execute('insert ignore into UserTopicImageLikes (topicTitle, username) values(%(topicTitle)s, %(username)s)', {'topicTitle': topic_title, 'username': username})

                    if rows_affected != 0:
                        change = " + 1"
                else:
                    rows_affected = cur.execute('delete from UserTopicImageLikes where topicTitle=%(topicTitle)s and username=%(username)s', {'topicTitle': topic_title, 'username': username})

                    if rows_affected != 0:
                        change = " - 1"

                query = "update TopicImages set likes = likes%s" %(change)
                query += " where topicTitle=%(topicTitle)s and username=%(username)s"
                cur.execute(query, {'topicTitle': topic_title, 'username': username})
                conn.commit()

                return generate_success_response("Updated %s vote for '%s'" %(username, topic_title))
            else:
                return generate_error_response(404, "'%s' not found" %(topic_title))

    except Exception as e:
        return generate_error_response(500, str(e))
