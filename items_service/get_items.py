import json
import pymysql

dataType = {
    "itemNames": [str],
    "username": str
}
def get_items(data: dataType, conn, logger):
    # Access DB
    try:
        itemsToGet = ",".join(map(lambda x: '"%s"' %(x), data['itemNames']))
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute('select * from Items where itemName in (%s)' %(itemsToGet))
            result = cur.fetchall()
        conn.commit()
    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    responseBody = json.dumps(result, default=str)

    logger.info("Retreived Items '%s' from Items table" %(responseBody))
    return 200, responseBody