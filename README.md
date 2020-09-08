# JT_Gmail
This is a simple interface for programmatically sending emails using the Gmail API.

```
pip install JT_Gmail
``` 

To get started you must <a href="https://console.developers.google.com/apis/library/gmail.googleapis.com">create a project 
and enable the Gmail API</a>, create OAuth2 credentials and download them in a json file.

Before you can use this module for the first time, you must run:
```python
import JT_Gmail as gmail

gmail.GetToken(scopes=['scope1', 'scope2'], email_address='user@gmail.com', cred_path="path_to_your_credentials.json")
```

Supply the scopes you plan on using as *args. A list of all the scopes can be found 
<a href="https://developers.google.com/gmail/api/auth/scopes">here<a>. Each function also includes the required scopes
in its docstring.

This will prompt for authentication and generate the proper token to use the scopes you supplied. The token and 
credentials are saved for later use, so you might only have to run that line once. As you perform actions, if they need 
new permissions, they will be requested. Authentication will be required for each gmail user you wish to use.

To send emails, it's as easy as:
```python
import JT_Gmail as gmail

with open("email.html") as file:
    gmail.SendHTMLEmail(
        sender='sender@gmail.com', 
        to="recipient@some.website", 
        subject="Example Email", 
        message_html=file.read()
)
```

This was base heavily on <a href="https://developers.google.com/gmail/api/quickstart/python">code snippets supplied by 
Google<a>.
