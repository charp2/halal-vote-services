# standard python imports
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import generate_timestamp
from datetime import timedelta

dataType = {
    "topicTitle": str,
    "prevType": str
}
def get_topic_analytics(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            topic_title = data['topicTitle']
            prev_type = data['prevType']
            end_time = generate_timestamp()

            if prev_type == "W":
                start_time = end_time - timedelta(days=7)
            elif prev_type == "M":
                start_time = end_time - timedelta(days=30)
            elif prev_type == "Y":
                start_time = end_time - timedelta(weeks=52)
            elif prev_type == "A":
                start_time = None
            else:
                return generate_error_response(400, "Previous type is invalid.")

            query_string = 'select timeStamp from UserTopicVotes where topicTitle=%(topicTitle)s'
            query_params = {'topicTitle': topic_title}

            if start_time != None:
                query_string += ' and timeStamp between %(startTime)s and %(endTime)s'
                query_params['startTime'] = start_time
                query_params['endTime'] = end_time
            
            query_string += ' order by timeStamp DESC'
            cur.execute(query_string, query_params)
            conn.commit()

            results = cur.fetchall()

            if results:
                len_results = len(results)
                
                counts = []
                in_days = True
                if len_results > 0:
                    if prev_type == "W":
                        counts = [0] * 7
                    elif prev_type == "M":
                        counts = [0] * 30
                    elif prev_type == "Y":
                        counts = [0] * 52
                        in_days = False
                    elif prev_type == "A":
                        start_time = results[len_results - 1]["timeStamp"]
                        num = (end_time - start_time).days
                        if num > 30:
                            num = num // 7
                            in_days = False
                        counts = [0] * (num + 1)

                    len_counts = len(counts)
                    for value in results:
                        current_time = value["timeStamp"]
                        diff = (end_time - current_time).days if in_days else (end_time - current_time).days // 7
                        counts[len_counts - 1 - diff] += 1

                return generate_success_response(counts)
            else:
                return generate_error_response(500, "Failed to fetch analytics.")

    except Exception as e:
        return generate_error_response(500, str(e))
