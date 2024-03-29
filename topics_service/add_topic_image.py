# standard python imports
import json
import os

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import create_presigned_post

addTopicDataType = {
    "topicTitle": str,
    "username": str,
    "image": str
}
def add_topic_image(data: addTopicDataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            topic_title = data['topicTitle']
            username = data['username']
            image = data['image']

            num_rows = cur.execute('select * from Topics where topicTitle=%(topicTitle)s', {'topicTitle': topic_title})

            if num_rows != 0:
                cur.execute('insert into TopicImages (topicTitle, username, image) values(%(topicTitle)s, %(username)s, %(image)s)', {'topicTitle': topic_title, 'username': username, 'image': image})
                cur.execute('SELECT LAST_INSERT_ID()')
                conn.commit()
                return generate_success_response(cur.fetchall())
            else:
                return generate_error_response(404, "Topic not found")

    except Exception as e:
        return generate_error_response(500, str(e))


presignedPostDataType = {
    "objectKey": str,
}
def presigned_media_upload(data: presignedPostDataType):
    object_key = data.get('objectKey')
    hv_media_bucket_name = os.environ["HV_MEDIA_BUCKET_NAME"]

    presigned_post = create_presigned_post(hv_media_bucket_name, object_key)

    if presigned_post != None:
        return generate_success_response(presigned_post)
    else:
        return generate_error_response(500, 'failed to generate presigned post')
