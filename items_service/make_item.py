
dataType = {
    "itemName": str,
    "username": str
}
def make_item(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            cur.execute('insert into Items (itemName, username, halalVotes, haramVotes, numComments) values(%(itemName)s, %(username)s, 0, 0, 0)', {'itemName': data['itemName'], 'username': data['username']})
        conn.commit()
    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    success_message = "Added Item '%s' into Items table" %(data['itemName'])
    logger.info(success_message)
    return 200, success_message
