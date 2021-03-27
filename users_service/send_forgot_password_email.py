# standard python imports
from secrets import token_hex
import json
import boto3
import os

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import generate_timestamp
from utils import format_email
from users_service.utils import get_hyperlink_base_url

def send_forgot_password_email(email: str, conn, logger):
    reset_token = token_hex(10)
    reset_timestamp = generate_timestamp()
    email = format_email(email)

    try:
        with conn.cursor() as cur:
            cur.execute('''
                select username, activeStatus from Users
                where email=%(email)s
            ''', {'email': email})

            result = cur.fetchone()

            if result:
                username, active_status = result

                if active_status != "ACTIVE":
                    return generate_error_response(400, "Account is not ACTIVE")
            else:
                return generate_error_response(500, "Email provided is not in use")

            sns = boto3.client('sns')

            hyperlink_base_url = get_hyperlink_base_url()

            message = {
                "email": email,
                "subject": "Reset password for halalvote.com",
                "body": "<div><span>You requested a change of password for user <b>%s</b>. Click </span><span><a href='%s?loginScreen=resetPasswordPage&username=%s&passwordResetToken=%s'>here</a></span><span> to reset your password.</span></div>" %(username, hyperlink_base_url, username, reset_token)
            }

            send_email_topic_arn = os.environ["SEND_EMAIL_TOPIC_ARN"]

            sns.publish(
                TopicArn=send_email_topic_arn,
                Message=json.dumps(message)
            )

            cur.execute('''
                update Users
                set passwordResetToken=%(passwordResetToken)s, passwordResetTimestamp=%(passwordResetTimestamp)s
                where username=%(username)s and email=%(email)s
            ''', {'passwordResetToken': reset_token, 'passwordResetTimestamp': reset_timestamp, 'username': username, 'email': email})
            conn.commit()

            return generate_success_response("Successfully sent password reset email")

    except Exception as e:
        conn.rollback()
        return generate_error_response(500, "There was an error")
