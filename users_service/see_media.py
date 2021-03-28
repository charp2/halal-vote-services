# standard python imports
import sys
import json
import pymysql

# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    'username': str,
    'mediaId': int
}
def see_media(data: dataType, request_headers: any, conn, logger):
    media_id = data.get('mediaId')
    username = data.get('username')

    # Access DB
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            if username != None and media_id != None:
                query_map = {'username': username, 'mediaId': media_id}

                cur.execute('select COUNT(*) as num from UserSeenMedia where username=%(username)s and mediaId=%(mediaId)s', query_map)
                alreadySeen = cur.fetchall()[0]['num']

                if (alreadySeen==0):
                    query = '''
                        insert into UserSeenMedia (username, mediaId) values(%(username)s, %(mediaId)s)
                    '''
                    cur.execute(query, query_map)
                    conn.commit()
                    return generate_success_response(str(media_id) + ' ' + username)
                else:
                    return generate_success_response('already seen')

    except Exception as e:
        return generate_error_response(500, str(e))