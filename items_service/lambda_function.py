# standard python imports
import sys
import logging
import pymysql
import json

# our imports
import rds_config
from items_service.add_item import add_item
from items_service.delete_item import delete_item
from items_service.get_items import get_items
from items_service.search_items import search_items
from items_service.vote_item import vote_item
from items_service.get_item_descriptions import get_item_descriptions
from items_service.add_item_description import add_item_description
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
no_session_token = ["/get-items", "/search-items", "/get-item-descriptions"]

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

    if (path == '/add-item'):
        responseStatus, responseBody = add_item(requestBody, conn, logger)
    elif (path == '/delete-item'):
        responseStatus, responseBody = delete_item(requestBody, conn, logger)
    elif (path == '/get-items'):
        responseStatus, responseBody = get_items(requestBody, requestHeaders, conn, logger)
    elif (path == '/vote-item'):
        responseStatus, responseBody = vote_item(requestBody, conn, logger)
    elif (path == '/search-items'):
        responseStatus, responseBody = search_items(queryStringParams, conn, logger)
    elif (path == '/get-item-descriptions'):
        responseStatus, responseBody = get_item_descriptions(queryStringParams, conn, logger)
    elif (path == '/add-item-description'):
        responseStatus, responseBody = add_item_description(requestBody, conn, logger)
    else:
        responseStatus, responseBody = 404, "No path found..."

    return { 'statusCode': responseStatus, 'body': responseBody, 'headers': get_response_headers() }
