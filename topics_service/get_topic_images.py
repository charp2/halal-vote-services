# standard python imports
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import valid_user

dataType = {
    "topicTitle": str,
    "username": str
}
def get_topic_images(data: dataType, request_headers: any, conn, logger):
    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            topic_title = data['topicTitle']
            username = data.get('username')
            sessiontoken = request_headers.get('sessiontoken', '')

            if username != None:
                status_code, msg = valid_user(username, sessiontoken, conn, logger)

                if status_code != 200:
                    return generate_error_response(status_code, msg)

                cur.execute('''
                    select TopicImages.*, UserTopicImageLikes.imageId is not null as userLike
                    from TopicImages left join UserTopicImageLikes on TopicImages.id = UserTopicImageLikes.imageId and UserTopicImageLikes.username = %(username)s
                    where topicTitle=%(topicTitle)s
                    order by TopicImages.likes DESC
                ''', {'username': username, 'topicTitle': topic_title})
                conn.commit()
            
            else:
                cur.execute('select id, username, image, likes from TopicImages where topicTitle=%(topicTitle)s order by likes DESC', {'topicTitle': topic_title})
                conn.commit()

            result = cur.fetchall()
            return generate_success_response(result)

    except Exception as e:
        return generate_error_response(500, str(e))
