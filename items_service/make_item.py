def make_item(data, conn):
    # Access DB
    with conn.cursor() as cur:
        cur.execute('insert into Items (itemName, username, halalVotes, haramVotes, numComments) values("%s", "%s", 0, 0, 0)' %(data['itemName'], data['username']))
        conn.commit()

    return "Added Item '%s' into Items table" %(data['itemName'])
