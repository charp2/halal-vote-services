# standard python imports
import sys
import logging
import pymysql
import json

# our imports
import rds_config
from items_service.make_item import make_item
from items_service.delete_item import delete_item
from common.user_auth import valid_user

# rds settings
rds_host  = rds_config.db_host
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name

# logging config
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
    requestBody = json.loads(event['body'])
    requestHeaders = event['headers']

    is_valid_user = valid_user(requestBody['username'], requestHeaders['sessionToken'], conn, logger)

    if not isinstance(is_valid_user, bool):
        return {'statusCode': 500, 'body': is_valid_user}
    elif not is_valid_user:
        return { 'statusCode': 401, 'body': 'User Not Authorized' }

    if (event['path'] == '/make-item'):
        responseStatus, responseBody = make_item(requestBody, conn, logger)
    elif (event['path'] == '/delete-item'):
        responseStatus, responseBody = delete_item(requestBody, conn, logger)
    else:
        responseStatus, responseBody = 404, "No path found..."

    return { 'statusCode': responseStatus, 'body': responseBody }
