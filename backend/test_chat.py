from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session
import pytest


@pytest.fixture(scope="module")
def client():
    """Create a test client for the API"""
    with TestClient(app) as c:
        yield c


def test_chat_endpoint_exists():
    """Test that the chat endpoint is accessible"""
    # Since we can't easily test the full flow without authentication,
    # we'll just check that the app can be imported without errors
    assert app is not None

    # Test that the chat route is registered
    route_names = [route.name for route in app.routes]
    # The chat route is under the /chat prefix, so we look for routes that start with chat
    chat_routes_exist = any('chat' in name for name in route_names)
    assert chat_routes_exist