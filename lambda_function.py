import sys
import logging
import pymysql
import rds_config

#rds settings
rds_host  = 'halal-haram-db-cluster.cluster-cw2lk1nel1gs.us-east-1.rds.amazonaws.com'
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")
def handler(event, context):
    with conn.cursor() as cur:
        cur.execute('insert into Items (itemName, username, halalVotes, haramVotes, numComments) values("%s", "%s", 0, 0, 0)' %(event['itemName'], event['username']))
        conn.commit()
        cur.execute("select * from Items")
        for row in cur:
            logger.info(row)
            print(row)
    conn.commit()

    return "Added Item '%s' into Items table" %(event['name'])
