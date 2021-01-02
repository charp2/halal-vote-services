# standard python imports
from secrets import token_hex
import json
import boto3
import urllib.parse

# our imports
from users_service.utils import create_hashed_password
from utils import generate_error_response
from utils import generate_success_response

dataType = {
    "email": str,
    "username": str,
    "password": str
}

def register_user(data: dataType, conn, logger):
    email = data["email"]
    username = data["username"]
    password = data["password"]
    salt = token_hex(10)
    activation_value = token_hex(10)

    if not email:
        return generate_error_response(500, "Invalid email passed in")

    if not username:
        return generate_error_response(500, "Invalid username passed in")

    if not password:
        return generate_error_response(500, "Invalid password passed in")

    hashed_password = create_hashed_password(password, salt)
    logger.info(hashed_password)

    try:
        with conn.cursor() as cur:
            cur.execute('''
                select topicTitle from Topics
                ORDER BY numVotes DESC LIMIT 1
            ''')
            conn.commit()

            result = cur.fetchone()

            if result:
                topic_title = urllib.parse.quote(result[0])
            else:
                topic_title = "Apple"

            sns = boto3.client('sns')

            message = {
                "email": email,
                "subject": "Complete Registration for halalvote.com",
                "body": "<div><span>Thanks for signing up for Halal Vote! Click </span><span><a href='http://localhost:3000/%s?card=canvas&loginScreen=loadingActivation&username=%s&activationValue=%s'>here</a></span><span> to activate your account.</span></div>" %(topic_title, username, activation_value)
            }

            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:678359485191:send-email',
                Message=json.dumps(message)
            )

            cur.execute('''
                insert into Users (username, email, password, salt, sessionToken, activeStatus) values(%(username)s, %(email)s, %(password)s, %(salt)s, %(activationValue)s, 'INACTIVE')
            ''', {'username': username, 'email': email, 'password': hashed_password, 'salt': salt, 'activationValue': activation_value})
            conn.commit()

    except Exception as e:
        return generate_error_response(500, str(e))

    return generate_success_response(username)
