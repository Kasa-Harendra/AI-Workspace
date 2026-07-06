import os.path
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from settings import settings

SCOPES = [
    'openid',
    'email',
    'profile',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/drive',      # Full access to Drive
    'https://www.googleapis.com/auth/documents',  # Full access to Docs
    'https://www.googleapis.com/auth/spreadsheets', # Full access to Sheets
    'https://www.googleapis.com/auth/calendar'
]

def authenticate_google_workspace():
    """Shows basic usage of the Gmail API to authenticate."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '../secrets/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds 

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_creds_from_refresh_token(refresh_token: str) -> Credentials:
    # 1. Define your OAuth variables
    # Best Practice: Load these from environment variables or a secret manager
    CLIENT_ID = settings.CLIENT_ID
    CLIENT_SECRET = settings.CLIENT_SECRET
    REFRESH_TOKEN = refresh_token
    
    # The standard Google endpoint for token exchanges
    TOKEN_URI = "https://oauth2.googleapis.com/token"

    # 2. Instantiate the Credentials object directly
    # We pass token=None because we don't have an active access token yet.
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    creds.refresh(Request())

    return creds

if __name__ == '__main__':

    creds = authenticate_google_workspace()
    # creds = get_creds_from_refresh_token(refresh_token=creds["refresh_token"])
