# standard python imports
from secrets import token_hex
import json
import boto3
import urllib.parse

# our imports
from utils import generate_error_response
from utils import generate_success_response
from utils import generate_timestamp

def send_forgot_password_email(email: str, conn, logger):
    reset_token = token_hex(10)
    reset_timestamp = generate_timestamp()

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

            cur.execute('''
                select topicTitle from Topics
                ORDER BY numVotes DESC LIMIT 1
            ''')

            result = cur.fetchone()

            if result:
                topic_title = urllib.parse.quote(result[0])
            else:
                topic_title = "Apple"

            sns = boto3.client('sns')

            message = {
                "email": email,
                "subject": "Forgot password for halalvote.com",
                "body": "<div><span>You requested a change of password for user <b>%s</b>. Click </span><span><a href='http://localhost:3000/%s?card=canvas&loginScreen=changePasswordPage&username=%s&passwordResetToken=%s'>here</a></span><span> to reset your password.</span></div>" %(username, topic_title, username, reset_token)
            }

            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:678359485191:send-email',
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
        return generate_error_response(500, "There was an error")
