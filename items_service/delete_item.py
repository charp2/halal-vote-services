def delete_item(data, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            cur.execute('delete from Items where itemName="%s"' %(data['itemName']))
        conn.commit()
    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    success_message = "Removed Item '%s' from Items table" %(data['itemName'])
    logger.info(success_message)
    return 200, success_message
