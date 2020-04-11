import os
import shutil
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def GetToken(*scopes, cred_path='JT_Gmail/gmail_credentials.json'):
    if not cred_path == 'JT_Gmail/gmail_credentials.json':
        shutil.copy(cred_path, 'JT_Gmail/gmail_credentials.json')

    if os.path.exists('JT_Gmail/token.pickle'):
        with open('JT_Gmail/token.pickle', 'rb') as token_file:
            creds = pickle.load(token_file)
    else:
        creds = None

    if not creds or not creds.valid:
        if creds and not set(scopes).issubset(creds.scopes) and creds.expired:
            creds.refresh(Request())
        else:
            if os.path.exists('JT_Gmail/gmail_credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file('JT_Gmail/gmail_credentials.json', scopes)
                creds = flow.run_local_server(port=0)
            else:
                raise NameError(
                    """
                    PLEASE SUPPLY A CREDENTIALS FILE
                    
                    IF YOU DO NOT HAVE ONE ENABLE THE GMAIL API:
                    
                    https://console.developers.google.com/apis/library/gmail.googleapis.com
                    """)
        with open('JT_Gmail/token.pickle', 'wb') as token_file:
            pickle.dump(creds, token_file)
    return creds


def CreateTextEmail(sender, to, subject, message_text):
    """
    Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """
    if type(to) is list:
        to = ','.join(to)

    email = MIMEText(message_text)
    email['to'] = to
    email['from'] = sender
    email['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(email.as_bytes()).decode()}


def CreateHTMLEmail(sender, to, subject, message_html):
    """
    Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_html: The html of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """
    if type(to) is list:
        to = ','.join(to)

    email = MIMEMultipart('alternative')
    email['to'] = to
    email['from'] = sender
    email['subject'] = subject

    part1 = MIMEText('', 'plain')
    part2 = MIMEText(message_html, 'html')

    email.attach(part1)
    email.attach(part2)

    return {'raw': base64.urlsafe_b64encode(email.as_bytes()).decode()}


def SendEmail(email):
    """
    Sends an already constructed base64url encoded email object.

    :param email: base64url encoded email object to send
    :return:
    """
    # Refresh the token
    creds = GetToken('https://www.googleapis.com/auth/gmail.send')

    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    return service.users().messages().send(userId="enhance.it.bot@gmail.com", body=email).execute()


def SendTextEmail(to, subject, message_text):
    """
    Constructs and sends a text-based email message

    :param to: Email address of the receiver.
    :param subject: Subject of the message.
    :param message_text: String of the message text.
    :return:
    """
    email = CreateTextEmail("enhance.it.bot@gmail.com", to, subject, message_text)
    return SendEmail(email)


def SendHTMLEmail(to, subject, message_html):
    """
    Constructs and sends a html-based email message

    :param to: Email address of the receiver.
    :param subject: Subject of the message.
    :param message_html: String of the message html
    :return:
    """
    email = CreateHTMLEmail("enhance.it.bot@gmail.com", to, subject, message_html)
    return SendEmail(email)
