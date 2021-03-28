# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import flatten_result

dataType = {
    "id": int
}
def delete_topic_image(data: dataType, conn, logger):
    image_id = data.get('id')

    # Access DB
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''delete from TopicImages where id=%(imageId)s''',
                {'imageId': image_id}
            )

            if cur.rowcount > 0:
                cur.execute(
                    '''delete from UserTopicImageLikes where imageId=%(imageId)s''',
                    {'imageId': image_id}
                )
                cur.execute(
                    '''delete from UserSeenMedia where mediaId=%(imageId)s''',
                    {'imageId': image_id}
                )
                conn.commit()
                return generate_success_response("Removed topic image %d" %(image_id))
            else:
                return generate_error_response(404, "Topic image not found")

    except Exception as e:
        return generate_error_response(500, str(e))
