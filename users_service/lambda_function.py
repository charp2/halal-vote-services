# standard python imports
import sys
import logging
import pymysql
import json
import os

# our imports
from users_service.register_user import register_user
from users_service.activate_user import activate_user
from users_service.login import login
from users_service.logout import logout
from users_service.user_created_media import user_created_media
from users_service.user_liked_media import user_liked_media
from users_service.user_created_topics import user_created_topics
from users_service.user_voted_topics import user_voted_topics
from users_service.user_comments import user_comments
from users_service.see_media import see_media
from users_service.get_users import get_users
from users_service.send_forgot_password_email import send_forgot_password_email
from users_service.reset_password import reset_password
from users_service.change_password import change_password
from users_service.delete_account import delete_account
from users_service.username_available import username_available
from users_service.email_available import email_available
from utils import valid_user
from utils import get_response_headers

# rds settings
rds_host  = os.environ["DB_HOST"]
name = os.environ["DB_USERNAME"]
password = os.environ["DB_PASSWORD"]
db_name = os.environ["DB_NAME"]

# logging config
logger = logging.getLogger()

# apis not requiring sessionToken
no_session_token = [
    "/register-user", 
    "/activate-user", 
    "/login", "/logout", 
    "/user-created-media",
    "/user-created-topics",
    "/user-comments", 
    "/get-users", 
    "/send-forgot-password-email", 
    "/reset-password", 
    "/username-available",
    "/email-available"
]

# verify db connection
try:
    conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()
logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")

eventType = {
    "resource": str,
    "path": str,
    "httpMethod": str,
    "headers": dict,
    "multiValueHeaders": any, #{List of strings containing incoming request headers}
    "queryStringParameters": any, #{query string parameters }
    "multiValueQueryStringParameters": any, #{List of query string parameters}
    "pathParameters": any, #{path parameters}
    "stageVariables": any, #{Applicable stage variables}
    "requestContext": any, #{Request context, including authorizer-returned key-value pairs}
    "body": str,
    "isBase64Encoded": any, #"A boolean flag to indicate if the applicable request payload is Base64-encode"
}
# lambda entry point
def handler(event: eventType, context):
    path = event['path']
    requestHeaders = event['headers']

    if event['httpMethod'] == 'POST':
        requestParams = json.loads(event['body'])
    elif event['httpMethod'] == 'GET':
        requestParams = event['queryStringParameters']

    if path not in no_session_token:
            status_code, msg = valid_user(requestParams.get('username'), requestHeaders.get('sessiontoken'), conn, logger, requestHeaders.get('issuperuser') == "true")
            if status_code != 200:
                return {'statusCode': status_code, 'body': msg, 'headers': get_response_headers()}

    if path == '/register-user':
        responseStatus, responseBody = register_user(requestParams, conn, logger)
    elif path == '/activate-user':
        username = requestParams['username']
        value = requestParams['value']
        responseStatus, responseBody = activate_user(username, value, conn, logger)
    elif path == '/login':
        ip_address = requestHeaders['X-Forwarded-For']
        responseStatus, responseBody = login(requestParams, ip_address, conn, logger)
    elif path == '/logout':
        responseStatus, responseBody = logout(requestParams, requestHeaders['sessionToken'], conn, logger)
    elif path == '/user-created-media':
        responseStatus, responseBody = user_created_media(requestParams, requestHeaders, conn, logger)
    elif path == '/user-created-topics':
        responseStatus, responseBody = user_created_topics(requestParams, requestHeaders, conn, logger)
    elif path == '/user-liked-media':
        responseStatus, responseBody = user_liked_media(requestParams, requestHeaders, conn, logger)
    elif path == '/user-voted-topics':
        responseStatus, responseBody = user_voted_topics(requestParams, requestHeaders, conn, logger)
    elif path == '/user-comments':
        responseStatus, responseBody = user_comments(requestParams, requestHeaders, conn, logger)
    elif path == '/user-see-media':
        responseStatus, responseBody = see_media(requestParams, requestHeaders, conn, logger)
    elif path == '/get-users':
        responseStatus, responseBody = get_users(requestParams, requestHeaders, conn, logger)
    elif path == '/send-forgot-password-email':
        email = requestParams['email']
        responseStatus, responseBody = send_forgot_password_email(email, conn, logger)
    elif path == '/reset-password':
        responseStatus, responseBody = reset_password(requestParams, conn, logger)
    elif path == '/change-password':
        responseStatus, responseBody = change_password(requestParams, conn, logger)
    elif path == '/delete-account':
        responseStatus, responseBody = delete_account(requestParams, conn, logger)
    elif path == '/username-available':
        responseStatus, responseBody = username_available(requestParams, conn, logger)
    elif path == '/email-available':
        responseStatus, responseBody = email_available(requestParams, conn, logger)        
    else:
        responseStatus, responseBody = 404, "No path found..."

    return {'statusCode': responseStatus, 'body': responseBody, 'headers': get_response_headers()}
