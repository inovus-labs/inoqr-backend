from authlib.integrations.starlette_client import OAuth
from app.config import config

oauth = OAuth(config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
    authorize_params={"code_challenge_method": "S256"},
)
oauth.register(
    name="github",
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email", "code_challenge_method": "S256"},
)
