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
    "prevType": str,
    "numPrev": str
}
def get_topic_analytics(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            topic_title = data['topicTitle']
            prev_type = data['prevType'].lower()
            num_prev = data.get('numPrev', None)
            end_time = generate_timestamp()

            if prev_type != "d" and prev_type != "w":
                return generate_error_response(400, "Previous type is invalid.")

            if num_prev == None:
                start_time = None
            elif prev_type == "d":
                num_prev = int(num_prev)
                start_time = end_time - timedelta(days=num_prev)
            else:
                num_prev = int(num_prev)
                start_time = end_time - timedelta(weeks=num_prev)

            query_string = 'select timeStamp from UserTopicVotes where topicTitle=%(topicTitle)s'
            query_params = {'topicTitle': topic_title}

            if start_time != None:
                query_string += ' and timeStamp > %(startTime)s'
                query_params['startTime'] = start_time
                query_params['endTime'] = end_time
            
            query_string += ' order by timeStamp DESC'
            cur.execute(query_string, query_params)
            conn.commit()

            results = cur.fetchall()

            if results and len(results) > 0:
                if num_prev == None:
                    start_time = results[len(results) - 1]["timeStamp"]
                    num_prev = (end_time - start_time).days

                    if prev_type == "w":
                        num_prev = num_prev // 7
                    
                    num_prev += 1
                
                counts = [0] * num_prev

                for value in results:
                    current_time = value["timeStamp"]
                    diff = (end_time - current_time).days if prev_type == "d" else (end_time - current_time).days // 7
                    counts[num_prev - 1 - diff] += 1

                return generate_success_response(counts)
            else:
                return generate_error_response(500, "Failed to fetch analytics.")

    except Exception as e:
        return generate_error_response(500, str(e))
