# JT_Gmail
This is a simple interface for programmatically sending emails using the Gmail API. 
I typically import it as 


To get started you must <a href="https://console.developers.google.com/apis/library/gmail.googleapis.com">enable the 
Gmail API</a> and save the `credential.json` file somewhere.

Before you can use this module for the first time, you must run:
```python
import JT_Gmail as gmail

gmail.GetToken('scope1', 'scope2', ..., cred_path="path_to_your_credentials")
```

Supply the scopes you plan on using as *args. A list of all the scopes can be found 
<a href="https://developers.google.com/gmail/api/auth/scopes">here<a>.

This will generate the proper token to use the scopes you supplied. The token and credentials are saved for later use, 
so you only have to run that line once.

To send emails, it's as easy as:
```python
import JT_Gmail as gmail

with open("email.html") as file:
    gmail.SendHTMLEmail(
        to="recipient@some.website", 
        subject="Example Email", 
        message_html=file.read()
)
```

This was base heavily on <a href="https://developers.google.com/gmail/api/quickstart/python">code snippets supplied by 
Google<a>.
