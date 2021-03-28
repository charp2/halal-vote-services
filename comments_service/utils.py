# standard python imports
import pymysql

def parent_depth_found(parent_depth):
    return parent_depth != None

def get_parent_depth(conn, parent_id: int):
    with conn.cursor() as cur:
        cur.execute('select depth from Comments where id=%(parentId)s', {'parentId': parent_id})
        result = cur.fetchone()
        conn.commit()

        return result if not result else result[0]
