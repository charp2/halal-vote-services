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

# lambda entry point
# event: {
#     "resource": "Resource path",
#     "path": "Path parameter",
#     "httpMethod": "Incoming request's method name"
#     "headers": {String containing incoming request headers}
#     "multiValueHeaders": {List of strings containing incoming request headers}
#     "queryStringParameters": {query string parameters }
#     "multiValueQueryStringParameters": {List of query string parameters}
#     "pathParameters":  {path parameters}
#     "stageVariables": {Applicable stage variables}
#     "requestContext": {Request context, including authorizer-returned key-value pairs}
#     "body": "A JSON string of the request payload."
#     "isBase64Encoded": "A boolean flag to indicate if the applicable request payload is Base64-encode"
# }
def handler(event, context):
    requestBody = json.loads(event['body'])
    requestHeaders = event['headers']

    if not valid_user(requestBody['username'], requestHeaders['sessionToken']):
        return { 'statusCode': 401, 'body': 'User Not Authorized' }
    

    if (event['path'] == '/make-item'):
        responseStatus, responseBody = make_item(requestBody, conn, logger)
    elif (event['path'] == '/delete-item'):
        responseStatus, responseBody = delete_item(requestBody, conn, logger)
    else:
        responseStatus, responseBody = 404, "No path found..."

    return { 'statusCode': responseStatus, 'body': responseBody }
