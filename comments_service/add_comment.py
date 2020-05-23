# our imports
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "username": str,
    "itemName": str,
    "parentId": str,
    "comment": str,
    "commentType": str
}
def add_comment(data: dataType, conn, logger):
    # Access DB
    try:
        with conn.cursor() as cur:
            cur.execute('insert into Comments (itemName, username, parentId, comment, commentType) values(%(itemName)s, %(username)s, %(parentId)s, %(comment)s, %(commentType)s)', {'itemName': data['itemName'], 'username': data['username'], 'parentId': data.get('parentId', 0), 'comment': data['comment'], 'commentType': data.get('commentType', 'OTHER')})
        conn.commit()
    except Exception as e:
        return generate_error_response(500, str(e))

    return generate_success_response("Added comment '%s' into Comments table" %(data['comment']))