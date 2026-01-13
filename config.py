import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Configuration for Rebel Operator application.

    NOTE: This file previously contained password-based credentials for
    browser automation, which has been removed for TOS compliance.

    All platform integrations now use official APIs with OAuth or API keys.
    See .env.example for the proper credential format.
    """
    pass
