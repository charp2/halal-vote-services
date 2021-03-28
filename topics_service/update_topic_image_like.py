# standard python imports
import json

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "imageId": int,
    "username": str,
    "like": bool
}
def update_topic_image_like(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            image_id = data['imageId']
            username = data['username']
            like = data['like']

            change = ""
            if like:
                rows_affected = cur.execute('insert ignore into UserTopicImageLikes (imageId, username) values(%(imageId)s, %(username)s)', {'imageId': image_id, 'username': username})

                if rows_affected != 0:
                    change = " + 1"
            else:
                rows_affected = cur.execute('delete from UserTopicImageLikes where imageId=%(imageId)s and username=%(username)s', {'imageId': image_id, 'username': username})

                if rows_affected != 0:
                    change = " - 1"

            query = "update TopicImages set likes = likes%s" %(change)
            query += " where id=%(id)s"
            cur.execute(query, {'id': image_id})

            cur.execute('select likes from TopicImages where id=%(imageId)s', {'imageId': image_id})

            result = cur.fetchone()

            if result:
                conn.commit()
                return generate_success_response({'likes': result[0]})
            else:
                return generate_error_response(404, "Image not found")

    except Exception as e:
        return generate_error_response(500, str(e))
