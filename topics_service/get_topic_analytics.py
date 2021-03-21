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
            requested_num_intervals = data.get('numIntervals', None)
            current_time = generate_timestamp()
            end_time = get_time_floor(current_time)

            if interval != "d" and interval != "w" and interval != "a":
                return generate_error_response(400, "interval type is invalid")

            if (interval == "d" or interval == "w") and requested_num_intervals == None:
                return generate_error_response(400, "numIntervals must be passed in for interval type d or w") 

            cur.execute('''
                select username, vote, voteTime from UserTopicVotes
                where topicTitle=%(topicTitle)s
                ORDER BY voteTime ASC
            ''', {'topicTitle': topic_title})
            vote_history = cur.fetchall()

            if vote_history and len(vote_history) > 0:
                start_time = get_time_floor(vote_history[0]["voteTime"])
                num_intervals = (end_time - start_time).days + 1

                if num_intervals <= 365:
                    interval_used = "d"
                    num_intervals = max(7, num_intervals)

                else:
                    interval_used = "w"
                    num_intervals = math.ceil(num_intervals / 7)

                requested_num_intervals = num_intervals if requested_num_intervals == None else int(requested_num_intervals)

            else:
                response = {"interval": "d", "halalCounts": [0] * 7, "haramCounts": [0] * 7}
                return generate_success_response(response)

            halal_counts = [0] * num_intervals
            haram_counts = [0] * num_intervals
            user_vote_map = {}

            for vote_record in vote_history:
                username = vote_record["username"]
                vote = vote_record["vote"]
                vote_time = vote_record["voteTime"]
                vote_time_floor = get_time_floor(vote_time)

                vote_time_diff = (end_time - vote_time_floor).days if interval_used == "d" else (end_time - vote_time_floor).days // 7

                current_halal_count = halal_counts[num_intervals - 1 - vote_time_diff]
                current_haram_count = haram_counts[num_intervals - 1 - vote_time_diff]

                if username in user_vote_map:
                    prev_vote = user_vote_map[username]

                    if prev_vote < 0:
                        current_haram_count -= 1
                    elif prev_vote > 0:
                        current_halal_count -= 1
                    
                if vote < 0:
                    current_haram_count += 1
                elif vote > 0:
                    current_halal_count += 1
                
                halal_counts[num_intervals - 1 - vote_time_diff] = current_halal_count
                haram_counts[num_intervals - 1 - vote_time_diff] = current_haram_count
                user_vote_map[username] = vote

            total_halal_points = 0
            total_haram_points = 0

            for index, halal_count in enumerate(halal_counts):
                if halal_count == None:
                    halal_counts[index] = total_halal_points
                else:
                    halal_counts[index] += total_halal_points
                total_halal_points = halal_counts[index]

            for index, haram_count in enumerate(haram_counts):
                if haram_count == None:
                    haram_counts[index] = total_haram_points
                else:
                    haram_counts[index] += total_haram_points
                total_haram_points = haram_counts[index]

            if interval == "d" or interval == "w":
                if requested_num_intervals > num_intervals:
                    halal_counts = ([0] * (requested_num_intervals - num_intervals)) + halal_counts
                    haram_counts = ([0] * (requested_num_intervals - num_intervals)) + haram_counts
                elif requested_num_intervals < num_intervals:
                    halal_counts = halal_counts[num_intervals - requested_num_intervals : num_intervals]
                    haram_counts = haram_counts[num_intervals - requested_num_intervals : num_intervals]
            
            return generate_success_response({"interval": interval_used, "halalCounts": halal_counts, "haramCounts": haram_counts})

    except Exception as e:
        return generate_error_response(500, str(e))
