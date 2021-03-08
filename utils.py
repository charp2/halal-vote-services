# standard python imports
import logging
import time
from datetime import datetime, timedelta
import json
import boto3
from botocore.exceptions import ClientError

# logging config
logger = logging.getLogger()

# response headers
response_headers = {'Access-Control-Allow-Origin': '*'}

def create_presigned_post(bucket_name, object_name, fields=None, conditions=None, expiration=120):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    # Generate a presigned S3 POST URL
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_post(
            bucket_name,
            object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL and required fields
    return response

def valid_user(username: str, session_token: str, conn, logger):
    if not username:
        return generate_error_response(400, "no username passed in")

    if not session_token:
        return generate_error_response(400, "no sessiontoken passed in")

    try:
        with conn.cursor() as cur:
            cur.execute("select sessionToken, sessionTimestamp, activeStatus from Users where username=%(username)s", {'username': username})
            results = cur.fetchone()
            conn.commit()

            if results:
                retrieved_session_token, session_timestamp, active_status = results
            else:
                return generate_error_response(404, "User not found")

            if session_token != retrieved_session_token:
                return generate_error_response(403, "Access to resource forbidden")
            elif active_status != "ACTIVE":
                return generate_error_response(401, "User is Not ACTIVE")
            elif is_session_expired(session_timestamp):
                return generate_error_response(401, "Session Expired")
            else:
                return generate_success_response("")

    except Exception as e:
        return generate_error_response(500, str(e))

def generate_error_response(status_code: int, error_msg: str):
    logger.error(error_msg)
    return status_code, json.dumps({ 'message': error_msg }, default=str)

def generate_success_response(data: object):
    dataJson = json.dumps(data, default=str)
    logger.info(dataJson)
    return 200, dataJson

def generate_timestamp():
    ts = time.time()
    return datetime.fromtimestamp(ts)

def is_session_expired(session_timestamp):
    current_timestamp = generate_timestamp()
    return session_timestamp < (current_timestamp - timedelta(hours=24))

def get_response_headers():
    return response_headers

def flatten_result(result):
    return list(map(lambda t: t[0], result))

def convert_bit_to_int(bit):
    return 0 if bit == b'\x00' else 1

def get_time_floor(time):
    return datetime.combine(time, datetime.min.time())

def pad_number(value):
    return '0' + str(value) if value < 10 else str(value)

def get_utc_offset(time):
    utc = generate_timestamp()

    diff_seconds = (utc - time).seconds
    diff_hours = pad_number(abs(diff_seconds // 3600))
    diff_minutes = pad_number(abs((diff_seconds // 60) % 60))

    sign = '-' if diff_seconds > 0 else '+'
    return '%s%s:%s' %(sign, diff_hours, diff_minutes)

def format_email(email: str):
    return email.lower()