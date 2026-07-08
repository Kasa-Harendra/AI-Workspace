from os import stat
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials 
import googleapiclient

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GMailClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: str = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token

        self.service = build("gmail", "v1", credentials= Credentials(
            token=access_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
            refresh_token=refresh_token
        ))

    @staticmethod
    def get_client_using_refresh_token(
        client_id: str,
        client_secret: str,
        refresh_token: str
    ) -> googleapiclient.discovery.Resource: 
        creds = Credentials(
            token=None,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
            refresh_token=refresh_token
        )

        creds.refresh(Request())

        return GMailClient(
            client_id=client_id,
            client_secret=client_secret,
            access_token=creds.token
        )

