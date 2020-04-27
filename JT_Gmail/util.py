import base64


def FindPart(part: dict, mime_type: str):
    """
    Recursively parses the parts of an email and returns the first part with the requested mime_type.

    :param part: Part of the email to parse (generally called on the payload).
    :param mime_type: MIME Type to look for.
    :return: The part of the email with the matching type.
    """
    if part['mimeType'] == mime_type:
        return part
    elif 'multipart' in part['mimeType']:
        for child in part['parts']:
            out = FindPart(child, mime_type)
            if out is not None:
                return out


def GetEmailHTML(email: dict):
    """
    Finds and Decodes the part of the email that is an html file.

    :param email: Email to look through - should be the outer email dict that has a payload.
    :return: Decoded string containing the html.
    """
    html_part = FindPart(email['payload'], 'text/html')
    return base64.urlsafe_b64decode(html_part['body']['data'])
