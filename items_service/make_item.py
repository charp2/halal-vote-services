
# data: {
#     "itemName": str,
#     "username": str
# }
def make_item(data, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            cur.execute('insert into Items (itemName, username, halalVotes, haramVotes, numComments) values("%s", "%s", 0, 0, 0)' %(data['itemName'], data['username']))
        conn.commit()
    except Exception as e:
        error_str = str(e)
        logger.error(error_str)
        return 500, error_str

    success_message = "Added Item '%s' into Items table" %(data['itemName'])
    logger.info(success_message)
    return 200, success_message
