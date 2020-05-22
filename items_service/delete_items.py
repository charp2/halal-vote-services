# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "itemNames": [str],
    "username": str
}
def delete_items(data: dataType, conn, logger):
    # Access DB
    try:
        itemsToDelete = ",".join(map(lambda x: '"%s"' %(x), data['itemNames']))
        with conn.cursor() as cur:
            cur.execute('delete from Items where itemName in (%s)' %(itemsToDelete))
        conn.commit()
    except Exception as e:
        return generate_error_response(500, str(e))

    return generate_success_response("Removed Item '%s' from Items table" %(data['itemNames']))
