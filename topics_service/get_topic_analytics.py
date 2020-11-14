# standard python imports
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import generate_timestamp
from utils import get_time_floor
from datetime import datetime, timedelta
import math

dataType = {
    "topicTitle": str,
    "interval": str,
    "numIntervals": str
}
def get_topic_analytics(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            topic_title = data['topicTitle']
            interval = data['interval'].lower()
            num_intervals = data.get('numIntervals', None)
            end_time = get_time_floor(generate_timestamp())

            if interval != "d" and interval != "w" and interval != "a":
                return generate_error_response(400, "interval type is invalid")

            elif interval == "a":
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
                    
                    halal_counts = [None] * num_intervals
                    haram_counts = [None] * num_intervals

                else:
                    response = {"interval": "d", "halalCounts": [0] * 7, "haramCounts": [0] * 7}
                    return generate_success_response(response)

            elif num_intervals != None:
                num_intervals = int(num_intervals)
                halal_counts = [None] * num_intervals
                haram_counts = [None] * num_intervals

                if interval == "d":
                    start_time = end_time - timedelta(days=num_intervals - 1)
                elif interval == "w":
                    start_time = end_time - timedelta(weeks=num_intervals - 1)
                    
            else:
                return generate_error_response(400, "numIntervals must be passed in for interval type d or w")

            cur.execute('''
                select utv.vote, utv.voteTime, utv.halalPoints, utv.haramPoints, utv.removalTime from UserTopicVotes utv
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
                    vote = vote_result["vote"]
                    vote_time = get_time_floor(vote_result["voteTime"])
                    halal_points = vote_result["halalPoints"]
                    haram_points = vote_result["haramPoints"]
                    removal_time = vote_result["removalTime"]

                    diff = (end_time - vote_time).days if interval == "d" else (end_time - vote_time).days // 7

                    if removal_time:
                        removal_time = get_time_floor(removal_time)

                        if vote_time == removal_time:
                            if vote > 0:
                                halal_points -= 1
                            elif vote < 0:
                                haram_points -= 1

                    halal_counts[num_intervals - 1 - diff] = halal_points
                    haram_counts[num_intervals - 1 - diff] = haram_points
            
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
                    last_halal_points = halal_counts[i]
                
                if haram_counts[i] == None:
                    haram_counts[i] = last_haram_points
                else:
                    last_haram_points = haram_counts[i]

            return generate_success_response({"interval": interval, "halalCounts": halal_counts, "haramCounts": haram_counts})

    except Exception as e:
        return generate_error_response(500, str(e))
