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
                start_time = None
            else:
                num_intervals = int(num_intervals)
                halal_counts = [None] * num_intervals
                haram_counts = [None] * num_intervals

                if interval == "d":
                    start_time = end_time - timedelta(days=num_intervals)
                else:
                    start_time = end_time - timedelta(weeks=num_intervals)

            query_string = 'select username, timeStamp, vote from UserTopicVotes where topicTitle=%(topicTitle)s'
            query_params = {'topicTitle': topic_title}

            if start_time != None:
                query_string += ' and timeStamp > %(startTime)s'
                query_params['startTime'] = start_time
                query_params['endTime'] = end_time
            
            query_string += ' order by timeStamp ASC'
            cur.execute(query_string, query_params)
            conn.commit()
            vote_results = cur.fetchall()

            cur.execute('''
                select halalPoints, haramPoints from Topics
                where topicTitle=%(topicTitle)s
            ''', {'topicTitle': topic_title})
            conn.commit()
            final_vote_results = cur.fetchone()

            final_halal_votes = 0
            final_haram_votes = 0

            if final_vote_results:
                final_halal_votes = final_vote_results["halalPoints"]
                final_haram_votes = final_vote_results["haramPoints"]

            running_halal_votes = 0
            running_haram_votes = 0

            if vote_results and len(vote_results) > 0:
                running_halal_voters = set()
                running_haram_voters = set()

                for value in vote_results:
                    current_user = value["username"]
                    current_time = value["timeStamp"]
                    current_vote = value["vote"]
                    diff = (end_time - current_time).days if interval == "d" else (end_time - current_time).days // 7

                    if current_vote > 0:
                        running_halal_votes += 1
                        running_halal_voters.add(current_user)
                        halal_counts[num_intervals - 1 - diff] = running_halal_votes

                        if current_user in running_haram_voters:
                            running_haram_votes -= 1
                            running_haram_voters.remove(current_user)

                            if haram_counts[num_intervals - 1 - diff] == None:
                                haram_counts[num_intervals - 1 - diff] = -1
                            else:
                                haram_counts[num_intervals - 1 - diff] -= 1

                    elif current_vote < 0:
                        running_haram_votes += 1
                        running_haram_voters.add(current_user)
                        haram_counts[num_intervals - 1 - diff] = running_haram_votes

                        if current_user in running_halal_voters:
                            running_halal_votes -= 1
                            running_halal_voters.remove(current_user)

                            if halal_counts[num_intervals - 1 - diff] == None:
                                halal_counts[num_intervals - 1 - diff] = -1
                            else:
                                halal_counts[num_intervals - 1 - diff] -= 1

            halal_count_diff = final_halal_votes - running_halal_votes
            haram_count_diff = final_haram_votes - running_haram_votes
            last_halal_count = 0
            last_haram_count = 0

            for i in range(num_intervals):
                if halal_counts[i] == None:
                    halal_counts[i] = last_halal_count
                else:
                    if halal_counts[i] < 0:
                        halal_counts[i] += last_halal_count
                    last_halal_count = halal_counts[i]
                halal_counts[i] += halal_count_diff

                if haram_counts[i] == None:
                    haram_counts[i] = last_haram_count
                else:
                    if haram_counts[i] < 0:
                        haram_counts[i] += last_haram_count
                    last_haram_count = haram_counts[i]
                haram_counts[i] += haram_count_diff

            return generate_success_response({"halalCounts": halal_counts, "haramCounts": haram_counts})

    except Exception as e:
        return generate_error_response(500, str(e))
