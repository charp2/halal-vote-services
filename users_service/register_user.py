# standard python imports
from secrets import token_hex
import json
import boto3
import os

# our imports
from users_service.utils import create_hashed_password
from utils import generate_error_response
from utils import generate_success_response
from utils import format_email
from users_service.utils import get_hyperlink_base_url

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
        return generate_error_response(400, "Invalid email passed in")
    else:
        email = format_email(email)

    if not username:
        return generate_error_response(400, "Invalid username passed in")

    if not password:
        return generate_error_response(400, "Invalid password passed in")

    hashed_password = create_hashed_password(password, salt)
    logger.info(hashed_password)

    try:
        with conn.cursor() as cur:
            cur.execute('''
                select username, email, activeStatus from Users
                where email=%(email)s or username=%(username)s
            ''', {'email': email, 'username': username})

            results = cur.fetchall()
            if results:
                for result in results:
                    used_username, used_email, active_status = result

                    if used_email == email and (used_username != username or active_status != "INACTIVE"):
                        return generate_error_response(400, "Email already in use")
                    if used_username == username and (used_email != email or active_status != "INACTIVE"):
                        return generate_error_response(400, "Username already in use")

            sns = boto3.client('sns')

            hyperlink_base_url = get_hyperlink_base_url()

            message = {
                "email": email,
                "subject": "halalvote.com Account Activation",
                "body": "<div><span>Click </span><span><a href='%s?loginScreen=loadingActivation&username=%s&activationValue=%s'>here</a></span><span> to activate your account.</span></div>" %(hyperlink_base_url, username, activation_value)
            }

            send_email_topic_arn = os.environ["SEND_EMAIL_TOPIC_ARN"]
            sns.publish(
                TopicArn=send_email_topic_arn,
                Message=json.dumps(message)
            )

            cur.execute('''
                insert into Users (username, email, password, salt, sessionToken, activeStatus) 
                values (%(username)s, %(email)s, %(password)s, %(salt)s, %(activationValue)s, 'INACTIVE')
                on duplicate key update `password` = values(`password`), `salt` = values(`salt`), `sessionToken` = values(`sessionToken`)
            ''', {'username': username, 'email': email, 'password': hashed_password, 'salt': salt, 'activationValue': activation_value})
            conn.commit()

    except Exception as e:
        return generate_error_response(500, "There was an error")

    return generate_success_response(username)
