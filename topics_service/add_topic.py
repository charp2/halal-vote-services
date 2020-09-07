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
def add_topic(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            topic_title = data.get('topicTitle')
            username = data.get('username')
            image = data.get('image')

            cur.execute('select exists(select * from Topics where topicTitle=%(topicTitle)s)', {'topicTitle': topic_title})
            conn.commit()

            result = cur.fetchone()
            if result:
                if result[0] == 1:
                    return generate_error_response(409, "Topic already exists")
                else:
                    cur.execute('insert into Topics (topicTitle, username, halalPoints, haramPoints, numVotes) values(%(topicTitle)s, %(username)s, 0, 0, 0)', {'topicTitle': topic_title, 'username': username})
                    
                    if image:
                        cur.execute('insert into TopicImages (topicTitle, username, image) values(%(topicTitle)s, %(username)s, %(image)s)', {'topicTitle': topic_title, 'username': username, 'image': image})
                    
                    conn.commit()
                    return generate_success_response(topic_title)
            else:
                return generate_error_response(500, "Checking if topic exists failed.")

    except Exception as e:
        return generate_error_response(500, str(e))
