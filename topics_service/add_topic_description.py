# standard python imports
import json

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "topicTitle": str,
    "username": str,
    "description": str
}
def add_topic_description(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            topic_title = data['topicTitle']
            username = data['username']
            description = data['description']

            cur.execute('select exists(select * from Topics where topicTitle=%(topicTitle)s)', {'topicTitle': topic_title})
            conn.commit()

            result = cur.fetchone()
            if result:
                if result[0] == 1:
                    cur.execute('insert into TopicDescriptions (topicTitle, username, description) values(%(topicTitle)s, %(username)s, %(description)s) on duplicate key update description=%(description)s', {'topicTitle': topic_title, 'username': username, 'description': description})
                    conn.commit()
                    return generate_success_response(topic_title)
                else:
                    return generate_error_response(404, "Topic not found")
            else:
                return generate_error_response(500, "Checking if topic exists failed.")

    except Exception as e:
        return generate_error_response(500, str(e))
