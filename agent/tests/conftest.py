import pytest
from src.client import is_reachable
from config import settings as S

@pytest.fixture(scope="session", autouse=True)
def _service_up():
    if not is_reachable():
        pytest.exit(f"Search service not reachable at {S.BASE_URL}. Check .env / VPN / test environment.")

@pytest.fixture(scope="session")
def base_url():
    return S.BASE_URL
