# Adapted from: https://developers.google.com/gmail/api/quickstart/python, [Authentication]
#               https://developers.google.com/gmail/api/guides/sending [Sending a mail]

import json
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from email.mime.text import MIMEText
import base64
from google.auth.transport.requests import Request

# IMPORTANT: if you modify the scopes delete the file token.pickle and re-authenticate
# The accesses that you want; checkout: https://developers.google.com/identity/protocols/oauth2/scopes 
# for more information

SCOPES = ['https://mail.google.com/']

def send_mail(subject, body):
    """
    Authenticates and sends the mail

    Parameters: 
        - subject: ... <str>
        - body: ... <str>

    Returns: None
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Send an email 
    with open('individuals.json') as fp:
        individuals = json.load(fp)

    message = create_message(individuals['from'], individuals['to'], subject, body)
    send_message(service, 'me', message)


def send_message(service, user_id, message):
    """Send an email message.

    Parameters:
        - service: Authorized Gmail API service instance.
        - user_id: User's email address. The special value "me"
                   can be used to indicate the authenticated user.
        - message: Message to be sent.

    Returns: Sent Message.
    """

    message = (service.users().messages().send(userId=user_id, body=message).execute())

    #print(f'Message Id: {message["id"]}')

    return message


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Parameters:
        - sender: Email address of the sender.
        - to: Email address of the receiver.
        - subject: The subject of the email message.
        - message_text: The text of the email message.

    Returns:
        An object containing a base64url encoded email object. <string>
    """

    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

