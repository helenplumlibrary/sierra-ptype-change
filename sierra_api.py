from requests.auth import HTTPBasicAuth
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

def sierra_session(client_id, client_secret, base_url):
    auth = HTTPBasicAuth(client_id, client_secret)
    client = BackendApplicationClient(client_id=client_id)
    session = OAuth2Session(client=client)
    session.fetch_token(token_url=base_url+'token', auth=auth)

    return session


