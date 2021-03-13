# standard python imports
import sys
import logging
import pymysql
import json
import os

# our imports
from comments_service.add_comment import add_comment
from comments_service.vote_comment import vote_comment
from comments_service.get_comments import get_comments
from comments_service.delete_comment import delete_comment
from utils import valid_user
from utils import get_response_headers

# rds settings
rds_host  = os.environ["DB_HOST"]
name = os.environ["DB_USERNAME"]
password = os.environ["DB_PASSWORD"]
db_name = os.environ["DB_NAME"]

# logging config
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# apis not requiring sessionToken
no_session_token = ['/get-comments']

# verify db connection
try:
    conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
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
    requestBody = json.loads(event['body'])
    requestHeaders = event['headers']

    if path not in no_session_token:
        status_code, msg = valid_user(requestBody.get('username'), requestHeaders.get('sessiontoken'), conn, logger)

        if status_code != 200:
            return {'statusCode': status_code, 'body': msg, 'headers': get_response_headers()}

    if (path == '/add-comment'):
        responseStatus, responseBody = add_comment(requestBody, conn, logger)
    elif (path == '/vote-comment'):
        responseStatus, responseBody = vote_comment(requestBody, conn, logger)
    elif (path == '/get-comments'):
        responseStatus, responseBody = get_comments(requestBody, conn, logger)
    elif (path == '/delete-comment'):
        responseStatus, responseBody = delete_comment(requestBody, conn, logger)
    else:
        responseStatus, responseBody = 404, "No path found..."

    return { 'statusCode': responseStatus, 'body': responseBody, 'headers': get_response_headers() }
