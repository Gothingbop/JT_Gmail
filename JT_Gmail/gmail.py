import base64
import io
import os
import pickle
import shutil
import json
import re
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Union

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import BatchHttpRequest

# TODO: Check if the supplied user name/email address is in the correct format and maybe correct it
#  (user -> user@gmail.com)


def GetToken(email_address: str, scopes: list, cred_path: str = 'creds/gmail_credentials.json'):
    """
    Function used to obtain/refresh the token used for authenticating the Gmail API. This needs to be run at least once\
    with a supplied credentials file. To obtain a credentials file, you need to enable the Gmail API:
    https://console.developers.google.com/apis/library/gmail.googleapis.com
    From there you can create OAuth2 credentials and download them in a json file.

    This will store the credentials file and the token so subsequent uses are simplified. They can be found at:
        - ./creds/gmail_credentials.json
        - ./creds/tokens/token.pickle

    :param scopes: A list of every scope you want to use. Available scopes can be found at:
                   https://developers.google.com/gmail/api/auth/scopes
    :param email_address: The email address of the account you want to use.
    :param cred_path: Path to the credential file - only needs to be supplied the first time.

    :return: The token used to authenticate
    """
    if not re.fullmatch(r"[\w.%+-]+@gmail.com", email_address):
        if re.fullmatch(r"[\w.%+-]+", email_address):
            email_address = f"{email_address}@gmail.com"
        else:
            raise Exception("INVALID USERNAME")

    scopes = set(scopes)
    scopes.add('https://www.googleapis.com/auth/gmail.readonly')
    token_path = f'creds/tokens/{email_address.lower()}.pkl'

    if not cred_path == 'creds/gmail_credentials.json':
        if not os.path.exists('creds'):
            os.mkdir('creds')
        shutil.copy(cred_path, 'creds/gmail_credentials.json')

    if email_address and os.path.exists(token_path):
        with open(token_path, 'rb') as token_file:
            print("Loading token...")
            token = pickle.load(token_file)
    else:
        token = None

    if not token or not token.valid or not scopes.issubset(token.scopes):
        if token and scopes.issubset(token.scopes) and token.expired:
            print('Refreshing Token...')
            token.refresh(Request())
        else:
            if token:
                print(f'Subset? {scopes.issubset(token.scopes)}')
                print(f'Current scopes: {token.scopes}')
                print(f'Requested Scopes: {scopes}')
                scopes = scopes.union(token.scopes)
            print('Generating New Token...')
            if os.path.exists('creds/gmail_credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file(
                    'creds/gmail_credentials.json',
                    scopes
                )
                token = flow.run_local_server(port=0)
                print(f"scopes: {scopes}")
            else:
                raise NameError(
                    """
                    PLEASE SUPPLY A CREDENTIALS FILE
                    
                    IF YOU DO NOT HAVE ONE ENABLE THE GMAIL API:
                    
                    https://console.developers.google.com/apis/library/gmail.googleapis.com
                    """)
        service = build('gmail', 'v1', credentials=token, cache_discovery=False)
        profile = service.users().getProfile(userId='me').execute()
        email = profile['emailAddress'].lower()
        print(f'creds/tokens/{email}')
        if not os.path.exists('creds/tokens'):
            os.mkdir('creds/tokens')
        try:
            with open(f'creds/tokens/{email}.pkl', 'wb+') as token_file:
                pickle.dump(token, token_file)
        except OSError:
            print('WARNING: Read-only file system - token will not be saved')
    else:
        print('Valid token!')
    return token


def GetService(email_address: str, scopes: list):
    """
    Returns a Gmail service with the requested scopes fo the given user.
    
    Calls GetToken() to request the required scopes if needed.
    
    :param email_address: The email address of the account you want to use.
    :param scopes: A list of every scope you want to use. Available scopes can be found at:
                   https://developers.google.com/gmail/api/auth/scopes
    :return: 
    """
    token = GetToken(
        email_address=email_address,
        scopes=scopes,
    )
    service = build('gmail', 'v1', credentials=token, cache_discovery=False)
    return service


def CreateTextEmail(sender, to, subject, message_text, headers: dict = None):
    """
    Create a message for an email.

    :param sender: Email address of the sender.
    :param to: Email address of the receiver.
    :param subject: The subject of the email message.
    :param message_text: The text of the email message.
    :param headers: (optional) Additional email headers to include with the message.

    :return: An object containing a base64url encoded email object.
    """
    if type(to) is list:
        to = ','.join(to)

    email = MIMEText(message_text)
    if headers is not None:
        for key, value in headers.items():
            email['key'] = value
    email['to'] = to
    email['from'] = sender
    email['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(email.as_bytes()).decode()}


def CreateHTMLEmail(
        sender: str, to: Union[str, list], subject, message_html, images: dict = None, headers: dict = None):
    """
    Create a message for an email.

    :param sender: Email address of the sender.
    :param to: Email address or addresses of the receiver(s).
    :param subject: The subject of the email message.
    :param message_html: The html of the email message.
    :param images: (optional) Used for embedding images in your email. This should be dictionary where the key is a
    string with the id of the image, and the value is either a path to the image or a file-like object containing the
    image data. To reference the image in the html file, you must use the format: <img src="cid:image_id">. Where
    image_id is the id you assign it in this dict.
    :param headers: (optional) Additional email headers to include with the message.

    :return: An object containing a base64url encoded email object.
    """
    if images is None:
        images = {}
    if type(to) is list:
        to = ','.join(to)

    email_multipart = MIMEMultipart('mixed')
    if headers is not None:
        for key, value in headers.items():
            email_multipart['key'] = value
    email_multipart['to'] = to
    email_multipart['from'] = sender
    email_multipart['subject'] = subject

    message_multipart = MIMEMultipart('alternative')  # Multipart that contains the message
    text_part = MIMEText('', 'plain')
    message_multipart.attach(text_part)

    html_multipart = MIMEMultipart('related')
    html_part = MIMEText(message_html, 'html')
    html_multipart.attach(html_part)

    for image_id, image_file in images.items():
        if isinstance(image_file, str):
            with open(image_file, 'rb') as _:
                image_file = io.BytesIO(_.read())
        image_part = MIMEImage(image_file.read())
        image_part.add_header('Content-ID', f'<{image_id}>')
        image_part.add_header('Content-Disposition', 'inline')
        html_multipart.attach(image_part)

    message_multipart.attach(html_multipart)
    email_multipart.attach(message_multipart)

    return {'raw': base64.urlsafe_b64encode(email_multipart.as_bytes()).decode()}


def SendTextEmail(sender: str, to: Union[str, list], subject: str, message_text: str, headers: dict = None):
    """
    Constructs and sends a text-based email message

    Required Scopes:
    [
        'https://www.googleapis.com/auth/gmail.send'
    ]

    :param sender: Email address of the sender.
    :param to: Email address of the receiver.
    :param subject: Subject of the message.
    :param message_text: String of the message text.
    :param headers: (optional) Additional email headers to include with the message.
    :return:
    """
    service = GetService(
        email_address=sender,
        scopes=[
            'https://www.googleapis.com/auth/gmail.send'
        ]
    )
    email = CreateTextEmail(sender, to, subject, message_text, headers)
    return service.users().messages().send(userId=sender, body=email).execute()


def SendHTMLEmail(sender: str, to: [str, list], subject: str, message_html: str, images=None, headers: dict = None):
    """
    Constructs and sends a html-based email message

    Required Scopes:
    [
        'https://www.googleapis.com/auth/gmail.send'
    ]

    :param sender: Email address of the sender.
    :param to: Email address of the receiver.
    :param subject: Subject of the message.
    :param message_html: String of the message html
    :param images: (optional) Used for embedding images in your email. This should be dictionary where the key is a
    string with the id of the image, and the value is either a path to the image or a file-like object containing the
    image data. To reference the image in the html file, you must use the format: <img src="cid:image_id">. Where
    image_id is the id you assign it in this dict.
    :param headers: (optional) Additional email headers to include with the message.

    :return:
    """
    if images is None:
        images = {}
    service = GetService(
        email_address=sender,
        scopes=[
            'https://www.googleapis.com/auth/gmail.send'
        ]
    )
    email = CreateHTMLEmail(sender, to, subject, message_html, images, headers)
    return service.users().messages().send(userId=sender, body=email).execute()


def GetLabels(user):
    """
    Retrieve all the available labels that a given user has.

    Required Scopes:
    [
        'https://www.googleapis.com/auth/gmail.labels'
    ]

    :param user: User to retrieve labels from
    :return: A list of dicts with label information
    """
    service = GetService(
        email_address=user,
        scopes=[
            'https://www.googleapis.com/auth/gmail.labels'
        ]
    )
    return service.users().labels().list(userId=user).execute()


def GetEmails(user: str, message_ids: list, email_format: str = 'full'):
    """
    Get's all of the emails given a list of message id's (typically from a list request).

    :param user: The user to get the emails from.
    :param message_ids: List of message id's to retrieve.
    :param email_format: The format that the email is returned as, default: "full".
        - "full":       Returns the full email message data with body content parsed in the payload field; the raw field
                        is not used. (default)
        - "metadata":   Returns only email message ID, labels, and email headers.
        - "minimal":    Returns only email message ID and labels; does not return the email headers, body, or payload.
        - "raw":        Returns the full email message data with body content in the raw field as a base64url encoded
                        string; the payload field is not used.

    :return: A list of dicts containing the emails and their metadata.
    """
    service = GetService(email_address=user, scopes=['https://www.googleapis.com/auth/gmail.readonly'])
    print('Getting Messages...')
    messages = []
    good = 0
    for i in range(0, len(message_ids), 1000):
        print(f"Messages: {i+1} - {min(i+1000, len(message_ids))}")
        batch = BatchHttpRequest()  # start building a batch request
        for message in message_ids[i:(i + 1000)]:  # add a request for each id
            batch.add(service.users().messages().get(
                userId='me',
                id=message,
                format=email_format
            ))

        batch.execute()
        for header, body in batch._responses.values():
            if header['status'] == '200':
                good += 1
                message = json.loads(body)
                messages.append(message)
    print(f"Successfully retrieved {good}/{len(message_ids)} messages!")
    return messages


def GetEmailsByLabel(user, labels=(), label_ids=(), email_format='full'):
    """
    Get all of the emails of a user with a given label.

    Note: labels and label_id's are different, each label has a unique id assigned on creation, so use labels if you
    want to find labels by name. You can use GetLabels() to look at all the labels and their id's.

    Required Scopes:
    [
        'https://www.googleapis.com/auth/gmail.readonly'
        'https://www.googleapis.com/auth/gmail.labels'
    ]

    :param user: The user to get the emails from.
    :param labels: the labels to look for.
    :param label_ids: The label_ids to look for.
    :param email_format: The format that the email is returned as, default: "full".
        - "full":       Returns the full email message data with body content parsed in the payload field; the raw field
                        is not used. (default)
        - "metadata":   Returns only email message ID, labels, and email headers.
        - "minimal":    Returns only email message ID and labels; does not return the email headers, body, or payload.
        - "raw":        Returns the full email message data with body content in the raw field as a base64url encoded
                        string; the payload field is not used.

    :return: A list of dicts containing the emails and their metadata.
    """
    GetToken(
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.labels',
            ],
        email_address=user,
    )
    if isinstance(label_ids, str):
        label_ids = [label_ids]
    if isinstance(labels, str):
        labels = [labels]
    label_dict = dict()
    if labels:
        available_labels = GetLabels(user)
        for label in available_labels['labels']:
            label_dict[label['name']] = label['id']
        for label in labels:
            if label in label_dict:
                label_ids.append(label_dict[label])
    if not labels and not label_ids:
        raise NameError('LABELS NOT VALID')
    message_ids = []
    i = 1
    service = GetService(
        email_address=user,
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
    )
    print('Getting Message Ids...')
    print(f'Page: {i}\r', end='')
    response = service.users().messages().list(userId='me', labelIds=label_ids).execute()
    message_ids.extend(response['messages'])
    while 'nextPageToken' in response:
        print(f'Page: {i}\r', end='')
        response = service.users().messages().list(userId='me', labelIds=label_ids,
                                                   pageToken=response['nextPageToken']).execute()
        message_ids.extend(response['messages'])
        i += 1
    print()
    return GetEmails(user, message_ids, email_format)


def GetEmailsByQuery(user, query: str, email_format='full'):
    """
    Get all of the emails of a user that match the given query.

    Supports the same query format as the Gmail search box. For example, "from:user@example.com msgid:rfc822 is:unread".

    Required Scopes:
    [
        'https://www.googleapis.com/auth/gmail.readonly'
    ]

    :param user: The user to get the emails from.
    :param query: The query to use
    :param email_format: The format that the email is returned as, default: "full".
        - "full":       Returns the full email message data with body content parsed in the payload field; the raw field
                        is not used. (default)
        - "metadata":   Returns only email message ID, labels, and email headers.
        - "minimal":    Returns only email message ID and labels; does not return the email headers, body, or payload.
        - "raw":        Returns the full email message data with body content in the raw field as a base64url encoded
                        string; the payload field is not used.

    :return: A list of dicts containing the emails and their metadata.
    """
    GetToken(
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly'
        ],
        email_address=user,
    )
    message_ids = set()
    i = 1
    service = GetService(
        email_address=user,
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
        ],
    )
    print('Getting Message Ids...')
    response = service.users().messages().list(userId='me', q=query).execute()
    if response["resultSizeEstimate"]:
        print(f'Page: {i}\r', end='')
        message_ids.update([message['id'] for message in response['messages']])
        while 'nextPageToken' in response:
            print(f'Page: {i}\r', end='')
            response = service.users().messages().list(userId='me', q=query,
                                                       pageToken=response['nextPageToken']).execute()
            message_ids.update([message['id'] for message in response['messages']])
            i += 1
        message_ids = list(message_ids)
        print()
        return GetEmails(user, message_ids, email_format)
    else:
        print("No Results!")
        return []


def ChangeLabels(user: str, message_ids=None, add_labels=None, remove_labels=None):
    """
    Changes the labels assigned to the messages.

    Required Scopes:
    [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.labels',
    ]

    :param user: The user to get and modify the emails from.
    :param message_ids: List of message id's to modify.
    :param add_labels: Labels to add to the messages.
    :param remove_labels: Labels to remove from tha messages.
    :return:
    """
    if remove_labels is None:
        remove_labels = []
    if add_labels is None:
        add_labels = []
    if message_ids is None:
        message_ids = []
    if isinstance(message_ids, str):
        message_ids = [message_ids]

    if isinstance(add_labels, str):
        add_labels = [add_labels]

    if isinstance(remove_labels, str):
        remove_labels = [remove_labels]

    label_dict = dict()
    available_labels = GetLabels(user)
    for label in available_labels['labels']:
        label_dict[label['name']] = label['id']

    add_label_ids = []
    for label in add_labels:
        if label in label_dict:
            add_label_ids.append(label_dict[label])

    remove_label_ids = []
    for label in remove_labels:
        if label in label_dict:
            remove_label_ids.append(label_dict[label])

    service = GetService(
        email_address=user,
        scopes=[
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.labels',
        ],
    )

    service.users().messages().batchModify(userId=user, body={
        "removeLabelIds": remove_label_ids,
        "ids": message_ids,
        "addLabelIds": add_label_ids,
    }).execute()


def SendHTMLReply(sender: str, message_id: str, message_html: str, images=None):
    """
    Replies to an email. Works similarly to SendHTMLEmail, except you must supply a message id to reply to.

    Note: The user must be able to read the email it is responding to.

    Required Scopes:
    [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]

    :param sender: User that will be sending the reply
    :param message_id: The id of the message to reply to.
    :param message_html: String of the message html
    :param images: (optional) Used for embedding images in your email. This should be dictionary where the key is a
        string with the id of the image, and the value is either a path to the image or a file-like object containing
        the image data. To reference the image in the html file, you must use the format: <img src="cid:image_id">.
        Where image_id is the id you assign it in this dict.
    :return:
    """
    if images is None:
        images = {}

    if images is None:
        images = {}
    service = GetService(
        email_address=sender,
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send'
        ]
    )

    message = service.users().messages().get(
        userId='me',
        id=message_id,
        format="metadata"
    ).execute()
    subject = None
    to = None
    reply_id = None
    for header in message['payload']['headers']:
        if header['name'] == "Subject":
            subject = header['value']
        if header['name'] == "From":
            to = header['value']
        if header['name'] == "Message-ID":
            reply_id = header['value']

    assert subject
    assert to
    assert reply_id

    if subject.lower()[:4] != "re: ":
        subject = "Re: " + subject

    email = CreateHTMLEmail(sender, to, subject, message_html, images, {'In-Reply-To': reply_id})
    return service.users().messages().send(userId=sender, body=email).execute()
