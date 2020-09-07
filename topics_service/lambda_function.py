# standard python imports
import sys
import logging
import pymysql
import json

# our imports
import rds_config
from topics_service.add_topic import add_topic
from topics_service.delete_topic import delete_topic
from topics_service.get_topics import get_topics
from topics_service.search_topics import search_topics
from topics_service.vote_topic import vote_topic
from topics_service.get_topic_images import get_topic_images
from topics_service.add_topic_image import add_topic_image
from topics_service.delete_topic_image import delete_topic_image
from utils import valid_user
from utils import get_response_headers

# rds settings
rds_host  = rds_config.db_host
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name

# logging config
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# apis not requiring sessionToken
no_session_token = ["/get-topics", "/search-topics", "/get-topic-images"]

# verify db connection
try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()
logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")


eventType = {
    "resource": str,
    "path": str,
    "httpMethod": str,
    "headers": dict,
    "multiValueHeaders": any, #{List of strings containing incoming request headers}
    "queryStringParameters": any, #{query string parameters }
    "multiValueQueryStringParameters": any, #{List of query string parameters}
    "pathParameters": any, #{path parameters}
    "stageVariables": any, #{Applicable stage variables}
    "requestContext": any, #{Request context, including authorizer-returned key-value pairs}
    "body": str,
    "isBase64Encoded": any, #"A boolean flag to indicate if the applicable request payload is Base64-encode"
}
# lambda entry point
def handler(event: eventType, context):
    path = event['path']
    if event['body']:
        requestBody = json.loads(event['body'])
    queryStringParams = event['queryStringParameters']
    requestHeaders = event['headers']

    if path not in no_session_token:
        status_code, msg = valid_user(requestBody.get('username'), requestHeaders.get('sessiontoken'), conn, logger)

        if status_code != 200:
            return {'statusCode': status_code, 'body': msg, 'headers': get_response_headers()}

    if (path == '/add-topic'):
        responseStatus, responseBody = add_topic(requestBody, conn, logger)
    elif (path == '/delete-topic'):
        responseStatus, responseBody = delete_topic(requestBody, conn, logger)
    elif (path == '/get-topics'):
        responseStatus, responseBody = get_topics(requestBody, requestHeaders, conn, logger)
    elif (path == '/vote-topic'):
        responseStatus, responseBody = vote_topic(requestBody, conn, logger)
    elif (path == '/search-topics'):
        responseStatus, responseBody = search_topics(queryStringParams, conn, logger)
    elif (path == '/get-topic-images'):
        responseStatus, responseBody = get_topic_images(queryStringParams, conn, logger)
    elif (path == '/add-topic-image'):
        responseStatus, responseBody = add_topic_image(requestBody, conn, logger)
    elif (path == '/delete-topic-image'):
        responseStatus, responseBody = delete_topic_image(requestBody, conn, logger)
    else:
        responseStatus, responseBody = 404, "No path found..."

    return { 'statusCode': responseStatus, 'body': responseBody, 'headers': get_response_headers() }
