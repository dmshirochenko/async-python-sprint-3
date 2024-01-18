import pytest
from dotenv import load_dotenv
import os

load_dotenv()

@pytest.fixture
def server_url():
    return os.getenv("SERVER_URL", "http://my-python-server:8000")
