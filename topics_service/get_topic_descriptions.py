# standard python imports
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "topicTitle": str
}
def get_topic_descriptions(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            topic_title = data['topicTitle']

            cur.execute('select username, description from TopicDescriptions where topicTitle=%(topicTitle)s', {'topicTitle': topic_title})
            conn.commit()

            result = cur.fetchall()
            if result:
                return generate_success_response(result)
            else:
                return generate_error_response(500, "Getting Topic Descriptions failed.")

    except Exception as e:
        return generate_error_response(500, str(e))
