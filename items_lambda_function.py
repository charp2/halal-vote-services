# standard python imports
import sys
import logging
import pymysql
import json

# our imports
import rds_config
from items_service.make_item import make_item
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
def handler(event, context):
    requestBody = json.loads(event['body'])
    requestHeaders = event['headers']

    is_valid_user = valid_user(requestBody['username'], requestHeaders['sessionToken'], conn, logger)

    if not isinstance(is_valid_user, bool):
        return {'statusCode': 500, 'body': is_valid_user}
    elif not is_valid_user:
        return { 'statusCode': 401, 'body': 'User Not Authorized' }

    if (event['path'] == '/make-item'):
        responseStatus, responseBody = make_item(requestBody, conn, logger)
    else:
        responseStatus, responseBody = 404, "No path found..."

    return { 'statusCode': responseStatus, 'body': responseBody }
