import json
import boto3

def handler(event, context):
    try:
        sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
        email = sns_message["email"]
        subject = sns_message["subject"]
        body = sns_message["body"]
        
        ses = boto3.client('ses')
    
        ses.send_email(
            Source='votehalalharam@gmail.com',
            Destination={
                'ToAddresses': [
                    email
                ]
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Html': {
                        'Data': body
                    }
                }
            }
        )
        return {
            'emailSent': True
        }
    except Exception as e:
        return {
            'emailSent': False
        }