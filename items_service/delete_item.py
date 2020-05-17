
# data: {
#     "itemNames": [str],
#     "username": str
# }
def delete_item(data, conn, logger):
    # Access DB
    try:
        itemsToDelete = ",".join(map(lambda x: '"%s"' %(x), data['itemNames']))
        with conn.cursor() as cur:
            cur.execute('delete from Items where itemName in (%s)' %(itemsToDelete))
        conn.commit()
    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    success_message = "Removed Item '%s' from Items table" %(data['itemNames'])
    logger.info(success_message)
    return 200, success_message
