# standard python imports
import json

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "topicTitle": str,
    "username": str,
    "image": str
}
def add_topic_image(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            topic_title = data['topicTitle']
            username = data['username']
            image = data['image']

            num_rows = cur.execute('select * from Topics where topicTitle=%(topicTitle)s', {'topicTitle': topic_title})
            conn.commit()

            if num_rows != 0:
                cur.execute('insert into TopicImages (topicTitle, username, image) values(%(topicTitle)s, %(username)s, %(image)s)', {'topicTitle': topic_title, 'username': username, 'image': image})
                conn.commit()
                return generate_success_response(topic_title)
            else:
                return generate_error_response(404, "Topic not found")

    except Exception as e:
        return generate_error_response(500, str(e))
