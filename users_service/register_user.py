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

            BODY_HTML = f"""<!DOCTYPE html>
<html>
	<head>
	</head>
	<body style="background: #181818; font-family: verdana, arial, helvetica, sans-serif;">
		<p>
			<div style='width: 100%; display:flex; align-items: center; justify-content: center;'>
				<div style='margin-left:auto; margin-right: auto; margin-top: 10vh; margin-bottom: 10vh; border: 2px #414141 solid; border-radius: 25px; width: 80vw; max-width: 600px; text-align: center; background-color: #2a2a2a'>
					<table style='width: 100%'>
						<thead>
							<tr>
								<th style='font-weight: 300; font-size: 7vh; display: inline-flex;'>
									<span style='color: #8756ad'>H</span>
									<span style='color: #57998e'>V</span>
								</th>
							</tr>
						</thead>
						<tr>
							<tr>
								<td>
									<div style='font-size: 2vh'>
										<span style='color: rgb(197, 197, 197)'>Activate your account below</span>
										<br>
											<button style='margin: 20px 0 20px 0; font-size: 3vh; width: 5em;padding: 6px;border-radius: 24px;color: rgb(197, 197, 197);background-color: #414141;border: none;outline: none;'>
												<a target='_blank' style='text-decoration: none; color: rgb(197, 197, 197);' href='{hyperlink_base_url}?loginScreen=loadingActivation&username={username}&activationValue={activation_value}'>Activate</a>
											</button>
										</div>
									</tb>
								</tr>
							</tr>
						</table>
					</div>
				</div>
			</p>
		</body>
	</html>"""

            message = {
                "email": email,
                "subject": "halalvote.com Account Activation",
                'body': BODY_HTML
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
