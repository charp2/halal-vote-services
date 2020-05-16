# standard python imports
import sys
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

# verify db connection
try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    print("ERROR: Unexpected error: Could not connect to MySQL instance.")
    print(e)
    sys.exit()
print("SUCCESS: Connection to RDS MySQL instance succeeded")

# lambda entry point
def handler(event, context):
    body = json.loads(event['body'])

    return { 'statusCode': 200, 'body': json.dumps(make_item(body, conn)) }
