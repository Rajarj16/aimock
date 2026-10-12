import os, pytest, requests
from metrics import BASE
def pytest_addoption(parser):
    parser.addoption("--base-url", default=os.getenv("BASE_URL", BASE))
@pytest.fixture(scope="session")
def base_url(request):
    url = request.config.getoption("--base-url")
    try: requests.get(url, timeout=3)
    except Exception: pytest.exit(f"Search service not reachable at {url}. Start it first (see README).")
    return url
