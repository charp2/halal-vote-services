# standard python imports
import sys
import logging
import pymysql
import json

# our imports
import rds_config
from items_service.make_item import make_item

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
    body = json.loads(event['body'])

    return make_item(body, conn, logger)
