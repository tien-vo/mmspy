__all__ = ["setup_request_session"]

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def setup_request_session(total=3, backoff_factor=1):
    session = requests.Session()
    retry_strategies = Retry(total=total, backoff_factor=backoff_factor)
    adapter = HTTPAdapter(max_retries=retry_strategies)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
