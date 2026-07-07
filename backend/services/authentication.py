import os.path
import base64
import os

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from settings import settings

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
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
            possible_paths = [
                'credentials.json',
                '../credentials.json',
                'secrets/credentials.json',
                '../secrets/credentials.json'
            ]
            cred_path = None
            for p in possible_paths:
                if os.path.exists(p):
                    cred_path = p
                    break
            
            if cred_path:
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            elif settings.CLIENT_ID and settings.CLIENT_ID != "your_google_client_id_here" and settings.CLIENT_SECRET and settings.CLIENT_SECRET != "your_google_client_secret_here":
                client_config = {
                    "installed": {
                        "client_id": settings.CLIENT_ID,
                        "client_secret": settings.CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["http://localhost"]
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            else:
                raise Exception("Google OAuth credentials not found! Please download 'credentials.json' from your Google Cloud Console (APIs & Services -> Credentials -> OAuth 2.0 Client IDs for Desktop App) and place it in the 'backend' folder, OR set your CLIENT_ID and CLIENT_SECRET in 'backend/.env'.")
                
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
    if not CLIENT_ID or CLIENT_ID == "your_google_client_id_here":
        possible_paths = ['credentials.json', '../credentials.json', 'secrets/credentials.json', '../secrets/credentials.json']
        for p in possible_paths:
            if os.path.exists(p):
                import json
                with open(p, 'r') as f:
                    data = json.load(f)
                    cred_info = data.get('installed') or data.get('web') or {}
                    CLIENT_ID = cred_info.get('client_id', CLIENT_ID)
                    CLIENT_SECRET = cred_info.get('client_secret', CLIENT_SECRET)
                break

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
