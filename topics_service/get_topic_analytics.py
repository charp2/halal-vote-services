# standard python imports
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import get_utc_offset
from utils import get_time_floor
from datetime import datetime, timedelta
import math

dataType = {
    "topicTitle": str,
    "interval": str,
    "numIntervals": str,
    "userTimestamp": str
}
def get_topic_analytics(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            topic_title = data['topicTitle']
            interval = data['interval'].lower()
            num_intervals = data.get('numIntervals', None)
            user_time = datetime.fromisoformat(data['userTimestamp'])
            end_time = get_time_floor(user_time)

            if interval != "d" and interval != "w" and interval != "a":
                return generate_error_response(400, "interval type is invalid")

            timezone = get_utc_offset(user_time)
            cur.execute('''
                set time_zone = %(timezone)s
            ''', {'timezone': timezone})
            conn.commit()

            if interval == "a":
                cur.execute('''
                    select voteTime from UserTopicVotes
                    where topicTitle = %(topicTitle)s
                    ORDER BY voteTime ASC LIMIT 1
                ''', {'topicTitle': topic_title})
                conn.commit()
                start_time = cur.fetchone()

                if start_time:
                    start_time = get_time_floor(start_time["voteTime"])
                    num_intervals = (end_time - start_time).days + 1

                    if num_intervals <= 365:
                        interval = "d"
                        num_intervals = max(7, num_intervals)

                    else:
                        interval = "w"
                        num_intervals = math.ceil(num_intervals / 7)

                else:
                    response = {"interval": "d", "halalCounts": [0] * 7, "haramCounts": [0] * 7}
                    return generate_success_response(response)

            elif num_intervals != None:
                num_intervals = int(num_intervals)

                if interval == "d":
                    start_time = end_time - timedelta(days=num_intervals - 1)
                elif interval == "w":
                    start_time = end_time - timedelta(weeks=num_intervals - 1)
                    
            else:
                return generate_error_response(400, "numIntervals must be passed in for interval type d or w")

            halal_counts = [None] * num_intervals
            haram_counts = [None] * num_intervals

            cur.execute('''
                select utv.voteTime, utv.halalPoints, utv.haramPoints from UserTopicVotes utv
                inner join 
                    (
                        select 
                        max(voteTime) max_vote_time
                        from UserTopicVotes
                        where voteTime >= %(startTime)s and topicTitle=%(topicTitle)s
                        group by date(`voteTime`)
                    ) as utv_maxes
                on utv.voteTime = utv_maxes.max_vote_time
            ''', {'startTime': start_time, 'topicTitle': topic_title})
            conn.commit()
            vote_results = cur.fetchall()

            if vote_results:
                for vote_result in vote_results:
                    vote_time = vote_result["voteTime"]
                    vote_time_floor = get_time_floor(vote_time)
                    halal_points = vote_result["halalPoints"]
                    haram_points = vote_result["haramPoints"]

                    vote_time_diff = (end_time - vote_time_floor).days if interval == "d" else (end_time - vote_time_floor).days // 7

                    current_halal_count = halal_counts[num_intervals - 1 - vote_time_diff]
                    current_haram_count = haram_counts[num_intervals - 1 - vote_time_diff]

                    if current_halal_count == None or current_halal_count["time"] < vote_time:
                        halal_counts[num_intervals - 1 - vote_time_diff] = {"points": halal_points, "time": vote_time}
                    
                    if current_haram_count == None or current_haram_count["time"] < vote_time:
                        haram_counts[num_intervals - 1 - vote_time_diff] = {"points": haram_points, "time": vote_time}
            
            last_halal_points = 0
            last_haram_points = 0

            cur.execute('''
                select halalPoints, haramPoints from UserTopicVotes
                where topicTitle = %(topicTitle)s and voteTime < %(startTime)s
                ORDER BY voteTime DESC LIMIT 1
            ''', {'topicTitle': topic_title, 'startTime': start_time})
            conn.commit()
            initial_count_results = cur.fetchone()

            if initial_count_results:
                last_halal_points = initial_count_results["halalPoints"]
                last_haram_points = initial_count_results["haramPoints"]

            for i in range(num_intervals):
                if halal_counts[i] == None:
                    halal_counts[i] = last_halal_points
                else:
                    halal_counts[i] = halal_counts[i]["points"]
                    last_halal_points = halal_counts[i]
                
                if haram_counts[i] == None:
                    haram_counts[i] = last_haram_points
                else:
                    haram_counts[i] = haram_counts[i]["points"]
                    last_haram_points = haram_counts[i]

            return generate_success_response({"interval": interval, "halalCounts": halal_counts, "haramCounts": haram_counts})

    except Exception as e:
        return generate_error_response(500, str(e))
