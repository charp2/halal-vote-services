# standard python imports
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import generate_timestamp
from datetime import datetime, timedelta

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
            end_time = generate_timestamp()

            if interval != "d" and interval != "w":
                return generate_error_response(400, "Previous type is invalid.")

            if num_intervals == None:
                start_time = datetime.min
            else:
                num_intervals = int(num_intervals)
                halal_counts = [None] * num_intervals
                haram_counts = [None] * num_intervals

                if interval == "d":
                    start_time = end_time - timedelta(days=num_intervals)
                else:
                    start_time = end_time - timedelta(weeks=num_intervals)
                
                start_time = datetime.combine(start_time, datetime.min.time())

            cur.execute('''
                select utv.vote, utv.voteTime, utv.halalPoints, utv.haramPoints, utv.removalTime from UserTopicVotes utv
                inner join 
                    (
                        select 
                        max(voteTime) max_vote_time
                        from UserTopicVotes
                        where voteTime > %(startTime)s and topicTitle=%(topicTitle)s
                        group by date(`voteTime`)
                    ) as utv_maxes
                on utv.voteTime = utv_maxes.max_vote_time
            ''', {'startTime': start_time, 'topicTitle': topic_title})
            conn.commit()
            vote_results = cur.fetchall()

            if vote_results:
                for vote_result in vote_results:
                    vote = vote_result["vote"]
                    vote_time = vote_result["voteTime"]
                    halal_points = vote_result["halalPoints"]
                    haram_points = vote_result["haramPoints"]
                    removal_time = vote_result["removalTime"]

                    diff = (end_time - vote_time).days if interval == "d" else (end_time - vote_time).days // 7

                    if removal_time:
                        vote_time_floor = datetime.combine(vote_time, datetime.min.time())
                        removal_time_floor = datetime.combine(removal_time, datetime.min.time())

                        if vote_time_floor == removal_time_floor:
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
                last_halal_points, last_haram_points = initial_count_results

            for i in range(num_intervals):
                if halal_counts[i] == None:
                    halal_counts[i] = last_halal_points
                else:
                    last_halal_points = halal_counts[i]
                
                if haram_counts[i] == None:
                    haram_counts[i] = last_haram_points
                else:
                    last_haram_points = haram_counts[i]

            return generate_success_response({"halalCounts": halal_counts, "haramCounts": haram_counts})

    except Exception as e:
        return generate_error_response(500, str(e))
