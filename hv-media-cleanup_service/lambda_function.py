# standard python imports
import sys
import logging
import json
import pymysql
import boto3
import os

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import get_response_headers

# logging config
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# s3 settings
bucket_name = os.environ["HV_MEDIA_BUCKET_NAME"]

# rds settings
rds_host  = os.environ["DB_HOST"]
name = os.environ["DB_USERNAME"]
password = os.environ["DB_PASSWORD"]
db_name = os.environ["DB_NAME"]

# verify db connection
try:
    conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()
logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")

eventType = {
    'version': any, 
    'id': any, 
    'detail-type': any, 
    'source': any, 
    'account': any, 
    'time': any, 
    'region': any, 
    'resources': any, 
    'detail': any
}
# lambda entry point
def handler(event: eventType, context):
    try:
        living_media = get_living_media()
        s3_media = get_s3_media()

        diff_set = s3_media.difference(living_media)
        if (len(diff_set) < len(s3_media)):
            num_deleted = delete_s3_media(diff_set)

        responseStatus, responseBody = generate_success_response(num_deleted)
    except Exception as e:
        responseStatus, responseBody = generate_error_response(500, str(e))

    return { 'statusCode': responseStatus, 'body': responseBody, 'headers': get_response_headers() }


def get_living_media():
    with conn.cursor() as cur:
        query = '''
            select image from TopicImages
        '''
        query_map = { }

        cur.execute(query, query_map)
        conn.commit()
        result = cur.fetchall()

        livingMedia = set()
        for row in result:
            livingMedia.add(row[0].replace("https://{}.s3.amazonaws.com/".format(bucket_name), ''))

        return livingMedia

def get_s3_media():
    s3 = boto3.client('s3')

    s3Media = set()
    continuationToken = None
    isTruncated = True
    while(isTruncated):
        response = s3.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuationToken) if continuationToken!=None else s3.list_objects_v2(Bucket=bucket_name)
        isTruncated = response['IsTruncated']
        if (response.get('NextContinuationToken', None) != None):
            continuationToken = response['NextContinuationToken']

        for x in response['Contents']:
            s3Media.add(x["Key"])

    return s3Media

def delete_s3_media(keys):
    s3 = boto3.client('s3')

    objects = [*map(lambda x: { 'Key': x }, keys)]

    response = s3.delete_objects(
        Bucket=bucket_name, 
        Delete={
            'Objects': objects,    
        }
    )

    for x in response['Deleted']:
        print("deleted: {}".format(x['Key']))

    return len(response['Deleted'])