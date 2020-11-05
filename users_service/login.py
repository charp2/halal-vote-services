# standard python imports
import json

# our imports
from users_service.utils import create_hashed_password
from utils import generate_error_response
from utils import generate_success_response
from utils import is_session_expired
from users_service.utils import create_session
from users_service.utils import get_user_location

dataType = {
    "username": str,
    "password": str
}

def login(data: dataType, ip_address: str, conn, logger):
    username = data["username"]
    password = data["password"]

    try:
        with conn.cursor() as cur:
            cur.execute("select password, salt, sessionToken, sessionTimestamp, activeStatus, lastIPAddress from Users where username=%(username)s", {'username': username})
            results = cur.fetchone()
            conn.commit()

            if results:
                fetched_password, fetched_salt, fetched_session_token, fetched_session_timestamp, fetched_active_status, fetched_ip_address = results
            else:
                return generate_error_response(404, "User not found")

            check_hash = create_hashed_password(password, fetched_salt)

            # if user is not active or deleted then return 403
            if fetched_active_status == "INACTIVE":
                return generate_error_response(403, "User is INACTIVE")
            elif fetched_active_status == "DELETED":
                return generate_error_response(403, "User is DELETED")
            elif fetched_password == check_hash:
                is_ip_updated = fetched_ip_address != ip_address

                if not fetched_session_token or is_session_expired(fetched_session_timestamp):
                    new_session_token, new_session_timestamp = create_session()
                    query_string = "update Users set sessionToken=%(sessionToken)s, sessionTimestamp=%(sessionTimestamp)s"
                    query_params = {'sessionToken': new_session_token, 'sessionTimestamp': new_session_timestamp, 'username': username}

                    if is_ip_updated:
                        location = get_user_location(ip_address)
                        
                        if location != None:
                            query_string += ", lastIPAddress=%(lastIPAddress)s, lastLatitude=%(lastLatitude)s, lastLongitude=%(lastLongitude)s"
                            query_params['lastIPAddress'] = ip_address
                            query_params["lastLatitude"] = location["latitude"]
                            query_params["lastLongitude"] = location["longitude"]

                    query_string += " where username=%(username)s"
                    cur.execute(query_string, query_params)
                    conn.commit()
                else:
                    if is_ip_updated:
                        location = get_user_location(ip_address)

                        if location != None:
                            query_string = "update Users set lastIPAddress=%(lastIPAddress)s, lastLatitude=%(lastLatitude)s, lastLongitude=%(lastLongitude)s where username=%(username)s"
                            query_params = {"lastIPAddress": ip_address, "lastLatitude": location["latitude"], "lastLongitude": location["longitude"], "username": username}
                            cur.execute(query_string, query_params)
                            conn.commit()
                    
                    new_session_token = fetched_session_token

                return generate_success_response(new_session_token)
            else:
                return generate_error_response(401, "Password is incorrect")


    except Exception as e:
        return generate_error_response(500, str(e))
