import os

# from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import Resource, build

# from liked_videos.logging import log

# load_dotenv()

API_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
OATH_CLIENT_SECRETS_FILE = os.getenv("OATH_CLIENT_SECRETS_FILE") or ""
OATH_TOKENS_FILE = os.getenv("OATH_TOKENS_FILE") or ""


def _fetch_new_oauth_tokens(
    client_secrets: str = OATH_CLIENT_SECRETS_FILE,
    scopes: list[str] = API_SCOPES,
) -> Credentials:
    """
    Fetches new Google Cloud OAuth tokens using client secrets file.

    OAuth client: https://console.cloud.google.com/apis/credentials?project=michael-uloth
    """
    assert client_secrets, "😱 No OAuth client secrets file provided"
    assert scopes, "😱 No OAuth scopes provided"
    print("🥁 Fetching new tokens...")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets, scopes)
        credentials = flow.run_local_server()
        return credentials
    except FileNotFoundError as e:
        print(f"😱 OAuth client secrets file not found: {e}")
        raise
    except Exception as e:
        print(f"😱 Unexpected error while fetching new OAuth tokens: {e}")
        raise


def _generate_oauth_credentials(tokens: str = OATH_TOKENS_FILE) -> Credentials:
    """
    Generates OAuth credentials from a saved, refreshed or new access token.
    """
    credentials = None

    print("🥁 Checking for saved tokens...")

    if os.path.exists(tokens):
        print("👍 Saved tokens found")
        try:
            print(f'🥁 Loading saved tokens from "{tokens}"...')
            credentials = Credentials.from_authorized_user_file(tokens)
        except Exception as e:
            print(f"😱 Error loading tokens: {e}")
            credentials = _fetch_new_oauth_tokens()
    else:
        print("👎 No saved tokens found")

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                print("🥁 Refreshing expired access token...")
                credentials.refresh(Request())
            except Exception as e:
                print(f"😱 Error refreshing token: {e}")
                credentials = _fetch_new_oauth_tokens()
        else:
            credentials = _fetch_new_oauth_tokens()

        print(f'🥁 Saving updated tokens to "{tokens}"...')
        with open(tokens, "w") as file:
            file.write(credentials.to_json())

    return credentials


def create_authenticated_client() -> Resource:
    """
    Creates an authenticated client to interact with the YouTube API.

    Corey Shafer tutorial: https://www.youtube.com/watch?v=vQQEaSnQ_bs
    Martin Heinz tutorial: https://martinheinz.dev/blog/84
    YouTube API docs: https://developers.google.com/youtube/v3/quickstart/python
    """
    credentials = _generate_oauth_credentials()
    return build(credentials=credentials, serviceName="youtube", version="v3")
