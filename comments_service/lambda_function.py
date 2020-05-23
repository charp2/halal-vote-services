# standard python imports
import sys
import logging
import pymysql
import json

# our imports
import rds_config
from comments_service.add_comment import add_comment
from utils import valid_user

# rds settings
rds_host  = rds_config.db_host
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name

# logging config
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# apis not requiring sessionToken
no_session_token = []

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
    requestBody = json.loads(event['body'])
    requestHeaders = event['headers']

    if path not in no_session_token:
        status_code, msg = valid_user(requestBody['username'], requestHeaders['sessionToken'], conn, logger)

        if status_code != 200:
            return {'statusCode': status_code, 'body': msg}

    if (path == '/add-comment'):
        responseStatus, responseBody = add_comment(requestBody, conn, logger)
    else:
        responseStatus, responseBody = 404, "No path found..."

    return { 'statusCode': responseStatus, 'body': responseBody }
