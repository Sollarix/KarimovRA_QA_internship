import pytest
import requests


@pytest.fixture(scope="session")
def base_url() -> str:
    return "https://qa-internship.avito.com"


@pytest.fixture(scope="session")
def api_client(base_url: str):
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    yield session
    session.close()